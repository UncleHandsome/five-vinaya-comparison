import os, re, glob, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)

def vol_paras(v):
    p = os.path.join(W, 'shisong', 'vol%02d.txt' % v)
    return [l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8')]

hi = set('这们时说过还进来对开关门问间长东车马鸟鱼龙风飞书写学觉见观听声义议论証识语话读谁请谢变边达运远连选阳阴队阶际随隐难页顶项顺须顾顿预领颇颈颊频颗题颜额饭饮饱饿馆驾骑骗鲜鸡鸣鸭鹅鹰麦黄齐齿龄龟个么儿几头尽层属岁')

UNITS = [
 ('vol01', [1], None, '卷1 初誦之一・四波羅夷法之一'),
 ('vol02', [2], None, '卷2 四波羅夷法之二'),
 ('vol03', [3], None, '卷3 十三僧殘法之初'),
 ('vol04', [4], None, '卷4 十三僧殘法之餘・二不定法'),
 ('vol05-06', [5, 6], None, '卷5～6 三十尼薩耆法之一、二'),
 ('vol07-08', [7, 8], None, '卷7～8 三十尼薩耆法之三、四'),
 ('vol09-10', [9, 10], None, '卷9～10 九十波夜提法之一、二'),
 ('vol11-12', [11, 12], None, '卷11～12 九十波逸提法之三、四'),
 ('vol13-14', [13, 14], None, '卷13～14 九十波逸提法（續）'),
 ('vol15-16', [15, 16], None, '卷15～16 九十波逸提法（續）'),
 ('vol17-18', [17, 18], None, '卷17～18 九十波逸提法（末）'),
 ('vol19-20', [19, 20], None, '卷19～20 波羅提舍尼・眾學法・七滅諍法'),
 ('vol21', [21], None, '卷21 七法中受具足戒法第一'),
 ('vol22', [22], None, '卷22 七法中布薩法第二'),
 ('vol23-24', [23, 24], None, '卷23～24 自恣法第三・安居法第四'),
 ('vol25', [25], None, '卷25 七法中皮革法第五'),
 ('vol26', [26], None, '卷26 七法中醫藥法第六'),
 ('vol27-28', [27, 28], None, '卷27～28 七法中衣法第七'),
 ('vol29', [29], None, '卷29 八法中迦絺那衣法第一'),
 ('vol30', [30], None, '卷30 俱舍彌法第二・瞻波法第三'),
 ('vol31-32', [31, 32], None, '卷31～32 般茶盧伽法第四・悔法第五'),
 ('vol33-34', [33, 34], None, '卷33～34 遮法第六・臥具法第七'),
 ('vol35', [35], None, '卷35 八法中諍事法第八'),
 ('vol36-37', [36, 37], None, '卷36～37 雜誦・調達事'),
 ('vol38-39', [38, 39], None, '卷38～39 明雜法之三、之四'),
 ('vol40-41', [40, 41], None, '卷40～41 明雜法之五、之六'),
 ('vol42-43', [42, 43], None, '卷42～43 尼律八波羅夷・十七僧殘'),
 ('vol44-45', [44, 45], None, '卷44～45 尼律三十捨墮・單提法'),
 ('vol46-47', [46, 47], None, '卷46～47 尼律單提・波羅提舍尼・八敬法'),
 ('vol48-49', [48, 49], None, '卷48～49 毘尼增一法（一、二）'),
 ('vol50', [50], None, '卷50 毘尼增一法（三）五法下至十法'),
 ('vol51', [51], (1, 73), '卷51 五法至十法（前段）'),
 ('vol51b', [51], (74, 145), '卷51 增十一相（後段）'),
 ('vol52', [52], None, '卷52 優波離問（初）'),
 ('vol53', [53], None, '卷53 優波離問'),
 ('vol54', [54], None, '卷54 優波離問'),
 ('vol55', [55], None, '卷55 優波離問'),
 ('vol56', [56], None, '卷56 優波離問'),
 ('vol57', [57], None, '卷57 優波離問'),
 ('vol58', [58], None, '卷58 優波離問'),
 ('vol59', [59], None, '卷59 優波離問'),
 ('vol60', [60], None, '卷60 五百比丘結集・七百集法（上）'),
 ('vol61a', [61], (1, 93), '卷61 七百集法之餘・毘尼中雜品'),
 ('vol61b', [61], (94, 204), '卷61 毘尼序下・優波離問'),
]

def src_text(vols, rng):
    out = []
    for v in vols:
        for n, t in vol_paras(v):
            if rng and not (rng[0] <= int(n) <= rng[1]):
                continue
            out.append(t)
    return norm(''.join(out))

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
    q = re.sub(r'^\s*（[^）]{0,20}）\s*', '', q)
    q = re.sub(r'^\s*卷?\s*\d+\s*[（(]?(?:節錄|節引)?[）)]?\s*[：:]\s*', '', q)
    return q.strip()

report = []
for name, vols, rng, title in UNITS:
    f = os.path.join(W, 'findings_ss', name + '.md')
    text = open(f, encoding='utf-8').read()
    cut = text.find('## 刪除項')
    keep_sec = text[:cut] if cut > 0 else text
    src = src_text(vols, rng)
    bad = []
    kept = 0
    for q in quote_lines(keep_sec):
        for seg in re.split(r'（中略[^）]*）|（節引）|（節錄）|……|\.\.\.', clean(q)):
            n = norm(seg)
            n2 = re.sub(r'[（(][^）)]{0,10}[）)]', '', n)
            kept += len(n)
            if len(n) >= 8 and n not in src and n2 not in src:
                bad.append(seg[:40])
    simp = ''.join(sorted(set(c for c in text if c in hi)))
    items = len(re.findall(r'^### ', keep_sec, re.M))
    report.append({'unit': name, 'title': title, 'src': len(src), 'kept': kept,
                   'items': items, 'bad': bad, 'simp': simp})

tot_src = sum(r['src'] for r in report)
tot_kept = sum(r['kept'] for r in report)
tot_items = sum(r['items'] for r in report)
print('units', len(report), 'items', tot_items, 'src', tot_src, 'kept', tot_kept, 'ratio', round(tot_kept/tot_src*100, 1))
for r in report:
    flag = '' if not r['bad'] else '  BAD %d' % len(r['bad'])
    print('%-10s %-34s src %6d kept %6d %4.1f%% items %3d%s' % (
        r['unit'], r['title'], r['src'], r['kept'], r['kept']/r['src']*100, r['items'], flag))
    for b in r['bad'][:4]:
        print('     MISS:', b)
    if r['simp']:
        print('     SIMP:', r['simp'])
json.dump(report, open(os.path.join(W, 'ss_qc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
