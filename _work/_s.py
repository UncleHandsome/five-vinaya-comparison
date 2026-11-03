import io, os, re, sys, glob

def load(d):
    out=[]
    for f in sorted(glob.glob(os.path.join(d,'*.txt'))):
        for line in io.open(f,encoding='utf-8'):
            line=line.rstrip('\n')
            if '\t' in line:
                n,t=line.split('\t',1)
            else:
                m=re.match(r'^(\d+)[：:]\s*(.*)$',line)
                if m: n,t=m.group(1),m.group(2)
                else: continue
            out.append((os.path.basename(f),n,t))
    return out

def main():
    kw=sys.argv[1]
    dirs=sys.argv[2:] or ['sifen','wufen','shisong']
    for d in dirs:
        rows=load(d)
        hits=[r for r in rows if kw in r[2]]
        print('=== %s  [%s]  hits=%d'%(d,kw,len(hits)))
        for f,n,t in hits[:40]:
            i=t.find(kw)
            print('  %s 段%s : ...%s...'%(f,n,t[max(0,i-40):i+60]))
if __name__=='__main__':
    main()
