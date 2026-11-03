# -*- coding: utf-8 -*-
import re, os, sys
W = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def clean(q):
    for _ in range(3):
        q = re.sub(r'[（(〔]\s*段\s*\d+[^）)〕]{0,24}[）)〕]', '', q)
        q = re.sub(r'\*\*\s*段\s*\d+[^*]{0,12}\*\*', '', q)
        q = re.sub(r'[（(]\s*(?:節引|節錄|後段|中段|前段|末句|僅引[^）)]{0,12})[）)]', '', q)
        q = re.sub(r'段\s*\d+\s*(?:[～~\-–]\s*\d+\s*)?[：:]', '', q)
    return q


def blocks(path):
    text = open(path, encoding='utf-8').read()
    out, buf = [], []
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('>'):
            buf.append(s.lstrip('>').strip())
        else:
            if buf:
                out.append(''.join(buf)); buf = []
    if buf:
        out.append(''.join(buf))
    return out


for v in (24, 25, 28, 29):
    src = norm(''.join(l.rstrip('\n').split('\t', 1)[1]
                       for l in open(os.path.join(W, 'wufen/vol%02d.txt' % v), encoding='utf-8') if '\t' in l))
    for b in blocks(os.path.join(W, 'findings/vol%02d.md' % v)):
        if '底本：' in b or '`_work/' in b:
            continue
        q = clean(b)
        for seg in re.split(r'（中略[^）]*）|……|\.\.\.', q):
            n = norm(seg)
            if len(n) < 6 or n in src:
                continue
            lo, hi = 0, len(n)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if n[:mid] in src:
                    lo = mid
                else:
                    hi = mid - 1
            print('=== vol%d len=%d break@%d' % (v, len(n), lo))
            print('  OK :', n[max(0, lo - 25):lo])
            print('  BAD:', n[lo:lo + 25])
            # what follows in source after the ok-prefix?
            i = src.find(n[max(0, lo - 25):lo])
            print('  SRC:', src[i + len(n[max(0, lo - 25):lo]):i + len(n[max(0, lo - 25):lo]) + 40])
