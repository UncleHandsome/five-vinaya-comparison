#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 expand_refs 後仍存「兩律」「三律」者，附五律欄位，供判定所指。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from errata import apply as apply_errata
from diff_fmt import expand_refs

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))
for r in rows:
    e = apply_errata(r)
    d = expand_refs(e.get('diff_full') or '', e)
    for m in re.finditer(r'[兩三二四]\s*律', d):
        cells = ' '.join(f'{k}={e.get(k, "")}' for k in ('v4', 'v5', 'v10', 'vMK', 'vGU'))
        print(f"### {r['id']} 主稿={r['canon']}  {cells}")
        print(f"  題：{e.get('title')}")
        print(f"  段：…{d[max(0, m.start() - 70):m.start() + 70]}…")
        print()
