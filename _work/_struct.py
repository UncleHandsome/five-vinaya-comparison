import re, io
md = io.open('findings_mk/vol12-13.md',encoding='utf-8').read()
main = md.split('## 保留項')[1].split('## 刪除項')[0]
items = re.split(r'^### ', main, flags=re.M)[1:]
need = ['- 位置：','- 四分律對照：','- 五分律對照：','- 十誦律對照：','- 差異說明：','- 原文：','- 白話：']
for it in items:
    title = it.split('\n')[0][:40]
    miss = [n for n in need if n not in it]
    if miss: print('MISSING', title, miss)
print('items:', len(items))
secs = re.findall(r'^## (.+)$', md, flags=re.M)
print('sections:', secs)
