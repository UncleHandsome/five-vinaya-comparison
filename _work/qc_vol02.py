# -*- coding: utf-8 -*-
import re, sys

md = open('_work/findings_ss/vol02.md', encoding='utf-8').read()
lines = open('_work/shisong/vol02.txt', encoding='utf-8').read().splitlines()
paras = {}
for line in lines:
    a = line.split('\t')
    if len(a) >= 2 and a[0].isdigit():
        paras[int(a[0])] = a[1]

full = ''.join(paras.values())

# 1. verify blockquotes
bad = []
quotes = []
for ln in md.splitlines():
    if ln.startswith('  > '):
        q = ln[4:].strip()
        if not q:
            continue
        quotes.append(q)
        if q not in full:
            bad.append(q[:40])
print('quotes:', len(quotes), 'bad:', len(bad))
for b in bad:
    print('  BAD:', b)

# 2. coverage
covered = set()
# item positions
for m in re.finditer(r'^- 位置：(.+)$', md, re.M):
    s = m.group(1)
    for part in re.split(r'[、,，]', s):
        nums = re.findall(r'(\d+)(?:–(\d+))?', part)
        for a, b in nums:
            a = int(a)
            b = int(b) if b else a
            if a == 4 and '中段' in part:
                covered.add(4)
            else:
                for n in range(a, b + 1):
                    covered.add(n)
print('covered by items:', sorted(covered))

# deletion table ranges
delcov = set()
for ln in md.splitlines():
    if ln.startswith('| ') and '–' in ln.split('|')[1]:
        cell = ln.split('|')[1].strip()
        nums = re.findall(r'(\d+)(?:–(\d+))?', cell)
        for a, b in nums:
            a = int(a)
            b = int(b) if b else a
            for n in range(a, b + 1):
                delcov.add(n)
    elif ln.startswith('| '):
        cell = ln.split('|')[1].strip()
        if cell.isdigit():
            delcov.add(int(cell))
print('deleted:', sorted(delcov))
missing = [n for n in range(1, 49) if n not in covered and n not in delcov]
print('MISSING:', missing)
both = [n for n in range(1, 49) if n in covered and n in delcov]
print('BOTH:', both)

# 3. simplified char check (rough list)
simp = '义为说语时东车马鸟龙门问间闻见观对难应还边这等么与书听师广众个将无发当会来後'
# only check for chars not present in source
diff = set(md) - set(full)
cand = [c for c in diff if c in simp]
print('SUSPECT SIMPLIFIED:', cand)
