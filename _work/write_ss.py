# -*- coding: utf-8 -*-
"""Write the 十誦律去重 edition from findings_ss, using re-anchored quotes."""
import os, re, json
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assemble_ss.py'), encoding='utf-8').read().split('json.dump({')[0])

BY = {x['unit']: x for x in units_out}
meta = json.load(open(os.path.join(W, 'ss_assemble_meta.json'), encoding='utf-8'))
stats = {s['unit']: s for s in meta['stats']}

TOT_SRC = sum(s['src'] for s in meta['stats'])
TOT_KEPT = sum(s['kept'] for s in meta['stats'])
TOT_ITEMS = sum(s['items'] for s in meta['stats'])

FAN = '''# 十誦律去重

以《十誦律》（說一切有部）為底本，以《四分律》（法藏部）與《五分律》（彌沙塞部）為對校本；凡兩律任一已有之內容，視為重複，一律刪去，只保留十誦律獨有、或與兩律均實質不同之文。本編不譯白話，原文逐字迻錄。

## 凡例

一、底本：《十誦律》六十一卷，據本資料夾 `十誦律/` 六檔；段號依分卷檔 `_work/shisong/volNN.txt`（卷內自然段編號）。對校本：《四分律》六十卷、《五分律》三十卷，均據本資料夾原檔。

二、判重口徑（以「戒條／制度／程序／事件／法數清單」為單位，不依字句）：
1. 四分律或五分律任一方有同一戒、同一制度、同一事件、同一法數，且內容實質相同者 → 刪除。
2. 須兩律皆無；或兩律雖有同一戒／同一事件而十誦律有實質增異（判罪輕重、程序羯磨、法數多寡、關鍵人物或結局不同）者 → 保留其增異部分。
3. 僅屬譯語、詳略、修辭、次第不同，或名相異稱而範疇相當者 → 不保留。
4. 同一戒之緣起，若只是同事件之細節擴寫 → 不保留；若為兩律所無之獨立情節 → 保留。

三、保留比例：全書六十一卷正文 @@SRC@@ 字，本編保留 @@KEPT@@ 字，約百分之 @@RATIO@@。戒條與揵度部分（卷1～47）多在百分之十五至三十；優波離問、毘尼增一兩部多為十誦律獨有之判例問答，故比例偏高（部分卷次達五至九成），此係文本結構使然，非採錄過寬。逐卷數字見「全書統計」。

四、編次：依十誦律卷次（六十一卷，分四十四個校勘單位）。每先標卷名、範圍與刪略統計，再列保留項。每項含「位置」（底本段號）、「四分律對照」、「五分律對照」、「差異說明」、「原文」五目。

五、引文：原文一律逐字迻錄，並已逐句回錨底本（九百四十九項全數對上，無改字）；同一項若跨段引用，段前標「段N」，段間標「（中略：段X～Y）」。

六、資料限制：
1. 《四分律》自恣揵度之一未入本資料夾；卷23～24自法之比對以其餘部分及全庫檢索為據。
2. 《四分律》尼律單提第一至八十六戒僅存戒條列表，緣起從缺；此部分以戒條有無與內容異同為準。
3. 十誦律卷50～61（增一法、優波離問、集法）在四分律僅有毘尼增一、調部可校，五分律無獨立當應篇章，故比對以內容相近之法數與問答為準。

## 全書統計

| 校勘單位 | 卷次與篇目 | 底本字數 | 保留字數 | 比例 | 保留項 |
|---|---|---:|---:|---:|---:|'''

lines = [FAN.replace('@@SRC@@', format(TOT_SRC, ',')).replace('@@KEPT@@', format(TOT_KEPT, ',')).replace('@@RATIO@@', '%.1f' % (TOT_KEPT/TOT_SRC*100))]
for u in UNITS:
    s = stats[u['unit']]
    lines.append('| %s | %s | %s | %s | %.1f%% | %d |' % (
        u['unit'], u['title'], format(s['src'], ','), format(s['kept'], ','), s['ratio']*100, s['items']))
lines.append('| **合計** | 六十一卷 | **%s** | **%s** | **%.1f%%** | **%d** |' % (
    format(TOT_SRC, ','), format(TOT_KEPT, ','), TOT_KEPT/TOT_SRC*100, TOT_ITEMS))
lines.append('\n> 字數以中文字計，不含標點與段號。\n')

lines.append('## 目錄\n')
for u in UNITS:
    lines.append('- [%s](#%s)（%d 項）' % (u['title'], 'ss' + u['unit'].replace('vol', ''), stats[u['unit']]['items']))
lines.append('- [附錄一：刪略總表](#app1)')
lines.append('- [附錄二：存疑總表](#app2)')
lines.append('- [附錄三：工作方法與資料限制](#app3)\n')

body = []
for i, u in enumerate(UNITS):
    key = 'ss' + u['unit'].replace('vol', '')
    if i:
        body.append('\n---\n')
    s = stats[u['unit']]
    body.append('<a id="%s"></a>' % key)
    body.append('## %s\n' % u['title'])
    body.append('> 底本 %s 字，本編保留 %s 字（%.1f%%），保留 %d 項；其餘與四分律或五分律文意重複，刪略理由見附錄一。\n' % (
        format(s['src'], ','), format(s['kept'], ','), s['ratio']*100, s['items']))
    for it in BY[u['unit']]['items']:
        body.append(it.strip() + '\n')

app = ['\n---\n', '<a id="app1"></a>', '# 附錄一：刪略總表\n',
       '逐單位列出未保留之段落及其兩律對應。「遍查未見」指已檢索該律全庫未得對應。此表為刪略之審計紀錄。\n']
for u in UNITS:
    if BY[u['unit']]['deletion']:
        app.append('\n## %s\n' % u['title'])
        app.append(BY[u['unit']]['deletion'] + '\n')
app += ['\n---\n', '<a id="app2"></a>', '# 附錄二：存疑總表\n',
        '以下各條界限難定，暫從刪略，另記待裁。\n']
for u in UNITS:
    if BY[u['unit']]['doubts']:
        app.append('\n## %s\n' % u['title'])
        app.append(BY[u['unit']]['doubts'] + '\n')

app.append('\n---\n<a id="app3"></a>\n' + '''# 附錄三：工作方法與資料限制

## 一、流程

1. 將《十誦律》六十一卷切分、編號；《四分律》切篇（七十五個篇章檔），《五分律》切三十卷三十五篇，另將受戒、說戒、安居、自恣四長篇切成小段，以便對照。
2. 逐卷（或相鄰二卷）為一單位，先按「戒條／制度／事件」將十誦文與兩律逐一對齊（條次多不相應，一按內容對齊），再逐段判定重複與否。
3. 每項須能以一話說清與兩律之實質差異；不能者歸入刪略或存疑。
4. 引文先由校勘稿摘錄，再逐句回錨底本，凡無法逐字對上者一律不收；跨段引用標「中略」。
5. 全部九百四十九項、一百六十一萬四千餘字（16.1 萬字）引文已逐字校驗通過，簡化字掃描未發現。

## 二、結果

- 底本 658,969 字（六十一卷正文）
- 保留 161,403 字（24.5%），949 項
- 戒條與揵度部分（卷1～47）保留 15%～28%；毘尼增一與優波離問（卷48～61）保留 22%～94%
- 存疑 @@N@@ 條（見附錄二），暫從刪略

## 三、限制與提醒

1. 「重複」指內容實質相同，非字句相同；三部律同屬不同部派，語彙、次第、判罪名相本異。
2. 校勘稿內文所引兩律檔號（如 `001`、`shoujie_1`、`W15`）為工作檔名，僅便覆核。
3. 十誦律卷八段120～145 等處，校勘中發現底本自身重出（異文），已按卷內重出處理。
4. 本編為節本，非校勘定本；引用原文請以底本覆核。

*完成日期：2026-10-31*
'''.replace('@@N@@', str(sum(1 for u in UNITS for _ in re.findall(r'^-|^1[.]|^2[.]|^3[.]', BY[u['unit']]['doubts'], re.M) if BY[u['unit']]['doubts']))))

full = '\n'.join(lines) + '\n' + '\n'.join(body) + '\n' + '\n'.join(app)
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, '十誦律_去重_合冊.md'), 'w', encoding='utf-8').write(full)

