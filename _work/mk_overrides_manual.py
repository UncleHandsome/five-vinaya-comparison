# -*- coding: utf-8 -*-
"""Manual cell fills for the ten collision groups (G1–G7, T1–T3).

Each entry records the paragraph that settles the cell.  「有」 needs a 卷段;
「無」 needs the 查詞 actually run, because an absence claim is only as good as
the terms it was searched with.
"""
import os, json

W = os.path.dirname(os.path.abspath(__file__))

# (canon, unit, no, field, value, evidence)
FILL = [
    # G1 僧不差入尼住處教誡
    ('五分', 'vol07', 1, 'vGU', '有', '根有 卷31段10：「若復苾芻僧不差，自往教誡苾芻尼者，波逸底迦。」'),
    ('僧祇', 'vol14-15', 26, 'vGU', '有', '根有 卷31段10 同制；卷31段8–9 六眾次第教授、佛令眾差七法'),
    # G2 大房覆蓋重數
    ('五分', 'vol06', 11, 'vMK', '有', '僧祇 卷15段37：「覆者……再三者，非五六，極齊三。」'),
    ('五分', 'vol06', 11, 'vGU', '有', '根有 卷30段27：「應二三重齊橫扂處，若過者波逸底迦。」'),
    ('十誦', 'vol11-12', 9, 'vMK', '有', '僧祇 卷15段37 極齊三'),
    ('十誦', 'vol11-12', 9, 'vGU', '有', '根有 卷30段27、段34（熟甎石木過重數無犯）'),
    # G3 知檀越欲與僧物迴與餘人
    ('五分', 'vol09', 1, 'vGU', '有', '根有 卷24段45–47：知與僧伽物迴與一人、二人、餘僧伽，皆惡作'),
    ('僧祇', 'vol20-21', 18, 'vGU', '有', '根有 卷24段45–47 同'),
    # G4 輕師／輕他
    ('五分', 'vol08', 10, 'vMK', '有', '僧祇 卷20段26：「輕他者，有八事……波夜提。」'),
    ('根有', 'vol42-43', 1, 'vMK', '有', '僧祇 卷20段26 八事同；段28 出白僧聽之諸緣'),
    # G6 波羅夷與學行法
    ('十誦', 'vol56', 32, 'vGU', '無', '遍查未見（查詞：學悔／波羅市迦學／盡形學處）'),
    ('僧祇', 'vol25-26', 24, 'vGU', '無', '遍查未見（查詞：學悔／波羅市迦學／盡形學處）'),
    # G7 食前食後至餘家
    ('十誦', 'vol54', 26, 'vMK', '有', '僧祇 卷20段57：「若比丘同食處，食前食後不白比丘行至餘家，除餘時，波夜提。餘時者，衣時……」'),
    ('根有', 'vol42-43', 4, 'vMK', '有', '僧祇 卷20段57 同制'),
    # T1 為官所執取清淨欲
    ('五分', 'vol18', 11, 'vGU', '無', '遍查未見（查詞：清淨欲／與欲清淨／非時集）'),
    ('僧祇', 'vol27-28', 22, 'vGU', '無', '遍查未見（查詞：清淨欲／與欲清淨／非時集）'),
    # 同組跨行校正：同一制度在同一律的存在性不得一行有一行無
    ('五分', 'vol08', 10, 'v10', '有', '十誦 卷17段24–28 記不恭敬事羯磨，未記前突吉羅、記已波逸提'),
    ('十誦', 'vol54', 26, 'v5', '有', '五分 卷9段168：「若比丘，受他請，食前至餘家，波逸提。」'),
    # T3 水火災共相助舉
    ('五分', 'vol25', 9, 'vGU', '無', '遍查未見（查詞：卒風雨／暴風／共收／收舉）'),
    ('僧祇', 'vol33', 14, 'vGU', '無', '遍查未見（查詞：卒風雨／暴風／共收／收舉）'),
]

ov, log = {}, []
for canon, unit, no, field, val, ev in FILL:
    k = '%s|%s|%d' % (canon, unit, no)
    ov.setdefault(k, {})[field] = val
    log.append({'key': k, 'cell': field, 'before': '未比', 'ref': ev[:80],
                'by': '核定', 'unit': '', 'topic': '', 'reason': ev[:80]})

json.dump(ov, open(os.path.join(W, 'cell_overrides_manual.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(log, open(os.path.join(W, 'cell_xref_log_manual.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('manual cells', len(log))
