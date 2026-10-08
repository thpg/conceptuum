"""Apply an explicitly reviewed data batch; dry-run (with rollback) by default.

python tools/apply_quality_batch.py tools/quality_20261008.json [--apply]
All new edges pass JnanaEngine.propose. The batch, closure and definitions
share one transaction. Applying requires a full SQL backup first.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jnana_engine import DB, JnanaEngine
from audit_quality import audit
from reviewed_merges import (grammar_changes, plan_merge_routes, validate_edge_reuse,
                             validate_reviewed_archive)


class BatchEngine(JnanaEngine):
    _edge_reload_only = False

    def reload(self):
        if not self._edge_reload_only:
            return super().reload()
        # Once concepts and terms are prepared, the repair phase changes only
        # edges. Keep grammar/lexical indexes, refresh the live DAG used by
        # propose, and verify this cache against a full reload before saving.
        self.cur.execute("SELECT dh1, dh2, kod, strength, status, id FROM edge")
        self.edges = self.cur.fetchall()
        self.parents = defaultdict(list)
        self.children_map = defaultdict(list)
        self.parent = {}
        self.cur.execute("SELECT dh1, dh2, universum_id FROM edge WHERE kod='14' AND status='ok'")
        for a, b, u in self.cur.fetchall():
            self.parents[a].append((b, u))
            self.children_map[b].append(a)
        self.children_map = defaultdict(list, {
            b: list(dict.fromkeys(kids)) for b, kids in self.children_map.items()})
        for a, pairs in self.parents.items():
            home = self.concept_u.get(a)
            self.parent[a] = next((b for b, u in pairs if u == home), pairs[0][0])
        return self

    def commit(self):
        # rebuild/define normally commit internally. Only main may commit here.
        self.reload()


def dump_database(path):
    executable = (shutil.which("mariadb-dump") or shutil.which("mysqldump"))
    if not executable:
        for version in ("10.4", "5.5"):
            candidate = Path("C:/Program Files") / ("MariaDB " + version) / "bin/mysqldump.exe"
            if candidate.exists():
                executable = str(candidate)
                break
    if not executable:
        raise RuntimeError("mysqldump is required before applying this batch")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError("Refusing to overwrite backup: " + str(path))
    environment = dict(os.environ, MYSQL_PWD=DB["password"])
    subprocess.run([
        executable, "--host=" + DB["host"], "--port=" + str(DB.get("port", 3306)),
        "--user=" + DB["user"], "--single-transaction", "--routines", "--triggers",
        "--events", "--default-character-set=utf8mb4", "--hex-blob",
        "--result-file=" + str(path), "--databases", DB["database"],
    ], env=environment, check=True, capture_output=True)
    if path.stat().st_size == 0:
        raise RuntimeError("Backup is empty")


def json_rows(cur):
    """Lossless manifest representation of the current query's SQL rows."""
    columns = [column[0] for column in cur.description]
    return json.loads(json.dumps([dict(zip(columns, row)) for row in cur.fetchall()],
                                 ensure_ascii=False, default=str))


def validate_leaf_archive(item, concept, terms, edges):
    """Only explicitly archived, unconnected lexical duplicates may be merged.

    A source with children, facts, negations, or rejected history needs a
    different review. Never silently retarget or discard any such evidence.
    """
    src = item["source_id"]
    archive = item["archive"]
    if src == item["target_id"] or concept.get("dharma") != src:
        raise ValueError("Invalid leaf merge identity")
    if concept != archive["concept"]:
        raise ValueError("Leaf concept changed since review: " + str(src))
    order = lambda rows: sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))
    if order(terms) != order(archive["terms"]):
        raise ValueError("Leaf terms changed since review: " + str(src))
    if order(edges) != order(archive["edges"]):
        raise ValueError("Leaf edges changed since review: " + str(src))
    if not edges or any(row["dh1"] != src or row["dh2"] == src or row["kod"] != "14"
                        or row["status"] != "ok" or row["strength"] == 0 for row in edges):
        raise ValueError("Merge source is not a leaf with only accepted positive genera: " + str(src))


