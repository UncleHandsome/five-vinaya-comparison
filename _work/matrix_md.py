# -*- coding: utf-8 -*-
"""Render the five-canon matrix to markdown."""
import json, os, re
from collections import Counter

from errata import apply as _apply_errata, dedup_xref, clean_title
from diff_fmt import expand_refs
from sifen_src import glyph_fix

W = os.path.dirname(os.path.abspath(__file__))
_raw = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))
rows = [_apply_errata(r) for r in _raw]
OUT = os.path.join(os.path.dirname(W), '03_成品', '五部律綜合異同矩陣.md')

CANONS = ['五分', '十誦', '僧祇', '根有']
LV = ['戒條', '制度', '法數', '事件']
ST = {'A': 'A 同條增異', 'B': 'B 同條開緣', 'C': 'C 四分所無', 'D': 'D 同條減略'}

# G/T 反查：M-#### → G1
_gt = json.load(open(os.path.join(W, 'gt_groups.json'), encoding='utf-8'))
ID2GT = {i: g for g, ids in _gt.items() for i in ids}

# 甲乙表為手工撰寫，從 _gt_static.md 讀入
_GT_STATIC = open(os.path.join(W, '_gt_static.md'), encoding='utf-8').read().rstrip()

ABSENT = ('遍查未見', '全無', '無此', '未見', '不見', '無對應', '俱無', '皆無', '並無')


def esc(s):
    return glyph_fix((s or '').replace('|', '｜').replace('\n', ' '))


def fill(canon, field):
    sub = [r for r in rows if r['canon'] == canon]
    y = n = u = 0
    for r in sub:
        f = r[field]
        if not f:
            u += 1
        elif any(k in f for k in ABSENT):
            n += 1
        else:
            y += 1
    return y, n, u


L = []
A = L.append

A('# 五部律綜合異同矩陣')
A('')
A('> 本表由 `_work/matrix_rows.json`（2,124 個保留項）機械生成，再疊入孤島碰撞的十組裁定。')
A('> 每一列即一稿之一個保留項，五欄各記該律「有／無／未比」，不補造證據。')
A('> 生成日期：2026-11-02。')
A('> 勘誤：M-1913 原判「四分所無」，經覆核四分律卷首實有五言偈，改判 A 同條增異，已於本表更正。')
A('> 原始數據見 `_work/matrix_built.json`，勘誤見 `_work/errata.py`。')
A('')
A('---')
A('')
A('## 一、欄位與口徑')
A('')
A('| 欄 | 內容 |')
A('|---|---|')
A('| 編號 | `M-0001` 起，全表連續 |')
A('| 主稿 | 不由欄位標示，見各段標題（五分／十誦／僧祇／根有） |')
A('| 層級 | 戒條／制度／法數／事件，依標題與差異說明判定 |')
A('| 狀態 | A 同條增異／B 同條開緣／C 四分所無／D 同條減略 |')
A('| 四分・五分・十誦・僧祇・根有 | 有／無／未比。**「無」是文獻學斷言，「未比」只是工作進度** |')
A('| 位置 | 主稿底本段號 |')
A('| 實質差異 | 節錄，全文見 CSV |')
A('| 補證 | 交叉引證（多數為「—」） |')
A('| 證據 | `unit#項號`，可回 `_work/findings*/` 覆核 |')
A('')
A('三條填寫紀律：')
A('')
A('1. **一格一狀態，不留空白。** 無證據者填「未比」，不得因該稿無此項就填「無」。')
A('2. **同一制度只佔一行。** 已歸併者見甲、乙二表，兩列並列同一 `G#`／`T#`。')
A('3. **狀態 C 須經孤島碰撞方可入表。** 未經碰撞的 C 項只作「孤本候選」。')
A('')
A('## 二、量化全貌')
A('')
A('### 2.1 各稿項數與狀態')
A('')
A('| 主稿 | 項數 | A 增異 | B 開緣 | C 四分所無 | D 減略 |')
A('|---|---:|---:|---:|---:|---:|')
tot = Counter()
for c in CANONS:
    sub = [r for r in rows if r['canon'] == c]
    cnt = Counter(r['st'] for r in sub)
    for k in 'ABCD':
        tot[k] += cnt[k]
    A('| %s | %d | %d | %d | %d | %d |' % (c, len(sub), cnt['A'], cnt['B'], cnt['C'], cnt['D']))
A('| **合計** | **%d** | **%d** | **%d** | **%d** | **%d** |'
  % (len(rows), tot['A'], tot['B'], tot['C'], tot['D']))
A('')
A('### 2.2 各稿對照欄的完備度')
A('')
A('矩陣的「有／無」不是憑空判斷，而是各稿對照欄的轉寫。下表顯示每一稿實際帶有哪幾個對照欄、'
  '其中多少條斷「有」、多少條斷「無」、多少條根本未設此欄。')
