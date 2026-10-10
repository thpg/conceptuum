"""Apply an explicit lexical-repair manifest atomically, with a full backup.

Only names, terms and cached definitions may change. Concept IDs, relation rows,
grammar and the genus closure must remain identical. Default mode is read-only.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apply_quality_batch import BatchEngine, dump_database, json_rows

TABLES = ('concept', 'concept_term', 'edge', 'relevant', 'universum', 'concept_path')


def fingerprint(rows):
    payload = sorted(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) for row in rows)
    return hashlib.sha256('\n'.join(payload).encode('utf-8')).hexdigest()


def snapshot(engine):
    # TIMESTAMP columns must serialize identically on local and hosted servers.
    engine.cur.execute("SET time_zone='+00:00'")
    output = {}
    for table in TABLES:
        engine.cur.execute('SELECT * FROM ' + table)
        output[table] = json_rows(engine.cur)
    return output


def validate(plan, before):
    if plan.get('schema') != 'conceptuum.lexical-repair.v1':
        raise ValueError('Unsupported manifest schema')
    if {table:fingerprint(rows) for table,rows in before.items()} != plan['before_table_sha256']:
        raise ValueError('Database changed since the manifest was reviewed')
    names = {row['dharma']:row['nama'] for row in before['concept']}
    terms = {(row['concept_id'],row['term'],row['lang']) for row in before['concept_term']}
    seen = set()
    for row in plan['renames']:
        if row['id'] in seen or names.get(row['id']) != row['before'] or not row['name'].strip():
            raise ValueError('Invalid or stale rename')
        seen.add(row['id'])
    additions = {(row['id'],row['term'],row['lang']) for row in plan['add_terms']}
    removals = {(row['id'],row['term'],row['lang']) for row in plan['remove_terms']}
    if not removals <= terms or additions & removals:
        raise ValueError('Invalid or stale term changes')
    if any(cid not in names or not term.strip() or lang not in ('ru','en') for cid,term,lang in additions | removals):
        raise ValueError('Invalid lexical change')
    final = (terms - removals) | additions
    for row in plan['renames']:
        if (row['id'],row['name'],'ru') not in final:
            raise ValueError('A replacement name must have a retained Russian term')


def apply(engine, plan, before):
    counts = Counter()
    for row in plan['renames']:
        engine.cur.execute('UPDATE concept SET nama=%s WHERE dharma=%s AND BINARY nama=%s', (row['name'],row['id'],row['before']))
        if engine.cur.rowcount != 1:
            raise ValueError('Rename precondition changed')
        counts['concepts_renamed'] += 1
    for row in plan['add_terms']:
        engine.cur.execute('INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)', (row['id'],row['term'],row['lang']))
        counts['terms_added'] += engine.cur.rowcount
    for row in plan['remove_terms']:
        engine.cur.execute('DELETE FROM concept_term WHERE concept_id=%s AND BINARY term=%s AND lang=%s', (row['id'],row['term'],row['lang']))
        if engine.cur.rowcount != 1:
            raise ValueError('Term precondition changed')
        counts['terms_removed'] += 1
    engine.reload()
    engine.define()  # BatchEngine suppresses the engine's internal commits.
    after = snapshot(engine)
    for table in ('edge','relevant','universum','concept_path'):
        if fingerprint(before[table]) != fingerprint(after[table]):
            raise ValueError('Unexpected structural change: ' + table)
    rename = {row['id']:row['name'] for row in plan['renames']}
    expected = {row['dharma']:dict(row, nama=rename.get(row['dharma'],row['nama'])) for row in before['concept']}
    if len(expected) != len(after['concept']):
        raise ValueError('Concept identities changed')
    for row in after['concept']:
        old = dict(expected[row['dharma']]); actual = dict(row)
        old.pop('defin'); actual.pop('defin')
        if old != actual:
            raise ValueError('Unexpected concept change')
    terms_before = {(r['concept_id'],r['term'],r['lang']) for r in before['concept_term']}
    expected_terms = (terms_before - {(r['id'],r['term'],r['lang']) for r in plan['remove_terms']}) | {(r['id'],r['term'],r['lang']) for r in plan['add_terms']}
    actual_terms = {(r['concept_id'],r['term'],r['lang']) for r in after['concept_term']}
    if expected_terms != actual_terms:
        raise ValueError('Unexpected term change or collation collision')
    return counts, after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--backup-dir', type=Path)
    args = parser.parse_args()
    plan = json.loads(args.manifest.read_text(encoding='utf-8'))
    engine = BatchEngine()
    try:
        before = snapshot(engine)
        validate(plan, before)
        if not args.apply:
            print(json.dumps(dict(valid=True, mode='read-only', renames=len(plan['renames']), remove_terms=len(plan['remove_terms']), add_terms=len(plan['add_terms']))))
            return
        if args.backup_dir is None:
            raise ValueError('--backup-dir is required when applying')
        directory = args.backup_dir.resolve()
        directory.mkdir(parents=True, exist_ok=True)
        if (directory/'applied.json').exists():
            raise ValueError('This backup directory already contains an applied receipt')
        dump_database(directory/'before.sql')
        (directory/'before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
        engine.conn.rollback()
        engine.conn.begin()
        # Lock every source row before validating the reviewed snapshot again.
        for table in TABLES:
            engine.cur.execute('SELECT * FROM ' + table + ' FOR UPDATE')
            engine.cur.fetchall()
        validate(plan, snapshot(engine))
        counts, after = apply(engine, plan, before)
        (directory/'after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
        receipt = dict(data_revision=plan['data_revision'], changes=dict(counts), counts={k:len(v) for k,v in after.items()},
                       table_sha256={k:fingerprint(v) for k,v in after.items()}, structure_unchanged=True,
                       manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest())
        engine.conn.commit()
        (directory/'applied.json').write_text(json.dumps(receipt, indent=2)+'\n',encoding='utf-8')
        print(json.dumps(receipt, indent=2))
    except Exception:
        engine.conn.rollback()
        raise
    finally:
        engine.close()


if __name__ == '__main__':
    main()
