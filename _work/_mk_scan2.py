import io,re,sys,os
sys.stdout.reconfigure(encoding='utf-8')
base='<PROJ>/_work/'
def load(f):
    d={}
    for line in io.open(base+f,encoding='utf-8'):
        p=line.rstrip('\n').split('\t',1)
        if len(p)<2:continue
        try: d[int(p[0])]=p[1]
        except: pass
    return d
V={'10':load('sengqi/vol10.txt'),'11':load('sengqi/vol11.txt')}
md=io.open(base+'findings_mk/vol10-11.md',encoding='utf-8').read()
print('=== 原文 mismatches (char-level) ===')
for m in re.finditer(r'>\s*〔卷(\d+)·段(\d+)〕(.*)',md):
    v,n,q=m.group(1),int(m.group(2)),m.group(3).strip()
    src=V[v].get(n,'')
    if q in src: continue
    # find longest common prefix to locate the mismatch
    i=0
    while i<len(q) and q[i] in src:
        # crude: locate mismatch by scanning for first char not in src at expected pos
        break
    # split at ellipsis
    parts=[p.strip() for p in re.split(r'……|…',q) if p.strip()]
    for p in parts:
        if p.startswith('（'): continue
        if p in src: continue
        # locate first bad char
        for k in range(len(p)):
            if p[:k+1] not in src:
                print('卷%s段%d: at %d -> %r' % (v,n,k,p[max(0,k-12):k+12]))
                print('   src :',repr(src[src.find(p[max(0,k-6):k]):src.find(p[max(0,k-6):k])+20]) if p[max(0,k-6):k] in src else '')
                break
print('=== chars in md not present in base corpus volumes ===')
allsrc=''.join(''.join(V[k].values()) for k in V)
uniq=set(md)
sus=[c for c in uniq if c.strip() and c not in allsrc]
print(''.join(sorted(sus)))
