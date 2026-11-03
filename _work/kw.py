# -*- coding: utf-8 -*-
import io, os, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))
def load(p):
    out=[]
    for ln in io.open(p,encoding='utf-8'):
        ln=ln.rstrip('\n')
        if '\t' in ln:
            k,t=ln.split('\t',1)
            out.append((k,t))
    return out
CORP=[]
for fn in sorted(os.listdir(os.path.join(BASE,'sifen'))):
    if fn.endswith('.txt'):
        tag='SF'+fn.split('_')[0]
        for k,t in load(os.path.join(BASE,'sifen',fn)): CORP.append((tag+'-'+k,t))
for v in range(1,31):
    for k,t in load(os.path.join(BASE,'wufen','vol%02d.txt'%v)): CORP.append(('WF%d-%s'%(v,k),t))
for w in sys.argv[1:]:
    print('#### %s'%w)
    n=0
    for k,t in CORP:
        if w in t:
            n+=1
            if n<=8:
                i=t.find(w)
                print('  %s: %s'%(k,t[max(0,i-40):i+90]))
    print('  total=%d'%n)
