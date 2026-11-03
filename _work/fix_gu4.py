# -*- coding: utf-8 -*-
"""修《根本說一切有部毘奈耶_去重白話》四項已查證之文字缺陷（先備份＋印 SHA）：
  F1 卷1·段109 白話：『扇侘（式叉摩那）』為名相錯植 → 扇侘即扇搋（ṣaṇḍha，黃門無根）
  F2 卷48 保留項5：標題與差異說明作『誣惱』，底本與引文作『誼惱』→ 歸位
  F3 凡例八.1：『《四分律》尼律單提法第一至八十六戒』係尼律之限制，誤植於苾芻律之本書
  F4 目錄：『卷2、3』與正文『## 卷2、卷3』體例不對稱 → 目錄補『卷』字
usage: python fix_gu4.py [--dry]"""
import io, os, re, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, '根本說一切有部毘奈耶_去重白話')
BK = os.path.join(ROOT, '_work', 'gu_fix_bak')
NM = '根本說一切有部毘奈耶'
DRY = '--dry' in sys.argv

PAIRS = [
    ('扇侘（式叉摩那）、半擇迦（黃門、二形）',
     '扇侘（即扇搋，謂黃門、無根之人）、半擇迦（兼二形者）'),
    ('### 5. 詐言不知之動機為令他憂悔、誣惱時眾',
     '### 5. 詐言不知之動機為令他憂悔、誼惱時眾'),
    ('其因緣各異；根有特釋「意欲令他心生憂悔、誣惱時眾」，以惱亂大眾為犯相要素',
     '其因緣各異；根有特釋「意欲令他心生憂悔、誼惱時眾」，以惱亂大眾為犯相要素'),
    ('1. 本資料夾《四分律》尼律單提法第一至八十六戒僅存戒條列表，緣起從缺，'
     '此部分以戒條有無與內容異同為準，不以緣起有無判為本律獨有。',
     '1. 本書只校《經分別》五十卷之苾芻諸學處，未及苾芻尼律；'
     '對校諸律中亦有僅存戒條列表而緣起從缺之篇（如《四分律》尼律單提法第一至八十六戒），'
     '此類篇目不引為本書有無之據。'),
]

FILES = [f for f in sorted(os.listdir(D)) if f.endswith('.md')]
if not os.path.isdir(BK) and not DRY:
    os.makedirs(BK)
print('檔 %d｜%s' % (len(FILES), 'DRY' if DRY else '備份 → _work/gu_fix_bak'))
res = {p[0][:14]: 0 for p in PAIRS}
for f in FILES:
    p = os.path.join(D, f)
    md = io.open(p, encoding='utf-8').read()
    if not DRY:
        io.open(os.path.join(BK, f), 'wb').write(md.encode('utf-8'))
    n0 = md
    for old, new in PAIRS:
        c = md.count(old)
        if c:
            md = md.replace(old, new)
            res[old[:14]] += c
    # F4：目錄行補『卷』字（僅目錄之列，錨點不動）
    toc = 0
    out = []
    for l in md.split('\n'):
        m = re.match(r'^(- \[)卷(\d+)、(\d+)(　.*)$', l)
        if m:
            l = '%s卷%s、卷%s%s' % (m.group(1), m.group(2), m.group(3), m.group(4))
            toc += 1
        out.append(l)
    md = '\n'.join(out)
    res['目錄補卷字'] = res.get('目錄補卷字', 0) + toc
    if md != n0 and not DRY:
        io.open(p, 'w', encoding='utf-8').write(md)

for k, v in res.items():
    print('  %-18s 命中 %d%s' % (k, v, '  ←【未命中，須查原文】' if v == 0 else ''))
print('\n除錯檢查：全書仍含「式叉摩那）」於扇侘之後？',
      any('扇侘（式叉摩那）' in io.open(os.path.join(D, f), encoding='utf-8').read() for f in FILES))
