# -*- coding: utf-8 -*-
"""Verify a rendered edition against its base text.

For every quoted block `> **卷N·段M**　TEXT` (or `> **段M**　TEXT` inside a
single-volume chapter) this checks two things:

  1. contiguity - each ellipsis-separated fragment occurs verbatim, as a
     contiguous run, somewhere in that volume;
  2. anchoring  - the fragment actually starts inside the paragraph the label
     names (so a reader who turns to 段M finds it there).

Usage:  python qc_book.py            (摩訶僧祇律)
        MK_CANON=genben python qc_book.py
"""
import os, re, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
CANON = os.environ.get('MK_CANON', 'sengqi')
C = {
    'sengqi': ('摩訶僧祇律_去重白話', 'sengqi', '摩訶僧祇律_去重白話_合冊.md'),
    'genben': ('根本說一切有部毘奈耶_去重白話', 'genben', '根本說一切有部毘奈耶_去重白話_合冊.md'),
    'wufen': ('五分律_去重白話', 'wufen', '五分律_去重白話_合冊.md'),
}[CANON]


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


paras, starts = {}, {}
for f in glob.glob(os.path.join(W, C[1], 'vol*.txt')):
    v = int(re.search(r'vol(\d+)', f).group(1))
    d, order = {}, []
    for ln in open(f, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' in ln:
            a, b = ln.split('\t', 1)
            if a.isdigit():
                d[int(a)] = b
                order.append(int(a))
    paras[v] = d
    # offset of each paragraph inside the volume's normalised text
    full, off, pos = [], {}, 0
    for p in order:
        n = norm(d[p])
        off[p] = (pos, pos + len(n))
        full.append(n)
        pos += len(n)
    starts[v] = (''.join(full), off)

path = os.path.join(ROOT, C[0], C[2])
cur = None
tot = bad_contig = bad_anchor = 0
problems = []
for ln in open(path, encoding='utf-8'):
    s = ln.rstrip('\n').strip()
    h = re.match(r'^##\s*卷(\d+)(?:、卷(\d+))?', s)
    if h:
        cur = [int(h.group(1))] + ([int(h.group(2))] if h.group(2) else [])
        continue
    m = re.match(r'^>\s*\*\*(?:卷(\d+)·)?段([\d～~–\-]+)(?:（[節引錄]{2}）)?\*\*\s*(.*)$', s)
    if not m:
        continue
    v = int(m.group(1)) if m.group(1) else (cur[0] if cur and len(cur) == 1 else None)
    p = int(re.match(r'\d+', m.group(2)).group(0))
    txt = m.group(3)
    tot += 1
    if v is None:
        problems.append(('NO-VOL', p, txt[:30]))
        bad_anchor += 1
        continue
    full, off = starts[v]
    for frag in re.split(r'…+|\.{3,}', txt):
        n = norm(frag)
        if len(n) < 4:
            continue
        i = full.find(n)
        if i < 0:
            bad_contig += 1
            problems.append(('CONTIG', v, p, frag[:36]))
            break
        lo, hi = off.get(p, (0, 0))
        if not (lo <= i < hi):
            # A phrase that recurs in the volume (verses, stock formulas) will be
            # found first at its earliest occurrence. Accept when the labelled
            # paragraph is one of the places it actually occurs.
            if n in norm(paras[v].get(p, '')):
                continue
            bad_anchor += 1
            problems.append(('ANCHOR', v, p, frag[:36]))
            break

print('blocks', tot)
print('fragments not contiguous in volume:', bad_contig)
print('fragments not starting in the labelled paragraph:', bad_anchor)
for x in problems[:15]:
    print('  ', x)
sys.exit(1 if (bad_contig or bad_anchor) else 0)
