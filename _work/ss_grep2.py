import sys, os, re, glob
kws = sys.argv[1:]
paths = sorted(glob.glob('_work/sifen/*.txt')) + sorted(glob.glob('_work/bundles/W*.txt'))
for kw in kws:
    print('#### KW:', kw)
    n=0
    for p in paths:
        try:
            lines=open(p,encoding='utf-8').read().split('\n')
        except: continue
        for ln in lines:
            if kw in ln:
                n+=1
                if n>40: break
                # print prefix and 60 chars around first occurrence
                i=ln.find(kw)
                pre=ln[:i]
                # segment id is prefix before tab
                seg=ln.split('\t')[0] if '\t' in ln[:12] else ''
                s=max(0,i-50); e=min(len(ln),i+70)
                print(f'{os.path.basename(p)}\t{seg}\t...{ln[s:e]}...')
        if n>40: break
    if n==0: print('  (none)')
