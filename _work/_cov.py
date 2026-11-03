import re, io
md = io.open('findings_mk/vol12-13.md',encoding='utf-8').read()
body = md.split('## 保留項')[1].split('## 統計')[0]
# find all 卷N·段X patterns and ranges
cov12=set(); cov13=set()
for m in re.finditer(r'卷(12|13)·段(\d+)(?:～段?(\d+))?', body):
    v=int(m.group(1)); a=int(m.group(2)); b=int(m.group(3)) if m.group(3) else a
    tgt = cov12 if v==12 else cov13
    for x in range(a,b+1): tgt.add(x)
print('卷12 missing:', sorted(set(range(1,48))-cov12))
print('卷13 missing:', sorted(set(range(1,41))-cov13))
