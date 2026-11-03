#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Longest-common-substring based parallel finder for 十誦 vol55."""
import io, os, sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    out = []
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip():
            continue
        k, v = line.split('\t', 1) if '\t' in line else ('?', line)
        out.append((k, v))
    return out


SS = load(os.path.join(BASE, 'shisong', 'vol55.txt'))
SF = []
for fn in sorted(os.listdir(os.path.join(BASE, 'sifen'))):
    if fn.endswith('.txt'):
        tag = fn.split('_')[0]
        for k, t in load(os.path.join(BASE, 'sifen', fn)):
            SF.append(('%s-%s' % (tag, k), t))
WF = []
for v in range(17, 31):
    p = os.path.join(BASE, 'wufen', 'vol%02d.txt' % v)
    for k, t in load(p):
        WF.append(('%d-%s' % (v, k), t))


def best(par, corpus, topn=3):
    res = []
    for k, t in corpus:
        m = SequenceMatcher(None, par, t, autojunk=False)
        blk = m.find_longest_match(0, len(par), 0, len(t))
        res.append((blk.size, k, t[blk.b:blk.b + 60]))
    res.sort(reverse=True)
    return res[:topn]


for k, v in SS:
    if len(v) < 12:
        continue
    b1 = best(v, SF)
    b2 = best(v, WF)
    print('=== %s (%d字)' % (k, len(v)))
    for n, kk, snip in b1:
        print('   SF %s  L=%d  %s' % (kk, n, snip))
    for n, kk, snip in b2:
        print('   WF %s  L=%d  %s' % (kk, n, snip))
