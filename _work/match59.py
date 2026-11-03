import io, re, os, glob, sys
sys.path.insert(0,'.')
from ss import SF, WF
def clean(s):
    return re.sub(r'[^\u4e00-\u9fff]','',s)
vol=[l.rstrip('\n') for l in io.open('shisong/vol59.txt',encoding='utf-8')]
segs=[]
for i,l in enumerate(vol,1):
    t=clean(l)
    if len(t)<6: continue
    segs.append((i,t,l.strip()))
def grams(s,n=4):
    return set(s[j:j+n] for j in range(len(s)-n+1))
SFg=[(b,i,t,grams(clean(t))) for b,i,t in SF]
WFg=[(tag,t,grams(clean(t))) for tag,t in WF]
def best(seg, pool, topn=3):
    g=grams(seg)
    if not g: return []
    res=[]
    for item in pool:
        gg=item[-1]
        inter=len(g&gg)
        if inter==0: continue
        score=inter/len(g)
        res.append((score,item))
    res.sort(key=lambda x:-x[0])
    return res[:topn]
for i,t,raw in segs:
    print('='*70)
    print('SEG %d (%d chars): %s' % (i,len(t),raw[:60]))
    for score,item in best(t,SFg):
        print('  S %.2f %s-%d: %s' % (score,item[0],item[1],item[2][:110]))
    for score,item in best(t,WFg):
        print('  W %.2f %s: %s' % (score,item[0],item[1][:110]))
