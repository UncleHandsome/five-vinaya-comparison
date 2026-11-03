import re, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    s = re.sub(r'[^\u4e00-\u9fff]', '', s)
    return s

vols = {}
for v in range(1, 31):
    p = os.path.join(W, 'wufen', 'vol%02d.txt' % v)
    vols[v] = norm(''.join(t for _, t in (l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8'))))

def clean(q):
    q = re.sub(r'^\s*\*\*[^*]{0,30}\*\*\s*', '', q)
    q = re.sub(r'^\s*〔[^〕]{0,20}〕\s*', '', q)
    q = re.sub(r'^\s*（[^）]{0,20}）\s*', '', q)
    q = re.sub(r'^\s*段\s*\d+[：:]\s*', '', q)
    q = re.sub(r'（(?:節引|節錄|中略|下略|上略|略)[^）]{0,6}）', '', q)
    q = re.sub(r'〔(?:節引|節錄|中略|下略|上略|略)[^〕]{0,6}〕', '', q)
    return q.strip()

for f in sorted(glob.glob(os.path.join(W, 'findings', 'vol*.md'))):
    m = re.match(r'vol(\d+)', os.path.basename(f))
    if not m:
        continue
    v = int(m.group(1))
    src = vols[v]
    lines = open(f, encoding='utf-8').read().split('\n')
    quotes, buf = [], []
    for ln in lines:
        s = ln.strip()
        if s.startswith('>'):
            buf.append(s.lstrip('>').strip())
        else:
            if buf:
                quotes.append(''.join(buf)); buf = []
    if buf: quotes.append(''.join(buf))
    bad = []
    for q in quotes:
        q = clean(q)
        # split on embedded paragraph markers
        segs = re.split(r'\*\*[^*]{0,20}\*\*|〔[^〕]{0,20}〕|（段[^）]{0,10}）|段\s*\d+[：:]|（中略）|（節引）|（節錄）|……|\.\.\.', q)
        for seg in segs:
            n = norm(seg)
            if len(n) < 8:
                continue
            # also try removing common editorial brackets
            n2 = re.sub(r'[（(][^）)]{0,10}[）)]', '', n)
            if n not in src and n2 not in src:
                bad.append(seg[:50])
    print('%s: quotes=%d bad=%d' % (os.path.basename(f), len(quotes), len(bad)))
    for b in bad[:8]:
        print('    NOT FOUND:', b)
