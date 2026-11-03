# -*- coding: utf-8 -*-
"""Phase 2 of the plan: horizontal collision among the 四分所無 (label C) items.

Titles are short and phrased independently in each draft, so character-overlap
similarity finds nothing. What does travel across drafts is the *rare term*: a
person, a place, a numbered doctrine, a piece of monastic furniture. Items that
share two or more rare terms are the candidates for "兩律共有、四分所無".

Rare = appears in at most DF_MAX of the 2,141 retained items.
"""
import json, os, re, itertools
from collections import Counter, defaultdict

W = os.path.dirname(os.path.abspath(__file__))
DF_MAX = int(os.environ.get('DF_MAX', 4))
MIN_SHARED = int(os.environ.get('MIN_SHARED', 2))

rows = json.load(open(os.path.join(W, 'matrix_rows.json'), encoding='utf-8'))
C = [r for r in rows if r['absent4']]


# editorial and grammatical vocabulary: sharing these means nothing
BAD = set('全無遍查未見三四五本二律誦祇有判罪戒法之者例與及其為而則所有無不得以於從若是此彼等亦皆即又故但唯'
          '一二三六七八九十百千萬多寡增減差別異同說製作犯輕重前後中上下內外時處人事物')


def terms(s, n=(3, 4)):
    s = re.sub(r'[^\u4e00-\u9fff]', '', s)
    out = set()
    for k in n:
        for i in range(len(s) - k + 1):
            g = s[i:i + k]
            if set(g) & BAD:
                continue
            out.add(g)
    return out


# document frequency over ALL retained items, so "rare" means rare in the corpus
df = Counter()
for r in rows:
    df.update(terms(r['title']))

T = []
for r in C:
    t = {g for g in terms(r['title']) if df[g] <= DF_MAX}
    T.append(t)

by_term = defaultdict(list)
for i, ts in enumerate(T):
    for g in ts:
        by_term[g].append(i)

hits = Counter()
shared_terms = defaultdict(list)
for g, idxs in by_term.items():
    if len(idxs) < 2:
        continue
    for i, j in itertools.combinations(sorted(set(idxs)), 2):
        if C[i]['canon'] == C[j]['canon']:
            continue
        k = (i, j)
        hits[k] += 1
        shared_terms[k].append(g)

pairs = [(n, i, j) for (i, j), n in hits.items() if n >= MIN_SHARED]
pairs.sort(key=lambda x: (-x[0], x[1]))

print('label-C items:', len(C), dict(Counter(r['canon'] for r in C)))
print('rare terms (df<={}):'.format(DF_MAX), len(by_term))
print('candidate pairs sharing >={} rare terms:'.format(MIN_SHARED), len(pairs))
for n, i, j in pairs[:20]:
    a, b = C[i], C[j]
    print('  [{}] {}  ||  [{}] {}   <{}>'.format(
        a['canon'], a['title'][:30], b['canon'], b['title'][:30],
        '、'.join(sorted(shared_terms[(i, j)])[:4])))

json.dump([{'shared': n, 'terms': sorted(shared_terms[(i, j)]),
            'a': {k: C[i][k] for k in ('canon', 'unit', 'no', 'title', 'pos')},
            'b': {k: C[j][k] for k in ('canon', 'unit', 'no', 'title', 'pos')}}
           for n, i, j in pairs],
          open(os.path.join(W, 'island_pairs.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
