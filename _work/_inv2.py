#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盤點 v2：按實際渲染管線（clean_title / expand_refs / glyph_fix）計殘留。"""
import json, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from errata import apply as apply_errata, clean_title
from build_compare import fix_terms
from diff_fmt import expand_refs
from sifen_src import glyph_fix

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))

# ── 指代殘留（差異說明經 expand_refs 後仍存者）──
res = []
for r in rows:
    e = apply_errata(r)
    d = expand_refs(e.get('diff_full') or '', e)
    t = clean_title(fix_terms(e.get('title') or '', e['canon']), r['id'])
    for fld, txt in (('diff', d), ('title', t)):
        for m in re.finditer(r'[兩三二四]\s*律', txt):
            res.append((r['id'], r['canon'], fld, txt[max(0, m.start() - 40):m.start() + 40]))
print(f'[指代] expand_refs 後殘留 {len(res)} 處（{len(set(x[0] for x in res))} id）')
for x in res:
    print(f'  {x[0]} {x[1]} {x[2]}: …{x[3]}…')

# ── 組字式殘留（經 glyph_fix）──
g = []
for r in rows:
    e = apply_errata(r)
    for fld in ('title', 'diff_full', 'orig', 'plain', 'ref4'):
        t = glyph_fix(e.get(fld) or '')
        for m in re.finditer(r'\[[^\[\]]{1,14}\]', t):
            g.append((r['id'], fld, m.group()))
print(f'\n[組字] glyph_fix 後殘留 {len(g)} 處：', Counter(x[2] for x in g).most_common())
for x in g:
    print(f'  {x[0]} {x[1]}: {x[2]}')

# ── S-ID 缺漏：第二部（四分所無）應有 S 號 ──
ids = {r['id'] for r in rows}
print(f'\n[編號] 總列 {len(rows)}　M 號 {sum(1 for r in rows if r["id"].startswith("M-"))}')
