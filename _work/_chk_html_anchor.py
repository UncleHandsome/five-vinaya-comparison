#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查 05_網頁版 各 HTML 的內鏈是否全部有對應 id。"""
import os, re, sys

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(W, '05_網頁版')
bad_total = 0
for fn in sorted(os.listdir(D)):
    if not fn.endswith('.html'):
        continue
    s = open(os.path.join(D, fn), encoding='utf-8').read()
    ids = set(re.findall(r'id="([^"]+)"', s))
    hrefs = re.findall(r'href="#([^"]+)"', s)
    miss = [h for h in hrefs if h not in ids]
    bad_total += len(miss)
    print(f'{fn}: id {len(ids):5d}　內鏈 {len(hrefs):5d}　失效 {len(miss)}')
    for m in miss[:5]:
        print('   ✗', m)
print('合計失效', bad_total)
