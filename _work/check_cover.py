# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

md = open('_work/findings_ss/vol09-10.md', encoding='utf-8').read()

# kept paragraphs from 原文 blocks
kept = {'9': set(), '10': set()}
for m in re.finditer(r'> 段(\d+)：', md):
    pass
# kept locations come from 位置 lines and 原文 blocks: use 原文 block section only
section = md.split('## 刪除項')[0]
for m in re.finditer(r'> 段(\d+)：', section):
    pass
# Determine vol context per item by 位置 line
items = re.split(r'### \d+\. ', section)[1:]
for it in items:
    vol = '9' if '卷9-' in it.split('\n')[1] else '10'
    for m in re.finditer(r'> 段(\d+)：', it):
        kept[vol].add(int(m.group(1)))

# parse table ranges
table = md.split('## 刪除項')[1].split('## 存疑')[0]
covered = {'9': set(), '10': set()}
for line in table.split('\n'):
    if not line.startswith('| 9-') and not line.startswith('| 10-'):
        continue
    cell = line.split('|')[1].strip()
    vol = cell.split('-')[0]
    rest = cell.split('-', 1)[1]
    for part in rest.split('、'):
        part = part.strip()
        if '～' in part:
            a, b = part.split('～')
            for i in range(int(a), int(b) + 1):
                covered[vol].add(i)
        else:
            covered[vol].add(int(part))

for vol, total in (('9', 119), ('10', 80)):
    allp = set(range(1, total + 1))
    print('vol', vol, 'kept', sorted(kept[vol]))
    print('   missing from keep+cover:', sorted(allp - kept[vol] - covered[vol]))
    print('   overlap keep&cover:', sorted(kept[vol] & covered[vol]))
    print('   out of range:', sorted(x for x in covered[vol] if x > total))
