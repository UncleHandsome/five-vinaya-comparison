# -*- coding: utf-8 -*-
import re
txt=open('findings_mk/vol20-21.md',encoding='utf-8').read()
lines=txt.split('\n')
keep=set(); dele=set(); narr=set()
cur=None
sec=None
for ln in lines:
    if ln.startswith('## 保留項'): sec='keep'
    elif ln.startswith('## 刪除項'): sec='del'
    elif ln.startswith('## 敘事抽取'): sec='narr'
    elif ln.startswith('## 存疑'): sec='x'
    elif ln.startswith('## 統計'): sec='s'
    m=re.match(r'^- 位置：(.+)$',ln)
    if m and sec in ('keep','narr'):
        s=m.group(1)
        v=None
        for part in re.split(r'[、，,]',s):
            mv=re.search(r'卷(\d+)',part)
            if mv: v=int(mv.group(1))
            for n in re.findall(r'段(\d+)',part):
                (keep if sec=='keep' else narr).add((v,int(n)))
    if sec=='del' and ln.startswith('| 卷'):
        cell=ln.split('|')[1].strip()
        mv=re.search(r'卷(\d+)',cell); v=int(mv.group(1))
        nums=re.findall(r'段(\d+)',cell)
        for n in nums: dele.add((v,int(n)))
        # ranges
        for a,b in re.findall(r'段(\d+)～段?(\d+)',cell):
            for k in range(int(a),int(b)+1): dele.add((v,k))
print('keep',len(keep),'del',len(dele),'narr',len(narr))
allp=set((20,i) for i in range(1,134))|set((21,i) for i in range(1,117))
cov=keep|dele|narr
print('missing',sorted(allp-cov))
print('extra',sorted(cov-allp))
print('overlap keep&del',sorted(keep&dele))
print('overlap narr&del',sorted(narr&dele))
print('overlap keep&narr',sorted(keep&narr))
