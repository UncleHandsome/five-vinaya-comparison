# -*- coding: utf-8 -*-
import re, os
BASE = '<PROJ>/_work'
def load(v):
    d = {}
    for line in open(os.path.join(BASE, v), encoding='utf-8').read().split('\n'):
        line = line.rstrip('\r')
        if not line.strip():
            continue
        p = line.split('\t', 1)
        if len(p) == 2:
            try:
                d[int(p[0])] = p[1]
            except Exception:
                pass
    return d
v4 = load('sengqi/vol04.txt'); v5 = load('sengqi/vol05.txt')
md = open(os.path.join(BASE, 'findings_mk', 'vol04-05.md'), encoding='utf-8').read()

# 1) verify every 原文 quote line is substring of cited paragraph
quote_re = re.compile(r'^  > 卷([45])·段(\d+)(?:（[^）]*）)?：(.*)$')
bad = []
nq = 0
for line in md.split('\n'):
    m = quote_re.match(line)
    if not m:
        continue
    nq += 1
    vol = int(m.group(1)); para = int(m.group(2)); txt = m.group(3).strip()
    # strip leading quote marks variations
    src = (v4 if vol == 4 else v5).get(para, '')
    # the quote may be wrapped with 「」 and may contain trailing content; check core
    core = txt
    if core.startswith('「'):
        core = core[1:]
    if core.endswith('」'):
        core = core[:-1]
    if core not in src:
        # try also full original line
        bad.append((vol, para, txt[:60]))
print('quote lines checked:', nq)
print('quote substring failures:', len(bad))
for b in bad:
    print('  FAIL 卷%d·段%d: %r' % b)

# 2) coverage: parse 保留項 (位置 lines), 刪除項 rows (卷N·段X and 段A–B), 敘事抽取 (位置)
def add_range(covered, vol, lo, hi):
    for i in range(lo, hi + 1):
        covered.add((vol, i))

def parse_segs(s):
    # returns list of (lo,hi) for a paragraph token like '19','109–118','17–18','61、67'
    segs = []
    for tok in s.replace('，', '、').split('、'):
        tok = tok.strip()
        if not tok:
            continue
        mm = re.match(r'^(\d+)(?:[–-](\d+))?$', tok)
        if mm:
            a = int(mm.group(1)); b = int(mm.group(2)) if mm.group(2) else a
            segs.append((a, b))
    return segs

covered = set()
lines = md.split('\n')
# 保留 位置 lines
for i, line in enumerate(lines):
    m = re.match(r'^- 位置：(.*)$', line.strip())
    if m:
        s = m.group(1)
        for vm in re.finditer(r'卷([45])·段([\d、–\-]+)', s):
            vol = int(vm.group(1))
            for (lo, hi) in parse_segs(vm.group(2)):
                add_range(covered, vol, lo, hi)
# handle 保留 L1 位置 '段109–118' (only one 卷 token? it says 卷4·段109–118) -> covered above
# 刪除 rows: '| 卷4·段1–2 | ... |'  and '卷5·段X'
for line in lines:
    m = re.match(r'^\| (卷[45]·段[\d、–\-]+) \|', line)
    if m:
        token = m.group(1)
        vm = re.match(r'卷([45])·段([\d、–\-]+)', token)
        vol = int(vm.group(1))
        for (lo, hi) in parse_segs(vm.group(2)):
            add_range(covered, vol, lo, hi)
# 敘事 位置 lines: '- 位置：卷4·段42–68（字數約 ...）'
for line in lines:
    m = re.match(r'^- 位置：(卷[45]·段[\d、–\-]+)', line.strip())
    if m:
        vm = re.match(r'卷([45])·段([\d、–\-]+)', m.group(1))
        vol = int(vm.group(1))
        for (lo, hi) in parse_segs(vm.group(2)):
            add_range(covered, vol, lo, hi)

# but 保留 L1 位置 was '卷4·段109–118' -> parse gives 109-118 (need en-dash support) OK
missing4 = [i for i in range(1, 126) if (4, i) not in covered]
missing5 = [i for i in range(1, 102) if (5, i) not in covered]
print('vol4 uncovered paragraphs:', missing4)
print('vol5 uncovered paragraphs:', missing5)

# duplicates check: a paragraph listed in more than one bucket? do separate sets
def bucket_ranges(kind):
    res = {}
    # simplistic: not needed if no missing
    return res
print('total paragraphs vol4:', len([1 for i in range(1,126)]), 'vol5:', len([1 for i in range(1,102)]))
