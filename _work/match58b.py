# -*- coding: utf-8 -*-
import io, os, sys, re, collections
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
            SF.append(('SF%s-%s'%(tag,k),t))
WF=[]
for v in range(1,31):
    for k,t in load(os.path.join(BASE,'wufen','vol%02d.txt'%v)):
        WF.append(('WF%d-%s'%(v,k),t))
CORP=SF+WF

def ngrams(s,n=5):
    s=re.sub(r'[，。？！「」『』：；、（）()\s0-9]','',s)
    return [s[i:i+n] for i in range(len(s)-n+1)]

# df
df=collections.Counter()
G={}
for k,t in CORP:
    g=set(ngrams(t))
    G[k]=g
    df.update(g)

def lcs(a,b):
    la,lb=len(a),len(b)
    prev=[0]*(lb+1); best=0; bi=0
    for i in range(1,la+1):
        cur=[0]*(lb+1); ai=a[i-1]
        for j in range(1,lb+1):
            if ai==b[j-1]:
                v=prev[j-1]+1
                cur[j]=v
                if v>best: best=v; bi=i-best
        prev=cur
    return best, a[bi:bi+best]

inv=collections.defaultdict(list)
for k,t in CORP:
    for g in G[k]:
        inv[g].append(k)

T=dict(CORP)
lo=int(sys.argv[1]); hi=int(sys.argv[2]); TOP=int(sys.argv[3]) if len(sys.argv)>3 else 4
for k,t in SS:
    n=int(k)
    if n<lo or n>hi: continue
    gs=ngrams(t)
    # weight by rarity
    sc=collections.Counter()
    for g in set(gs):
        d=df.get(g,0)
        if d==0 or d>25: continue
        w=1.0/(d**0.5)
        for kk in inv[g]:
            sc[kk]+=w
    cands=[kk for kk,_ in sc.most_common(60)]
    res=[]
    for kk in cands:
        L,snip=lcs(t,T[kk])
        res.append((L+sc[kk], L, sc[kk], kk, snip))
    res.sort(reverse=True)
    print('=== %s (%d字) %s'%(k,len(t),t[:36]))
    for s,L,w,kk,snip in res[:TOP]:
        print('  %s L=%d w=%.1f |%s| %s'%(kk,L,w,snip,T[kk][:150]))
