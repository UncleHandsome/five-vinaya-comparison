#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全書完整性自檢。CI 或本地皆可跑，失敗時以非零碼退出。

檢查五事：
  一、各 HTML 是否正常閉合（防截斷）
  二、D-／S- 項號是否連續無跳、無重
  三、HTML 內部錨點是否全部可解析
  四、三書項數是否一致（對照本／矩陣／CSV）
  五、各分卷之 D 號是否首尾相接，無重疊、無斷裂

用法：
  python tools/verify_integrity.py
"""
import os, re, sys, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '03_成品')
WEB = os.path.join(ROOT, '05_網頁版')

fail = []


def err(msg):
    fail.append(msg)
    print('  ✗ ' + msg)


def ok(msg):
    print('  ✓ ' + msg)


# ── 一、HTML 閉合 ──
print('[1/5] HTML 閉合')
for f in sorted(os.listdir(WEB)):
    if not f.endswith('.html'):
        continue
    p = os.path.join(WEB, f)
    s = open(p, encoding='utf-8', errors='ignore').read()
    if not s.rstrip().endswith('</html>'):
        err('%s 未以 </html> 收尾，疑遭截斷' % f)
    elif '<main' not in s:
        err('%s 無 <main>，結構不完整' % f)
    else:
        ok('%s  %.1f MB' % (f, os.path.getsize(p) / 1048576))

# ── 二、項號連續 ──
print('[2/5] 項號連續')
md = open(os.path.join(OUT, '五部律差異對照本.md'), encoding='utf-8').read()
for pre in ('D', 'S'):
    nums = sorted(set(int(m) for m in re.findall(r'\*\*%s-(\d{4})\*\*' % pre, md)))
    if not nums:
        err('%s- 號一個也未找著' % pre)
        continue
    gaps = [(a, b) for a, b in zip(nums, nums[1:]) if b != a + 1]
    if gaps:
        err('%s- 跳號 %d 處，首例 %04d→%04d' % (pre, len(gaps), gaps[0][0], gaps[0][1]))
    elif nums[0] != 1:
        err('%s- 不從 0001 起（實起 %04d）' % (pre, nums[0]))
    else:
        ok('%s- 0001–%04d 共 %d 項，無跳號' % (pre, nums[-1], len(nums)))

# ── 三、錨點 ──
print('[3/5] HTML 錨點')
for f in sorted(os.listdir(WEB)):
    if not f.endswith('.html'):
        continue
    s = open(os.path.join(WEB, f), encoding='utf-8', errors='ignore').read()
    ids = set(re.findall(r'\bid="([^"]+)"', s))
    links = set(re.findall(r'href="#([^"]+)"', s))
    dead = links - ids - {''}
    if dead:
        err('%s 失效錨點 %d 個，如 %s' % (f, len(dead), ', '.join(sorted(dead)[:3])))
    else:
        ok('%s  id %d／內鏈 %d／失效 0' % (f, len(ids), len(links)))

# ── 四、三書項數 ──
print('[4/5] 三書項數')
nD = len(set(re.findall(r'\*\*D-(\d{4})\*\*', md)))
nS = len(set(re.findall(r'\*\*S-(\d{4})\*\*', md)))
try:
    with open(os.path.join(OUT, '五部律綜合異同矩陣.csv'), encoding='utf-8') as fh:
        nCSV = sum(1 for _ in fh) - 1
except Exception as e:
    nCSV = -1
    err('矩陣 CSV 讀取失敗：%s' % e)
mx = open(os.path.join(OUT, '五部律綜合異同矩陣.md'), encoding='utf-8').read()
nMX = len(re.findall(r'^\| *M-\d{4} ', mx, re.M))
if nCSV != nMX:
    err('CSV %d 行 ≠ 矩陣 MD %d 列' % (nCSV, nMX))
if nD + nS + 9 != nCSV:
    err('D %d ＋ S %d ＋ G/T 9 ＝ %d，與矩陣 %d 不符' % (nD, nS, nD + nS + 9, nCSV))
else:
    ok('D %d ＋ S %d ＋ G/T 9 ＝ 矩陣 %d' % (nD, nS, nCSV))

# ── 五、分卷首尾相接 ──
print('[5/5] 分卷首尾')
segs = []
for f in sorted(os.listdir(OUT)):
    m = re.match(r'五部律差異對照本_(卷.+?)\.md$', f)
    if not m:
        continue
    s = open(os.path.join(OUT, f), encoding='utf-8').read()
    d = sorted(set(int(x) for x in re.findall(r'\*\*D-(\d{4})\*\*', s)))
    if d:
        segs.append((f, d[0], d[-1], len(d)))
segs.sort(key=lambda t: t[1])
prev = None
for f, a, b, n in segs:
    if prev and a != prev + 1:
        err('%s 起於 D-%04d，前卷訖於 D-%04d，不接' % (f, a, prev))
    prev = b
    ok('%s  D-%04d–%04d（%d 項）' % (f, a, b, n))
if segs and (segs[0][1] != 1 or segs[-1][2] != nD):
    err('分卷合計 D-%04d–%04d，與全書 D-0001–D-%04d 不符' % (segs[0][1], segs[-1][2], nD))

print()
if fail:
    print('不合格 %d 項。' % len(fail))
    sys.exit(1)
print('全部通過。')
