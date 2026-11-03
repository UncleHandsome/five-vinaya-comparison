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

SS=load(os.path.join(BASE,'shisong','vol58.txt'))
SF=[]
for fn in sorted(os.listdir(os.path.join(BASE,'sifen'))):
    if fn.endswith('.txt'):
        tag=fn.split('_')[0]
        for k,t in load(os.path.join(BASE,'sifen',fn)):
            SF.append(('%s-%s'%(tag,k),t))
WF=[]
for v in range(1,31):
    for k,t in load(os.path.join(BASE,'wufen','vol%02d.txt'%v)):
        WF.append(('%d-%s'%(v,k),t))

def grams(s,n=3):
    s=re.sub(r'[，。？！「」『』：；、（）()0-9]','',s)
    return set(s[i:i+n] for i in range(len(s)-n+1))

def lcs(a,b):
    # longest common substring length via dp (bounded)
    la,lb=len(a),len(b)
    if la*lb>4_000_000:
        a=a[:1500]; b=b[:1500]; la,lb=len(a),len(b)
    prev=[0]*(lb+1); best=0; bi=0
    for i in range(1,la+1):
        cur=[0]*(lb+1)
        ai=a[i-1]
        for j in range(1,lb+1):
            if ai==b[j-1]:
                cur[j]=prev[j-1]+1
                if cur[j]>best:
                    best=cur[j]; bi=i-best
        prev=cur
    return best, a[bi:bi+best]

def best(par,corpus,topn=2):
    g=grams(par)
    res=[]
    for k,t in corpus:
        if len(t)<8: continue
        gt=grams(t)
        inter=len(g&gt)
        score=inter/max(1,len(g))**0.5 + inter/max(1,len(gt))**0.5
        res.append((score,inter,k,t))
    res.sort(reverse=True)
    out=[]
    for score,inter,k,t in res[:topn]:
        L,snip=lcs(par,t)
        out.append((score,inter,L,k,snip,t))
    return out

if __name__=='__main__':
    lo=int(sys.argv[1]); hi=int(sys.argv[2])
    for k,t in SS:
        n=int(k)
        if n<lo or n>hi: continue
        print('=== %s (%d字) %s'%(k,len(t),t[:40]))
        for tag,corp in (('SF',SF),('WF',WF)):
            for score,inter,L,kk,snip,full in best(t,corp):
                print('  %s %s sc=%.1f shared3=%d LCS=%d | %s'%(tag,kk,score,inter,L,snip))
                print('     FULL: %s'%full[:220])
