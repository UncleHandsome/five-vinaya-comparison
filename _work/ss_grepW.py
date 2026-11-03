import sys, glob, os

kwfile = sys.argv[1]
pat = sys.argv[2] if len(sys.argv) > 2 else 'W2*.txt'
kws = [l.strip() for l in open(kwfile, encoding='utf-8') if l.strip()]
paths = sorted(glob.glob('_work/bundles/' + pat))
print('PATHS:', [os.path.basename(p) for p in paths])
limit = 15
for kw in kws:
    print('#### KW:', kw)
    n = 0
    for p in paths:
        for ln in open(p, encoding='utf-8'):
            if kw in ln:
                n += 1
                if n > limit:
                    break
                i = ln.find(kw)
                seg = ln.split('\t')[0]
                s = max(0, i - 40)
                e = min(len(ln), i + 60)
                print('%s\t%s\t...%s...' % (os.path.basename(p), seg, ln[s:e].strip()))
        if n > limit:
            break
    if n == 0:
        print('  (none)')
