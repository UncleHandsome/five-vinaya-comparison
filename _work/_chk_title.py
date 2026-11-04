#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""標題體例驗收：主標題長度、殘留長題、篇內重複、目錄與正文一致。"""
import json, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from errata import apply as apply_errata, clean_title, split_title, TITLE_MAIN
import build_compare as bc

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))

long_main, still_long, dup = [], [], defaultdict(list)
for r in rows:
    t = clean_title(bc.fix_terms(apply_errata(r)['title'], r['canon']), r['id'])
    main, sub = split_title(t, r['id'])
    if len(main) > 16:
        long_main.append((len(main), r['id'], main))
    if not sub and len(t) >= 30:
        still_long.append((len(t), r['id'], t))
    n = bc.PLACED.get(r['id'], {}).get('n')
    dup[(n, main)].append(r['id'])

print('主標題 >16 字：', len(long_main))
for x in sorted(long_main, reverse=True)[:10]:
    print('  ', x)
print('仍無副標題且 ≥30 字：', len(still_long))
for x in sorted(still_long, reverse=True)[:10]:
    print('  ', x)
d = [(k, v) for k, v in dup.items() if len(v) > 1]
print('同篇內主標題重複：', len(d))
for k, v in d[:12]:
    print('   篇', k[0], k[1], v)
print('TITLE_MAIN 條數：', len(TITLE_MAIN))
