#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 ≥30 字且尚未人工定主標題者，依 id 排序，分批輸出供裁定。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from errata import apply as apply_errata, clean_title, split_title, TITLE_MAIN
from build_compare import fix_terms

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))
todo = []
for r in rows:
    t = clean_title(fix_terms(apply_errata(r)['title'], r['canon']), r['id'])
    if len(t) < 30 or r['id'] in TITLE_MAIN:
        continue
    main, sub = split_title(t, r['id'])
    todo.append({'id': r['id'], 'canon': r['canon'], 'unit': r['unit'],
                 'auto': main, 'full': t})
json.dump(todo, open(os.path.join(W, '_todo_title.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('待定', len(todo))
for i, x in enumerate(todo):
    print(f"{i+1}\t{x['id']}\t{x['canon']}\t{x['full']}")
