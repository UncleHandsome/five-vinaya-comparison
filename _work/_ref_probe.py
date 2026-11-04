#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試探：以「無／有」語境挑選律名，能否多判定殘留指代；並看既有判定會否被改動。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from errata import apply as apply_errata
from diff_fmt import CANONS, ORDER, NUM, RE_REF, _sets, expand_refs

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))


def sets2(row, tail):
    others, whole = _sets(row)
    no = [n for k, n in CANONS if n != row.get('canon') and row.get(k) == '無']
    yes = [n for k, n in CANONS if n != row.get('canon') and row.get(k) == '有']
    no.sort(key=ORDER.index)
    yes.sort(key=ORDER.index)
    if re.match(r'^[^，。；]{0,4}(無|不|缺|闕|未)', tail):
        return no
    if re.match(r'^[^，。；]{0,4}(有|同)', tail):
        return yes
    return None


gain, change = [], []
for r in rows:
    e = apply_errata(r)
    for fld in ('diff_full', 'title'):
        t = e.get(fld) or ''
        for m in RE_REF.finditer(t):
            n = NUM[m.group(1)]
            if m.group(2) and m.group(1) == '二':
                continue
            others, whole = _sets(e)
            cur = ('、'.join(others) if len(others) == n
                   else '、'.join(whole) if len(whole) == n else None)
            cand = sets2(e, t[m.end():])
            if cand is not None and len(cand) == n:
                if cur is None:
                    gain.append((r['id'], fld, m.group(), cand, t[max(0, m.start() - 20):m.end() + 20]))
                elif '、'.join(cand) != cur:
                    change.append((r['id'], fld, m.group(), cur, '、'.join(cand), t[max(0, m.start() - 20):m.end() + 20]))

print('可新增判定', len(gain))
for x in gain:
    print('  +', x[0], x[1], x[2], '→', '、'.join(x[3]), '｜', x[4])
print('會改動既有判定', len(change))
for x in change[:15]:
    print('  ~', x[0], x[2], x[3], '→', x[4], '｜', x[5])
