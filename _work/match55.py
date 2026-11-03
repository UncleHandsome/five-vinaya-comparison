#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""For each 十誦 vol55 paragraph, find best n-gram overlaps in 四分律 and 五分律."""
import io, os, sys

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


def grams(s, n=4):
    s = ''.join(ch for ch in s if ch not in '「」『』，。、；：？！（）《》◎')
    return set(s[i:i + n] for i in range(len(s) - n + 1))


SS = load(os.path.join(BASE, 'shisong', 'vol55.txt'))
SF = []
for fn in sorted(os.listdir(os.path.join(BASE, 'sifen'))):
    if not fn.endswith('.txt'):
        continue
    tag = fn.split('_')[0]
    for k, t in load(os.path.join(BASE, 'sifen', fn)):
        SF.append(('%s-%s' % (tag, k), t))
WF = []
for v in (24, 25, 28, 29):
    for k, t in load(os.path.join(BASE, 'wufen', 'vol%02d.txt' % v)):
        WF.append(('%d-%s' % (v, k), t))

sf_grams = [(k, grams(v), v) for k, v in SF]
wf_grams = [(k, grams(v), v) for k, v in WF]

for k, v in SS:
    g = grams(v)
    if not g:
        continue
    b1 = sorted(((len(g & gg), kk) for kk, gg, vv in sf_grams), reverse=True)[:3]
    b2 = sorted(((len(g & gg), kk) for kk, gg, vv in wf_grams), reverse=True)[:3]
    print('%s\t%d\t四分:%s\t五分:%s' % (k, len(g),
          ' '.join('%s(%d)' % (kk, n) for n, kk in b1),
          ' '.join('%s(%d)' % (kk, n) for n, kk in b2)))