def apply_batch(eng, plan):
    counts = Counter()
    touched = set()
    withdrawn_subjects = set()
    created = {}
    source = plan["source"]

    def resolve(ref):
        if isinstance(ref, int):
            if ref not in eng.names:
                raise ValueError("Missing concept: " + str(ref))
            return ref
        return created[ref]

    def term(cid, text, lang):
        if (text, lang) in eng.terms_of[cid]:
            return
        eng.cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
                        (cid, text, lang))
        counts["terms_added"] += eng.cur.rowcount
        eng.terms_of[cid].append((text, lang))

    def edge(a, kod, b, reason, strength=None, universum_id=None):
        a, b = resolve(a), resolve(b)
        kod = str(kod)
        if a == b:
            raise ValueError("Self-loop in reviewed batch")
        if eng.rules[kod]["sym"] and a > b:
            a, b = b, a
        uid = universum_id if universum_id is not None else eng.concept_u[a]
        eng.cur.execute(
            "SELECT id,status,strength FROM edge WHERE dh1=%s AND dh2=%s AND kod=%s AND universum_id=%s",
            (a, b, kod, uid))
        existing = eng.cur.fetchone()
        if existing:
            validate_edge_reuse(existing, strength)
            counts["existing_edges_reused"] += 1
            return
        eid, message = eng.propose(a, kod, b, strength=strength, universum_id=uid,
                                   source=source, rationale=reason, auto=True)
        if eid is None:
            raise ValueError(message)
        counts["edges_added"] += 1
        touched.add(a)

    for item in plan.get("grammar_repairs", []):
        old, new = item["before"], item["after"]
        changes = grammar_changes(old, new)
        eng.cur.execute("SELECT * FROM relevant WHERE kod=%s FOR UPDATE", (old["kod"],))
        current = json_rows(eng.cur)
        if current == [new]:
            counts["existing_grammar_repairs_reused"] += 1
            continue
        if current != [old]:
            raise ValueError("Grammar changed since review: " + old["kod"])
        for key, value in changes.items():
            if key.startswith("sig_") and value is not None:
                resolve(value)
        columns = sorted(changes)
        eng.cur.execute("UPDATE relevant SET " + ",".join(k + "=%s" for k in columns) + " WHERE kod=%s",
                        [changes[k] for k in columns] + [old["kod"]])
        counts["grammar_rows_repaired"] += 1
    if plan.get("grammar_repairs"):
        eng.reload()

    merges = plan.get("leaf_merges", [])
    merge_sources = {item["source_id"] for item in merges}
    if len(merge_sources) != len(merges) or any(item["target_id"] in merge_sources for item in merges):
        raise ValueError("Leaf merges must have unique sources and no merge chains")
    rename_targets = {item["id"]: item["name"] for item in plan.get("renames", [])}
    for item in merges:
        src, dst = item["source_id"], resolve(item["target_id"])
        if eng.names[dst] not in {item["target_name"], rename_targets.get(dst)}:
            raise ValueError("Merge destination sense changed: " + str(dst))
        if src not in eng.names:
            # A replay must find the intended surviving lexical forms.
            if not all((text, lang) in eng.terms_of[dst] for text, lang in item["retained_terms"]):
                raise ValueError("Missing merge source without its surviving terms: " + str(src))
            counts["existing_merges_reused"] += 1
            continue
        eng.cur.execute("SELECT * FROM concept WHERE dharma=%s FOR UPDATE", (src,))
        concept = json_rows(eng.cur)
        eng.cur.execute("SELECT * FROM concept_term WHERE concept_id=%s FOR UPDATE", (src,))
        source_terms = json_rows(eng.cur)
        eng.cur.execute("SELECT * FROM edge WHERE dh1=%s OR dh2=%s FOR UPDATE", (src, src))
        source_edges = json_rows(eng.cur)
        if len(concept) != 1:
            raise ValueError("Missing reviewed merge source: " + str(src))
        validate_leaf_archive(item, concept[0], source_terms, source_edges)
        for text, lang in item["retained_terms"]:
            term(dst, text, lang)
        # Delete only rows just matched to the full archive in the manifest.
        for row in source_edges:
            eng.cur.execute("DELETE FROM edge WHERE id=%s", (row["id"],))
            counts["leaf_genus_edges_removed"] += eng.cur.rowcount
        for row in source_terms:
            eng.cur.execute("DELETE FROM concept_term WHERE concept_id=%s AND term=%s AND lang=%s",
                            (src, row["term"], row["lang"]))
            counts["leaf_terms_removed"] += eng.cur.rowcount
        eng.cur.execute("SELECT COUNT(*) FROM concept_term WHERE concept_id=%s", (src,))
        if eng.cur.fetchone()[0]:
            raise ValueError("Unexpected terms on merge source: " + str(src))
        eng.cur.execute("DELETE FROM concept_path WHERE ancestor=%s OR descendant=%s", (src, src))
        eng.cur.execute("DELETE FROM concept WHERE dharma=%s", (src,))
        if eng.cur.rowcount != 1:
            raise ValueError("Leaf deletion failed: " + str(src))
        counts["leaf_concepts_merged"] += 1
        del eng.names[src]
    if merges:
        eng.reload()
        print("Reviewed lexical leaf merges:", len(merges), flush=True)

    for item in plan.get("renames", []):
        cid = item["id"]
        if eng.names.get(cid) == item["before"]:
            # Renaming already updates names in memory. Rebuild the lexical
            # indexes once after this loop, before creating any new concepts.
            ok, message = eng.rename_concept(cid, item["name"], reload=False)
            if not ok:
                raise ValueError(message)
            counts["concepts_renamed"] += 1
        elif eng.names.get(cid) != item["name"]:
            raise ValueError("Rename precondition failed: " + str(item))
        for text, lang in item.get("terms", []):
            term(cid, text, lang)

    if plan.get("renames"):
        eng.reload()

    for concept_number, item in enumerate(plan.get("concepts", []), 1):
        matching = [cid for cid, name in eng.names.items()
                    if name == item["name"] and eng.concept_u[cid] == item.get("universum_id", 1)]
        parent = resolve(item["parent"])
        if matching:
            if len(matching) != 1 or not eng.in_subtree(matching[0], parent):
                raise ValueError("Existing concept has a different sense/genus: " + item["name"])
            cid = matching[0]
        else:
            # add_concept inserts its initial genus directly; use propose for
            # this edge too, so even new nodes follow the relation grammar.
            cid, message = eng.add_concept(item["name"], parent, lang="ru",
                                           universum_id=item.get("universum_id", 1),
                                           auto=False)
            if cid is None:
                raise ValueError(message)
            eng.cur.execute("DELETE FROM edge WHERE dh1=%s AND kod='14' AND status='candidate'",
                            (cid,))
            # add_concept has loaded the new node and its lexical data. Only
            # the temporary genus changes until the next concept is created.
            eng._edge_reload_only = True
            eng.reload()
            edge(cid, "14", parent, item["reason"])
            eng._edge_reload_only = False
            eng.set_processed(cid, 1)
            counts["concepts_added"] += 1
        created[item["key"]] = cid
        for text, lang in item["terms"]:
            term(cid, text, lang)
        if concept_number % 10 == 0:
            print("Concepts prepared:", concept_number, "/", len(plan["concepts"]), flush=True)

    for item in plan.get("terms", []):
        cid = resolve(item["id"])
        if eng.names[cid] != item["name"]:
            raise ValueError("Term sense precondition failed: " + str(item))
        for text, lang in item["terms"]:
            term(cid, text, lang)
    for item in plan.get("remove_terms", []):
        cid = resolve(item["id"])
        eng.cur.execute("DELETE FROM concept_term WHERE concept_id=%s AND term=%s AND lang=%s",
                        (cid, item["term"], item["lang"]))
        counts["terms_removed"] += eng.cur.rowcount

    eng.reload()
    eng._edge_reload_only = True
    # Connect previously isolated anchors before validating their descendants.
    # These additions use the same grammar and transaction as all other edges.
    for item in plan.get("initial_edges", []):
        edge(item["subject"], item["kod"], item["object"], item["reason"],
             item.get("strength"), item.get("universum_id"))
    print("Terms and new concepts prepared; validating reviewed repairs...", flush=True)
    for repair_number, item in enumerate(plan["repairs"], 1):
        expected = item["before"]
        eng.cur.execute("SELECT dh1,kod,dh2,universum_id,status,rationale FROM edge WHERE id=%s FOR UPDATE",
                        (item["id"],))
        row = eng.cur.fetchone()
        if not row or list(row[:4]) != expected:
            raise ValueError("Edge precondition failed: " + str(item["id"]))
        if row[4] == "ok":
            reason = ((row[5] or "") + " | " + source + ": " + item["reason"])[-500:]
            eng.cur.execute("UPDATE edge SET status='rejected',rationale=%s WHERE id=%s",
                            (reason, item["id"]))
            counts["edges_rejected"] += 1
            if row[1] == "14":
                eng.reload()  # taxonomy validation must see the removed parent
        elif row[4] != "rejected" or source not in (row[5] or ""):
            raise ValueError("Unexpected edge status: " + str(item["id"]))
        for replacement in item.get("replacements", []):
            edge(*replacement[:3], reason=item["reason"],
                 strength=replacement[3] if len(replacement) > 3 else None,
                 universum_id=replacement[4] if len(replacement) > 4 else None)
        if repair_number % 25 == 0:
            print("Reviewed repairs:", repair_number, "/", len(plan["repairs"]), flush=True)

    print("Validating additional properties...", flush=True)
    for item in plan["edges"]:
        edge(item["subject"], item["kod"], item["object"], item["reason"],
             item.get("strength"), item.get("universum_id"))

    # Sources may share an edge (a child and its parent can both be duplicates).
    # Validate every snapshot first, then remove each old row only once.
    reviewed = plan.get("reviewed_merges", [])
    routes = plan_merge_routes(reviewed, plan.get("merge_routes", []), resolve, eng.rules)
    present = {m["source_id"] for m in reviewed if m["source_id"] in eng.names}
    if present and len(present) != len(reviewed):
        raise ValueError("Partially missing reviewed merge batch")
    for item in reviewed:
        src, dst = item["source_id"], resolve(item["target_id"])
        if eng.names[dst] not in {item["target_name"], rename_targets.get(dst)}:
            raise ValueError("Reviewed merge destination sense changed: " + str(dst))
        if not present:
            if not all((t, l) in eng.terms_of[dst] for t, l in item["retained_terms"]):
                raise ValueError("Reviewed merge lost its surviving terms: " + str(src))
            counts["existing_reviewed_merges_reused"] += 1
            continue
        eng.cur.execute("SELECT * FROM concept WHERE dharma=%s FOR UPDATE", (src,))
        concepts = json_rows(eng.cur)
        eng.cur.execute("SELECT * FROM concept_term WHERE concept_id=%s FOR UPDATE", (src,))
        terms = json_rows(eng.cur)
        eng.cur.execute("SELECT * FROM edge WHERE dh1=%s OR dh2=%s FOR UPDATE", (src, src))
        edges = json_rows(eng.cur)
        if len(concepts) != 1:
            raise ValueError("Missing reviewed concept: " + str(src))
        validate_reviewed_archive(item, concepts[0], terms, edges)
    if present:
        for route in routes:
            eng.cur.execute("DELETE FROM edge WHERE id=%s", (route["old"]["id"],))
            counts["archived_merge_edges_removed"] += eng.cur.rowcount
        for item in reviewed:
            src, dst = item["source_id"], item["target_id"]
            for t, lang in item["retained_terms"]:
                term(dst, t, lang)
            eng.cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (src,))
            counts["archived_merge_terms_removed"] += eng.cur.rowcount
            eng.cur.execute("DELETE FROM concept_path WHERE ancestor=%s OR descendant=%s", (src, src))
            eng.cur.execute("DELETE FROM concept WHERE dharma=%s", (src,))
            if eng.cur.rowcount != 1:
                raise ValueError("Reviewed concept deletion failed: " + str(src))
            counts["reviewed_concepts_merged"] += 1
        eng._edge_reload_only = False
        eng.reload()
        eng._edge_reload_only = True
        for route in routes:
            old = route["old"]
            reason = ("Archived edge #" + str(old["id"]) + " (" + str(old["source"]) + "): " +
                      route["reason"] + " | " + (old.get("rationale") or ""))[:500]
            edge(route["subject"], route["kod"], route["object"], reason,
                 route["strength"], route["universum_id"])

    # A revised manifest may withdraw its own earlier additions. On a fresh
    # database these rows do not exist; never retire another source's fact.
    for item in plan.get("retired_additions", []):
        a, b = resolve(item["subject"]), resolve(item["object"])
        eng.cur.execute(
            "SELECT id,status,source FROM edge WHERE dh1=%s AND kod=%s AND dh2=%s AND universum_id=%s",
            (a, item["kod"], b, eng.concept_u[a]))
        row = eng.cur.fetchone()
        if not row:
            continue
        if row[2] != source:
            raise ValueError("Cannot retire another source's addition: " + str(row[0]))
        if row[1] == "ok":
            eng.cur.execute("UPDATE edge SET status='rejected',rationale=%s WHERE id=%s",
                            (source + ": " + item["reason"], row[0]))
            counts["own_additions_withdrawn"] += 1
            touched.add(a)
            withdrawn_subjects.add(a)

    eng.reload()
    cached = {key: getattr(eng, key) for key in ("edges", "parents", "children_map", "parent")}
    eng._edge_reload_only = False
    eng.reload()
    if any(cached[key] != getattr(eng, key) for key in cached):
        raise ValueError("Batch graph cache differs from a full engine reload")
    accepted = [e for e in eng.edges if e[4] == "ok"]
    specific = {a for a, b, k, s, st, eid in accepted if k in eng.PROC_SPEC}
    parallel = {a for a, b, k, s, st, eid in accepted if k in eng.PROC_PARA}
    for cid in touched & specific:
        eng.cur.execute("SELECT processed FROM concept WHERE dharma=%s", (cid,))
        current = eng.cur.fetchone()[0] or 0
        level = 3 if cid in parallel else 2
        if current < level or (cid in withdrawn_subjects and current > level):
            eng.set_processed(cid, level)
            counts["processed_raised" if current < level else "processed_corrected"] += 1
    print("Rebuilding closure and definitions in the same transaction...", flush=True)
    eng.rebuild()
    eng.define()
    return dict(counts), created


