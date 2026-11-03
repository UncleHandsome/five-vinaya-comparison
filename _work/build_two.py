# -*- coding: utf-8 -*-
"""Split 根本說一切有部毘奈耶 (50 juan) and 摩訶僧祇律 (40 juan) into volume files."""
import os, re, glob, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
def cn2int(s):
    s = s.strip()
    if s == '十':
        return 10
    if len(s) == 1:
        return cn.get(s)
    if s.startswith('十'):
        return 10 + cn.get(s[1:], 0)
    if s.endswith('十'):
        return cn[s[0]] * 10
    if '十' in s:
        a, b = s.split('十', 1)
        return cn[a] * 10 + (cn[b] if b else 0)
    return None

SPECS = {
    'genben': ('根本說一切有部毗奈耶', re.compile(r'^根本說一切有部\S{2,3}卷第([一二三四五六七八九十]+)'), 'genben'),
    'sengqi': ('摩訶僧祇律', re.compile(r'^摩訶僧祇律卷第([一二三四五六七八九十]+)'), 'sengqi'),
}

for key, (folder, pat, tag) in SPECS.items():
    d = os.path.join(W, tag)
    os.makedirs(d, exist_ok=True)
    vols = {}
    cur = None
    for f in sorted(glob.glob(os.path.join(ROOT, folder, '*.txt'))):
        src = os.path.basename(f)
        raw = [l.strip() for l in open(f, encoding='utf-8').read().split('\n')]
        nxt = {}
        for i, s in enumerate(raw):
            for j in range(i + 1, min(i + 5, len(raw))):
                if raw[j]:
                    nxt[i] = raw[j]
                    break
        for i, s in enumerate(raw):
            if not s:
                continue
            m = pat.match(s)
            if m:
                v = cn2int(m.group(1))
                real = bool(re.search(r'(三藏|制譯|譯)', nxt.get(i, '')))
                if v is None or not real or v in vols:
                    continue
                cur = v
                vols[v] = {'source': src, 'paras': []}
                continue
            if cur is None:
                continue
            vols[cur]['paras'].append(s)
    index = []
    for v, info in sorted(vols.items()):
        with open(os.path.join(d, 'vol%02d.txt' % v), 'w', encoding='utf-8') as fh:
            for i, p in enumerate(info['paras'], 1):
                fh.write('%d\t%s\n' % (i, p))
        heads = [p for p in info['paras'] if len(p) < 40 and re.search(r'(學處|法之|品第|卷第|法初|法第一|跋渠|犍度|揵度|法竟|戒法)', p)]
        index.append({'v': v, 'n': len(info['paras']), 'chars': sum(len(p) for p in info['paras']),
                      'source': info['source'], 'heads': heads[:12]})
    json.dump(index, open(os.path.join(W, tag + '_index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(tag, 'vols', len(vols), 'total chars', sum(len(p) for i in vols.values() for p in i['paras']),
          'total paras', sum(len(i['paras']) for i in vols.values()))

print()
for tag in ('genben', 'sengqi'):
    idx = json.load(open(os.path.join(W, tag + '_index.json'), encoding='utf-8'))
    print('=====', tag)
    for r in idx:
        print('  v%-3d n=%-4d c=%-6d %s' % (r['v'], r['n'], r['chars'], ' | '.join(r['heads'][:3])[:90]))
