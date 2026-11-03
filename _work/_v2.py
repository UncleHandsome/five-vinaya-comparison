import re, io
md = io.open('findings_mk/vol12-13.md',encoding='utf-8').read()
main = md.split('## 保留項')[1].split('## 刪除項')[0]
for line in main.split('\n'):
    if line.startswith('- 位置：'):
        print(line.strip())
