#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精確校勘：本稿原文（唯一逐字引文）是否真在該律原文中。

方法：
  1. 取 originals_index 的 orig
  2. 剝除段號標記（卷N·段M、段N、〔…〕）與標點
  3. 切成 12 字窗口，逐窗在該律全文中查找
  4. 若半數以上窗口命中，判為「可查」；否則記為待查

輸出：_work/_audit/precise.md
"""
import os, re, json
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
RAW = os.path.join(ROOT, '01_原文')
OUT = os.path.join(BASE, '_audit')

CANON = {'四分': '四分律', '五分': '五分律', '十誦': '十誦律',
         '僧祇': '摩訶僧祇律', '根有': '根本說一切有部毘奈耶'}


def load():
    T = {}
    for c, d in CANON.items():
        p = os.path.join(RAW, d)
        buf = []
        for fn in sorted(os.listdir(p)):
            if fn.endswith('.txt'):
                buf.append(open(os.path.join(p, fn), encoding='utf-8', errors='ignore').read())
        T[c] = re.sub(r'[^\u4e00-\u9fff]', '', ''.join(buf))
    return T


def clean_orig(s):
    """剝除段號標記與引號，只留正文"""
    s = s or ''
    s = re.sub(r'[〔【]\s*卷?\s*\d*\s*[·・]?\s*段?\s*\d*\s*[〕】]', '', s)
    s = re.sub(r'段\s*\d+', '', s)
    s = re.sub(r'卷\s*\d+', '', s)
    s = re.sub(r'^\s*\d+[-–]\d+\s*', '', s)
    s = s.replace('……', '').replace('…', '')
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def windows(s, w=12, step=6):
    return [s[i:i + w] for i in range(0, max(1, len(s) - w + 1), step)]


def main():
    T = load()
    orig = json.load(open(os.path.join(BASE, 'originals_index.json'), encoding='utf-8'))
    rows = json.load(open(os.path.join(BASE, 'matrix_built.json'), encoding='utf-8'))

    ok = 0
    bad = []
    for r in rows:
        key = f"{r['canon']}|{r['unit']}|{r['no']}"
        o = orig.get(key, {}).get('orig', '')
        if not o.strip():
            continue
        body = clean_orig(o)
        if len(body) < 12:
            continue
        ws = windows(body)
        if not ws:
            continue
        text = T.get(r['canon'], '')
        hit = sum(1 for w in ws if w in text)
        ratio = hit / len(ws)
        if ratio >= 0.5:
            ok += 1
        else:
            bad.append((r['id'], r['canon'], round(ratio, 2), body[:60], o[:80]))

    print(f'本稿原文：可查 {ok}，待查 {len(bad)}（{(1-ok/(ok+len(bad)))*100:.2f}% 待查）')

    # 待查者：查是否屬他律
    lines = ['# 本稿原文精確校勘', '',
             f'- 可查（窗口命中 ≥50%）：{ok}',
             f'- 待查：{len(bad)}', '']
    cross = 0
    for rid, canon, ratio, body, raw in bad:
        where = [c for c in T if body[:14] in T[c]]
        tag = '、'.join(where) if where else '五部皆無'
        if where and canon not in where:
            cross += 1
        lines.append(f'- `{rid}` [{canon}] 命中率 {ratio} → 見於「{tag}」')
        lines.append(f'  - 正文：{body[:56]}')
        lines.append(f'  - 原記：{raw[:70]}')
    lines.insert(4, f'- 其中疑屬他律：{cross}')
    lines.append('')
    open(os.path.join(OUT, 'precise.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    print(f'疑屬他律：{cross}')
    print(f'報告：{os.path.join(OUT, "precise.md")}')


if __name__ == '__main__':
    main()
