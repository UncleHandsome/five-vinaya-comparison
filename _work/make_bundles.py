import os, json, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
os.makedirs(os.path.join(WORK, 'bundles'), exist_ok=True)
os.makedirs(os.path.join(WORK, 'findings'), exist_ok=True)

# load wufen volumes
vols = {}
for v in range(1, 31):
    p = os.path.join(WORK, 'wufen', 'vol%02d.txt' % v)
    vols[v] = [l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8')]

# section definitions: (id, title, start(vol, keytext), end(vol, keytext) exclusive)
SECS = [
    (1,  '第一分初波羅夷法',      (1, '第一分初波羅夷法'),      (2, '五分律第一分之二僧殘法')),
    (2,  '第一分之二僧殘法',      (2, '五分律第一分之二僧殘法'), (4, '第一分之三不定法')),
    (3,  '第一分之三不定法',      (4, '第一分之三不定法'),      (4, '五分律第一分之四捨墮法')),
    (4,  '第一分之四捨墮法',      (4, '五分律第一分之四捨墮法'), (6, '初分之五墮初')),
    (5,  '第一分之五墮法（單提）', (6, '初分之五墮初'),          (10, '第一分之六悔過法')),
    (6,  '第一分之六悔過法',      (10, '第一分之六悔過法'),     (10, '五分律第一分之七眾學法')),
    (7,  '第一分之七眾學法',      (10, '五分律第一分之七眾學法'), (10, '五分律第一分之八七滅諍法')),
    (8,  '第一分之八七滅諍法',    (10, '五分律第一分之八七滅諍法'), (11, '第二分初尼律波羅夷法')),
    (9,  '第二分初尼律波羅夷法',  (11, '第二分初尼律波羅夷法'), (11, '五分律第二分之二尼律僧殘法')),
    (10, '第二分之二尼律僧殘法',  (11, '五分律第二分之二尼律僧殘法'), (12, '第二分之三尼律捨墮法')),
    (11, '第二分之三尼律捨墮法',  (12, '第二分之三尼律捨墮法'), (12, '五分律第二分之四尼律墮法')),
    (12, '第二分之四尼律墮法',    (12, '五分律第二分之四尼律墮法'), (14, '五分律第二分之五尼律悔過法')),
    (13, '第二分之五尼律悔過法',  (14, '五分律第二分之五尼律悔過法'), (14, '五分律第二分之六尼律眾學法')),
    (14, '第二分之六尼律眾學法',  (14, '五分律第二分之六尼律眾學法'), (15, '第三分初受戒法上')),
    (15, '第三分初受戒法',        (15, '第三分初受戒法上'),     (18, '第三分之四布薩法')),
    (16, '第三分之三布薩法',      (18, '第三分之四布薩法'),     (19, '第三分之三安居法')),
    (17, '第三分之三安居法',      (19, '第三分之三安居法'),     (19, '五分律第三分之四自恣法')),
    (18, '第三分之四自恣法',      (19, '五分律第三分之四自恣法'), (20, '第三分之五衣法上')),
    (19, '第三分之五衣法',        (20, '第三分之五衣法上'),     (21, '五分律第三分之六皮革法')),
    (20, '第三分之六皮革法',      (21, '五分律第三分之六皮革法'), (22, '第三分之七藥法')),
    (21, '第三分之七藥法',        (22, '第三分之七藥法'),       (22, '第三分之八食法')),
    (22, '第三分之八食法',        (22, '第三分之八食法'),       (22, '第三分之九迦絺那衣法')),
    (23, '第三分之九迦絺那衣法',  (22, '第三分之九迦絺那衣法'), (23, '第四分初滅諍法')),
    (24, '第四分初滅諍法',        (23, '第四分初滅諍法'),       (23, '五分律第四分之二羯磨法')),
    (25, '第四分之二羯磨法',      (23, '五分律第四分之二羯磨法'), (25, '第五分初破僧法')),
    (26, '第五分初破僧法',        (25, '第五分初破僧法'),       (25, '第五分之二臥具法')),
    (27, '第五分之二臥具法',      (25, '第五分之二臥具法'),     (26, '第五分雜法')),
    (28, '第五分之三雜法',        (26, '第五分雜法'),           (27, None)),
    (29, '第五分之四威儀法',      (27, None),                   (28, '第五分之五遮布薩法')),
    (30, '第五分之五遮布薩法',    (28, '第五分之五遮布薩法'),   (28, '五分律第五分之六別住法')),
    (31, '第五分之六別住法',      (28, '五分律第五分之六別住法'), (28, '五分律第五分之七調伏法')),
    (32, '第五分之七調伏法',      (28, '五分律第五分之七調伏法'), (29, '第五分之八比丘尼法')),
    (33, '第五分之八比丘尼法',    (29, '第五分之八比丘尼法'),   (30, '第五分之九五百集法')),
    (34, '第五分之九五百集法',    (30, '第五分之九五百集法'),   (30, '五分律第五分之十七百集法')),
    (35, '第五分之十七百集法',    (30, '五分律第五分之十七百集法'), (31, None)),
]

def norm(s):
    return s.lstrip('◎').removeprefix('五分律')

def find(vol, key):
    if key is None:
        return 0
    ps = vols[vol]
    k = norm(key)
    for i, (n, t) in enumerate(ps):
        if norm(t).startswith(k):
            return i
    raise SystemExit('NOT FOUND vol%d %r' % (vol, key))

# build per-section paragraph lists
bounds = []
for idx, (sid, title, s, e) in enumerate(SECS):
    sv, sk = s
    ev, ek = e
    si = find(sv, sk)
    if ev > 30:
        ev, ei = 30, len(vols[30])
    elif ev == sv:
        ei = find(ev, ek)
    else:
        ei = find(ev, ek)
    if ek is None:
        ei = len(vols[ev])
    bounds.append((sid, title, sv, si, ev, ei))

out = []
for sid, title, sv, si, ev, ei in bounds:
    paras = []
    if sv == ev:
        paras = [(sv, n, t) for n, t in vols[sv][si:ei]]
    else:
        paras += [(sv, n, t) for n, t in vols[sv][si:]]
        for v in range(sv + 1, ev):
            paras += [(v, n, t) for n, t in vols[v]]
        paras += [(ev, n, t) for n, t in vols[ev][:ei]]
    path = os.path.join(WORK, 'bundles', 'W%02d.txt' % sid)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('【五分律篇%02d】%s\n' % (sid, title))
        fh.write('（段落格式：卷-段<TAB>原文）\n\n')
        prev = None
        for v, n, t in paras:
            if v != prev:
                fh.write('\n===== 卷%d =====\n' % v)
                prev = v
            fh.write('%d-%s\t%s\n' % (v, n, t))
    out.append({'id': sid, 'title': title, 'chars': sum(len(t) for _, _, t in paras),
                'paras': len(paras), 'start': '%d-%d' % (sv, si + 1), 'end': '%d-%d' % (ev, ei)})

with open(os.path.join(WORK, 'sections.json'), 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

for r in out:
    print(r['id'], r['title'], r['paras'], r['chars'], r['start'], r['end'])
