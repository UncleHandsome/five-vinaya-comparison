#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
P = {}
for line in io.open(os.path.join(BASE, 'shisong', 'vol55.txt'), encoding='utf-8'):
    k, t = line.rstrip('\n').split('\t', 1)
    P[int(k)] = t
md = io.open(os.path.join(BASE, 'findings_ss', 'vol55.md'), encoding='utf-8').read()

# 1. quote check
bad = 0
for m in re.finditer(r'^  > 55-(\d+)：(.*)$', md, re.M):
    n = int(m.group(1)); q = m.group(2)
    if q not in P[n]:
        bad += 1
        print('QUOTE MISMATCH', n, q[:40])
print('quotes checked, bad =', bad)

# 2. coverage
kept = set()
for m in re.finditer(r'- 位置：55-([0-9～、]+)', md):
    for part in re.split('、', m.group(1)):
        part = part.split('（')[0]
        if '～' in part:
            a, b = part.split('～'); kept.update(range(int(a), int(b) + 1))
        elif part.strip():
            kept.add(int(part))
print('kept count', len(kept))

delp = set()
for line in md.splitlines():
    if line.startswith('| 55-'):
        cell = line.split('|')[1].strip()
        cell = cell.split('（')[0].replace('55-', '')
        for part in cell.split('、'):
            if '～' in part:
                a, b = part.split('～'); delp.update(range(int(a), int(b) + 1))
            elif part.strip():
                delp.add(int(part))
print('del table count', len(delp))
missing = [i for i in range(1, 152) if i not in kept and i not in delp]
print('missing', missing)
both = sorted(kept & delp)
print('both', both)

# 3. table col count
for line in md.splitlines():
    if line.startswith('| 55-'):
        if line.count('|') != 5:
            print('BAD ROW', line)
print('rows', sum(1 for l in md.splitlines() if l.startswith('| 55-')))
