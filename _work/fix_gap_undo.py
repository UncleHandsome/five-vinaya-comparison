# -*- coding: utf-8 -*-
"""Remove the mis-placed （中略：…） lines inserted by fix_gap.py (v1)."""
import os, re
W = os.path.dirname(os.path.abspath(__file__))
BAD = {24: 62, 25: 99, 28: 103, 29: [79, 110]}
for v, ln in BAD.items():
    path = os.path.join(W, 'findings/vol%02d.md' % v)
    lines = open(path, encoding='utf-8').read().split('\n')
    for i in sorted(ln if isinstance(ln, list) else [ln], reverse=True):
        idx = i - 1
        if '中略：段' in lines[idx]:
            print('DEL vol%02d line %d: %s' % (v, i, lines[idx].strip()))
            del lines[idx]
        else:
            print('SKIP vol%02d line %d not a marker: %s' % (v, i, lines[idx][:40]))
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))
