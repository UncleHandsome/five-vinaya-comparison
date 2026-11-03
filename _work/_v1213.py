import re, io, sys
src = io.open('sengqi/vol12.txt',encoding='utf-8').read()+io.open('sengqi/vol13.txt',encoding='utf-8').read()
src = re.sub(r'^\s*\d+\t','',src,flags=re.M).replace('\n','')
src = re.sub(r'\s','',src)
md = io.open('findings_mk/vol12-13.md',encoding='utf-8').read()
main = md.split('## 保留項')[1].split('## 刪除項')[0]
ok=bad=0; tot=0
for line in main.split('\n'):
    if not line.startswith('  > '): continue
    t = line[4:].strip()
    t = re.sub(r'^〔[^〕]*〕','',t)
    if t.startswith('（中略'): continue
    t = re.sub(r'（中略[^）]*）','',t)
    t = re.sub(r'\s','',t)
    tot += len(re.findall(r'[\u4e00-\u9fff]',t))
    if t in src: ok+=1
    else:
        bad+=1
        print('  X', t[:60])
print('quotes OK:',ok,'BAD:',bad)
print('retained CJK:',tot)
srcCJK = len(re.findall(r'[\u4e00-\u9fff]', src))
print('base CJK:', srcCJK, 'ratio %.1f%%'%(100.0*tot/srcCJK))
