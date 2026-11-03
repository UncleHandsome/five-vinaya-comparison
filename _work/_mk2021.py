# -*- coding: utf-8 -*-
import re, io
def load(v):
    d={}
    for line in open('sengqi/vol%d.txt'%v,encoding='utf-8'):
        m=re.match(r'^(\d+)\t(.*)$',line.rstrip('\n'))
        if m: d[int(m.group(1))]=m.group(2)
    return d
S={20:load(20),21:load(21)}
def q(v,n,start=None,end=None):
    t=S[v][n]; i=0
    if start:
        i=t.index(start)
    j=len(t)
    if end:
        j=t.index(end,i)+len(end)
    return '> 〔卷%d·段%d〕%s'%(v,n,t[i:j])
