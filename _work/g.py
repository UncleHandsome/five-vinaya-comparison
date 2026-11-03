#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Grep helper across 律 corpus."""
import io, os, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))


def load(p):
    out = []
    for l in io.open(p, encoding='utf-8'):
        l = l.rstrip('\n')
        if not l.strip():
            continue
        k, v = l.split('\t', 1) if '\t' in l else ('?', l)
        out.append((k, v))
    return out


corp = []
for fn in sorted(os.listdir(os.path.join(BASE, 'sifen'))):
    if fn.endswith('.txt'):
        for k, t in load(os.path.join(BASE, 'sifen', fn)):
            corp.append(('四' + fn[:3] + '-' + k, t))
for v in range(1, 31):
    for k, t in load(os.path.join(BASE, 'wufen', 'vol%02d.txt' % v)):
        corp.append(('五%d-%s' % (v, k), t))

qs = sys.argv[1:]
for q in qs:
    print('##### ' + q)
    n = 0
    for tag, t in corp:
        for m in re.finditer(re.escape(q), t):
            s = max(0, m.start() - 70)
            print('  %s  ...%s' % (tag, t[s:m.start() + 90].replace('\n', ' ')))
            n += 1
            break
    if not n:
        print('  (無)')
    print('  paras=%d' % n)
