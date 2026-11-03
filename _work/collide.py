# -*- coding: utf-8 -*-
"""Phase 2b: corpus-based collision for the 669 「四分所無」 (label C) items.

The title-overlap method in `matrix_islands.py` only compares drafts with each
other, so an item whose title is phrased differently in another canon is
invisible.  This pass goes to the corpora instead: for every C item it builds a
set of *rare* n-grams from the item's own wording, then looks for a paragraph in
each of the other three canons that contains several of them at once.  A
paragraph matching two or more rare terms is a collision candidate.

Rarity is measured against the target canon itself: a term that occurs in more
than `MAXPARA` paragraphs there carries no discriminating power, and a term that
occurs nowhere is useless for finding anything.

Output: `_work/collide.json`
    [{'canon','unit','no','title','vs':[{'canon','vol','seg','score',
      'terms':[...],'snip':'...'}...]}]
"""
import os, re, json, glob
from collections import defaultdict, Counter

W = os.path.dirname(os.path.abspath(__file__))
MAXPARA = int(os.environ.get('MAXPARA', 40))
MINSCORE = int(os.environ.get('MINSCORE', 2))
MAXTERM = 12          # keep the most discriminative terms per item

BAD = set('全無遍查未見三四五本二律誦祇有判罪戒法之者例與及其為而則所有無不得以於從若是此彼等亦皆即又故但唯'
          '一二三六七八九十百千萬多寡增減差別異同說製作犯輕重前後中上下內外時處人事物'
          '原文白話以是佛言諸比丘僧如是若復應當聽許爾時世尊')

CORP = {'四分': 'sifen', '五分': 'wufen', '十誦': 'shisong',
        '僧祇': 'sengqi', '根有': 'genben'}


def norm(s):
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def load(canon):
    """-> list of (vol, seg, text)"""
    d = os.path.join(W, CORP[canon])
    out = []
    for f in sorted(glob.glob(os.path.join(d, 'vol*.txt'))):
        v = int(re.search(r'vol(\d+)', f).group(1))
        for ln in open(f, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if '\t' not in ln:
                continue
            a, b = ln.split('\t', 1)
            if a.isdigit():
                out.append((v, int(a), b))
    return out


def grams(s, ks=(3, 4)):
    s = norm(s)
    out = set()
    for k in ks:
        for i in range(len(s) - k + 1):
            g = s[i:i + k]
            if set(g) & BAD:
                continue
            out.add(g)
    return out


rows = json.load(open(os.path.join(W, 'matrix_rows.json'), encoding='utf-8'))
C = [r for r in rows if r['absent4']]
print('C items', len(C))

# --- query terms per item ---------------------------------------------------
Q = []
for r in C:
    body = re.split(r'-\s*原文|原文：|-\s*白話|白話：', r['diff'] or '')[0]
    Q.append(grams((r['title'] or '') + '。' + body))

allq = set()
for q in Q:
    allq |= q
print('distinct query terms', len(allq))

# --- index only the query terms --------------------------------------------
paras, index = {}, {}
for canon in ('十誦', '僧祇', '根有'):
    ps = load(canon)
    paras[canon] = ps
    idx = defaultdict(list)
    for i, (v, s, t) in enumerate(ps):
        for g in grams(t):
            if g in allq:
                idx[g].append(i)
    index[canon] = idx
    print('%-3s paragraphs %5d  indexed terms %6d' % (canon, len(ps), len(idx)))

# --- score ----------------------------------------------------------------
def spans_of(text, terms):
    """Merge overlapping hit n-grams into maximal matched spans.

    Six overlapping 3-grams from one eight-character phrase are one piece of
    evidence, not six; counting merged spans keeps the score honest.
    """
    n = norm(text)
    iv = []
    for g in terms:
        st = 0
        while True:
            i = n.find(g, st)
            if i < 0:
                break
            iv.append((i, i + len(g)))
            st = i + 1
    if not iv:
        return []
    iv.sort()
    out = [list(iv[0])]
    for a, b in iv[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out if b - a >= 3]


res = []
for r, q in zip(C, Q):
    vs = []
    for canon in ('十誦', '僧祇', '根有'):
        if canon == r['canon']:
            continue
        idx = index[canon]
        # keep terms that are rare enough in this canon to discriminate
        use = [g for g in q if 0 < len(idx.get(g, ())) <= MAXPARA]
        if len(use) < MINSCORE:
            continue
        cnt = Counter()
        for g in use:
            for i in idx[g]:
                cnt[i] += 1
        cand = [i for i, c in cnt.items() if c >= MINSCORE]
        scored = []
        for i in cand:
            v, s, t = paras[canon][i]
            hit = [g for g in use if i in idx[g]]
            sp = spans_of(t, hit)
            nt = norm(t)
            raw = sorted({nt[a:b] for a, b in sp}, key=len, reverse=True)
            # drop strings that merely repeat part of a longer match: the same
            # phrase occurring twice in one paragraph is not two evidences
            texts = [x for x in raw if not any(x != y and x in y for y in raw)]
            cover = sum(len(x) for x in texts)
            # two independent matches, or one long rare string (a proper name)
            if not (len(texts) >= 2 or (texts and len(texts[0]) >= 4 and cover >= 4)):
                continue
            scored.append((len(texts), cover, i, texts, t))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        for nsp, cover, i, texts, t in scored[:2]:
            v, s, _ = paras[canon][i]
            vs.append({'canon': canon, 'vol': v, 'seg': s, 'score': nsp,
                       'cover': cover, 'terms': texts[:6], 'snip': t[:90]})
    if vs:
        vs.sort(key=lambda x: (-x['score'], -x['cover']))
        res.append({'canon': r['canon'], 'unit': r['unit'], 'no': r['no'],
                    'title': r['title'], 'vs': vs})

json.dump(res, open(os.path.join(W, 'collide.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('items with a candidate', len(res), '/', len(C))
print('span distribution', Counter(min(v['score'], 8) for x in res for v in x['vs']))
