# -*- coding: utf-8 -*-
import re, os
W = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


src = norm(''.join(l.rstrip('\n').split('\t', 1)[1] for l in open(os.path.join(W, 'wufen/vol15.txt'), encoding='utf-8') if '\t' in l))
txt = open(os.path.join(W, 'findings/vol15.md'), encoding='utf-8').read()
# first item block
blk = re.split(r'^### ', txt, flags=re.M)[1]
lines = [l.strip().lstrip('>').strip() for l in blk.split('\n') if l.strip().startswith('>')]
q = ''.join(lines)
q = re.sub(r'^\s*（[^）]{0,20}）\s*', '', q)
q = re.sub(r'（段\s*\d+[^）]{0,8}）', '', q)
nq = norm(q)
print('quote len', len(nq))
print('head', nq[:40])
print('tail', nq[-40:])
print('in src?', nq in src)
# bisect: find longest prefix present
lo, hi = 0, len(nq)
while lo < hi:
    mid = (lo + hi + 1) // 2
    if nq[:mid] in src:
        lo = mid
    else:
        hi = mid - 1
print('longest prefix ok', lo, 'of', len(nq))
print('break at:', nq[max(0, lo - 30):lo + 30])
