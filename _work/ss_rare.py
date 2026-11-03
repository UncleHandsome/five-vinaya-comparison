# -*- coding: utf-8 -*-
"""Candidate finder for 五分 items that have no citation evidence.

Strategy: build an inverted index of *rare* n-grams (absolute document frequency
<= DFCAP) over the 十誦 corpus, then for each query item collect the paragraphs
that share at least MINHIT distinct rare grams.  Rare grams are mostly proper
nouns, numerals-in-compounds and technical terms, which survive translation.
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict

W = os.path.dirname(os.path.abspath(__file__))
DFCAP = int(os.environ.get('DFCAP', '6'))
MINHIT = int(os.environ.get('MINHIT', '2'))


def norm(s):
    return re.sub(r'[^\u4e00-\u9fff]', '', re.sub(r'[\s　]', '', s))


def load():
    vols, flat = {}, []
    for f in sorted(glob.glob(os.path.join(W, 'shisong', 'vol*.txt'))):
        v = int(re.search(r'vol(\d+)', f).group(1))
        d = {}
        for ln in open(f, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if '\t' in ln:
                a, b = ln.split('\t', 1)
                if a.isdigit():
                    d[int(a)] = b
        vols[v] = d
        for p, t in d.items():
            flat.append((v, p, norm(t)))
    return vols, flat


def items(path):
    txt = open(path, encoding='utf-8').read()
    out = []
    for p in re.split(r'^### ', txt, flags=re.M)[1:]:
        h = p.split('\n', 1)[0]
        m = re.match(r'(\d+)\.\s*(.*)', h)
        if m:
            out.append({'no': int(m.group(1)), 'title': m.group(2).strip(), 'body': p})
    return out


def field(b, n):
    m = re.search(r'^-\s*' + n + r'[：:](.*)$', b, re.M)
    return m.group(1).strip() if m else ''


STOP = set('比丘僧佛律戒犯不無有是為以於而則與及若此彼等亦皆即又故但唯說作得應聽從'
           '一二三四五六七八九十百千萬多少前後中上下內外時處人事物者之所其')


def grams(s, lo=2, hi=4):
    s = norm(s)
    out = set()
    for k in range(lo, hi + 1):
        for i in range(len(s) - k + 1):
            g = s[i:i + k]
            if g[0] in STOP and g[-1] in STOP:
                continue
            out.add(g)
    return out


def main():
    vols, flat = load()
    df = defaultdict(int)
    for v, p, t in flat:
        for g in grams(t):
            df[g] += 1
    post = defaultdict(list)
    for i, (v, p, t) in enumerate(flat):
        for g in grams(t):
            if df[g] <= DFCAP:
                post[g].append(i)
    print('paras', len(flat), 'rare grams', len(post))

    res = {}
    for f in sorted(glob.glob(os.path.join(W, 'findings', 'vol*.md'))):
        v = int(re.search(r'vol(\d+)', f).group(1))
        for it in items(f):
            q = field(it['body'], '原文') + ' ' + it['title'] + ' ' + field(it['body'], '差異說明')
            qg = [g for g in grams(q) if df.get(g, 0) <= DFCAP]
            cnt = defaultdict(int)
            for g in qg:
                for i in post.get(g, ()):
                    cnt[i] += 1
            best = [(i, c) for i, c in cnt.items() if c >= MINHIT]
            best.sort(key=lambda x: -x[1])
            cands = []
            for i, c in best[:4]:
                vv, pp, tt = flat[i]
                cands.append({'vol': vv, 'para': pp, 'hits': c,
                              'terms': sorted({g for g in qg if g in tt})[:8],
                              'text': vols[vv][pp][:180]})
            res['%d-%d' % (v, it['no'])] = {'title': it['title'], 'cands': cands}
    json.dump(res, open(os.path.join(W, 'ss_rare.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    n = sum(1 for r in res.values() if r['cands'])
    print('items', len(res), 'with candidates', n)


if __name__ == '__main__':
    main()