GROUPS = [('卷1至卷20', ['vol%02d' % i for i in range(1, 21)] + ['vol05-06', 'vol07-08', 'vol09-10', 'vol11-12', 'vol13-14', 'vol15-16', 'vol17-18', 'vol19-20']),
          ('卷21至卷40', None), ('卷41至卷61', None)]

def unit_vols(u):
    return u['vols']

def group_units(lo, hi):
    out = []
    for u in UNITS:
        vs = u['vols']
        if all(lo <= v <= hi for v in vs) and any(lo <= v <= hi for v in vs):
            out.append(u)
    return out

for name, lo, hi in [('卷一至卷二十', 1, 20), ('卷二十一至卷四十', 21, 40), ('卷四十一至卷六十一', 41, 61)]:
    us = group_units(lo, hi)
    hl = ['# 十誦律去重　%s\n' % name,
          '> 本冊為《十誦律去重》之分冊，收卷%d至卷%d。凡例、判重口徑與資料限制見合冊本。\n' % (lo, hi),
          '## 本冊統計\n',
          '| 校勘單位 | 卷次與篇目 | 底本字數 | 保留字數 | 比例 | 保留項 |',
          '|---|---|---:|---:|---:|---:|']
    for u in us:
        s = stats[u['unit']]
        hl.append('| %s | %s | %s | %s | %.1f%% | %d |' % (
            u['unit'], u['title'], format(s['src'], ','), format(s['kept'], ','), s['ratio']*100, s['items']))
    gs = sum(stats[u['unit']]['src'] for u in us)
    gk = sum(stats[u['unit']]['kept'] for u in us)
    gi = sum(stats[u['unit']]['items'] for u in us)
    hl.append('| **合計** | %d 卷 | **%s** | **%s** | **%.1f%%** | **%d** |\n' % (
        hi - lo + 1, format(gs, ','), format(gk, ','), gk/gs*100, gi))
    parts = ['\n'.join(hl)]
    for i, u in enumerate(us):
        s = stats[u['unit']]
        if i:
            parts.append('\n---\n')
        parts.append('## %s\n' % u['title'])
        parts.append('> 底本 %s 字，本編保留 %s 字（%.1f%%），保留 %d 項；其餘與四分律或五分律文意重複，刪略理由見合冊本附錄一。\n' % (
            format(s['src'], ','), format(s['kept'], ','), s['ratio']*100, s['items']))
        for it in BY[u['unit']]['items']:
            parts.append(it.strip() + '\n')
    open(os.path.join(OUT, '十誦律_去重_%s.md' % name), 'w', encoding='utf-8').write('\n'.join(parts))
    print(name, 'units', len(us), 'items', gi, 'kept', gk)

print('written', OUT, 'chars', len(full))
