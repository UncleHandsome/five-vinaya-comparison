import glob,re,sys,json
segs=[]
for f in sorted(glob.glob('shisong/vol*.txt')):
    v=int(re.search(r'vol(\d+)',f).group(1))
    for ln in open(f,encoding='utf-8'):
        ln=ln.rstrip('\n')
        if '\t' not in ln: continue
        n,t=ln.split('\t',1)
        if not n.isdigit(): continue
        segs.append((v,int(n),t))
print('segs',len(segs))
def q(*kws,ctx=0,w=60,limit=8):
    print('='*10,' '.join(kws))
    for kw in kws:
        hits=[(v,n,t) for v,n,t in segs if kw in t]
        print(f'  [{kw}] {len(hits)}')
        for v,n,t in hits[:limit]:
            i=t.find(kw)
            print(f'    {v}-{n}: ...{t[max(0,i-w):i+w]}...')
for kw in sys.argv[1:]:
    q(kw)
