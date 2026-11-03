# -*- coding: utf-8 -*-
import io, os, re, sys, glob
BASE = os.path.dirname(os.path.abspath(__file__))

def load(kind):
    d = os.path.join(BASE, kind)
    out = []
    for p in sorted(glob.glob(os.path.join(d, '*.txt'))):
        for l in io.open(p, encoding='utf-8').read().split('\n'):
            if not l.strip():
                continue
            seg, txt = l.split('\t', 1)
            out.append((os.path.basename(p), seg, txt))
    return out

CACHE = {}
def corpus(kind):
    if kind not in CACHE:
        CACHE[kind] = load(kind)
    return CACHE[kind]

def search(kw, kinds=('sifen','wufen','shisong'), width=60, limit=6):
    for kind in kinds:
        hits = []
        for f, seg, txt in corpus(kind):
            for m in re.finditer(re.escape(kw), txt):
                a = max(0, m.start()-width); b = min(len(txt), m.end()+width)
                hits.append((f, seg, txt[a:b]))
        print('## %s : %s  (%d hits)' % (kind, kw, len(hits)))
        for f, seg, sn in hits[:limit]:
            print('  [%s 段%s] ...%s...' % (f, seg, sn))
        if len(hits) > limit:
            print('  ... +%d more' % (len(hits)-limit))
        print()

if __name__ == '__main__':
    for kw in sys.argv[1:]:
        search(kw)
