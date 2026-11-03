import re, sys, glob, os
base = os.path.dirname(os.path.abspath(__file__))

def load(school, vols):
    out = []
    for v in vols:
        p = os.path.join(base, school, 'vol%02d.txt' % v)
        if not os.path.exists(p): continue
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            m = re.match(r'^(\d+)\t(.*)$', line)
            if m:
                out.append((v, int(m.group(1)), m.group(2)))
    return out

def search(school, vols, kws, ctx=60, limit=40):
    rows = load(school, vols)
    for kw in kws:
        print('=== %s :: %s ===' % (school, kw))
        n = 0
        for v, seg, txt in rows:
            if kw in txt:
                n += 1
                if n > limit: 
                    print('  ...more'); break
                i = txt.find(kw)
                s = max(0, i-ctx); e = min(len(txt), i+len(kw)+ctx)
                print('  vol%02d 段%d: ...%s...' % (v, seg, txt[s:e]))
        if n == 0:
            print('  (未見)')

if __name__ == '__main__':
    school = sys.argv[1]
    vols = range(int(sys.argv[2]), int(sys.argv[3])+1)
    kws = sys.argv[4:]
    search(school, vols, kws)