A('')
A('| 主稿 | 對照欄 | 有 | 無 | 未設 |')
A('|---|---|---:|---:|---:|')
for c, fields in [('五分', [('四分律對照', 'ref4'), ('十誦律對照', 'ref10')]),
                  ('十誦', [('四分律對照', 'ref4'), ('五分律對照', 'ref5')]),
                  ('僧祇', [('四分律對照', 'ref4'), ('五分律對照', 'ref5'), ('十誦律對照', 'ref10')]),
                  ('根有', [('四分律對照', 'ref4'), ('五分律對照', 'ref5'), ('十誦律對照', 'ref10')])]:
    for name, key in fields:
        y, n, u = fill(c, key)
        A('| %s | %s | %d | %d | %d |' % (c, name, y, n, u))
A('')
A('> 三點說明：①五分稿的「十誦律對照」只施於 110 個 C 項，故 268 項未設，此非疏漏而是體例；'
  '②五分稿「四分律對照」欄斷「無」者 116 條，其中 6 條係關鍵詞誤判（實為同戒而規制不同），'
  '2.1 的 C 數已改以人工核定的 110 為準；③僧祇、根有二稿本即帶三分對照，完備度最高，'
  '故矩陣於此二稿的「未比」最少。')
A('')
A('### 2.3 層級分布')
A('')
A('| 層級 | 項數 |')
A('|---|---:|')
cnt_lv = Counter(r['lv'] for r in rows)
for k in LV:
    A('| %s | %d |' % (k, cnt_lv[k]))
A('')
A('---')
A('')
A(_GT_STATIC)
A('')
A('---')
A('')
A('## 五、丙表：證據層矩陣（%s 列）' % format(len(rows), ','))
A('')
A('依主稿分四段。同稿內依原項次排列；`G#`／`T#` 表示該列已與他稿歸併。')
A('')
for c in CANONS:
    sub = [r for r in rows if r['canon'] == c]
    A('### %s（%d 項）' % (c, len(sub)))
    A('')
    A('| 編號 | 層級 | 狀態 | 主題 | 四分 | 五分 | 十誦 | 僧祇 | 根有 | 位置 | 實質差異 | 補證 | 證據 |')
    A('|---|---|---|---|:--:|:--:|:--:|:--:|:--:|---|---|---|---|')
    for r in sub:
        ev = '%s#%s' % (r['unit'], r['no'])
        g = ID2GT.get(r['id'])
        if g:
            ev += ' ' + g
        A('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            r['id'], esc(r['lv']), r['st'], esc(clean_title(r['title'], r['id'])),
            r.get('v4', '未比'), r.get('v5', '未比'), r.get('v10', '未比'),
            r.get('vMK', '未比'), r.get('vGU', '未比'),
            esc(r['pos']), esc(expand_refs(r['diff'] or '', r)),
            esc(dedup_xref(r.get('xref', ''))) or '—', ev))
    A('')
A('---')
A('')
A('## 六、未決事項')
A('')
A('1. **僧祇、根有二欄多為「未比」。** 五分稿與十誦稿未設此二對照欄，故矩陣於此二欄留白。'
  '補法：以 `_work/findings_mk/`、`findings_gu/` 為主稿，逐項回查五分、十誦底本。')
_nC = sum(1 for r in rows if r['st'] == 'C')
A('2. **C 項的碰撞已全掃，但未全裁。** C 項現為 %d（碰撞時 669，M-1913 後經覆核改判 A），'
  '皆已過三路檢索：①標題稀有詞共現（22 組）、②語料逐段碰撞（669 項全掃，224 項得候選，'
  '55 項強候選已逐條裁定）、③各稿刪除表交叉引用（15 項 26 條）。'
  '已捕獲 7 組同條、3 組同題異制，另有 2 項經語料碰撞改判。'
  '餘 169 項弱候選（多為單一人名地名）尚待逐條回讀。' % _nC)
A('3. **十誦稿的「五分律對照」欄已全備（949/949）**，但其 C 項 321 個尚未與僧祇、根有碰撞。')
A('4. **本表非定本。** 「未比」格一經補查即須改寫；凡改寫皆應同時更新 `matrix_rows.json` 與本表，'
  '不得只改表。')
A('')
A('---')
A('')
A('*資料來源：`_work/matrix_rows.json`（2,124 項）、`_work/island_verdicts.md`（22 組裁定）、'
  '`_work/sscol/*.tsv`（五分×十誦 111 條）、`_work/collide.json`（語料碰撞 224 候選）、'
  '`_work/crossref.json`（刪除表交叉引用 26 條）、`_work/audit_ss.json`（十誦刪除表 935 處反向校驗）。*')

open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
print(f'written {OUT} {len(L)} lines')
