#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""標題切分原型：先規則切，列出需人工處理者。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from errata import apply as apply_errata, clean_title
from build_compare import fix_terms

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))

OPEN, CLOSE = '（「『〈《【', '）」』〉》】'


def toplevel_marks(t):
    """回傳 (位置, 字元) 之頂層分隔符清單"""
    d, out = 0, []
    for i, ch in enumerate(t):
        if ch in OPEN:
            d += 1
        elif ch in CLOSE:
            d = max(0, d - 1)
        elif d == 0 and ch in '：:，；':
            out.append((i, ch))
    return out


def split_title(t, limit=16):
    t = (t or '').strip()
    if len(t) <= limit:
        return t, '', 'short'
    marks = toplevel_marks(t)
    # 1. 冒號優先（前段 4–limit）
    for i, ch in marks:
        if ch in '：:' and 4 <= i <= limit:
            return t[:i], t[i + 1:], 'colon'
    # 2. 逗號／分號（取最長之前段）
    cand = [i for i, ch in marks if ch in '，；' and 4 <= i <= limit]
    if cand:
        i = max(cand)
        return t[:i], t[i + 1:], 'comma'
    # 3. 首個頂層括號／引號之前
    d = 0
    for i, ch in enumerate(t):
        if ch in OPEN:
            if d == 0 and i >= 4:
                return t[:i], t[i:], 'paren'
            d += 1
        elif ch in CLOSE:
            d = max(0, d - 1)
    # 4. 放寬至 22 字
    for i, ch in marks:
        if 4 <= i <= 22:
            return t[:i], t[i + 1:], 'wide'
    return t, '', 'fail'


out = []
for r in rows:
    t = clean_title(fix_terms(apply_errata(r)['title'], r['canon']), r['id'])
    if len(t) < 30:
        continue
    m, s, how = split_title(t)
    out.append((how, r['id'], r['canon'], m, s, t))

from collections import Counter
print(Counter(x[0] for x in out))
json.dump([{'how': a, 'id': b, 'canon': c, 'main': d, 'sub': e, 'full': f}
           for a, b, c, d, e, f in out],
          open(os.path.join(W, '_split.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(len(out), '條 → _split.json')
