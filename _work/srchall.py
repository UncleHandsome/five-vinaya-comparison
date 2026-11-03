#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Whole-corpus search over 四分律 (sifen/0*.txt) and 五分律 (wufen/vol*.txt)."""
import io, os, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))
CORP = []
for f in sorted(os.listdir(os.path.join(BASE, 'sifen'))):
    if not f.endswith('.txt'):
        continue
    tag = '四分' + f[:3]
    for line in io.open(os.path.join(BASE, 'sifen', f), encoding='utf-8'):
        line = line.rstrip('\n')
        k, v = line.split('\t', 1) if '\t' in line else ('?', line)
        CORP.append((tag, k, v))
for v in range(1, 31):
    p = os.path.join(BASE, 'wufen', 'vol%02d.txt' % v)
    if not os.path.exists(p):
        continue
    for line in io.open(p, encoding='utf-8'):
        line = line.rstrip('\n')
        k, t = line.split('\t', 1) if '\t' in line else ('?', line)
        CORP.append(('五分%02d' % v, k, t))


def search(kw, span=55, limit=6):
    hits = [(t, k, v) for t, k, v in CORP if kw in v]
    print('=== %s (%d)' % (kw, len(hits)))
    for t, k, v in hits[:limit]:
        i = v.find(kw)
        s = max(0, i - span)
        print('%-8s %-6s %s' % (t, k, v[s:i + span]))
    print()


if __name__ == '__main__':
    for kw in sys.argv[1:]:
        search(kw)
