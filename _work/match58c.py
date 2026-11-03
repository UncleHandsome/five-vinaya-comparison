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
T=dict(CORP)

STOCK=['白佛','佛言','波羅夷','偷蘭遮','突吉羅','波夜提','諸比丘','比丘','作是念','我將無','得波','是事','生疑','不得','無罪','是名','長老','世尊','若比','何等','云何','何以故']
def clean(s):
    for w in STOCK:
        s=s.replace(w,'○')
    return s

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

def ngrams(s,n=4):
    s=re.sub(r'[，。？！「」『』：；、（）()\s0-9○]','',s)
    return set(s[i:i+n] for i in range(len(s)-n+1))

G={k:ngrams(clean(t)) for k,t in CORP}
df=collections.Counter()
for k,g in G.items(): df.update(g)
inv=collections.defaultdict(list)
for k,g in G.items():
    for x in g: inv[x].append(k)

lo=int(sys.argv[1]); hi=int(sys.argv[2]); TOP=int(sys.argv[3]) if len(sys.argv)>3 else 4
for k,t in SS:
    n=int(k)
    if n<lo or n>hi: continue
    gs=ngrams(clean(t))
    sc=collections.Counter()
    for x in gs:
        d=df.get(x,0)
        if d==0 or d>30: continue
        w=1.0/(d**0.5)
        for kk in inv[x]: sc[kk]+=w
    res=[]
    for kk,_ in sc.most_common(50):
        L,snip=lcs(clean(t),clean(T[kk]))
        content=len(re.sub(r'[○，。？！「」：；、]','',snip))
        res.append((content+sc[kk]*0.5, L, content, kk, snip))
    res.sort(reverse=True)
    print('=== %s (%d字) %s'%(k,len(t),t[:30]))
    for s,L,c,kk,snip in res[:TOP]:
        print('  %s L=%d c=%d |%s| %s'%(kk,L,c,snip,T[kk][:130]))
