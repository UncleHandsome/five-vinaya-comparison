# -*- coding: utf-8 -*-
import re
md = open('findings_gu/vol02-03.md', encoding='utf-8').read()

def load(f):
    d = {}
    for line in open(f, encoding='utf-8'):
        m = re.match(r'^(\d+)\t(.*)$', line.rstrip('\n'))
        if m:
            d[int(m.group(1))] = m.group(2)
    return d

src = {2: load('genben/vol02.txt'), 3: load('genben/vol03.txt')}
pat = re.compile(r'^\s*> 〔卷(\d)·段(\d+)〕(.*)$', re.M)
bad = []
tot = 0
n = 0
for m in pat.finditer(md):
    v, s, q = int(m.group(1)), int(m.group(2)), m.group(3).strip()
    if q.startswith('（中略'):
        continue
    n += 1
    tot += len(re.sub(r'\s', '', q))
    if s not in src[v]:
        bad.append(('NOSEG', v, s, q[:30]))
        continue
    if q not in src[v][s]:
        bad.append(('MISMATCH', v, s, q[:50]))
print('引文行', n, '字數', tot)
print('不合格', len(bad))
for b in bad:
    print(' ', b)
print('樣本:', pat.findall(md)[:3])
