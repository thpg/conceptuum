"""QA semantics, source fidelity and export behavior on a synthetic graph."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_concept_algebra import fixture
from concept_algebra import AlgebraError, ConceptAlgebra, ConceptGraph
from concept_algebra.qa import QuestionGenerator, Rejected, checked_options, graph_fingerprint
from concept_algebra.qa_check import verify_record
from concept_algebra.qa_format import messages, wording
from concept_algebra.web import AlgebraService


class QuestionTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()
        self.graph = ConceptGraph(self.data)
        self.generator = QuestionGenerator(self.graph, policy={})

    def property(self, subject, distractor=None):
        if distractor is None and self.graph.fact(subject, '22', 9).state == 'unknown':
            distractor = next(e.id for e in self.graph.edges if (e.subject, e.code, e.target) == (3, '22', 9))
        return self.generator.make(('property', dict(a=subject, relation='22', target=9, distractor_edge=distractor), None, []))

    def test_four_states_override_and_incomparable_conflict(self):
        for subject, state in [(3, 'positive'), (4, 'negative'), (10, 'unknown'), (15, 'conflict'), (20, 'positive')]:
            with self.subTest(subject=subject):
                record = self.property(subject)
                self.assertEqual(record['expected']['value'], state)
                self.assertEqual(verify_record(record, self.graph), [])
        self.assertTrue(self.property(4)['expected']['overridden_ids'])
        self.assertEqual(len(self.property(15)['expected']['evidence_ids']), 2)
        self.assertEqual(len(self.property(20)['expected']['overridden_ids']), 2)

    def test_property_does_not_inherit_upward_or_through_coextension(self):
        bird_flight = next(e.id for e in self.graph.edges if (e.subject, e.code, e.target) == (3, '22', 9))
        record = self.property(2, bird_flight)
        self.assertEqual(record['expected']['value'], 'unknown')
        self.assertIn('not an explicit negative', record['answer'])
        self.assertEqual(self.property(14)['expected']['value'], 'unknown')

    def test_domain_property_optimization_matches_all_four_full_sets(self):
        algebra = ConceptAlgebra(self.graph)
        for selector in ('has', 'lacks', 'unknown', 'conflicts'):
            full = set(algebra.evaluate(f'{selector}(22, #9)').ids)
            for cid in (3, 4, 10, 15, 20):
                restricted = algebra.evaluate(f'{selector}(22, #9)', within=f'exact(#{cid})')
                self.assertEqual(set(restricted.ids), full & {cid})

    def test_ancestry_in_both_directions_and_tampered_path(self):
        edges = [e for e in self.graph.edges if e.code == '14' and (e.subject, e.target) in {(4, 3), (3, 2)}]
        for a, b, expected in [(4, 2, True), (2, 4, False)]:
            record = self.generator.make(('ancestry', dict(a=a, b=b, path=[4, 3, 2]), edges, []))
            self.assertIs(record['expected']['value'], expected)
            broken = deepcopy(record)
            broken['spec']['path'] = [4, 7, 2]
            self.assertIn('malformed_record', verify_record(broken))

    def test_overlap_multiple_parents_and_finite_catalog_difference(self):
        record = self.generator.make(('intersection', dict(a=3, b=16), None, None))
        self.assertEqual(record['expected']['value'], [15, 20])
        difference = self.generator.make(('difference', dict(a=3, b=16), None, None))
        self.assertEqual(difference['expected']['value'], [3, 4, 5, 14])
        empty = self.generator.make(('intersection', dict(a=3, b=7), None, None))
        self.assertEqual(empty['expected']['value'], [])
        self.assertIn('does not prove', empty['answer'])

    def test_count_has_distractors_and_deduplicates_overlap(self):
        record = self.generator.make(('count', dict(a=3, b=16), None, None))
        self.assertEqual(record['expected']['value'], 7)
        self.assertGreater(len(record['grounding']['domain']), 7)

    def test_shared_genus_neither_proves_disjointness_nor_reverse_inclusion(self):
        edges = [e for e in self.graph.edges if e.code == '14' and e.subject in (4, 5)]
        for name, value in [('siblings_disjoint', 'not_entailed'), ('shared_membership', 'entailed')]:
            record = self.generator.make(('inference', dict(a=4, b=5, parent=3, inference=name), edges, []))
            self.assertEqual(record['expected']['value'], value)
        reverse = self.generator.make(('inference', dict(a=4, b=3, inference='reverse_genus'), edges[:1], []))
        self.assertEqual(reverse['expected']['value'], 'not_entailed')

    def test_changed_answer_fact_and_missing_override_are_rejected(self):
        record = self.property(4)
        changed = deepcopy(record)
        changed['expected']['value'] = 'positive'
        self.assertIn('answer_mismatch', verify_record(changed, self.graph))
        changed = deepcopy(record)
        changed['grounding']['facts'][-1]['strength'] = 27
        self.assertIn('unsupported_fact', verify_record(changed, self.graph))
        changed = deepcopy(record)
        missing = changed['expected']['overridden_ids'][0]
        changed['grounding']['facts'] = [e for e in changed['grounding']['facts'] if e['id'] != missing]
        self.assertIn('incomplete_property_evidence', verify_record(changed, self.graph))

    def test_bad_types_duplicate_domain_and_cycles_are_rejected(self):
        record = self.generator.make(('intersection', dict(a=3, b=16), None, None))
        bad = deepcopy(record)
        bad['grounding']['domain'].append(bad['grounding']['domain'][0])
        self.assertIn('invalid_domain', verify_record(bad))
        bad = deepcopy(record)
        bad['grounding']['facts'][0]['strength'] = -1
        self.assertIn('invalid_fact', verify_record(bad))
        bad = deepcopy(record)
        bad['grounding']['facts'].append(dict(id=999, subject=2, relation='14', target=3, strength=None))
        self.assertIn('cyclic_genus', verify_record(bad))

    def test_policy_excludes_assertions_including_inherited_evidence(self):
        policy = dict(excluded_assertions=[dict(subject=3, relation='22', target=9, strength=80)])
        self.generator = QuestionGenerator(self.graph, policy=policy)
        with self.assertRaisesRegex(Rejected, 'reviewed_assertion_exclusion'):
            self.property(4)
        self.assertNotEqual(self.generator.source['qa_policy_sha256'], QuestionGenerator(self.graph, policy={}).source['qa_policy_sha256'])

    def test_source_fingerprint_includes_terms_and_context(self):
        original = graph_fingerprint(self.graph)
        self.data['concept_term'][0]['term'] = 'changed'
        self.assertNotEqual(original, graph_fingerprint(ConceptGraph(self.data)))
        self.assertNotEqual(original, graph_fingerprint(ConceptGraph(fixture(), context=3)))

    def test_reproducible_unique_output_and_no_fake_padding(self):
        one = self.generator.generate(30, seed=11)
        two = QuestionGenerator(self.graph, policy={}).generate(30, seed=11)
        self.assertEqual(one, two)
        self.assertEqual(len({r['question'] for r in one['records']}), len(one['records']))
        self.assertNotEqual(one['records'], self.generator.generate(30, seed=12)['records'])
        empty = QuestionGenerator(ConceptGraph(fixture(), context=3), policy={}).generate(50)
        self.assertFalse(empty['report']['complete'])
        self.assertLess(empty['report']['generated'], 50)

    def test_russian_templates_and_exact_language_labels(self):
        translations = {1:'сущность', 2:'животное', 3:'птица', 4:'пингвин', 9:'полёт'}
        self.data['concept_term'] += [dict(concept_id=cid, term=name, lang='ru') for cid, name in translations.items()]
        self.generator = QuestionGenerator(ConceptGraph(self.data), 'ru', policy={})
        record = self.property(4)
        self.assertIn('Отрицательный', record['answer'])
        self.assertIn('полёт', record['question'])
        self.assertEqual(verify_record(record, self.generator.graph), [])

    def test_legacy_pseudo_english_terms_do_not_admit_artificial_russian_names(self):
        self.data['concept_term'] = [t for t in self.data['concept_term'] if t['concept_id'] != 4]
        self.data['concept_term'] += [dict(concept_id=4, term='ВЫЧИСЛЯТЬ', lang='en'), dict(concept_id=4, term='вычисляние', lang='ru')]
        for language in ('en','ru'):
            generator = QuestionGenerator(ConceptGraph(self.data), language, policy=dict(require_valid_english_label=True))
            with self.assertRaisesRegex(Rejected, 'missing_or_unsuitable_label'):
                generator.label(4)

    def test_web_limits_filters_and_invalid_input_before_loading(self):
        calls = []
        service = AlgebraService(loader=lambda context: calls.append(context) or self.graph)
        for request in [{'count':51}, {'count':True}, {'seed':-1}, {'root':False}, {'tasks':['property','property']}, {'lang':'xx'}, {'sql':'DROP'}]:
            with self.subTest(request=request), self.assertRaises(AlgebraError):
                service.generate(request)
        self.assertEqual(calls, [])
        result = service.generate(dict(count=4, tasks=['property']))
        self.assertEqual(len(result['records']), 4)
        self.assertEqual({r['task'] for r in result['records']}, {'property'})

    def test_cli_exports_messages_only_and_protects_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            snapshot, annotated, sft, report = [path / name for name in ('graph.json','qa.jsonl','sft.jsonl','report.json')]
            snapshot.write_text(json.dumps(self.data), encoding='utf-8')
            args = [sys.executable, '-m', 'concept_algebra.qa', '--snapshot', str(snapshot), '--count','12', '--output',str(annotated), '--messages-output',str(sft), '--report',str(report)]
            result = subprocess.run(args, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
            records = [json.loads(line) for line in annotated.read_text(encoding='utf-8').splitlines()]
            chats = [json.loads(line) for line in sft.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(records), 12)
            for record, chat in zip(records, chats):
                self.assertEqual(chat, dict(messages=record['messages']))
                self.assertEqual([m['role'] for m in chat['messages']], ['system','user','assistant'])
                self.assertEqual(chat['messages'][-1]['content'], record['answer'])
                self.assertEqual(verify_record(record, self.graph), [])
            self.assertEqual(subprocess.run(args, capture_output=True).returncode, 2)
            overwrite = args[:args.index('--output')] + ['--output', str(snapshot), '--force']
            self.assertEqual(subprocess.run(overwrite, capture_output=True).returncode, 2)


if __name__ == '__main__':
    unittest.main()
