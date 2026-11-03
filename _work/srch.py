import sys, os, re, glob
pat=sys.argv[1]
dirs=sys.argv[2:] or ['_work/sifen','_work/bundles']
for d in dirs:
    for f in sorted(glob.glob(os.path.join(d,'*.txt'))):
        try:
            txt=open(f,encoding='utf-8').read().splitlines()
        except: continue
        for i,ln in enumerate(txt,1):
            if re.search(pat,ln):
                # print label
                lbl=''
                m=re.match(r'^(\d+)\t(.*)$',ln)
                if m: lbl=f[0:80]+' '+m.group(1)
                else: lbl=f'{os.path.basename(f)} L{i}'
                s=re.search(pat,ln)
                a=max(0,s.start()-40); b=min(len(ln),s.end()+60)
                print(lbl,'|',ln[a:b].replace('\t',' '))
