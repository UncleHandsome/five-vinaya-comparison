# -*- coding: utf-8 -*-
"""Search keywords (read from UTF-8 file, one per line) across the whole 四分/五分 corpus."""
import io, os, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))

CORP = []
for fn in sorted(os.listdir(os.path.join(BASE, 'sifen'))):
    if not fn.endswith('.txt'):
        continue
    tag = '四' + fn[:3]
    for line in io.open(os.path.join(BASE, 'sifen', fn), encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip():
            continue
        k, v = line.split('\t', 1) if '\t' in line else ('?', line)
        CORP.append((tag, k, v))
for v in range(1, 31):
    p = os.path.join(BASE, 'wufen', 'vol%02d.txt' % v)
    if not os.path.exists(p):
        continue
    for line in io.open(p, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip():
            continue
        k, t = line.split('\t', 1) if '\t' in line else ('?', line)
        CORP.append(('五%02d' % v, k, t))

kws = [l.strip() for l in io.open(os.path.join(BASE, 'kw61.txt'), encoding='utf-8') if l.strip()]
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
for kw in kws:
    hits = [(t, k, v) for t, k, v in CORP if kw in v]
    print('=== %s (%d)' % (kw, len(hits)))
    for t, k, v in hits[:limit]:
        i = v.find(kw)
        s = max(0, i - 55)
        print('  %-6s %-5s ...%s...' % (t, k, v[s:i + 60]))
    print()
