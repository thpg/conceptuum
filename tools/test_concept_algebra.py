"""Behavioral checks for concept expressions; no real database or LLM required."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from concept_algebra import (AlgebraError, AmbiguousConceptError, ConceptAlgebra,
                             ConceptGraph, ParseError, UnknownConceptError,
                             format_expression, parse)
from concept_algebra.__main__ import main


def fixture():
    names = {
        1: "entity", 2: "animal", 3: "bird", 4: "penguin", 5: "sparrow",
        6: "flying mammal", 7: "mammal", 8: "water", 9: "flight",
        10: "stone", 11: "fish", 12: "sports bat", 13: "glass",
        14: "avian", 15: "mixed ancestry", 16: "grounded animal",
        17: "café", 18: "wing", 19: "soaring", 20: "specific override",
    }
    data = {
        "concept": [{"dharma": cid, "nama": name, "universum_id": 3 if cid == 12 else 1} for cid, name in names.items()],
        "concept_term": [{"concept_id": cid, "term": name, "lang": "en"} for cid, name in names.items()],
        "universum": [{"id": 1, "nama": "everyday"}, {"id": 3, "nama": "technical"}],
        "relevant": [{"kod": str(code), "long_name": f"relation {code}", "is_symmetric": int(code in {30, 61, 64})}
                     for code in (14, 15, 20, 21, 22, 23, 24, 25, 26, 27, 30, 61, 64, 70)],
        "edge": [],
    }
    data["concept_term"].extend([
        {"concept_id": 6, "term": "bat", "lang": "en"},
        {"concept_id": 12, "term": "bat", "lang": "en"},
        {"concept_id": 6, "term": "летучая мышь", "lang": "ru"},
        {"concept_id": 12, "term": "бита", "lang": "ru"},
        {"concept_id": 5, "term": 'bird "sparrow"', "lang": "en"},
        {"concept_id": 5, "term": "SPARROW", "lang": "en"},
    ])

    def edge(a, code, b, strength=None, context=1, status="ok"):
        data["edge"].append(dict(id=len(data["edge"]) + 1, dh1=a, kod=str(code), dh2=b,
                                 universum_id=context, strength=strength, status=status))

    for child, parent in [(2, 1), (3, 2), (4, 3), (5, 3), (7, 2), (6, 7),
                          (11, 2), (16, 2), (15, 3), (15, 16), (20, 15), (19, 9)]:
        edge(child, 14, parent)
    edge(3, 30, 14)
    edge(3, 22, 9, 80)
    edge(4, 22, 9, 0)
    edge(16, 22, 9, 0)
    edge(20, 22, 9)
    edge(3, 20, 18)
    edge(5, 23, 13)
    edge(5, 61, 6)
    edge(4, 14, 12, context=3)
    edge(5, 14, 16, status="candidate")
    edge(11, 14, 3, status="rejected")
    edge(17, 14, 3, strength=0)
    return data


class AlgebraTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()
        self.graph = ConceptGraph(self.data)
        self.algebra = ConceptAlgebra(self.graph)

    def ids(self, expression, **kwargs):
        return set(self.algebra.evaluate(expression, **kwargs).ids)

    def test_partial_overlap_comes_from_multiple_inheritance(self):
        self.assertEqual(self.ids('bird & "grounded animal"'), {15, 20})
        self.assertEqual(self.ids('bird - "grounded animal"'), {3, 4, 5, 14})
        self.assertEqual(self.ids('bird ^ "grounded animal"'), {3, 4, 5, 14, 16})

    def test_precedence_parentheses_and_left_associative_difference(self):
        self.assertEqual(self.ids('exact(#4) | exact(#5) & exact(#6)'), {4})
        self.assertEqual(self.ids('(exact(#4) | exact(#5)) & exact(#6)'), set())
        self.assertEqual(self.ids('bird - exact(#4) & exact(#5)'), {5})
        self.assertEqual(self.ids('bird - exact(#4) - exact(#5)'), {3, 14, 15, 20})

    def test_unicode_and_arithmetic_aliases(self):
        expected = {15, 20}
        for expression in ['bird ∩ "grounded animal"', 'bird * "grounded animal"', 'bird and "grounded animal"']:
            self.assertEqual(self.ids(expression), expected)
        self.assertEqual(self.ids('exact(#4) + exact(#5)'), {4, 5})
        self.assertEqual(self.ids('bird ∖ exact(#4)'), {3, 5, 14, 15, 20})
        self.assertEqual(self.ids('∅'), set())

    def test_scoped_complement_and_demorgan_laws(self):
        self.assertEqual(self.ids('~penguin', within='bird'), {3, 5, 14, 15, 20})
        self.assertEqual(self.ids('U', within='EMPTY'), set())
        for a, b in [('bird', 'mammal'), ('bird', '"grounded animal"'), ('EMPTY', 'bird')]:
            with self.subTest(a=a, b=b):
                self.assertEqual(self.ids(f'~({a} | {b})'), self.ids(f'~{a} & ~{b}'))
                self.assertEqual(self.ids(f'~({a} & {b})'), self.ids(f'~{a} | ~{b}'))
                self.assertEqual(self.ids(f'{a} | ~{a}'), set(self.graph.ids))

    def test_comparison_and_cardinality_are_typed(self):
        for expr in ['bird <= animal', 'bird < animal', 'bird == avian', 'empty(EMPTY)',
                     'disjoint(penguin, sparrow)', 'count(bird) == 6', 'count(bird) > 2',
                     'count(bird) ≥ 2', 'count(bird) ≤ 6']:
            self.assertIs(self.algebra.evaluate(expr).value, True, expr)
        self.assertIs(self.algebra.evaluate('animal <= bird').value, False)
        for expr in ['count(bird) & bird', 'bird == 6', 'empty(bird) < empty(EMPTY)', 'count(2)']:
            with self.subTest(expr=expr), self.assertRaises(AlgebraError):
                self.algebra.evaluate(expr)

    def test_exact_record_and_genus_navigation(self):
        self.assertEqual(self.ids('exact(bird)'), {3})
        self.assertEqual(self.ids('parents(exact(#15))'), {3, 16})
        self.assertEqual(self.ids('ancestors(exact(penguin))'), {1, 2, 3})
        self.assertEqual(self.ids('children(exact(bird))'), {4, 5, 15})
        self.assertEqual(self.ids('descendants(exact(bird))'), {4, 5, 15, 20})

    def test_coextension_changes_catalog_extent_not_intensional_attributes(self):
        self.assertEqual(self.ids('avian'), self.ids('bird'))
        self.assertEqual(self.graph.fact(14, '22', 9).state, 'unknown')
        self.assertEqual(self.ids('ancestors(exact(avian))'), set())

    def test_rejected_candidate_and_negative_genus_edges_are_not_membership(self):
        self.assertNotIn(11, self.ids('bird'))
        self.assertNotIn(17, self.ids('bird'))
        self.assertNotIn(5, self.ids('"grounded animal"'))

    def test_contexts_are_not_mixed_or_selected_by_home_parent(self):
        other = ConceptAlgebra(ConceptGraph(self.data, context=3))
        self.assertEqual(set(other.evaluate('#12').ids), {4, 12})
        self.assertEqual(set(other.evaluate('bird').ids), {3})
        self.assertEqual(self.ids('#12'), {12})
        self.assertEqual(set(other.evaluate('U').ids), set(self.graph.ids))
        self.assertEqual(other.graph.fact(4, '22', 9).state, 'unknown')
        with self.assertRaises(AlgebraError):
            ConceptGraph(self.data, context=2)

    def test_homonyms_return_all_candidates_instead_of_first_term(self):
        with self.assertRaises(AmbiguousConceptError) as caught:
            self.algebra.evaluate('bat')
        self.assertEqual([c['id'] for c in caught.exception.candidates], [6, 12])
        self.assertEqual(self.ids('ru:"летучая мышь"'), {6})
        self.assertEqual(self.ids('ru:"бита"'), {12})
        self.assertEqual(self.ids('en:"  SPARROW  "'), {5})

    def test_explicit_language_and_unicode_normalization(self):
        self.assertEqual(self.ids('en:"cafe\u0301"'), {17})
        self.assertEqual(self.ids('en:"bird \\"sparrow\\""'), {5})
        english = ConceptAlgebra(self.graph, language='en')
        self.assertEqual(set(english.evaluate('ru:"бита"').ids), {12})
        with self.assertRaises(UnknownConceptError):
            english.evaluate('"бита"')

    def test_unknown_inputs_and_no_short_circuit_sense_hiding(self):
        for expr in ['#99999', '"not a concept"', 'EMPTY & bat', 'U | "missing"']:
            with self.subTest(expr=expr), self.assertRaises(AlgebraError):
                self.algebra.evaluate(expr)

    def test_direct_projections_preserve_direction_and_stored_symmetry(self):
        self.assertEqual(self.ids('related(material, exact(sparrow))'), {13})
        self.assertEqual(self.ids('subjects(23, glass)'), {5})
        self.assertEqual(self.ids('related(61, exact(sparrow))'), {6})
        self.assertEqual(self.ids('related(61, exact(#6))'), {5})
        self.assertEqual(self.ids('related(23, exact(glass))'), set())
        self.assertEqual(self.ids('subjects(22, flight)'), {3, 20})

    def test_inherited_negative_overrides_positive_genus_property(self):
        self.assertEqual(self.ids('has(action, flight)'), {3, 5, 20})
        self.assertEqual(self.ids('lacks(22, flight)'), {4, 16})
        fact = self.graph.explain_fact(4, '22', 9)
        self.assertEqual(fact['state'], 'negative')
        self.assertEqual([e['edge']['subject'] for e in fact['evidence']], [4])
        self.assertEqual(len(fact['overridden_edge_ids']), 1)
        self.assertEqual(self.graph.fact(5, '22', 9).evidence[0].strength, 80)

    def test_multiple_inheritance_retains_conflict_and_direct_override(self):
        self.assertEqual(self.ids('conflicts(22, flight)'), {15})
        self.assertEqual({e.subject for e in self.graph.fact(15, '22', 9).evidence}, {3, 16})
        self.assertEqual(self.graph.fact(20, '22', 9).state, 'positive')
        self.assertEqual([e.subject for e in self.graph.fact(20, '22', 9).evidence], [20])
        self.assertNotIn(15, self.ids('has(22, flight) | lacks(22, flight)'))

    def test_property_states_partition_domain_without_closed_world_negation(self):
        parts = [self.ids(f'{name}(22, flight)') for name in ['has', 'lacks', 'unknown', 'conflicts']]
        self.assertEqual(set().union(*parts), set(self.graph.ids))
        self.assertEqual(sum(map(len, parts)), len(self.graph.ids))
        self.assertIn(1, self.ids('~has(22, flight)'))
        self.assertNotIn(1, self.ids('lacks(22, flight)'))
        self.assertIn(15, self.ids('~has(22, flight)'))

    def test_inheritance_target_is_exact_not_a_target_subtree(self):
        self.assertEqual(self.ids('has(22, soaring)'), set())
        with self.assertRaises(ParseError):
            self.algebra.evaluate('has(22, flight | soaring)')
        with self.assertRaises(AlgebraError):
            self.algebra.evaluate('has(70, flight)')

    def test_more_specific_owner_wins_even_when_its_path_is_longer(self):
        data = fixture()
        data['edge'] = [
            dict(id=i, dh1=a, kod=str(k), dh2=b, universum_id=1, strength=s, status='ok')
            for i, (a, k, b, s) in enumerate([
                (2, 14, 1, None), (3, 14, 2, None), (4, 14, 3, None), (4, 14, 1, None),
                (1, 22, 9, None), (2, 22, 9, 0)], 1)
        ]
        graph = ConceptGraph(data)
        self.assertEqual(graph.fact(4, '22', 9).state, 'negative')
        self.assertEqual([e.subject for e in graph.fact(4, '22', 9).evidence], [2])

    def test_incomparable_owners_conflict_even_at_different_distances(self):
        data = fixture()
        data['edge'] = [e for e in data['edge'] if e['dh1'] != 20]
        for a, b in [(20, 3), (20, 17), (17, 16)]:
            data['edge'].append(dict(id=100 + len(data['edge']), dh1=a, kod='14', dh2=b,
                                     universum_id=1, strength=None, status='ok'))
        self.assertEqual(ConceptGraph(data).fact(20, '22', 9).state, 'conflict')

    def test_cycles_terminate_without_arbitrarily_discarding_assertions(self):
        data = fixture()
        for a, b in [(3, 16), (16, 3)]:
            data['edge'].append(dict(id=100 + len(data['edge']), dh1=a, kod='14', dh2=b,
                                     universum_id=1, strength=None, status='ok'))
        graph = ConceptGraph(data)
        self.assertIn(20, graph.extent(3))
        self.assertEqual(graph.fact(15, '22', 9).state, 'conflict')

    def test_within_restricts_output_without_cutting_inheritance_paths(self):
        self.assertEqual(self.ids('has(22, flight)', within='exact(sparrow)'), {5})
        self.assertEqual(self.ids('ancestors(exact(penguin))', within='bird'), {3})
        with self.assertRaises(AlgebraError):
            self.algebra.evaluate('U', within='count(bird)')

    def test_evidence_and_display_limits_do_not_change_result(self):
        result = self.algebra.evaluate('bird & "grounded animal"', explain=20)
        report = result.to_dict(limit=1, include_ast=True)
        self.assertEqual(report['count'], 2)
        self.assertEqual(report['returned'], 1)
        self.assertTrue(report['truncated'])
        self.assertEqual(result.ids, (15, 20))
        self.assertTrue(report['explanation']['member'])
        self.assertTrue(all(branch['path'] for branch in report['explanation']['operands']))
        self.assertEqual(report['resolved_expression'], '(#3 & #16)')
        self.assertEqual(report['ast']['kind'], 'binary')

    def test_property_explanation_has_source_edge_and_inheritance_path(self):
        report = self.algebra.evaluate('has(22, flight)', explain=5).to_dict()
        fact = report['explanation']['fact']
        self.assertEqual(fact['evidence'][0]['edge']['subject'], 3)
        self.assertEqual(fact['evidence'][0]['genus_path'][0]['subject'], 5)
        self.assertEqual(fact['state'], 'positive')
        report = self.algebra.evaluate('~has(22, flight)', explain=1).to_dict()
        self.assertTrue(report['explanation']['member'])
        self.assertEqual(report['explanation']['operands'][0]['fact']['state'], 'unknown')

    def test_projection_and_navigation_explanations(self):
        cases = [('subjects(23, glass)', 5, 'edges'),
                 ('related(23, exact(sparrow))', 13, 'edges'),
                 ('ancestors(exact(penguin))', 2, 'path')]
        for expression, cid, evidence in cases:
            with self.subTest(expression=expression):
                explanation = self.algebra.evaluate(expression, explain=cid).explanation
                self.assertTrue(explanation['member'])
                self.assertTrue(explanation[evidence])

    def test_snapshot_is_not_mutated_or_used_as_unscoped_path_cache(self):
        data = deepcopy(self.data)
        data['concept_path'] = [{'ancestor': 3, 'descendant': 12, 'depth': 1}]
        before = deepcopy(data)
        algebra = ConceptAlgebra(ConceptGraph(data))
        self.assertNotIn(12, algebra.evaluate('bird').ids)
        algebra.evaluate('has(22, flight) | ~has(23, glass)')
        self.assertEqual(data, before)
        data['concept'][0]['nama'] = 'changed externally'
        self.assertEqual(algebra.graph.concepts[1].name, 'entity')

    def test_bad_snapshot_rows_fail_instead_of_creating_phantom_members(self):
        for change in ['endpoint', 'strength', 'duplicate_id', 'missing_table']:
            data = fixture()
            if change == 'endpoint': data['edge'][0]['dh2'] = 99999
            if change == 'strength': data['edge'][0]['strength'] = -1
            if change == 'duplicate_id': data['edge'][1]['id'] = data['edge'][0]['id']
            if change == 'missing_table': del data['concept_term']
            with self.subTest(change=change), self.assertRaises(AlgebraError):
                ConceptGraph(data)


class ParserTests(unittest.TestCase):
    def test_error_positions_and_injection_like_text(self):
        for expression in ['bird &', 'bird; DROP TABLE concept', '__import__("os")',
                           '#0', '#-1', '#', 'bird animal', 'bird <= animal <= U',
                           '"unterminated', '"bad\\q"', 'related(23)', 'exact(bird | animal)',
                           'count()', 'disjoint(bird)', 'has(23, glass, bird)']:
            with self.subTest(expression=expression), self.assertRaises(ParseError):
                parse(expression)
        with self.assertRaises(ParseError) as caught:
            parse('bird |\n @')
        self.assertEqual((caught.exception.line, caught.exception.column), (2, 2))

    def test_round_trip_formatting_preserves_meaning(self):
        algebra = ConceptAlgebra(ConceptGraph(fixture()))
        for expression in ['bird & ~penguin', 'has(material, "glass")', 'ru:"бита" | sparrow',
                           'count(bird) >= 2', 'bird ∩ ("grounded animal" ∪ penguin)']:
            formatted = format_expression(parse(expression))
            self.assertEqual(algebra.evaluate(expression).value, algebra.evaluate(formatted).value)
        ast = parse('#3')
        serialized = ast.to_dict()
        serialized['value']['id'] = 999
        self.assertEqual(format_expression(ast), '#3')

    def test_limits_handle_groups_unary_calls_and_left_deep_trees(self):
        for expression in ['(' * 80 + 'U' + ')' * 80, '~' * 80 + 'U',
                           'count(' * 80 + 'U' + ')' * 80, ' | '.join(['U'] * 100),
                           'U' * 8193]:
            with self.subTest(prefix=expression[:25]), self.assertRaises(ParseError):
                parse(expression)


class LoadingAndCLITests(unittest.TestCase):
    def test_database_loader_uses_one_snapshot_and_never_commits(self):
        import pymysql
        cursor, connection = MagicMock(), MagicMock()
        cursor.__enter__.return_value = cursor
        connection.cursor.return_value = cursor
        data = fixture()
        cursor.fetchall.side_effect = [data[t] for t in ('concept', 'concept_term', 'edge', 'relevant', 'universum')]
        with patch('pymysql.connect', return_value=connection):
            graph = ConceptGraph.from_database()
        self.assertEqual(len(graph.concepts), 20)
        sql = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertTrue(all(q.startswith(('SET ', 'START TRANSACTION ', 'SELECT ')) for q in sql))
        self.assertIn('START TRANSACTION WITH CONSISTENT SNAPSHOT', sql)
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()

    def test_loader_closes_on_read_failure_and_redacts_connection_error(self):
        import pymysql
        cursor, connection = MagicMock(), MagicMock()
        connection.cursor.return_value = cursor
        cursor.__enter__.return_value = cursor
        cursor.execute.side_effect = pymysql.OperationalError(1, 'private database detail')
        with patch('pymysql.connect', return_value=connection), self.assertRaises(AlgebraError) as caught:
            ConceptGraph.from_database()
        self.assertNotIn('private database detail', str(caught.exception))
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()
        with patch('pymysql.connect', side_effect=pymysql.OperationalError(1, 'secret credential')), self.assertRaises(AlgebraError) as caught:
            ConceptGraph.from_database()
        self.assertNotIn('secret credential', str(caught.exception))

    def test_parse_only_needs_no_database(self):
        with patch.object(ConceptAlgebra, 'from_database') as database, redirect_stdout(StringIO()) as out:
            self.assertEqual(main(['#3 & #16', '--ast']), 0)
        database.assert_not_called()
        self.assertEqual(json.loads(out.getvalue())['kind'], 'binary')

    def test_json_cli_snapshot_success_and_ambiguity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'snapshot.json'
            path.write_text(json.dumps(fixture(), ensure_ascii=False), encoding='utf-8')
            with redirect_stdout(StringIO()) as out:
                code = main(['bird & "grounded animal"', '--snapshot', str(path), '--json', '--limit', '1'])
            result = json.loads(out.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual((result['count'], result['returned']), (2, 1))
            with redirect_stderr(StringIO()) as err:
                code = main(['bat', '--snapshot', str(path), '--json'])
            self.assertEqual(code, 2)
            self.assertEqual(len(json.loads(err.getvalue())['error']['candidates']), 2)

    def test_bad_syntax_does_not_connect(self):
        with patch.object(ConceptAlgebra, 'from_database') as database, redirect_stderr(StringIO()) as err:
            self.assertEqual(main(['bird; DROP TABLE concept', '--json']), 2)
        database.assert_not_called()
        self.assertEqual(json.loads(err.getvalue())['error']['type'], 'ParseError')


if __name__ == '__main__':
    unittest.main()
