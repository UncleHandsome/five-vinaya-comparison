# -*- coding: utf-8 -*-
"""Quick corpus search for vol56 collation.
Usage: python _work/s56q.py 詞1 詞2 ...   (each term searched in sifen+wufen; prints ref + 40 chars context)
"""
import sys, glob, os, re, io
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_sifen():
    out = []
    for p in sorted(glob.glob('_work/sifen/*.txt')):
        name = os.path.basename(p).replace('.txt', '')
        for ln in open(p, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln.strip():
                continue
            parts = ln.split('\t', 1)
            if len(parts) == 2 and parts[0].strip().isdigit():
                out.append((name, parts[0].strip(), parts[1]))
            else:
                out.append((name, '0', ln))
    return out

def load_wufen():
    out = []
    for p in sorted(glob.glob('_work/bundles/W*.txt')):
        name = os.path.basename(p).replace('.txt', '')
        for ln in open(p, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln.strip():
                continue
            parts = ln.split('\t', 1)
            if len(parts) == 2 and re.match(r'^\d+-\d+$', parts[0].strip()):
                out.append((name, parts[0].strip(), parts[1]))
    return out

SF = load_sifen()
WF = load_wufen()

def show(corpus, term, label, ctx=45, limit=12):
    hits = [(n, p, t) for n, p, t in corpus if term in t]
    print(f'--- {label} 「{term}」 hits={len(hits)}')
    for n, p, t in hits[:limit]:
        i = t.find(term)
        s = max(0, i - ctx)
        e = min(len(t), i + len(term) + ctx)
        print(f'  [{n} {p}] ...{t[s:e]}...')

if __name__ == '__main__':
    for term in sys.argv[1:]:
        show(SF, term, '四分')
        show(WF, term, '五分')
        print()
