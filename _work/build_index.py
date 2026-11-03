import re, os, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')

WUFEN_VOL = re.compile(r'^(?:彌沙塞部和醯五分律卷|五分律卷)第([一二三四五六七八九十]+)')
SIFEN_SEC_PAT = re.compile(r'^(?:[一二三四五六七八九十百]+(?:波羅夷|僧殘|不定|捨墮|單提|悔過|眾學|滅諍|波逸提|學法)法(?:之[一二三四五六七八九十]+)?|式叉迦羅尼法|受戒揵度|說戒揵度|安居揵度|自恣揵度|皮革揵度|衣揵度|藥揵度|迦絺那衣揵度.*|拘睒彌揵度.*|瞻波揵度.*|呵責揵度.*|人揵度.*|覆藏揵度.*|遮揵度.*|破僧揵度.*|滅諍揵度.*|比丘尼揵度.*|尼揵度.*|法揵度.*|房舍揵度.*|雜揵度.*|集法毘尼五百人|七百集法毘尼|調部.*|毘尼增一.*|四波羅夷法.*|十三僧殘法.*|二不定法.*|三十捨墮法.*|九十單提法.*|四悔過法.*|百眾學法.*|百種學法.*|七滅諍法.*|八波羅夷法.*|十七僧殘法.*|一百七十八單提法.*)')

cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
def cn2int(s):
    if s == '十': return 10
    if len(s) == 1: return cn[s]
    if s.startswith('十'): return 10 + cn.get(s[1],0)
    if s.endswith('十'): return cn[s[0]]*10
    if '十' in s:
        a,b = s.split('十'); return cn[a]*10 + (cn[b] if b else 0)
    return None

# ---------- wufen ----------
wf_vols = {}
for f in sorted(glob.glob(os.path.join(ROOT, '五分律', '*.txt'))):
    lines = open(f, encoding='utf-8').read().split('\n')
    cur = None
    for ln in lines:
        s = ln.strip().lstrip('◎')
        if not s:
            continue
        m = WUFEN_VOL.match(s)
        if m:
            v = cn2int(m.group(1))
            cur = v
            wf_vols.setdefault(v, {'source': os.path.basename(f), 'paras': []})
            continue
        if cur is None:
            continue
        wf_vols[cur]['paras'].append(s)

# ---------- sifen ----------
sf_sections = []
for f in sorted(glob.glob(os.path.join(ROOT, '四分律', '*.txt'))):
    lines = open(f, encoding='utf-8').read().split('\n')
    cur = {'file': os.path.basename(f), 'title': '(開頭)', 'paras': []}
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if SIFEN_SEC_PAT.match(s) and len(s) < 30:
            if cur['paras'] or cur['title'] != '(開頭)':
                sf_sections.append(cur)
            cur = {'file': os.path.basename(f), 'title': s, 'paras': []}
            continue
        cur['paras'].append(s)
    sf_sections.append(cur)

os.makedirs(os.path.join(WORK, 'wufen'), exist_ok=True)
for v, d in sorted(wf_vols.items()):
    with open(os.path.join(WORK, 'wufen', 'vol%02d.txt' % v), 'w', encoding='utf-8') as fh:
        for i, p in enumerate(d['paras'], 1):
            fh.write('%d\t%s\n' % (i, p))

with open(os.path.join(WORK, 'wufen_index.json'), 'w', encoding='utf-8') as fh:
    json.dump({str(v): {'source': d['source'], 'n': len(d['paras'])} for v, d in sorted(wf_vols.items())}, fh, ensure_ascii=False, indent=1)

os.makedirs(os.path.join(WORK, 'sifen'), exist_ok=True)
idx = []
for n, sec in enumerate(sf_sections):
    safe = re.sub(r'[^\w\u4e00-\u9fff]+', '_', sec['title'])[:40]
    path = os.path.join(WORK, 'sifen', '%03d_%s.txt' % (n, safe))
    with open(path, 'w', encoding='utf-8') as fh:
        for i, p in enumerate(sec['paras'], 1):
            fh.write('%d\t%s\n' % (i, p))
    idx.append({'n': n, 'title': sec['title'], 'file': sec['file'],
                'paras': len(sec['paras']), 'chars': sum(len(p) for p in sec['paras']),
                'path': os.path.basename(path)})

with open(os.path.join(WORK, 'sifen_index.json'), 'w', encoding='utf-8') as fh:
    json.dump(idx, fh, ensure_ascii=False, indent=1)

print('wufen vols:', len(wf_vols), [ (v, len(d['paras'])) for v,d in sorted(wf_vols.items()) ])
print('sifen sections:', len(sf_sections))
for r in idx:
    print(r['n'], r['title'], r['paras'], r['chars'])
