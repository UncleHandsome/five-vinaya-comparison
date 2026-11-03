import sys, os, glob

kwfile = sys.argv[1] if len(sys.argv) > 1 else '_work/kw.txt'
kws = [l.strip() for l in open(kwfile, encoding='utf-8') if l.strip()]
paths = sorted(glob.glob('_work/sifen/*.txt')) + sorted(glob.glob('_work/bundles/W*.txt'))
limit = 12
for kw in kws:
    print('#### KW:', kw)
    n = 0
    for p in paths:
        try:
            lines = open(p, encoding='utf-8').read().split('\n')
        except Exception:
            continue
        for ln in lines:
            if kw in ln:
                n += 1
                if n > limit:
                    break
                i = ln.find(kw)
                head = ln.split('\t')
                seg = head[0] if len(head) > 1 and len(head[0]) < 10 else ''
                s = max(0, i - 45)
                e = min(len(ln), i + 55)
                print('%s\t%s\t...%s...' % (os.path.basename(p), seg, ln[s:e]))
        if n > limit:
            break
    if n == 0:
        print('  (none)')
