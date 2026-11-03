# -*- coding: utf-8 -*-
"""Search helper for 十誦律 vol54 vs 四分律 / 五分律."""
import io, os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))

def load_sifen():
    out = []
    for p in sorted(glob.glob(os.path.join(BASE, 'sifen', '*.txt'))):
        name = os.path.basename(p)[:3]
        for line in io.open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if '\t' in line:
                k, v = line.split('\t', 1)
                out.append(('四分' + name, k, v))
    return out

def load_wufen():
    out = []
    for p in sorted(glob.glob(os.path.join(BASE, 'wufen', 'vol*.txt'))):
        name = os.path.basename(p)[3:5]
        for line in io.open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if '\t' in line:
                k, v = line.split('\t', 1)
                out.append(('五分' + name, k, v))
    return out

CORP = load_sifen() + load_wufen()

def search(kw, span=60, limit=8, which=None):
    hits = [(t, k, v) for t, k, v in CORP if kw in v and (not which or t.startswith(which))]
    print('=== %s (%d)' % (kw, len(hits)))
    for t, k, v in hits[:limit]:
        i = v.find(kw)
        s = max(0, i - span)
        print('%-8s %-6s %s' % (t, k, v[s:i + span]))
    print()

if __name__ == '__main__':
    args = sys.argv[1:]
    lim = 8
    span = 60
    which = None
    kws = []
    for a in args:
        if a.startswith('--n='):
            lim = int(a[4:])
        elif a.startswith('--w='):
            span = int(a[4:])
        elif a.startswith('--f='):
            which = a[4:]
        else:
            kws.append(a)
    for kw in kws:
        search(kw, span=span, limit=lim, which=which)
