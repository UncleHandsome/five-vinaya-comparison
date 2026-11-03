import os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')

vols = {}
for v in range(1, 31):
    p = os.path.join(WORK, 'wufen', 'vol%02d.txt' % v)
    vols[v] = [l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8')]

queries = json.load(open(sys.argv[1], encoding='utf-8')) if len(sys.argv) > 1 else []
for q in queries:
    pat = re.compile(q['q'])
    print('===== %s | %s' % (q.get('id', ''), q.get('note', '')))
    hits = 0
    for v in range(1, 31):
        for n, t in vols[v]:
            if pat.search(t):
                hits += 1
                print('  [%d-%s] %s' % (v, n, t[:260]))
                if hits >= q.get('max', 6):
                    break
        if hits >= q.get('max', 6):
            break
    if not hits:
        print('  (no hit)')
