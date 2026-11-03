#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""For each 十誦 vol50 paragraph, find best 4-gram overlap with 四分073/074 and 五分26-28."""
import io, os, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    out = []
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        k, v = line.split('\t', 1) if '\t' in line else ('?', line)
        out.append((k, v))
    return out


def grams(s, n=4):
    s = ''.join(ch for ch in s if ch not in '「」『』，。、；：？！（）《》')
    return set(s[i:i + n] for i in range(len(s) - n + 1))


SS = load(os.path.join(BASE, 'shisong', 'vol50.txt'))
SF = load(os.path.join(BASE, 'sifen', '073_毘尼增一之三.txt')) + load(os.path.join(BASE, 'sifen', '074_毘尼增一之四.txt'))
WF = []
for v in (26, 27, 28):
    for k, t in load(os.path.join(BASE, 'wufen', 'vol%d.txt' % v)):
        WF.append(('%d-%s' % (v, k), t))

sf_grams = [(k, grams(v), v) for k, v in SF]
wf_grams = [(k, grams(v), v) for k, v in WF]

for k, v in SS:
    g = grams(v)
    if not g:
        continue
    best = sorted(((len(g & gg), kk, vv) for kk, gg, vv in sf_grams), reverse=True)[:1]
    bestw = sorted(((len(g & gg), kk, vv) for kk, gg, vv in wf_grams), reverse=True)[:1]
    s1 = best[0] if best else (0, '', '')
    s2 = bestw[0] if bestw else (0, '', '')
    print('%s\t%d/%d\t四分%s\t五分%s' % (k, s1[0], len(g), s1[1], s2[0] if s2 else 0))
