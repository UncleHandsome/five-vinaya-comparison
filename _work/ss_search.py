#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Keyword search over 四分律 / 五分律 paragraph files."""
import io, glob, os, sys, re

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SIFEN = sorted(glob.glob('_work/sifen/0*.txt'))
WUFEN = sorted(glob.glob('_work/wufen/vol*.txt'))

def load(f):
    out = []
    for i, line in enumerate(io.open(f, encoding='utf-8'), 1):
        line = line.rstrip('\n')
        if '\t' in line and re.match(r'^\d+-\d+\t', line):
            k, v = line.split('\t', 1)
        else:
            k, v = str(i), line
        out.append((k, v))
    return out

CORPUS = []
for f in SIFEN:
    tag = '四分' + os.path.basename(f)[:3]
    for k, v in load(f):
        CORPUS.append((tag, k, v))
for f in WUFEN:
    tag = '五分卷' + re.search(r'vol(\d+)', f).group(1)
    for k, v in load(f):
        CORPUS.append((tag, k, v))

def search(kw, limit=12, ctx=70):
    hits = [(t, k, v) for t, k, v in CORPUS if kw in v]
    print('=== %s  (%d)' % (kw, len(hits)))
    for t, k, v in hits[:limit]:
        i = v.find(kw)
        s = max(0, i - ctx // 2)
        print('%-10s %-8s %s' % (t, k, v[s:s + ctx * 2]))
    return len(hits)

if __name__ == '__main__':
    for kw in sys.argv[1:]:
        search(kw)
