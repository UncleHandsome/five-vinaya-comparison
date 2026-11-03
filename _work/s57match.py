# -*- coding: utf-8 -*-
"""Similarity match: 十誦 vol57 paragraphs vs 四分/五分 paragraphs."""
import io, glob, os, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

def load_shisong(path):
    out = {}
    for ln in io.open(path, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip():
            continue
        n, t = ln.split('\t', 1)
        out[int(n)] = t
    return out

V = load_shisong('_work/shisong/vol57.txt')

def load_corpus():
    corpus = []
    for f in sorted(glob.glob('_work/sifen/0*.txt')):
        tag = '四分' + os.path.basename(f)[:3]
        for i, line in enumerate(io.open(f, encoding='utf-8'), 1):
            line = line.rstrip('\n')
            if '\t' in line and re.match(r'^\d+-\d+\t', line):
                k, v = line.split('\t', 1)
            else:
                k, v = str(i), line
            if len(v) < 8:
                continue
            corpus.append((tag, k, v))
    for f in sorted(glob.glob('_work/wufen/vol*.txt')):
        tag = '五分' + re.search(r'vol(\d+)', f).group(1)
        for i, line in enumerate(io.open(f, encoding='utf-8'), 1):
            line = line.rstrip('\n')
            if '\t' in line and re.match(r'^\d+-\d+\t', line):
                k, v = line.split('\t', 1)
            else:
                k, v = str(i), line
            if len(v) < 8:
                continue
            corpus.append((tag, k, v))
    return corpus

C = load_corpus()

def grams(s, n=3):
    s = re.sub(r'[，。、？！：；「」『』（）()\s]', '', s)
    return set(s[i:i+n] for i in range(max(0, len(s)-n+1)))

GC = [grams(v) for _, _, v in C]

def best(par, topn=4):
    g = grams(V[par])
    if not g:
        return []
    res = []
    for (tag, k, v), gg in zip(C, GC):
        if not gg:
            continue
        inter = len(g & gg)
        if inter < 6:
            continue
        score = inter / (min(len(g), len(gg)) + 1e-9)
        res.append((score, tag, k, v))
    res.sort(reverse=True)
    return res[:topn]

if __name__ == '__main__':
    args = [int(a) for a in sys.argv[1:]] or list(V)
    for p in args:
        print('### §%d (%d字) %s' % (p, len(V[p]), V[p][:40]))
        for score, tag, k, v in best(p):
            print('   %.2f %-8s %-7s %s' % (score, tag, k, v[:90]))
        print()
