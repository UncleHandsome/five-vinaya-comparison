import io, os, glob, re, sys
def load_sifen():
    out=[]
    for f in sorted(glob.glob('sifen/*.txt')):
        base=os.path.basename(f)[:3]
        lines=io.open(f,encoding='utf-8').read().split('\n')
        idx=0
        for ln in lines:
            ln=ln.strip()
            if not ln: continue
            idx+=1
            out.append((base, idx, ln))
    return out
def load_wufen():
    out=[]
    for f in sorted(glob.glob('bundles/W*.txt')):
        lines=io.open(f,encoding='utf-8').read().split('\n')
        for ln in lines:
            if '\t' not in ln: continue
            tag,txt=ln.split('\t',1)
            tag=tag.strip(); txt=txt.strip()
            if not re.match(r'^\d+-\d+$',tag): continue
            out.append((tag, txt))
    return out
SF=load_sifen(); WF=load_wufen()
def gs(kw, limit=18, n=1):
    hits=[x for x in SF if kw in x[2]]
    print('### SIFEN [%s] hits=%d' % ('+'.join(kw) if isinstance(kw,list) else kw, len(hits)))
    for b,i,t in hits[:limit]:
        print('  %s-%d: %s' % (b,i,t[:n and 260]))
def gw(kw, limit=18, n=1):
    hits=[x for x in WF if kw in x[1]]
    print('### WUFEN [%s] hits=%d' % ('+'.join(kw) if isinstance(kw,list) else kw, len(hits)))
    for tag,t in hits[:limit]:
        print('  %s: %s' % (tag,t[:n and 260]))
