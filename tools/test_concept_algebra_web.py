"""API behavior and transport checks using a synthetic graph, without MariaDB."""
from http.client import HTTPConnection
from http.server import HTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest

from test_concept_algebra import fixture
from concept_algebra import AlgebraError, ConceptAlgebra, ConceptGraph
from concept_algebra.web import AlgebraService, MAX_BODY, checked_request, error_document, make_handler


class AlgebraWebTests(unittest.TestCase):
    def setUp(self):
        self.loaded = []

        def loader(context):
            self.loaded.append(context)
            data = fixture()
            data['universum'] = [{'id': i, 'nama': str(i)} for i in range(1, 6)]
            return ConceptGraph(data, context=context)

        self.service = AlgebraService(loader=loader)

    def test_paginated_export_keeps_all_ids_and_resolved_ast(self):
        result = self.service.evaluate({'expression': 'bird', 'lang': 'en', 'limit': 2, 'offset': 2})
        self.assertEqual(result['ids'], [3, 4, 5, 14, 15, 20])
        self.assertEqual([item['id'] for item in result['items']], [5, 14])
        self.assertEqual(result['count'], 6)
        self.assertTrue(result['has_more'])
        self.assertEqual(result['ast']['value'], {'id': 3})
        final = self.service.evaluate({'expression': 'bird', 'limit': 2, 'offset': 4})
        self.assertFalse(final['has_more'])
        self.assertEqual(final['ids'], result['ids'])

    def test_scalar_result_and_finite_domain(self):
        count = self.service.evaluate({'expression': 'count(U)', 'within': 'bird'})
        self.assertEqual(count['value'], 6)
        self.assertEqual(count['kind'], 'integer')
        self.assertEqual(count['within'], '#3')
        self.assertNotIn('ids', count)
        self.assertTrue(self.service.evaluate({'expression': 'bird <= animal'})['value'])

    def test_false_subset_has_exact_regions_and_counterexample(self):
        result = self.service.evaluate({'expression': 'bird <= penguin', 'explain': 5})
        self.assertIs(result['value'], False)
        regions = {region['key']: region for region in result['diagnostics']['regions']}
        self.assertEqual(regions['left_only']['count'], 5)
        self.assertEqual(regions['intersection']['count'], 1)
        self.assertEqual(regions['right_only']['count'], 0)
        self.assertTrue(regions['left_only']['counterexamples'])
        explanation = result['explanation']
        self.assertIs(explanation['value'], False)
        self.assertEqual([operand['member'] for operand in explanation['operands']], [True, False])
        self.assertTrue(explanation['operands'][0]['path'])
        self.assertIsNone(explanation['operands'][1]['path'])

    def test_equal_sets_are_not_a_proper_subset_without_invented_counterexamples(self):
        result = self.service.evaluate({'expression': 'bird < avian'})
        self.assertFalse(result['value'])
        self.assertIn('equal', result['diagnostics']['note'])
        self.assertFalse(any(region['counterexamples'] for region in result['diagnostics']['regions']))
        self.assertEqual(result['diagnostics']['regions'][1]['count'], 6)

    def test_set_comparisons_and_disjointness_have_correct_witness_regions(self):
        cases = [('bird <= penguin', ['left_only']), ('bird < penguin', ['left_only']),
                 ('penguin >= bird', ['right_only']), ('penguin > bird', ['right_only']),
                 ('bird == mammal', ['left_only', 'right_only']),
                 ('disjoint(bird, penguin)', ['intersection']), ('bird != avian', []),
                 ('penguin <= bird', []), ('penguin < bird', []), ('bird > penguin', []),
                 ('bird >= penguin', []), ('bird == avian', []), ('bird != penguin', [])]
        for expression, expected in cases:
            with self.subTest(expression=expression):
                result = self.service.evaluate({'expression': expression})
                regions = result['diagnostics']['regions']
                self.assertEqual([r['key'] for r in regions if r['counterexamples']], expected)

    def test_diagnostics_follow_the_finite_domain_and_keep_counts_when_sampled(self):
        full = self.service.evaluate({'expression': 'U <= EMPTY', 'limit': 1})
        region = full['diagnostics']['regions'][0]
        self.assertEqual(region['count'], 20)
        self.assertEqual(len(region['items']), 5)
        self.assertTrue(region['truncated'])
        scoped = self.service.evaluate({'expression': 'bird <= penguin', 'within': 'penguin'})
        self.assertTrue(scoped['value'])
        self.assertEqual([r['count'] for r in scoped['diagnostics']['regions']], [0, 1, 0])

    def test_count_and_empty_explanations_inspect_the_underlying_set(self):
        count = self.service.evaluate({'expression': 'count(bird)', 'explain': 4})
        self.assertEqual(count['value'], 6)
        self.assertTrue(count['explanation']['operands'][0]['member'])
        self.assertEqual(count['diagnostics']['regions'][0]['count'], 6)
        empty = self.service.evaluate({'expression': 'empty(bird)', 'explain': 4})
        self.assertFalse(empty['value'])
        self.assertTrue(empty['diagnostics']['regions'][0]['counterexamples'])
        zero = self.service.evaluate({'expression': 'count(EMPTY)'})
        self.assertEqual(zero['diagnostics']['regions'][0]['items'], [])
        self.assertEqual(zero['value'], 0)

    def test_count_comparison_and_nested_boolean_explanations_remain_typed(self):
        result = self.service.evaluate({'expression': 'count(bird) > count(mammal)', 'explain': 4})
        self.assertTrue(result['value'])
        a, b = result['diagnostics']['operands']
        self.assertEqual((a['value'], b['value']), (6, 2))
        self.assertEqual(a['counted_set']['count'], 6)
        self.assertEqual(result['explanation']['operands'][0]['kind'], 'integer')
        nested = self.service.evaluate({'expression': '(penguin <= bird) == empty(EMPTY)', 'explain': 4})
        self.assertTrue(nested['value'])
        self.assertEqual(nested['explanation']['operands'][0]['kind'], 'boolean')

    def test_nonmember_inspection_preserves_negative_and_unknown_property_states(self):
        negative = self.service.evaluate({'expression': 'penguin <= has(action, flight)', 'explain': 4})
        self.assertFalse(negative['value'])
        self.assertEqual(negative['explanation']['operands'][1]['fact']['state'], 'negative')
        unknown = self.service.evaluate({'expression': 'has(action, flight)', 'explain': 10})
        self.assertFalse(unknown['explanation']['member'])
        self.assertEqual(unknown['explanation']['fact']['state'], 'unknown')
        outside = self.service.evaluate({'expression': 'bird <= penguin', 'within': 'penguin', 'explain': 5})
        self.assertFalse(outside['explanation']['in_universe'])
        self.assertEqual([branch['member'] for branch in outside['explanation']['operands']], [False, False])

    def test_four_states_and_negative_evidence_survive_transport(self):
        result = self.service.evaluate({'expression': 'lacks(action, #9)', 'explain': 4})
        fact = result['explanation']['fact']
        self.assertEqual(fact['state'], 'negative')
        self.assertEqual(fact['evidence'][0]['edge']['strength'], 0)
        self.assertTrue(fact['overridden_edge_ids'])
        states = [set(self.service.evaluate({'expression': f'{name}(action, #9)'})['ids'])
                  for name in ('has', 'lacks', 'unknown', 'conflicts')]
        self.assertEqual(set.union(*states), set(range(1, 21)))
        self.assertEqual(sum(map(len, states)), 20)

    def test_term_errors_identify_the_input_and_replacement_span(self):
        for data, field in [({'expression': 'bird | "bat"'}, 'expression'),
                            ({'expression': 'U', 'within': '"bat"'}, 'within')]:
            with self.subTest(field=field), self.assertRaises(AlgebraError) as caught:
                self.service.evaluate(data)
            error = error_document(caught.exception)['error']
            self.assertEqual(error['field'], field)
            self.assertEqual(data[field][error['position']:error['end']], '"bat"')
            self.assertEqual([c['id'] for c in error['candidates']], [6, 12])
        with self.assertRaises(AlgebraError) as caught:
            checked_request({'expression': 'U', 'within': 'bird &'})
        self.assertEqual(caught.exception.field, 'within')

    def test_reject_invalid_requests_before_loading_database(self):
        for data in [None, [], {}, {'expression': 1}, {'expression': 'U', 'offset': -1},
                     {'expression': 'U', 'context': True}, {'expression': 'U', 'limit': 101},
                     {'expression': 'U', 'explain': 0}, {'expression': 'U', 'lang': 'xx'},
                     {'expression': 'U', 'within': False}, {'expression': 'U', 'sql': 'SELECT 1'}]:
            with self.subTest(data=data), self.assertRaises(AlgebraError):
                self.service.evaluate(data)
        self.assertEqual(self.loaded, [])

    def test_http_work_budget_counts_both_inputs(self):
        six = ' | '.join(['has(action, #9)'] * 6)
        checked_request({'expression': six, 'within': six})
        with self.assertRaisesRegex(AlgebraError, '12 property selectors'):
            checked_request({'expression': six, 'within': six + ' | has(action, #9)'})

    def test_cache_keeps_two_contexts_and_reloads_new_data(self):
        with tempfile.TemporaryDirectory() as directory:
            self.service.version_file = Path(directory) / 'version.json'
            self.service.version_file.write_text('{"data_revision":"Q39","private":"hidden"}')
            for context in [1, 3, 1, 2, 3]:
                self.service.evaluate({'expression': 'U', 'context': context})
            self.assertEqual(self.loaded, [1, 3, 2, 3])
            self.service.version_file.write_text('{"data_revision":"Q40"}')
            result = self.service.evaluate({'expression': 'U', 'context': 3})
            self.assertEqual(self.loaded, [1, 3, 2, 3, 3])
            self.assertEqual(result['source'], {'data_revision': 'Q40'})

    def test_bad_version_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            self.service.version_file = Path(directory) / 'version.json'
            for text in ['[]', 'null', 'broken']:
                self.service.version_file.write_text(text)
                with self.assertRaises(AlgebraError):
                    self.service.evaluate({'expression': 'U'})
            self.assertEqual(self.loaded, [])

    def test_python_result_pagination_validates_offset(self):
        result = ConceptAlgebra(ConceptGraph(fixture())).evaluate('bird')
        for offset in [-1, True, 1.5]:
            with self.assertRaises(AlgebraError):
                result.to_dict(offset=offset)
        self.assertEqual(result.to_dict(offset=100, include_ids=True)['returned'], 0)

    def test_http_worker_status_codes_and_json_errors(self):
        server = HTTPServer(('127.0.0.1', 0), make_handler(self.service))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()

        def request(method, path, body=None, headers=None):
            connection = HTTPConnection('127.0.0.1', server.server_port, timeout=3)
            try:
                connection.request(method, path, body=body, headers=headers or {})
                response = connection.getresponse()
                self.assertEqual(response.getheader('Cache-Control'), 'no-store')
                return response.status, json.loads(response.read())
            finally:
                connection.close()

        try:
            self.assertEqual(request('GET', '/health')[1]['concepts'], 20)
            self.assertEqual(request('GET', '/evaluate')[0], 405)
            self.assertEqual(request('POST', '/other')[0], 404)
            self.assertEqual(request('POST', '/evaluate', '{}')[0], 415)
            headers = {'Content-Type': 'application/json'}
            self.assertEqual(request('POST', '/evaluate', '{', headers)[0], 422)
            status, error = request('POST', '/evaluate', '{"expression":"bird &"}', headers)
            self.assertEqual(status, 422)
            self.assertEqual(error['error']['type'], 'ParseError')
            status, result = request('POST', '/evaluate', '{"expression":"penguin <= bird"}', headers)
            self.assertEqual(status, 200)
            self.assertTrue(result['value'])
            status, batch = request('POST', '/generate', '{"count":12,"lang":"en"}', headers)
            self.assertEqual(status, 200)
            self.assertEqual(batch['schema'], 'conceptuum.qa.batch.v1')
            self.assertEqual(batch['report']['verified'], 12)
            self.assertEqual(request('POST', '/generate', '{"count":51}', headers)[0], 422)
            self.assertEqual(request('POST', '/evaluate', None, dict(headers, **{'Content-Length': str(MAX_BODY + 1)}))[0], 413)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
