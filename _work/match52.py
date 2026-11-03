# -*- coding: utf-8 -*-
"""Fuzzy paragraph matcher: vol52 shisong vs sifen/wufen corpora (5-gram Jaccard)."""
import io, os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))

def load_seg(path, pat):
    out = []
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        m = re.match(pat, line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out

TARGET = load_seg(os.path.join(BASE, 'shisong', 'vol52.txt'), r'^(\d+)\t(.*)$')
TARGET = [(k, v) for k, v in TARGET if len(v) > 8]

CORP = []
for f in sorted(glob.glob(os.path.join(BASE, 'sifen', '0*.txt'))):
    tag = '四分' + os.path.basename(f)[:3]
    for k, v in load_seg(f, r'^(\d+)\t(.*)$'):
        CORP.append((tag, k, v))
for v in range(1, 31):
    p = os.path.join(BASE, 'wufen', 'vol%02d.txt' % v)
    if os.path.exists(p):
        for k, t in load_seg(p, r'^(\d+)\t(.*)$'):
            CORP.append(('五分%02d' % v, k, t))

def grams(s, n=5):
    s = re.sub(r'[，。、？！：「」『』（）()\[\]0-9\s]', '', s)
    return set(s[i:i+n] for i in range(len(s) - n + 1))

CG = [(t, k, v, grams(v)) for t, k, v in CORP]

def best(k, v, which, topn=4):
    g = grams(v)
    res = []
    for t, kk, vv, gg in CG:
        if which == 'sifen' and not t.startswith('四分'):
            continue
        if which == 'wufen' and not t.startswith('五分'):
            continue
        inter = len(g & gg)
        if not inter:
            continue
        score = inter / min(len(g), len(gg))
        res.append((score, t, kk, vv))
    res.sort(reverse=True)
    return res[:topn]

if __name__ == '__main__':
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 145
    which = sys.argv[3] if len(sys.argv) > 3 else 'both'
    for k, v in TARGET:
        if not (lo <= int(k) <= hi):
            continue
        print('#### 段%s %s' % (k, v[:60]))
        for s, t, kk, vv in best(k, v, which):
            print('  %-8s %-5s %.2f %s' % (t, kk, s, vv[:70]))
        print()
