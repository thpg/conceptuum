# -*- coding: utf-8 -*-
"""Translate relevant.long_name to English, regenerate defin cache."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

TR = {
    '0': 'no data',
    '1': 'incomparable',
    '10': 'full inclusion (subordination) [deprecated]',
    '11': 'universe (discourse context)',
    '12': 'domain-related',
    '13': 'family (genus-to-genus) [deprecated]',
    '14': 'genus (is-a)',
    '15': 'essential attribute',
    '20': 'non-essential attribute',
    '21': 'inherent attribute (inseparable part/phase)',
    '23': 'frequent attribute',
    '25': 'occasional attribute',
    '27': 'rare attribute',
    '30': 'coextensive (equal scope)',
    '40': 'overlapping',
    '41': 'full overlap with possible exception [deprecated]',
    '43': 'strong overlap',
    '45': 'roughly equal overlap',
    '47': 'slight overlap',
    '48': 'possible overlap',
    '49': 'complementary [deprecated]',
    '60': 'incompatible',
    '61': 'coordinate (co-hyponyms)',
    '62': 'mutually implying (converses)',
    '63': 'contrary (opposite)',
    '64': 'contradictory',
    '70': 'causal (produces)',
    '71': 'hindrance (prevents)',
    '72': 'temporal precedence',
    '73': 'simultaneity',
    '74': 'dependence',
    '80': 'function (purpose)',
    '81': 'material',
    '82': 'agent',
    '83': 'patient (object of action)',
}

eng = JnanaEngine()
for kod, name in TR.items():
    eng.cur.execute("UPDATE relevant SET long_name=%s WHERE kod=%s", (name, kod))
eng.commit()
weak = eng.define()
print('defin regenerated, weak:', len(weak))
print(eng.stats())
for t in ('Java', 'bug', 'programming language', 'вода'):
    cid = eng.resolve(t)
    if cid:
        eng.cur.execute('SELECT defin FROM concept WHERE dharma=%s', (cid,))
        print(t, '::', eng.cur.fetchone()[0])
eng.close()
