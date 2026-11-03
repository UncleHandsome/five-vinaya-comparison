#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 matrix_built.json 的 2,124 項按「四分律」位置歸位，
產出以四分律為閱讀主線的五部差異對照本。

歸位策略：
  1. 解析 ref4 中的四分律篇號（000-074）與段號
  2. 四分所無（st=C）的 669 項，另立一部，按主題歸類
  3. 無法解析者，歸入「待歸位」並列於附錄
"""
import json, re, os
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
WORK = BASE
ROOT = os.path.dirname(BASE)

# ---------- 四分律篇目索引 ----------
sifen = json.load(open(os.path.join(WORK, 'sifen_index.json'), encoding='utf-8'))
SI = {x['n']: x for x in sifen}

# 卷次推定：依 file 欄位與篇目順序
# 01-10原文.txt 涵蓋卷1-10（篇000-012）；11-21 卷11-21（013-025）；
# 22-30 卷22-30（026-037）；31-37 卷31-37（038）；38-49 卷38-49（039-060）；
# 50-60 卷50-60（061-074）
def guess_juan(n):
    """依篇號推定所屬卷次（粗估，用於分章標題）"""
    if n <= 12:   return '卷一至卷十'
    if n <= 25:   return '卷十一至卷二十一'
    if n <= 37:   return '卷二十二至卷三十'
    if n == 38:   return '卷三十一至卷三十七'
    if n <= 60:   return '卷三十八至卷四十九'
    return '卷五十至卷六十'

# 受戒揵度等分塊檔 → 篇038
CHUNK_MAP = {
    'shoujie': 38, 'shuojie': 38, 'anju': 38, 'zizi': 38,
}

# ---------- 解析 ref4 ----------
RE_FILE3 = re.compile(r'(\d{3})[_A-Za-z\u4e00-\u9fff]*\.txt')
# 段號兩種寫法：「第4段」與「段4」
RE_SEG_AFTER = re.compile(r'[`」\s]{0,3}(?:第\s*(\d+)\s*段|段\s*(\d+))')
RE_NUM3_SEG = re.compile(r'(?<![\d`])(\d{3})(?![\d])\s*[`\s]{0,3}(?:第\s*(\d+)\s*段|段\s*(\d+))')
RE_CHUNK = re.compile(r'(shoujie|shuojie|anju|zizi)[_\d]*\.txt[`」\s]{0,3}(?:第\s*(\d+)\s*段|段\s*(\d+))')
RE_CHUNK2 = re.compile(r'(shoujie|shuojie|anju|zizi)[_\d]*[`」\s]{0,3}(?:第\s*(\d+)\s*段|段\s*(\d+))')
RE_BARE_NUM3 = re.compile(r'^`?(\d{3})`?\s*(?:第\s*(\d+)\s*段|段\s*(\d+))')
RE_SIFEN_PREFIX = re.compile(r'四分\s*(\d{3})[_A-Za-z\u4e00-\u9fff]*\s*(?:第\s*(\d+)\s*段|段\s*(\d+))')
# 「043.27：」篇號.段號
RE_DOT = re.compile(r'(?<![\d.])(\d{3})\.(\d{1,3})(?![\d])')
# 「044-37」篇號-段號
RE_DASH = re.compile(r'(?<![\d])(\d{3})-(\d{1,3})(?![\d])')
# 「四分005_十三僧殘法之三-18」篇名-段號
RE_NAME_DASH = re.compile(r'(\d{3})[_A-Za-z\u4e00-\u9fff]{1,20}-(\d{1,3})(?![\d])')
# 兜底：3 位篇號 + 任意短前綴 + 「段M」
RE_LOOSE = re.compile(r'(?<![\d])(\d{3})[^\d段]{0,30}段\s*(\d{1,4})(?![\d])')
# 「001_四波羅夷法之一 段22」篇名（無 .txt）+ 段號
RE_NAME_SEG = re.compile(r'(\d{3})[_A-Za-z\u4e00-\u9fff]{1,20}?\s+(?:第\s*(\d+)\s*段|段\s*(\d+))')


def _seg(m):
    """從含兩個可選段號組的 match 取段號"""
    if not m:
        return None
    for i in (2, 3):
        try:
            v = m.group(i)
        except IndexError:
            continue
        if v:
            return int(v)
    return None

def parse_ref4(ref):
    """回傳 (篇號, 起始段, None, 方式) 或 None"""
    if not ref:
        return None
    s = ref.strip()

    # 1) 分塊檔
    m = RE_CHUNK.search(s) or RE_CHUNK2.search(s)
    if m:
        key = m.group(1)
        seg = _seg(m)
        return (CHUNK_MAP.get(key, 38), seg or 1, None, 'chunk')

    # 2) 「四分005_...」
    m = RE_SIFEN_PREFIX.search(s)
    if m:
        return (int(m.group(1)), _seg(m) or 1, None, 'sifen_prefix')

    # 3) 開頭裸數字+段
    m = RE_BARE_NUM3.search(s)
    if m:
        return (int(m.group(1)), _seg(m) or 1, None, 'bare')

    # 4) `NNN_xxx.txt` 第M段
    m = RE_FILE3.search(s)
    if m:
        n = int(m.group(1))
        rest = s[m.end():]
        m2 = RE_SEG_AFTER.search(rest)
        # 注意：RE_SEG_AFTER 無前置捕獲組，段號在 group(1) 或 group(2)
        seg = None
        if m2:
            seg = m2.group(1) or m2.group(2)
        if seg is not None:
            return (n, int(seg), None, 'file')
        return (n, 1, None, 'file_only')

    # 5) 文中任處的「NNN 段M」
    m = RE_NUM3_SEG.search(s)
    if m:
        return (int(m.group(1)), _seg(m) or 1, None, 'num_seg')

    # 6) 「043.27」篇號.段號
    m = RE_DOT.search(s)
    if m:
        return (int(m.group(1)), int(m.group(2)), None, 'dot')

    # 6b) 「044-37」篇號-段號
    m = RE_DASH.search(s)
    if m:
        return (int(m.group(1)), int(m.group(2)), None, 'dash')

    # 7) 「001_四波羅夷法之一 段22」
    m = RE_NAME_SEG.search(s)
    if m:
        return (int(m.group(1)), _seg(m) or 1, None, 'name_seg')

    # 8) 「四分005_十三僧殘法之三-18」
    m = RE_NAME_DASH.search(s)
    if m:
        return (int(m.group(1)), int(m.group(2)), None, 'name_dash')

    # 9) 兜底：「038__開頭_·段181」等任意前綴 + 段號
    m = RE_LOOSE.search(s)
    if m:
        return (int(m.group(1)), int(m.group(2)), None, 'loose')

    return None


def main():
    rows = json.load(open(os.path.join(WORK, 'matrix_built.json'), encoding='utf-8'))

    # 載入四分各篇正文（每段一行，行號即段號）
    texts = {}
    for n, info in SI.items():
        p = os.path.join(WORK, 'sifen', info['path'])
        if os.path.exists(p):
            texts[n] = open(p, encoding='utf-8').read().split('\n')

    def quote_locate(ref):
        """以引文檢索兜底：取「」內最長引文，回 (篇, 段) 或 None"""
        qs = re.findall(r'「([^」]{6,})」', ref)
        if not qs:
            return None
        qs.sort(key=len, reverse=True)
        for q in qs[:4]:
            probe = q[:40]
            hits = []
            for n, lines in texts.items():
                for i, ln in enumerate(lines, 1):
                    if probe in ln:
                        hits.append((n, i))
                        if len(hits) > 1:
                            break
                if len(hits) > 1:
                    break
            if len(hits) == 1:
                return hits[0]
            if len(hits) > 1:
                # 多處命中，取第一篇（篇號小者，通常為本戒正出處）
                hits.sort()
                return hits[0]
        return None

    # 硬編：引文不足或原稿筆誤者，依語義定
    FORCE = {
        'M-0624': (38, 1),    # 卷37自恣揵度之一，未入庫，歸 038 篇首
        'M-0625': (38, 1),
        'M-1724': (2, 1),     # 妄語波羅夷戒，屬四波羅夷法之二
        # 原稿 ref4 作「050_呵責揵度·段145」，然 050 篇僅 19 段，
        # 「弟子有五事」實見 038 篇段145（全庫唯一），故正之。
        'M-1633': (38, 145),
        # 四分律卷首五言偈（000 篇段3），原稿判為四分所無，實有而簡
        'M-1913': (0, 3),
    }

    # 套用 G/T 歸併標記
    gt = {}
    for r in rows:
        m = re.search(r'\b(G\d+|T\d+)\b', r.get('xref', '') or '')
        if m:
            gt[r['id']] = m.group(1)

    placed = []      # 可歸位
    absent = []      # 四分所無
    unplaced = []    # 無法歸位

    for r in rows:
        if r['st'] == 'C':
            absent.append(r)
            continue

        loc = parse_ref4(r.get('ref4', ''))
        # 解析成功且段號未越界者，直接採用
        if loc and 1 <= loc[1] <= SI[loc[0]]['paras']:
            placed.append((r, loc[0], loc[1], loc[3]))
            continue

        # 兜底一：硬編（原稿筆誤，已考定者）
        if r['id'] in FORCE:
            n, seg = FORCE[r['id']]
            placed.append((r, n, seg, 'force'))
            continue
        # 兜底二：引文檢索
        ql = quote_locate(r.get('ref4', ''))
        if ql:
            placed.append((r, ql[0], ql[1], 'quote'))
            continue
        # 兜底三：有解析但段號越界，夾至篇末並記明
        if loc:
            n = loc[0]
            placed.append((r, n, SI[n]['paras'], 'clamp'))
            continue
        unplaced.append(r)

    print(f'總計 {len(rows)} 項')
    print(f'  可歸位（四分有對應）: {len(placed)}')
    print(f'  四分所無（C）: {len(absent)}')
    print(f'  無法歸位: {len(unplaced)}')
    print()
    c = Counter(p[3] for p in placed)
    print('解析方式:', dict(c))
    print()
    # 篇號分布異常檢查
    badn = [(r['id'], n, seg, r.get('ref4', '')[:60]) for r, n, seg, _ in placed if n not in SI]
    print(f'篇號越界: {len(badn)}')
    for x in badn[:10]:
        print('  ', x)
    print()
    print('無法歸位樣本:')
    for r in unplaced[:20]:
        print(f"  [{r['id']} {r['canon']} {r['st']}] {r.get('ref4','')[:100]}")

    # 存中間結果
    out = {
        'placed': [{'id': r['id'], 'n': n, 'seg': seg, 'how': how} for r, n, seg, how in placed],
        'absent': [r['id'] for r in absent],
        'unplaced': [r['id'] for r in unplaced],
    }
    json.dump(out, open(os.path.join(WORK, '_locate.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n已存 _locate.json')


if __name__ == '__main__':
    main()
