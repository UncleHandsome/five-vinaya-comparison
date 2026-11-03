# -*- coding: utf-8 -*-
import re
md = open('findings_gu/vol02-03.md', encoding='utf-8').read()
cov = set()

# 1. 引文標籤
for m in re.finditer(r'〔卷([23])·段(\d+)〕', md):
    cov.add((int(m.group(1)), int(m.group(2))))

# 2. 刪除表每列
for line in md.splitlines():
    if not line.startswith('| 卷'):
        continue
    mm = re.match(r'\| 卷([23])·段(\d+)(?:[–～](\d+))?(?:（[^）]*）)? \|', line)
    if not mm:
        print('TABLE PARSE FAIL:', line[:40]); continue
    v = int(mm.group(1)); a = int(mm.group(2)); b = int(mm.group(3) or a)
    for s in range(a, b + 1):
        cov.add((v, s))

# 3. 敘事「位置：段X～Y」
for m in re.finditer(r'位置：段(\d+)[～–-](\d+)', md):
    # 敘事節屬卷2
    for s in range(int(m.group(1)), int(m.group(2)) + 1):
        cov.add((2, s))
# 4. 敘事單段
for m in re.finditer(r'位置：段(\d+)（', md):
    cov.add((2, int(m.group(1))))

miss = []
for v, tot in ((2, 68), (3, 54)):
    for s in range(1, tot + 1):
        if (v, s) not in cov:
            miss.append((v, s))
print('未覆蓋段:', miss)
print('覆蓋數:', len(cov))
