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
    import sifen_src as S
    b, n = [], []
    for no in range(1, 26):
        for u in S.units(no):
            if u.get('cn'):
                b.append((no, u['cn'], u.get('name') or '', crime_of(no)))
    for no in range(26, 38):
        for u in S.units(no):
            if u.get('cn'):
                n.append((no, u['cn'], u.get('name') or '', crime_of(no)))
    print('比丘 %d 戒／尼 %d 戒' % (len(b), len(n)))

    pairs = []
    for no, cn, nm, cr in b:
        best, bs = None, 0.0
        for no2, cn2, nm2, cr2 in n:
            if not compatible(FAM.get(no), FAM.get(no2)):
                continue
            v = sim(nm, nm2)
            if v > bs:
                best, bs = (no2, cn2, nm2, cr2), v
        if best and bs >= 0.40:
            pairs.append((no, cn, nm, cr, best, bs, '自動對位'))
    # 編者判定：異名、或跨罪屬而確為共戒者（使用者所舉「摩觸」即此）
    manual = [
        ((3, '二', '摩觸女人', crime_of(3)),
         (26, '五', '染污心，共染污心男子', crime_of(26)),
         '罪名由僧殘升為波羅夷'),
    ]
    for (no, cn, nm, cr), best, why in manual:
        found = False
        for i, p in enumerate(pairs):
            if p[0] == no and p[1] == cn:
                pairs[i] = (no, cn, nm, cr, best, p[5], '編者判定：' + why)
                found = True
                break
        if not found:
            pairs.append((no, cn, nm, cr, best, None, '編者判定：' + why))

    pairs.sort(key=lambda p: (p[0], p[1]))
    L = ['### 附錄五　比丘／比丘尼共戒對位表', '',
         '> **範圍**：只列二部共有之戒（共戒）；比丘獨有、比丘尼獨有者不列。'
         '波羅夷、僧殘、捨墮、**單提（波逸提）**、**眾學法**各類皆納入對位。',
         '>',
         '> **判準**：以戒名字元相似度 ≥ 0.30 自動候選；異名而確為共戒者由編者判定補入。'
         '「罪名異同」一欄為本表重點——同題之戒，二部所結之罪未必相同。'
         '相似度僅為檢索之便，**非判定**；表列「待覆核」者請回二部戒文自校，'
         '本書不強配（凡例六）。',
         '',
         '| 比丘 | 比丘戒名 | 罪屬 | 比丘尼 | 比丘尼戒名 | 罪屬 | 罪名異同 | 依據 |',
         '|---|---|---|---|---|---|---|---|']
    cnt = collections.Counter()
    for no, cn, nm, cr, best, s, tag in pairs:
        no2, cn2, nm2, cr2 = best
        same = '同' if FAM.get(no) == FAM.get(no2) else '**異**'
        cnt[same] += 1
        why = ('相似度 %.2f' % s) if s is not None else '編者判定'
        L.append('| %03d-%s | %s | %s | %03d-%s | %s | %s | %s | %s／%s |' %
                 (no, cn, nm[:26], cr, no2, cn2, nm2[:26], cr2, same, tag, why))
    L += ['', '> 共戒對位 **%d** 組：罪屬相同 %d 組、相異 %d 組。'
          '罪名相異者即二部立法輕重之別，讀者可循篇號回正文覆核。' %
          (len(pairs), cnt['同'], cnt['**異**']), '']
    # 眾學法：尼律不另立條目，須單獨交代，否則「眾學法都做」會落空
    import sifen_src as S
    xue = []
    for no in (22, 23, 24):
        for u in S.units(no):
            xue.append((no, u.get('name') or '', u['a'], u['b']))
    L += ['#### 附錄五之一　眾學法（二部共遵，無對位可列）', '',
          '> 查尼律諸篇（026–037）**全無「眾學／式叉迦羅尼／應當學」之獨立條目**；'
          '眾學法為二部共遵之威儀法，比丘尼不另立戒條。'
          '故本表無「比丘眾學 ↔ 尼眾學」之對位——非遺漏，乃體例如是。'
          '為便讀者掌握，下列比丘眾學全部 %d 目（篇 022–024），'
          '尼眾亦同遵此批威儀。' % len(xue), '',
          '| 篇 | 眾學目 | 段次 |', '|---|---|---|']
    for no, nm, a, bb in xue:
        L.append('| %03d | %s | %d–%d |' % (no, nm[:34] or '（承上省語）', a, bb))
    L += ['', '> 又尼律篇 037 之末別出〔波羅提提舍尼〕「乞酥食」等目，'
          '與比丘四提舍尼同制，亦屬二部共戒；本書正文已於各該節對讀，不另列表。', '']
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
    # 去重並限列，避免與既有矩陣完全重覆
    L = ['### 附錄六　五部律開遮持犯差異表（差異導向）', '',
         '> **範圍**：只列「有差異可說」者——同條開緣（狀態 B）或差異說明涉及'
         '不犯／開緣／罪名輕重之戒條項。此表**不是**逐戒全表；'
         '空白一律為「未比」（未經比勘），**非謂該部無此開緣**（凡例六）。',
         '>',
         '> **讀法**：「有／無」記該部於此項是否見其制；欲知其實，循「證據」欄'
         '（所屬律卷檔#項序）回矩陣，再按附錄四之法反查本書正文。',
         '',
         '| 事由 | 狀態 | 四分 | 五分 | 十誦 | 僧祇 | 根有 | 差異類型 | 證據 |',
         '|---|---|---|---|---|---|---|---|---|']
    for e in picked:
        t = (e.get('title') or '').replace('|', '／')[:38]
        v = [e.get(k, '') for k in ('v4', 'v5', 'v10', 'vMK', 'vGU')]
        v = ['未比' if x == '未比' else x for x in v]
        dt = {'A': '同條增異', 'B': '同條開緣', 'C': '四分所無', 'D': '同條減略'}.get(e['st'], e['st'])
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s %s#%s |' %
                 (t, e['st'], *v, dt, e['canon'], e['unit'], e['no']))
    L += ['', '> 共 **%d** 列。表內「未比」不得讀作「無」；'
          '若欲逐戒全表（每戒 × 五部 × 制／開／犯／不犯），'
          '須另立資料層，非本次差異項抽取所能任。' % len(picked), '']
    print('附錄六', len(picked), '列')
    return '\n'.join(L)


def main():
    a5, a6 = build5(), build6()
    open(os.path.join(WORK, 'appendix5.md'), 'w', encoding='utf-8').write(a5)
    open(os.path.join(WORK, 'appendix6.md'), 'w', encoding='utf-8').write(a6)
    print('附錄五／六已寫出')


if __name__ == '__main__':
    main()