def check_result(before, after, eng, plan, created):
    for key in ("self_loops", "taxonomy_cycles", "dangling_edges", "signature_violations",
                "deprecated_codes", "invalid_strength"):
        old = {(row["id"], row.get("side")) for row in before["issues"].get(key, [])}
        new = {(row["id"], row.get("side")) for row in after["issues"].get(key, [])}
        if new - old:
            raise ValueError("Batch introduced " + key + ": " + str(new - old))
    for key in ("missing_ru", "missing_en", "without_latin_en"):
        old = {row["id"] for row in before["issues"].get(key, [])}
        new = {row["id"] for row in after["issues"].get(key, [])}
        if new - old:
            raise ValueError("Batch introduced " + key + ": " + str(new - old))
    old = {(row["id"], term) for row in before["issues"].get("cyrillic_only_en", [])
           for term in row["terms"]}
    new = {(row["id"], term) for row in after["issues"].get("cyrillic_only_en", [])
           for term in row["terms"]}
    if new - old:
        raise ValueError("Batch introduced Cyrillic-only English terms: " + str(new - old))
    for item in plan.get("leaf_merges", []) + plan.get("reviewed_merges", []):
        src, dst = item["source_id"], item["target_id"]
        if src in eng.names or any(src in e[:2] for e in eng.edges) or eng.terms_of.get(src):
            raise ValueError("Merged leaf still referenced: " + str(src))
        if dst not in eng.names or not all((t, lang) in eng.terms_of[dst]
                                          for t, lang in item["retained_terms"]):
            raise ValueError("Merged forms lost their destination: " + str(dst))
    for item in plan.get("grammar_repairs", []):
        eng.cur.execute("SELECT * FROM relevant WHERE kod=%s", (item["after"]["kod"],))
        if json_rows(eng.cur) != [item["after"]]:
            raise ValueError("Grammar repair postcondition failed")
    if plan.get("reviewed_merges"):
        resolve = lambda ref: created.get(ref, ref)
        for route in plan_merge_routes(plan["reviewed_merges"], plan["merge_routes"], resolve, eng.rules):
            eng.cur.execute("SELECT status,strength FROM edge WHERE dh1=%s AND kod=%s AND dh2=%s AND universum_id=%s",
                            (route["subject"], route["kod"], route["object"], route["universum_id"]))
            if eng.cur.fetchall() != (("ok", route["strength"]),):
                raise ValueError("Merged edge lost its relation, degree or universe: " + str(route["old"]["id"]))
    for item in plan.get("checks", []):
        a = created.get(item["subject"], item["subject"])
        b = created.get(item["object"], item["object"])
        matches = [e for e in eng.edges if e[0] == a and e[1] == b
                   and e[2] == item["kod"] and e[4] == "ok"]
        if bool(matches) != item["present"]:
            raise ValueError("Semantic regression: " + str(item))
        if "strength" in item and not any(e[3] == item["strength"] for e in matches):
            raise ValueError("Strength regression: " + str(item))
    for item in plan.get("subtree_checks", []):
        cid = created.get(item["subject"], item["subject"])
        ancestor = created.get(item["ancestor"], item["ancestor"])
        if eng.in_subtree(cid, ancestor) != item["present"]:
            raise ValueError("Sense/genus regression: " + str(item))
    for item in plan.get("term_checks", []):
        cid = created.get(item["subject"], item["subject"])
        if ((item["term"], item["lang"]) in eng.terms_of[cid]) != item["present"]:
            raise ValueError("Term sense regression: " + str(item))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    batch_bytes = args.batch.read_bytes()
    plan = json.loads(batch_bytes.decode("utf-8"))
    backup = None
    if args.apply:
        backup = ROOT.parent / "conceptuum-backups" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-before-quality.sql")
        dump_database(backup)
        print("Backup:", backup, flush=True)
    # Persist definitions from canonical concept labels. A language override
    # may choose an inflected or legacy misspelled alias as the display name.
    eng = BatchEngine()
    try:
        before = audit(eng)
        negative_edges = {e[5] for e in eng.edges if e[3] == 0 and e[4] == "ok"}
        counts, created = apply_batch(eng, plan)
        after = audit(eng)
        check_result(before, after, eng, plan, created)
        if not negative_edges <= {e[5] for e in eng.edges if e[3] == 0 and e[4] == "ok"}:
            raise ValueError("An existing explicit negation was lost")
        if args.apply:
            eng.conn.commit()
        else:
            eng.conn.rollback()
        report = dict(applied=args.apply, backup=str(backup) if backup else None,
                      batch_sha256=hashlib.sha256(batch_bytes).hexdigest(),
                      operations=counts, created=created,
                      before=before["metrics"], after=after["metrics"],
                      remaining_issues=after["issues"])
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
        print(json.dumps({key: report[key] for key in ("applied", "operations", "created", "after")},
                         ensure_ascii=False, indent=2))
    except BaseException:
        eng.conn.rollback()
        raise
    finally:
        eng.close()


if __name__ == "__main__":
    main()
