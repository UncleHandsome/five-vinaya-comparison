#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盤點體例各項：標題過長、密集列舉、指代、組字式、無 S-ID。
只讀不寫，輸出清單供裁定。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from errata import apply as apply_errata, clean_title
from build_compare import fix_terms

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))
out = []


def title_of(r):
    return clean_title(fix_terms(apply_errata(r)['title'], r['canon']), r['id'])


# ── 1. 標題長度 ──
lens = []
for r in rows:
    t = title_of(r)
    lens.append((len(t), r['id'], r['canon'], t))
lens.sort(reverse=True)
over30 = [x for x in lens if x[0] >= 30]
over40 = [x for x in lens if x[0] >= 40]
print(f'[標題] ≥30字 {len(over30)}　≥40字 {len(over40)}　最長 {lens[0][0]}')
from collections import Counter
print('[標題] 分佈：', sorted(Counter(min(l[0] // 10 * 10, 80) for l in lens).items()))

# ── 2. 密集列舉：單句頓號 ≥10 ──
def sents(t):
    return [s for s in re.split(r'(?<=[。；！？])', t or '') if s.strip()]

dense = []
for r in rows:
    d = apply_errata(r).get('diff_full') or ''
    for s in sents(d):
        n = s.count('、')
        if n >= 10:
            dense.append((n, r['id'], r['canon'], s.strip()))
dense.sort(reverse=True)
print(f'[密集] 單句 ≥10頓號 {len(dense)} 項（涉及 {len(set(x[1] for x in dense))} 個 id）')

# ── 3. 指代 ──
refs = []
for r in rows:
    e = apply_errata(r)
    for fld in ('title', 'diff_full'):
        t = e.get(fld) or ''
        for m in re.finditer(r'[兩三二四]\s*律|本律|此律', t):
            refs.append((r['id'], fld, m.group(), t[max(0, m.start() - 25):m.start() + 25]))
print(f'[指代] 兩律/三律等 {len(refs)} 處（{len(set(x[0] for x in refs))} 個 id）')
print('[指代] 詞頻：', Counter(x[2] for x in refs).most_common())

# ── 4. 組字式 ──
gaiji = re.compile(r'\[[^\[\]]{1,14}\]|[\u3400-\u4DBF\uF900-\uFAFF]')
g = []
for r in rows:
    e = apply_errata(r)
    for fld in ('title', 'diff_full', 'orig', 'plain'):
        t = e.get(fld) or ''
        for m in gaiji.finditer(t):
            s = m.group()
            if re.fullmatch(r'\[[^\]]*[*/@＊][^\]]*\]', s):
                g.append((r['id'], fld, s))
print(f'[組字] 殘留 {len(g)} 處：', Counter(x[2] for x in g).most_common())

# ── 5. 無 S-ID ──
noid = [r['id'] for r in rows if not re.fullmatch(r'M-\d{4}', r['id'] or '')]
print(f'[編號] 非 M- 格式 {len(noid)}：', noid[:15])

# ── 輸出 ──
json.dump({
    'titles': [{'len': l, 'id': i, 'canon': c, 'title': t} for l, i, c, t in lens],
    'dense': [{'n': n, 'id': i, 'canon': c, 'sent': s} for n, i, c, s in dense],
    'refs': [{'id': i, 'fld': f, 'word': w, 'ctx': c} for i, f, w, c in refs],
    'gaiji': [{'id': i, 'fld': f, 's': s} for i, f, s in g],
}, open(os.path.join(W, '_inv.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n→ _inv.json')
print('\n最長 12 條：')
for l, i, c, t in lens[:12]:
    print(f'  {l:3d} {i} {c} {t}')
