# -*- coding: utf-8 -*-
"""Find best parallel paragraphs for each 十誦 vol54 segment."""
import io, os, sys, glob, re
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))

def load(path, kind):
    out = []
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip() or '\t' not in line:
            continue
        k, v = line.split('\t', 1)
        out.append((k, v))
    return out

SF = []
for p in sorted(glob.glob(os.path.join(BASE, 'sifen', '*.txt'))):
    tag = os.path.basename(p)[:3]
    for k, v in load(p, 's'):
        SF.append(('四分' + tag, k, v))
WF = []
for p in sorted(glob.glob(os.path.join(BASE, 'wufen', 'vol*.txt'))):
    tag = os.path.basename(p)[3:5]
    for k, v in load(p, 'w'):
        WF.append(('五分' + tag, k, v))

def grams(t, n=4):
    t = re.sub(r'[，。、：；「」『』？！（）()\s]', '', t)
    return set(t[i:i+n] for i in range(len(t)-n+1))

def best(seg, corp, topn=2, n=4):
    g = grams(seg, n)
    if not g:
        return []
    scored = []
    for tag, k, v in corp:
        gv = grams(v, n)
        if not gv:
            continue
        inter = len(g & gv)
        if inter == 0:
            continue
        # containment relative to segment
        sc = inter / len(g)
        scored.append((sc, inter, tag, k, v))
    scored.sort(key=lambda x: -x[0])
    return scored[:topn]

if __name__ == '__main__':
    segs = load(os.path.join(BASE, 'shisong', 'vol54.txt'), 't')
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    for k, v in segs:
        if not k.isdigit():
            continue
        i = int(k)
        if i < lo or i > hi:
            continue
        print('##### %s  %s' % (k, v[:50]))
        for corp, nm in ((SF, '四分'), (WF, '五分')):
            for sc, inter, tag, kk, vv in best(v, corp):
                if sc < 0.10:
                    continue
                # locate first shared gram position
                print('   %s %.2f %s %s :: %s' % (nm, sc, tag, kk, vv[:90]))
        print()
