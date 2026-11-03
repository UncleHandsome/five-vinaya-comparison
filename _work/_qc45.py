# -*- coding: utf-8 -*-
import re, os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
def load(fn):
    d = {}
    for line in open(os.path.join(BASE, 'genben', fn), encoding='utf-8').read().split('\n'):
        line = line.replace('\r','')
        if not line.strip(): continue
        p = line.split('\t',1)
        if len(p)==2: d[int(p[0])] = p[1]
    return d
SRC = {'4': load('vol04.txt'), '5': load('vol05.txt')}
md = open(os.path.join(BASE,'findings_gu','vol04-05.md'), encoding='utf-8').read()
lines = md.split('\n')

# 1) 收集引文行
pat = re.compile(r'^\s*> 〔卷([45])·段(\d+)〕(.*)$')
blocks = []   # (vol, seg, text)
cur = None
for ln in lines:
    m = pat.match(ln)
    if m:
        v, s, t = m.group(1), int(m.group(2)), m.group(3)
        if cur and cur[0]==v and cur[1]==s:
            cur[2] += t
        else:
            if cur: blocks.append(cur)
            cur = [v, s, t]
    else:
        if cur: blocks.append(cur); cur = None
if cur: blocks.append(cur)

bad = []
for v, s, t in blocks:
    if t not in SRC[v][s]:
        bad.append((v, s, t[:60]))
print('引文塊數 =', len(blocks))
print('逐字不符 =', len(bad))
for b in bad[:10]: print('  !!', b)

# 2) 段號是否存在
miss = [(v,s) for v,s,t in blocks if s not in SRC[v]]
print('段號不存在 =', len(miss), miss[:5])

# 3) 簡化字掃描
simp = '这应说门开兴计与么价处头对录怀户扩时来约节装让论话还进随项须风龄为个样义归万与书习争亏仅从众优会伤众'
found = {}
for i, ln in enumerate(lines, 1):
    for ch in ln:
        if ch in simp:
            found.setdefault(ch, []).append(i)
print('簡化字可疑 =', {k: v[:3] for k,v in found.items()})

# 4) 五節
for sec in ['## 保留項','## 刪除項（彙總）','## 敘事抽取','## 存疑','## 統計']:
    print(sec, '->', sec in md)

# 5) 敘事首末句長度
for m in re.finditer(r'首句[：:]\s*「(.+?)」', md):
    t = m.group(1)
    if len(t) > 40: print('首句過長', len(t), t)
for m in re.finditer(r'末句[：:]\s*「(.+?)」', md):
    t = m.group(1)
    if len(t) > 40: print('末句過長', len(t), t)
print('檢查完畢')
