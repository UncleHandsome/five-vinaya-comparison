# -*- coding: utf-8 -*-
import re
def load(f):
    d={}
    for l in open(f,encoding='utf-8').read().split('\n'):
        if not l.strip(): continue
        m=re.match(r'^(\d+)\t(.*)$', l)
        if m: d[int(m.group(1))]=m.group(2)
    return d
V={36:load('sengqi/vol36.txt'),37:load('sengqi/vol37.txt')}
md=open('findings_mk/vol36-37.md',encoding='utf-8').read()
bad=[];cnt=0;segs=set()
for line in md.split('\n'):
    m=re.match(r'^\s*> 〔卷(\d+)·段(\d+)〕(.*)$', line)
    if not m: continue
    cnt+=1
    v,s,t=int(m.group(1)),int(m.group(2)),m.group(3)
    segs.add((v,s))
    if t not in V[v][s]:
        bad.append((v,s,t[:30]))
print('quotes',cnt,'bad',len(bad))
for b in bad[:20]: print(b)
# 簡化字檢查
simp='这说门开兴计与么价处头对录怀户扩时来约节装让论话还进随项须风龄国图应发变边过当经历严产认识为书东车轮转轻点热爱业务'
hits=[]
for ch in set(simp):
    if ch in md: hits.append((ch,md.count(ch)))
print('simp',sorted(hits))
# 段覆蓋
miss36=[i for i in range(1,144) if (36,i) not in segs]
miss37=[i for i in range(1,35) if (37,i) not in segs]
print('miss36',miss36)
print('miss37',miss37)
