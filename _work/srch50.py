#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Search 四分律 073/074 + 五分律 26-28 for comparison with 十誦律 vol50."""
import io, os, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))

FILES = [
    ('四分073', os.path.join(BASE, 'sifen', '073_毘尼增一之三.txt')),
    ('四分074', os.path.join(BASE, 'sifen', '074_毘尼增一之四.txt')),
    ('五分26', os.path.join(BASE, 'wufen', 'vol26.txt')),
    ('五分27', os.path.join(BASE, 'wufen', 'vol27.txt')),
    ('五分28', os.path.join(BASE, 'wufen', 'vol28.txt')),
]

CORP = []
for tag, path in FILES:
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if '\t' in line:
            k, v = line.split('\t', 1)
        else:
            k, v = '?', line
        CORP.append((tag, k, v))


def search(kw, span=60, limit=8):
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
