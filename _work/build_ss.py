import re, os, glob, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
os.makedirs(os.path.join(WORK, 'shisong'), exist_ok=True)

cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
def cn2int(s):
    s = s.strip()
    if s == '十': return 10
    if len(s) == 1: return cn.get(s)
    if s.startswith('十'): return 10 + cn.get(s[1:], 0)
    if s.endswith('十'): return cn[s[0]] * 10
    if '十' in s:
        a, b = s.split('十', 1)
        return cn[a] * 10 + (cn[b] if b else 0)
    return None

VOL = re.compile(r'^十誦律卷第([一二三四五六七八九十]+)')
vols = {}
cur = None
for f in sorted(glob.glob(os.path.join(ROOT, '十誦律', '*.txt'))):
    for ln in open(f, encoding='utf-8'):
        s = ln.strip()
        if not s:
            continue
        m = VOL.match(s)
        if m:
            v = cn2int(m.group(1))
            if v == cur:
                continue  # textual variant note
            cur = v
            vols.setdefault(v, {'paras': [], 'source': os.path.basename(f)})
            continue
        if cur is None:
            continue
        vols[cur]['paras'].append(s)

for v, d in sorted(vols.items()):
    with open(os.path.join(WORK, 'shisong', 'vol%02d.txt' % v), 'w', encoding='utf-8') as fh:
        for i, p in enumerate(d['paras'], 1):
            fh.write('%d\t%s\n' % (i, p))

json.dump({str(v): {'n': len(d['paras']), 'chars': sum(len(p) for p in d['paras']), 'source': d['source']}
           for v, d in sorted(vols.items())},
          open(os.path.join(WORK, 'shisong_index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('vols', len(vols))
for v, d in sorted(vols.items()):
    print(v, len(d['paras']), sum(len(p) for p in d['paras']))
