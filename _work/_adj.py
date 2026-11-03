# -*- coding: utf-8 -*-
"""Print strong collision candidates with enough context to adjudicate.

Usage:  python _adj.py 0 18      (start, end; 0-based, sorted by score)
"""
import os, sys, json, re

W = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(W, 'collide.json'), encoding='utf-8'))
rows = json.load(open(os.path.join(W, 'matrix_rows.json'), encoding='utf-8'))
by = {(r['canon'], r['unit'], r['no']): r for r in rows}
CORP = {'四分': 'sifen', '五分': 'wufen', '十誦': 'shisong', '僧祇': 'sengqi', '根有': 'genben'}


def para(canon, vol, seg):
    p = os.path.join(W, CORP[canon], 'vol%02d.txt' % vol)
    for ln in open(p, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' in ln:
            a, b = ln.split('\t', 1)
            if a.isdigit() and int(a) == seg:
                return b
    return '(未得)'


def clip(s, n):
    s = re.sub(r'\s+', '', s or '')
    return s[:n] + ('…' if len(s) > n else '')


strong = [x for x in res if x['vs'][0]['score'] >= 2]
strong.sort(key=lambda x: (-x['vs'][0]['score'], -x['vs'][0]['cover']))
a, b = int(sys.argv[1]), int(sys.argv[2])
for i, x in enumerate(strong[a:b], a + 1):
    r = by.get((x['canon'], x['unit'], x['no']), {})
    v = x['vs'][0]
    print('#%d %s %s#%s  %s' % (i, x['canon'], x['unit'], x['no'], clip(x['title'], 44)))
    print('   本稿：%s' % clip(r.get('diff'), 130))
    print('   對律 %s 卷%d段%d 命中：%s' % (v['canon'], v['vol'], v['seg'], '／'.join(v['terms'])))
    print('   > %s' % clip(para(v['canon'], v['vol'], v['seg']), 190))
    print()
