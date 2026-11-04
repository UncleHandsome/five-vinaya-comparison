#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""節名體檢：過短、以虛字收尾、與戒文首句不符者列出。"""
import glob, io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_compare as bc

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print('W =', W)
_pat = os.path.join(W, '03_成品', '五部律差異對照本_卷*.md')
print('glob =', _pat)
print('hit  =', len(glob.glob(_pat)))
rows = []
for f in sorted(glob.glob(os.path.join(W, '03_成品', '五部律差異對照本_卷*.md'))):
    vol = os.path.basename(f)[len('五部律差異對照本_'):-3]
    for ln in io.open(f, encoding='utf-8'):
        m = re.match('^##### (第[\u4e00-\u9fa5]+戒)\u3000(.*)$', ln.rstrip('\n'))
        if m:
            rows.append((vol, m.group(1), m.group(2)))

print('節名總數', len(rows))

TAIL = ('故', '已', '者', '時', '若', '而', '與', '如是語', '如是', '竟')
short = [x for x in rows if len(x[2]) <= 5]
tail = [x for x in rows if x[2].endswith(TAIL) and len(x[2]) <= 12]

print('\n— 節名 <=5 字：%d' % len(short))
for x in short:
    print('   %-18s %s  %s' % (x[0], x[1], x[2]))

print('\n— 以虛字收尾且 <=12 字：%d' % len(tail))
for x in tail:
    print('   %-18s %s  %s' % (x[0], x[1], x[2]))
