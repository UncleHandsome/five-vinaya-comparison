# -*- coding: utf-8 -*-
import re
md=open('findings_mk/vol36-37.md',encoding='utf-8').read()
cov={36:set(),37:set()}
def add(v,a,b=None):
    b=b or a
    for i in range(a,b+1): cov[v].add(i)
# 保留項 位置
for m in re.finditer(r'^- 位置：卷(\d+)·段(\d+)(?:～(\d+))?',md,re.M):
    add(int(m.group(1)),int(m.group(2)),int(m.group(3)) if m.group(3) else None)
# 刪除表列
for m in re.finditer(r'^\| 卷(\d+) 段(\d+)～(\d+) \|',md,re.M):
    add(int(m.group(1)),int(m.group(2)),int(m.group(3)))
for m in re.finditer(r'^\| 卷(\d+) 段(\d+) \|',md,re.M):
    add(int(m.group(1)),int(m.group(2)))
# 敘事 位置
for m in re.finditer(r'^- 位置：段(\d+)～(\d+)',md,re.M):
    pass
miss36=[i for i in range(1,144) if i not in cov[36]]
miss37=[i for i in range(1,148) if i not in cov[37]]
print('miss36',miss36)
print('miss37',miss37)
print('dup? 檢查保留項位置重疊')
print('白話 count',md.count('- 白話：'),'保留項 count',len(re.findall(r'^### \d+\.',md,re.M)))
for h in ['## 保留項','## 刪除項（彙總）','## 敘事抽取','## 存疑','## 統計']:
    print(h, h in md)
