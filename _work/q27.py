# -*- coding: utf-8 -*-
import io, os, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))

def load(p):
    out = []
    for ln in io.open(p, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' in ln:
            k, t = ln.split('\t', 1)
            out.append((k, t))
    return out

CORP = []
for fn in sorted(os.listdir(os.path.join(BASE, 'sifen'))):
    if fn.endswith('.txt'):
        for k, t in load(os.path.join(BASE, 'sifen', fn)):
            CORP.append(('SF:' + fn[:3] + ':' + k, t))
for v in range(1, 31):
    for k, t in load(os.path.join(BASE, 'wufen', 'vol%02d.txt' % v)):
        CORP.append(('WF:v%02d:%s' % (v, k), t))
for v in range(1, 62):
    p = os.path.join(BASE, 'shisong', 'vol%02d.txt' % v)
    if os.path.exists(p):
        for k, t in load(p):
            CORP.append(('SS:v%02d:%s' % (v, k), t))
for v in range(1, 41):
    p = os.path.join(BASE, 'sengqi', 'vol%02d.txt' % v)
    if os.path.exists(p):
        for k, t in load(p):
            CORP.append(('SQ:v%02d:%s' % (v, k), t))

lim = 6
for w in sys.argv[1:]:
    print('#### %s' % w)
    n = 0
    for k, t in CORP:
        if w in t:
            n += 1
            if n <= lim:
                i = t.find(w)
                print('  %s | %s' % (k, t[max(0, i - 45):i + 75].replace('\n', ' ')))
    print('  total=%d' % n)
