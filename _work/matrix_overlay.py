# -*- coding: utf-8 -*-
"""Overlay the island-collision verdicts onto the built matrix."""
import json, re, os

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))
idx = {(r['canon'], r['unit'], r['no']): r for r in rows}

VERDICTS = [
    # (group, kind, (canonA, unitA, noA), (canonB, unitB, noB))
    ('G1', '同條', ('五分', 'vol07', 1), ('僧祇', 'vol14-15', 26)),
    ('G2', '同條', ('五分', 'vol06', 11), ('十誦', 'vol11-12', 9)),
    ('G3', '同條', ('五分', 'vol09', 1), ('僧祇', 'vol20-21', 18)),
    ('G4', '同條', ('五分', 'vol08', 10), ('根有', 'vol42-43', 1)),
    ('G5', '同條', ('僧祇', 'vol27-28', 12), ('根有', 'vol50', 7)),
    ('G6', '同條', ('十誦', 'vol56', 32), ('僧祇', 'vol25-26', 24)),
    ('G7', '同條', ('十誦', 'vol54', 26), ('根有', 'vol42-43', 4)),
    ('T1', '同題異制', ('五分', 'vol18', 11), ('僧祇', 'vol27-28', 22)),
    ('T2', '同題異制', ('僧祇', 'vol29-30', 19), ('根有', 'vol10-11', 4)),
    ('T3', '同題異制', ('五分', 'vol25', 9), ('僧祇', 'vol33', 14)),
]

KEY = {'五分': 'v5', '十誦': 'v10', '僧祇': 'vMK', '根有': 'vGU'}
missing = []
for g, kind, a, b in VERDICTS:
    ra, rb = idx.get(a), idx.get(b)
    if not ra or not rb:
        missing.append((g, a if not ra else b))
        continue
    ra[KEY[b[0]]] = '有'
    rb[KEY[a[0]]] = '有'
    ra['grp'] = g
    rb['grp'] = g
    ra['gkind'] = kind
    rb['gkind'] = kind

print('missing', missing)
json.dump(rows, open(os.path.join(W, 'matrix_built.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
from collections import Counter
print('grouped rows', sum(1 for r in rows if r.get('grp')))
print(Counter(r.get('gkind') for r in rows if r.get('grp')))
