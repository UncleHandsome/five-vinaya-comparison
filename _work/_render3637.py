# -*- coding: utf-8 -*-
import json,re,os
qs=json.load(open('_q3637b.json',encoding='utf-8'))
tpl=open('_tpl3637.md',encoding='utf-8').read()
def render(k):
    parts=qs[k]
    lines=[]
    for vol,seg,txt in parts:
        lines.append('  > 〔卷%d·段%d〕%s'%(vol,seg,txt))
    return '\n'.join(lines)
def repl(m):
    k=m.group(1)
    if k not in qs: raise KeyError(k)
    return render(k)
out=re.sub(r'@@q(\d+)@@',repl,tpl)
os.makedirs('findings_mk',exist_ok=True)
open('findings_mk/vol36-37.md','w',encoding='utf-8').write(out)
print('left tokens',len(re.findall(r'@@',out)))
print('len',len(out))
