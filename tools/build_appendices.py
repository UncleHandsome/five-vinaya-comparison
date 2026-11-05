#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""附錄五（比丘／比丘尼共戒對位表）與附錄六（五部開遮持犯差異表）。

使用者指示：共戒表「只針對共戒深度做，不相關的不用管；波逸提、眾學法都做」。
故以字元 bigram 相似度找共戒候選，低度者不列；已知不同名之共戒另以編者判定補入。
開遮持犯表為「差異導向」——只列有差異可說者，空白一律標「未比」，
避免重蹈凡例六所戒「未比誤讀為無」。

產出 _work/appendix5.md / _work/appendix6.md，由 build_compare.build_appendix() 讀入。
"""
import os, re, json, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
sys.path.insert(0, WORK)


def bigrams(s):
    s = re.sub(r'[\s，。、；：？！「」『』（）()\[\]＊*]', '', s)
    return set(s[i:i + 2] for i in range(len(s) - 1)) or {s}


def sim(a, b):
    x, y = bigrams(a), bigrams(b)
    return len(x & y) / len(x | y) if x | y else 0


CRIME_OF = {}
FAM = {1:'波羅夷',2:'波羅夷',3:'僧殘',4:'僧殘',5:'僧殘',6:'僧殘',7:'二不定',
       8:'捨墮',9:'捨墮',10:'捨墮',11:'捨墮',12:'捨墮',
       13:'單提',14:'單提',15:'單提',16:'單提',17:'單提',18:'單提',
       19:'單提',20:'單提',21:'單提',22:'眾學',23:'眾學',24:'眾學',25:'滅諍',
       26:'波羅夷',27:'僧殘',28:'僧殘',29:'捨墮',30:'捨墮',
       31:'單提',32:'單提',33:'單提',34:'單提',35:'單提',36:'單提',37:'單提'}

def crime_of(no):
    f = FAM.get(no, '')
    return {'波羅夷':'波羅夷','僧殘':'僧殘','二不定':'二不定',
            '捨墮':'捨墮（尼薩耆波逸提）','單提':'單提（波逸提）',
            '眾學':'眾學（式叉迦羅尼）','滅諍':'滅諍'}.get(f, '')


def compatible(fb, fn):
    """共戒須同罪屬；比丘眾學在尼律併入單提法，故特許相配。"""
    return fb == fn or (fb == '眾學' and fn == '單提')


def build5():
    """附錄五：二部共戒對位。

    以《四分》二部戒名為據，先依罪類作單調名合（同名、異名皆計分），
    再以編者核定之別名補足（如「壞生種」↔「壞生草木」）；跨罪者另註
    （如女身相觸戒比丘結僧殘、比丘尼結波羅夷）。凡不能確定者不列。
    """
    import difflib
    import sifen_src as S
    names = json.load(open(os.path.join(WORK, 'jie_names.json'), encoding='utf-8'))
    nim = json.load(open(os.path.join(WORK, 'ni_jie_map.json'), encoding='utf-8'))
    FAMS = ['波羅夷', '僧殘', '捨墮', '單提', '提舍尼']
    TOT_N = {'波羅夷': 8, '僧殘': 17, '捨墮': 30, '單提': 178, '提舍尼': 8}

    def clean(x):
        return re.sub(r'^(?:[一二三四五六七八九十百零]+、)+', '', x or '').strip()

    B = {f: [] for f in FAMS}
    for no in range(1, 26):
        for u in S.units(no):
            fam = S.jie_family(no, u)
            if not fam:
                continue
            f = fam.replace('比丘', '')
            if f not in B:
                continue
            lb = S.unit_label(u, no) or ''
            for x in re.findall(r'(?:^|／)([一二三四五六七八九十百零]+)、', lb):
                i = S._cn2int(x)
                if not i:
                    continue
                B[f].append({'no': no, 'cn': u['cn'], 'a': u['a'], 'i': i,
                             'name': clean(names.get('%s|%d' % (fam, i)))})

    N = {f: [] for f in FAMS}
    for no in range(26, 38):
        for u in S.units(no):
            fam = S.jie_family(no, u)
            if not fam:
                continue
            f = fam.replace('尼', '')
            if f not in N:
                continue
            if f == '單提':
                for nm in nim.get('%d|%d' % (no, u['a']), []):
                    N[f].append({'no': no, 'cn': u['cn'], 'a': u['a'], 'name': nm})
            else:
                lb = S.unit_label(u, no) or ''
                m = re.match(r'([一二三四五六七八九十百零]+)、', lb)
                if m:
                    N[f].append({'no': no, 'cn': u['cn'], 'a': u['a'],
                                 'i': S._cn2int(m.group(1)), 'name': clean(lb)})

    # 編者核定之別名（比丘名片段, 尼名片段）
    ALIAS = [
        ('壞生種', '壞生草木'), ('異語惱他', '異語惱僧'),
        ('露敷臥具不舉', '露敷僧物不舉'), ('覆房過三節', '過三節覆房'),
        ('過洗浴', '半月洗浴'), ('著新衣不壞色', '著未壞色衣'),
        ('離三衣宿', '離五衣宿'), ('從非親俗人乞衣', '從非親里居士乞衣'),
        ('非親織師作衣', '自乞縷使非親織衣'),
        ('勸織師增織衣', '勸非親織師增織衣'),
        ('向未具說自證', '向未受具說得道'),
        ('輙著淨施衣', '淨施衣'), ('兜羅綿貯褥', '兜羅綿貯'),
        ('作高牀', '床足過量'), ('輙入宮閾', '入王宮'), ('捉寶物', '捉寶'),
        ('瞋打比丘', '瞋打尼'), ('瞋搏比丘', '以手搏尼'),
        ('畜長鉢', '畜長鉢'), ('度未滿二十', '年不滿二十'),
        ('與婦女同室宿', '共男子同室宿'),
        ('與未具人宿過限', '共未受戒女同宿過限'),
        ('與女人過說法', '與女人過說法'),
    ]

    def core(x):
        return (x or '').replace('戒', '')

    def sim(a, b):
        return difflib.SequenceMatcher(None, core(a), core(b)).ratio()

    pairs = {f: {} for f in FAMS}      # 比丘 idx → (尼 idx, 依據)
    for f in FAMS:
        for fb, fn in ALIAS:
            bi = next((k for k, x in enumerate(B[f]) if fb in x['name']), None)
            nj = next((k for k, x in enumerate(N[f]) if fn in x['name']), None)
            if bi is None or nj is None or bi in pairs[f]:
                continue
            if nj in [v[0] for v in pairs[f].values()]:
                continue
            _r = sim(B[f][bi]['name'], N[f][nj]['name'])
            pairs[f][bi] = (nj, '戒名小異' if _r >= 0.5
                            else '編者判定：戒名雖異，實同一戒', f)
        # 名合：高分優先，保持單調
        cand = []
        for i, b in enumerate(B[f]):
            if i in pairs[f]:
                continue
            for j, n in enumerate(N[f]):
                r = sim(b['name'], n['name'])
                if r >= 0.5:
                    cand.append((r, i, j))
        for r, i, j in sorted(cand, reverse=True):
            if i in pairs[f] or j in [v[0] for v in pairs[f].values()]:
                continue
            if any(k < i and v[0] > j for k, v in pairs[f].items()):
                continue
            if any(k > i and v[0] < j for k, v in pairs[f].items()):
                continue
            pairs[f][i] = (j, '同題對位' if r >= 0.99 else '戒名小異', f)

    # 二部次序偶有互倒（如畜長鉢：比丘第 21、尼第 24），單調對位會漏；
    # 故再作一輪「名幾乎全同」之補配，不受次序限制。
    for f in FAMS:
        used = [v[0] for v in pairs[f].values()]
        for i, b in enumerate(B[f]):
            if i in pairs[f]:
                continue
            best = None
            for j, n in enumerate(N[f]):
                if j in used:
                    continue
                r = sim(b['name'], n['name'])
                if r >= 0.9 and (best is None or r > best[0]):
                    best = (r, j)
            if best:
                pairs[f][i] = (best[1], '同題對位' if best[0] >= 0.99 else '戒名小異', f)
                used.append(best[1])

    # 跨罪：女身相觸（比丘僧殘）↔ 染心摩觸（尼波羅夷）
    bi = next((k for k, x in enumerate(B['僧殘']) if '女身相觸' in x['name']), None)
    nj = next((k for k, x in enumerate(N['波羅夷']) if '染心摩觸' in x['name']), None)
    CROSS = None
    if bi is not None and nj is not None:
        CROSS = (bi, nj)
        pairs['僧殘'][bi] = (nj, '編者判定：罪名由僧殘升為波羅夷', '波羅夷')

    rows = []
    for f in FAMS:
        for i, b in enumerate(B[f]):
            if i not in pairs[f]:
                continue
            j, why, nf = pairs[f][i]
            n = N[nf][j]
            cb, cn = f, nf
            same = '同' if cb == cn else '**異**'
            rows.append((b, n, cb, cn, same, why, f))

    L = ['### 附錄五　比丘／比丘尼共戒對位表', '',
         '> **範圍**：只列二部共有之戒（共戒）；比丘獨有、比丘尼獨有者不列。'
         '波羅夷、僧殘、捨墮、**單提（波逸提）**、提舍尼各類皆逐條核名；'
         '眾學法見附錄五之三。',
         '>',
         '> **判準**：以《四分》二部戒名為據，同罪類內按戒名相似度作**單調對位**'
         '（次序不得顛倒），再逐條覆核。戒名全同者註「同題對位」；'
         '同一戒而用字有異者（如「壞生種」↔「壞生草木」）註「戒名小異」；'
         '戒名懸殊或跨罪而經內容核定者註「編者判定」。'
         '「罪名異同」一欄為本表重點——同題之戒，二部所結之罪未必相同。'
         '凡未能確定者不列，**不強配**（凡例六）。',
         '>',
         '> **「同題」非「同序」**：二部編次自單提中段起即不相當（如比丘 31 對尼 21），'
         '故本表所稱「對位」指**同一戒條**，不指編號相同。',
         '>',
         '> **編號讀法**：「001-一」為「篇號-節號」，即本書正文之篇次與該篇節次，'
         '非大正藏卷頁；循此可回《五部律差異對照本》相應篇節覆核。'
         '尼方編號偶跨篇（如捨墮分見 029、030），係原書分篇如此，非誤植。',
         '>',
         '> **比丘尼品（比丘單提 21–30）**：此十戒（教誡尼、與尼衣、與尼同行同船等）'
         '為比丘對尼眾之制，尼律無同條可對；其對待之制（如尼「半月往僧中求教授」）'
         '散見尼單提，非同一戒，故不入本表，亦不列為「共戒」。',
         '',
         '| 比丘 | 比丘戒名 | 罪屬 | 比丘尼 | 比丘尼戒名 | 罪屬 | 罪名異同 | 依據 |',
         '|---|---|---|---|---|---|---|---|']
    cnt = collections.Counter()
    for b, n, cb, cn, same, why, f in rows:
        cnt[same] += 1
        L.append('| %03d-%s | %s | %s | %03d-%s | %s | %s | %s | %s |' %
                 (b['no'], b['cn'], b['name'][:26], cb,
                  n['no'], n['cn'], n['name'][:26], cn, same, why))
    L += ['', '> 共戒對位 **%d** 組：罪屬相同 %d 組、相異 %d 組。'
          '罪名相異者即二部立法輕重之別，讀者可循篇號回正文覆核。' %
          (len(rows), cnt['同'], cnt['**異**']), '']

    # 各類對位與獨有之數
    tb = {f: len(B[f]) for f in FAMS}
    pb = collections.Counter(r[6] for r in rows)
    pn = collections.Counter()
    for b, n, cb, cn, same, why, f in rows:
        pn[cn if cn == '波羅夷' and f == '僧殘' else f] += 1
    L += ['#### 附錄五之二　各類對位與獨有之數', '',
          '| 罪類 | 比丘 | 已對位 | 比丘獨有 | 比丘尼 | 已對位 | 比丘尼獨有 |',
          '|---|---|---|---|---|---|---|']
    for k in FAMS:
        L.append('| %s | %d | %d | %d | %d | %d | %d |' %
                 (k, tb[k], pb[k], tb[k] - pb[k],
                  TOT_N[k], pn[k], TOT_N[k] - pn[k]))
    sum_b = sum(tb.values())
    sum_n = sum(TOT_N.values())
    L.append('| **五篇合計** | **%d** | **%d** | **%d** | **%d** | **%d** | **%d** |' %
             (sum_b, sum(pb.values()), sum_b - sum(pb.values()),
              sum_n, sum(pn.values()), sum_n - sum(pn.values())))
    L += ['', '> **合計之義**：上表只計波羅夷、僧殘、捨墮、單提、提舍尼五篇，'
          '故比丘 %d、比丘尼 %d，**非二部戒條總數**。'
          '比丘更加不定 2、眾學 100、滅諍 7，共 **250 戒**；'
          '比丘尼無不定，加眾學 100、滅諍 7，共 **348 戒**。'
          '（尼單提一欄作 178 者，依戒本之數；本書正文分節得 176 目，'
          '二目未能分立，詳附錄五之三。）' % (sum_b, sum_n), '',
          '| 罪類 | 比丘 | 比丘尼 | 說明 |', '|---|---|---|---|',
          '| 不定 | 2 | 0 | 尼律無不定法，故無可對 |',
          '| 眾學 | 100 | 100 | 二部共遵，尼律不別立條目（見附錄五之三） |',
          '| 滅諍 | 7 | 7 | 二部共遵，名目法式全同，不另對位 |',
          '| **總計** | **250** | **348** | 四分律二部戒條之數 |', '',
          '> **跨罪之一例**：女身相觸戒，比丘結僧殘、比丘尼結波羅夷，'
          '故波羅夷列比丘 4、尼 5，僧殘列比丘 8、尼 7——'
          '相差之 1 即此戒，非統計錯誤。', '',
          '> 尼提舍尼 8 條皆為「無病乞酥油蜜石蜜乳酪魚肉」，'
          '與比丘四提舍尼（受尼食、不止尼代索、學家、恐處）**制各不同**，'
          '無對位可列，故「已對位」為 0。', '']

    # 眾學法：尼律不另立條目，須單獨交代
    xue = []
    for no in (22, 23, 24):
        for u in S.units(no):
            if u.get('cn'):
                xue.append((no, u.get('name') or '', u['a'], u['b']))
    last = xue[-1] if xue else None
    L += ['#### 附錄五之三　眾學法（二部共遵，無對位可列）', '',
          '> 查尼律諸篇（026–037）**未見「眾學／式叉迦羅尼／應當學」之獨立條目**；'
          '眾學法為二部共遵之威儀法，四分廣律於尼律不別立條目。'
          '（然《四分比丘尼戒本》一系仍完整誦出百眾學，'
          '故此言「廣律不別立」，非謂尼眾不持。）'
          '本表無「比丘眾學 ↔ 尼眾學」之對位，非遺漏，乃體例如是。',
          '>',
          '> **此表只列本書已分節者 %d 目**，非百眾學之全。'
          '眾學法定 100 條；本書分節於篇 022 得 8、篇 023 得 32、篇 024 得 18，'
          '末目（段 107–178）實含後 42 條未分節之威儀（塔寺、說法諸戒），'
          '故段次跨度特大，非一條橫跨七十二段。' % len(xue), '',
          '| 序 | 篇 | 眾學目 | 段次 |', '|---|---|---|---|']
    for i, (no, nm, a2, b2) in enumerate(xue, 1):
        span = '%d–%d' % (a2, b2)
        if (no, nm, a2, b2) == last:
            span = '%d–%d（含後 42 條未分節）' % (a2, b2)
        L.append('| %d | %03d | %s | %s |' % (i, no, nm[:34] or '（承上省語）', span))
    L += ['', '> 補記：末目以下之 42 條（不得塔中埋死屍、不得向塔燒死屍、'
          '不得為持劍人說法等），原文自段 107 起逐段羅列，'
          '本書尚未分節，故不列目；他日補分節，此表當增至 100 目。', '']
    return '\n'.join(L)


def build6():
    rows = json.load(open(os.path.join(WORK, 'matrix_built.json'), encoding='utf-8'))
    import errata
    KEY = re.compile(r'不犯|無犯|開緣|開許|聽許|除.{0,8}時|突吉羅|波逸提|偷蘭遮|波羅夷|僧殘|尼薩耆|輕|重')
    picked = []
    for r in rows:
        e = errata.apply(r)
        if e['st'] == 'B' or (KEY.search(e.get('diff_full') or '') and e.get('lv') == '戒條'):
            picked.append(e)
    # 僧祇／根有補比（見 tools/fill_mk_gu.py）：只補「有」，附卷次與檢得詞
    fp = os.path.join(WORK, 'mk_gu_fill.json')
    FILL = json.load(open(fp, encoding='utf-8')) if os.path.exists(fp) else {}
    L = ['### 附錄六　五部律開遮持犯差異表（差異導向）', '',
         '> **範圍**：只列「有差異可說」者——同條開緣（狀態 B）或差異說明涉及'
         '不犯／開緣／罪名輕重之戒條項。此表**不是**逐戒全表；'
         '空白一律為「未比」（未經比勘），**非謂該部無此開緣**（凡例六）。',
         '>',
         '> **讀法**：「有／無」記該部於此項是否見其制；欲知其實，循「證據」欄'
         '（所屬律卷檔#項序）回矩陣，再按附錄四之法反查本書正文。',
         '>',
         '> **本輪補比**：僧祇、根有兩欄原多「未比」。今補 **%d** 格為「有」'
         '（僧祇 %d、根有 %d）：根有依其「學處第N」編次與四分戒序對位，'
         '僧祇則以查詢詞回原典檢得制戒語者為限；皆附卷次。'
         '**未檢得者仍標「未比」，不據以斷無**；補比明細見'
         '`_work/審閱/僧祇根有補比.csv`。' % (
             sum(len(v) for v in FILL.values()),
             sum(1 for v in FILL.values() if 'vMK' in v),
             sum(1 for v in FILL.values() if 'vGU' in v)),
         '',
         '| 事由 | 狀態 | 四分 | 五分 | 十誦 | 僧祇 | 根有 | 差異類型 | 證據 |',
         '|---|---|---|---|---|---|---|---|---|']
    for e in picked:
        t = (e.get('title') or '').replace('|', '／')[:38]
        f = FILL.get(e['id'], {})
        v = [e.get(k, '') for k in ('v4', 'v5', 'v10', 'vMK', 'vGU')]
        v = ['未比' if x == '未比' else x for x in v]
        for i, k in enumerate(('v4', 'v5', 'v10', 'vMK', 'vGU')):
            if k in f:
                v[i] = f[k]['v']
        dt = {'A': '同條增異', 'B': '同條開緣', 'C': '四分所無', 'D': '同條減略'}.get(e['st'], e['st'])
        ev = '%s %s#%s' % (e['canon'], e['unit'], e['no'])
        for k, nm in (('vMK', '僧祇'), ('vGU', '根有')):
            if k in f:
                ev += '；%s「%s」' % (f[k]['cite'], f[k]['term'])
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' %
                 (t, e['st'], *v, dt, ev))
    L += ['', '> 共 **%d** 列。表內「未比」不得讀作「無」；'
          '若欲逐戒全表（每戒 × 五部 × 制／開／犯／不犯），'
          '須另立資料層，非本次差異項抽取所能任。' % len(picked), '']

    # 補比一覽：僧祇 22 格全列；根有僅列分佈
    if FILL:
        mk = [(mid, d['vMK']) for mid, d in sorted(FILL.items()) if 'vMK' in d]
        gu = [(mid, d['vGU']) for mid, d in sorted(FILL.items()) if 'vGU' in d]
        idx = {r['id']: r for r in rows}
        L += ['#### 附錄六之一　僧祇・根有補比', '',
              '> 只補「有」，不補「無」。根有 %d 格，依「學處第N」定位；'
              '僧祇 %d 格，逐條覆核上下文確為制戒語者。' % (len(gu), len(mk)), '']
        if mk:
            L += ['**僧祇（%d 格）**' % len(mk), '',
                  '| 項號 | 事由 | 出處 | 檢得詞 |', '|---|---|---|---|']
            for mid, d in mk:
                r = idx[mid]
                L.append('| %s | %s | %s | %s |' %
                         (mid, (r.get('title') or '')[:30], d['cite'], d['term']))
            L.append('')
        if gu:
            import collections as _c
            cc = _c.Counter(d['cite'].rsplit(' ', 1)[-1] for _, d in gu)
            L += ['**根有（%d 格，依卷分佈）**' % len(gu), '',
                  '| 卷 | 格數 |', '|---|---|']
            for k in sorted(cc):
                L.append('| %s | %d |' % (k, cc[k]))
            L += ['', '> 逐格明細（項號、學處序、上下文）見 `_work/審閱/僧祇根有補比.csv`。', '']
    print('附錄六', len(picked), '列；補比', sum(len(v) for v in FILL.values()), '格')
    return '\n'.join(L)


def main():
    a5, a6 = build5(), build6()
    open(os.path.join(WORK, 'appendix5.md'), 'w', encoding='utf-8', newline='\n').write(a5)
    open(os.path.join(WORK, 'appendix6.md'), 'w', encoding='utf-8', newline='\n').write(a6)
    print('附錄五／六已寫出')


if __name__ == '__main__':
    main()
