"""Guards for explicit, source-preserving lexical cleanup."""
from copy import deepcopy
import ast
from pathlib import Path
import unittest

from repair_lexicon import TABLES, fingerprint, validate


class LexicalRepairTests(unittest.TestCase):
    def setUp(self):
        self.before = {name:[] for name in TABLES}
        self.before['concept'] = [dict(dharma=1,nama='вычисляние'),dict(dharma=2,nama='задержание')]
        self.before['concept_term'] = [dict(concept_id=1,term='вычисляние',lang='ru'),
                                      dict(concept_id=2,term='задержание',lang='ru'),
                                      dict(concept_id=2,term='задержаание',lang='ru')]
        self.plan = dict(schema='conceptuum.lexical-repair.v1',
                         before_table_sha256={k:fingerprint(v) for k,v in self.before.items()},
                         renames=[dict(id=1,before='вычисляние',name='вычислять')],
                         add_terms=[dict(id=1,term='вычислять',lang='ru')],
                         remove_terms=[dict(id=1,term='вычисляние',lang='ru'),dict(id=2,term='задержаание',lang='ru')])

    def test_explicit_cleanup_retains_the_real_word(self):
        validate(self.plan, self.before)
        original={(r['concept_id'],r['term'],r['lang']) for r in self.before['concept_term']}
        removed={(r['id'],r['term'],r['lang']) for r in self.plan['remove_terms']}
        self.assertIn((2,'задержание','ru'), original-removed)

    def test_stale_snapshot_and_wrong_source_name_are_rejected(self):
        changed=deepcopy(self.before)
        changed['concept'][0]['nama']='already corrected'
        with self.assertRaisesRegex(ValueError,'changed'):
            validate(self.plan,changed)
        wrong=deepcopy(self.plan)
        wrong['renames'][0]['before']='other word'
        with self.assertRaisesRegex(ValueError,'rename'):
            validate(wrong,self.before)

    def test_missing_replacement_term_and_remove_add_collision_are_rejected(self):
        missing=deepcopy(self.plan)
        missing['add_terms']=[]
        with self.assertRaisesRegex(ValueError,'Russian term'):
            validate(missing,self.before)
        collision=deepcopy(self.plan)
        collision['add_terms'].append(dict(id=2,term='задержаание',lang='ru'))
        with self.assertRaisesRegex(ValueError,'term changes'):
            validate(collision,self.before)

    def test_fingerprint_ignores_row_order_but_detects_content_changes(self):
        rows=self.before['concept_term']
        self.assertEqual(fingerprint(rows),fingerprint(list(reversed(rows))))
        changed=deepcopy(rows);changed[0]['lang']='en'
        self.assertNotEqual(fingerprint(rows),fingerprint(changed))

    def test_predicted_nonword_is_never_accepted_as_a_dictionary_noun(self):
        # Extract the pure predicate without importing a legacy CLI that opens
        # database connections and replaces stdout at module scope.
        import pymorphy3
        source=Path(__file__).with_name('rename_inf_to_noun.py')
        tree=ast.parse(source.read_text(encoding='utf-8'))
        predicate=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='real_noun')
        namespace={'morph':pymorphy3.MorphAnalyzer()}
        exec(compile(ast.Module(body=[predicate],type_ignores=[]),str(source),'exec'),namespace)
        for word in ('задержаание','вычисляние','навредение'):
            self.assertFalse(namespace['real_noun'](word),word)
        self.assertTrue(namespace['real_noun']('задержание'))


if __name__=='__main__':
    unittest.main()
