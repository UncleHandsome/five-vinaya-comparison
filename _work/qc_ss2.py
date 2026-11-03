import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)

def vol_paras(v):
    p = os.path.join(W, 'shisong', 'vol%02d.txt' % v)
    return [l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8')]

import importlib.util
spec = importlib.util.spec_from_file_location('qc', os.path.join(W, 'qc_ss.py'))

UNITS = json.load(open(os.path.join(W, 'ss_units.json'), encoding='utf-8'))

def src_text(vols, rng):
    out = []
    for v in vols:
        for n, t in vol_paras(v):
            if rng and not (rng[0] <= int(n) <= rng[1]):
                continue
            out.append(t)
    return norm(''.join(out))

LABEL = re.compile(r'(?:卷?\s*\d+\s*[-－]\s*)?段?\s*\d{1,3}\s*(?:後段|前段|中段)?\s*[：:]')

def quote_lines(text):
    qs, buf = [], []
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('>'):
            buf.append(s.lstrip('>').strip())
        else:
            if buf:
                qs.append(''.join(buf)); buf = []
    if buf:
        qs.append(''.join(buf))
    return qs

def clean(q):
    q = re.sub(r'^\s*\*\*[^*]{0,40}\*\*\s*', '', q)
    q = re.sub(r'^\s*〔[^〕]{0,20}〕\s*', '', q)
    q = re.sub(r'^\s*[（(][^）)]{0,20}[）)][：:]?\s*', '', q)
    return q.strip()

tot = {'src': 0, 'kept': 0, 'items': 0, 'bad': 0}
for u in UNITS:
    f = os.path.join(W, 'findings_ss', u['unit'] + '.md')
    text = open(f, encoding='utf-8').read()
    cut = text.find('## 刪除項')
    keep_sec = text[:cut] if cut > 0 else text
    rng = u['rng']
    src = src_text(u['vols'], rng)
    bad, kept = [], 0
    for q in quote_lines(keep_sec):
        q = clean(q)
        if not q:
            continue
        for part in re.split(LABEL, q):
            for seg in re.split(r'（中略[^）]*）|（節引）|（節錄）|……|\.\.\.|「[^」]*$', part):
                n = norm(seg)
                n2 = re.sub(r'[（(][^）)]{0,10}[）)]', '', n)
                kept += len(n)
                if len(n) >= 10 and n not in src and n2 not in src:
                    bad.append(seg[:46])
    items = len(re.findall(r'^### ', keep_sec, re.M))
    u['src'], u['kept'], u['items'], u['bad'] = len(src), kept, items, bad
    tot['src'] += len(src); tot['kept'] += kept; tot['items'] += items; tot['bad'] += len(bad)
    flag = '' if not bad else '   <<< BAD %d' % len(bad)
    print('%-9s src %6d kept %6d %5.1f%% items %3d%s' % (u['unit'], len(src), kept, kept/len(src)*100, items, flag))
    for b in bad[:6]:
        print('     MISS:', b)
print('TOTAL', tot)
json.dump(UNITS, open(os.path.join(W, 'ss_units_qc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
