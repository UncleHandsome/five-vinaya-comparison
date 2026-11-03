# -*- coding: utf-8 -*-
"""Find candidate 十誦 paragraphs for each 五分 retained item.

Both texts are Chinese translations of the same underlying Vinaya material, so
even across translators there is heavy shared vocabulary.  We score every 十誦
paragraph by how many *rare* character n-grams it shares with the 五分 item,
where "rare" means the gram occurs in only a small fraction of paragraphs.
"""
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict

W = os.path.dirname(os.path.abspath(__file__))


def load_corpus(base):
    """{vol: {para: text}} plus a flat list of (vol, para, norm_text)."""
    vols = {}
    flat = []
    for f in sorted(glob.glob(os.path.join(W, base, 'vol*.txt'))):
        v = int(re.search(r'vol(\d+)', f).group(1))
        d = {}
        for ln in open(f, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if '\t' not in ln:
                continue
            a, b = ln.split('\t', 1)
            if a.isdigit():
                d[int(a)] = b
        vols[v] = d
        for p, t in d.items():
            flat.append((v, p, norm(t)))
    return vols, flat


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def grams(s, lo=2, hi=4):
    s = norm(s)
    out = set()
    for k in range(lo, hi + 1):
        for i in range(len(s) - k + 1):
            out.add(s[i:i + k])
    return out


def items(path):
    txt = open(path, encoding='utf-8').read()
    out = []
    for p in re.split(r'^### ', txt, flags=re.M)[1:]:
        head = p.split('\n', 1)[0]
        m = re.match(r'(\d+)\.\s*(.*)', head)
        if m:
            out.append({'no': int(m.group(1)), 'title': m.group(2).strip(), 'body': p})
    return out


def field(body, name):
    m = re.search(r'^-\s*' + name + r'[：:](.*)$', body, re.M)
    return m.group(1).strip() if m else ''


def quotes(body):
    """Quoted 五分 text: the 原文 block, minus the paragraph label lines."""
    m = re.search(r'^-\s*原文[：:]\s*$(.*?)(?=^-\s*白話|\Z)', body, re.M | re.S)
    seg = m.group(1) if m else body
    out = []
    for ln in seg.split('\n'):
        s = ln.strip()
        if s.startswith('>'):
            s = re.sub(r'^>\s*', '', s)
            s = re.sub(r'^\*\*[^*]*\*\*\s*', '', s)
            s = re.sub(r'^〔[^〕]*〕\s*', '', s)
            if norm(s):
                out.append(s)
    return ''.join(out)


def build():
    vols, flat = load_corpus('shisong')
    n = len(flat)
    df = defaultdict(int)
    pgrams = []
    for v, p, t in flat:
        g = grams(t)
        pgrams.append(g)
        for x in g:
            df[x] += 1
    print('paragraphs', n, 'distinct grams', len(df))

    post = defaultdict(list)
    for i, g in enumerate(pgrams):
        for x in g:
            post[x].append(i)

    MAXDF = float(os.environ.get('MAXDF', '0.02'))  # gram must be in <=2% of paras
    res = {}
    for f in sorted(glob.glob(os.path.join(W, 'findings', 'vol*.md'))):
        v = int(re.search(r'vol(\d+)', f).group(1))
        for it in items(f):
            q = quotes(it['body'])
            qg = [x for x in grams(q) if len(x) >= 3 and df.get(x, 0) <= MAXDF * n]
            # longer grams carry more signal
            score = defaultdict(float)
            for x in qg:
                w = len(x) - 1.5
                idf = math.log(n / max(df[x], 1))
                for i in post.get(x, ())[:400]:
                    score[i] += w * idf
            best = sorted(score.items(), key=lambda kv: -kv[1])[:4]
            cands = []
            for i, sc in best:
                vv, pp, tt = flat[i]
                cands.append({'vol': vv, 'para': pp, 'score': round(sc, 1),
                              'text': vols[vv][pp][:200]})
            res['%d-%d' % (v, it['no'])] = {'vol': v, 'no': it['no'],
                                            'title': it['title'],
                                            'nq': len(qg), 'cands': cands}
    json.dump(res, open(os.path.join(W, 'ss_cands.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    hit = sum(1 for r in res.values() if r['cands'])
    print('items', len(res), 'with candidates', hit)


if __name__ == '__main__':
    build()
