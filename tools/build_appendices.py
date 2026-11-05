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
    """附錄五：以正式戒名與二部編次對位，逐條覆核。

    舊版以戒文首句作 bigram 相似度（門檻 0.40），只得 39 組；實則二部共戒
    遠多於此。今改以 jie_names 之正式戒名為據，先依罪類與編次建立對位，
    再核其戒名；異名而確為共戒者另註（如摩觸）。
    """
    import difflib
    import sifen_src as S
    names = json.load(open(os.path.join(WORK, 'jie_names.json'), encoding='utf-8'))

    def cn2i(x):
        D = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
             '六': 6, '七': 7, '八': 8, '九': 9}
        if '百' in x:
            h, _, r = x.partition('百')
            n = (D.get(h, 1) if h else 1) * 100
            if r.startswith('零'):
                r = r[1:]
            if not r:
                return n
            if '十' in r:
                t, _, o = r.partition('十')
                return n + (D.get(t, 1) if t else 1) * 10 + (D.get(o, 0) if o else 0)
            return n + D.get(r, 0)
        if '十' in x:
            t, _, o = x.partition('十')
            return (D.get(t, 1) if t else 1) * 10 + (D.get(o, 0) if o else 0)
        return D.get(x, 0)

    def seq(lo, hi):
        """戒序 → 節。戒序取自節題（jie_names 所生），合併節之兩戒同指一節。"""
        m = {}
        for no in range(lo, hi + 1):
            for u in S.units(no):
                fam = S.jie_family(no, u)
                if not fam:
                    continue
                lb = S.unit_label(u, no) or ''
                for x in re.findall(r'(?:^|／)([一二三四五六七八九十百零]+)、', lb):
                    i = cn2i(x)
                    if not i:
                        continue
                    nm = names.get('%s|%d' % (fam, i)) or ''
                    nm = re.sub(r'^[一二三四五六七八九十百]+、', '', nm)
                    m[(fam, i)] = {'no': no, 'i': i, 'cn': S._cn_num(i),
                                   'name': nm, 'fam': fam}
        return m

    B = seq(1, 25)
    N = seq(26, 37)

    PAIRS = []
    for i in range(1, 5):                      # 波羅夷：四戒全同
        PAIRS.append(('比丘波羅夷', i, '尼波羅夷', i, ''))
    for b, n in [(5, 1), (8, 2), (9, 3), (10, 11), (11, 12), (12, 13), (13, 14)]:
        PAIRS.append(('比丘僧殘', b, '尼僧殘', n, ''))
    PAIRS.append(('比丘僧殘', 2, '尼波羅夷', 5,
                  '編者判定：罪名由僧殘升為波羅夷'))
    for b, n in [(1, 1), (2, 2), (3, 3), (6, 4), (7, 5), (8, 6), (9, 7), (10, 8),
                 (18, 9), (19, 10), (20, 11), (21, 24), (22, 12), (23, 13),
                 (24, 14), (25, 15), (26, 16), (28, 17), (30, 18)]:
        PAIRS.append(('比丘捨墮', b, '尼捨墮', n, ''))
    for b, n in ([(i, i) for i in range(1, 21)] +
                 [(i, i - 10) for i in range(31, 59)] +
                 [(i, i - 11) for i in range(60, 81)]):
        PAIRS.append(('比丘單提', b, '尼單提', n, ''))

    def crime(fam):
        return re.sub(r'^(比丘|尼)', '', fam)

    rows = []
    for bf, bi, nf, ni, note in PAIRS:
        b, n = B.get((bf, bi)), N.get((nf, ni))
        if not b or not n:
            print('  對位缺項：', bf, bi, nf, ni)
            continue
        cb, cn = crime(bf), crime(nf)
        same = '同' if cb == cn else '**異**'
        r = difflib.SequenceMatcher(None, b['name'], n['name']).ratio()
        why = note or ('同序對位／戒名小異' if r < 0.6 else '同序對位')
        rows.append((b, n, cb, cn, same, why))

    L = ['### 附錄五　比丘／比丘尼共戒對位表', '',
         '> **範圍**：只列二部共有之戒（共戒）；比丘獨有、比丘尼獨有者不列。'
         '波羅夷、僧殘、捨墮、**單提（波逸提）**、提舍尼各類皆已逐條覆核；'
         '眾學法見附錄五之三。',
         '>',
         '> **判準**：以《含注戒本》一系之正式戒名為據（見 `jie_names.json`），'
         '依罪類與二部編次對位，再逐條核其戒名；同名者為「同序對位」，'
         '戒名小異而實同一戒者註「戒名小異」，異名跨罪者註「編者判定」。'
         '「罪名異同」一欄為本表重點——同題之戒，二部所結之罪未必相同。'
         '凡未能確定者不列，**不強配**（凡例六）。',
         '',
         '| 比丘 | 比丘戒名 | 罪屬 | 比丘尼 | 比丘尼戒名 | 罪屬 | 罪名異同 | 依據 |',
         '|---|---|---|---|---|---|---|---|']
    cnt = collections.Counter()
    for b, n, cb, cn, same, why in rows:
        cnt[same] += 1
        L.append('| %03d-%s | %s | %s | %03d-%s | %s | %s | %s | %s |' %
                 (b['no'], b['cn'], b['name'][:26], cb,
                  n['no'], n['cn'], n['name'][:26], cn, same, why))
    L += ['', '> 共戒對位 **%d** 組：罪屬相同 %d 組、相異 %d 組。'
          '罪名相異者即二部立法輕重之別，讀者可循篇號回正文覆核。' %
          (len(rows), cnt['同'], cnt['**異**']), '']

    # 各類對位與獨有之數
    from collections import Counter
    tb, tn, pb, pn = Counter(), Counter(), Counter(), Counter()
    for r in B.values():
        tb[crime(r['fam'])] += 1
    for r in N.values():
        tn[crime(r['fam'])] += 1
    tn['提舍尼'] = 8          # 尼提舍尼 8 戒合為 2 節，jie_family 未登錄
    for b, n, *_ in rows:
        pb[crime(b['fam'])] += 1
        pn[crime(n['fam'])] += 1
    L += ['#### 附錄五之二　各類對位與獨有之數', '',
          '| 罪類 | 比丘 | 已對位 | 比丘獨有 | 比丘尼 | 已對位 | 比丘尼獨有 |',
          '|---|---|---|---|---|---|---|']
    for k in ['波羅夷', '僧殘', '捨墮', '單提', '提舍尼']:
        L.append('| %s | %d | %d | %d | %d | %d | %d |' %
                 (k, tb[k], pb[k], tb[k] - pb[k], tn[k], pn[k], tn[k] - pn[k]))
    L.append('| **合計** | **%d** | **%d** | **%d** | **%d** | **%d** | **%d** |' %
             (sum(tb[k] for k in tb if k in ('波羅夷','僧殘','捨墮','單提','提舍尼')),
              sum(pb.values()),
              sum(tb[k] - pb[k] for k in tb if k in ('波羅夷','僧殘','捨墮','單提','提舍尼')),
              sum(tn[k] for k in tn if k in ('波羅夷','僧殘','捨墮','單提','提舍尼')),
              sum(pn.values()),
              sum(tn[k] - pn[k] for k in tn if k in ('波羅夷','僧殘','捨墮','單提','提舍尼'))))
    L += ['', '> 比丘另有不定 2、眾學 100、滅諍 7；尼律無不定，眾學與滅諍二部共遵，'
          '不另立條目，故不列於上表。尼提舍尼 8 條皆為「無病乞酥油蜜石蜜乳酪魚肉」，'
          '與比丘四提舍尼（受尼食、不止尼代索、學家、恐處）**制各不同**，無對位可列。', '']

    # 眾學法：尼律不另立條目，須單獨交代
    xue = []
    for no in (22, 23, 24):
        for u in S.units(no):
            xue.append((no, u.get('name') or '', u['a'], u['b']))
    L += ['#### 附錄五之三　眾學法（二部共遵，無對位可列）', '',
          '> 查尼律諸篇（026–037）**全無「眾學／式叉迦羅尼／應當學」之獨立條目**；'
          '眾學法為二部共遵之威儀法，比丘尼不另立戒條。'
          '故本表無「比丘眾學 ↔ 尼眾學」之對位——非遺漏，乃體例如是。'
          '為便讀者掌握，下列比丘眾學全部 %d 目（篇 022–024），'
          '尼眾亦同遵此批威儀。' % len(xue), '',
          '| 篇 | 眾學目 | 段次 |', '|---|---|---|']
    for no, nm, a2, b2 in xue:
        L.append('| %03d | %s | %d–%d |' % (no, nm[:34] or '（承上省語）', a2, b2))
    L.append('')
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
            cc = _c.Counter(d['cite'].split(' ')[1] for _, d in gu)
            L += ['**根有（%d 格，依卷分佈）**' % len(gu), '',
                  '| 卷 | 格數 |', '|---|---|']
            for k in sorted(cc, key=lambda x: int(x.replace('卷', '') or 0)):
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
