# -*- coding: utf-8 -*-
"""Ad-hoc corpus grep: python _find.py <canon> <pattern> [max]
canon in 四分 五分 十誦 僧祇 根有
"""
import os, re, sys, glob

W = os.path.dirname(os.path.abspath(__file__))
CORP = {'四分': 'sifen', '五分': 'wufen', '十誦': 'shisong',
        '僧祇': 'sengqi', '根有': 'genben'}
canon, pat = sys.argv[1], sys.argv[2]
lim = int(sys.argv[3]) if len(sys.argv) > 3 else 12
rx = re.compile(pat)
n = 0
for f in sorted(glob.glob(os.path.join(W, CORP[canon], 'vol*.txt'))):
    vol = re.search(r'vol(\d+)', f).group(1)
    for ln in open(f, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' not in ln:
            continue
        a, b = ln.split('\t', 1)
        if not a.isdigit():
            continue
        if rx.search(b):
            print('%s 卷%s 段%s: %s' % (canon, int(vol), a, b[:200]))
            n += 1
            if n >= lim:
                sys.exit(0)
print('-- total shown', n)
