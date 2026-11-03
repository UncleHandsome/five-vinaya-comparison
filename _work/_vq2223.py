# -*- coding: utf-8 -*-
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

def load(v):
    d = {}
    for line in open(v, encoding='utf-8').read().split('\n'):
        line = line.rstrip('\r')
        if not line.strip():
            continue
        p = line.split('\t', 1)
        if len(p) == 2:
            try:
                d[int(p[0])] = p[1]
            except Exception:
                pass
    return d

S = {'22': load('genben/vol22.txt'), '23': load('genben/vol23.txt')}
txt = open('findings_gu/vol22-23.md', encoding='utf-8').read()
lines = txt.split('\n')
pat = re.compile(r'^\s*>\s*〔卷(22|23)·段(\d+)〕(.*)$')
fails = []
n = 0
for i, l in enumerate(lines):
    m = pat.match(l)
    if not m:
        continue
    n += 1
    vol, seg, body = m.group(1), int(m.group(2)), m.group(3)
    src = S[vol].get(seg, '')
    if body not in src:
        fails.append((i + 1, vol, seg, body[:60]))
print('quote lines:', n)
print('fails:', len(fails))
for f in fails:
    print(' FAIL line', f[0], '卷' + f[1], '段' + str(f[2]), f[3])
