#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從各稿 findings 抽取每一項的主稿「原文」（及白話），
建立 (canon, unit, no) → {orig, plain} 索引。

做法：先把檔案切成「### N. 標題」為界的區塊，再於區塊內用正則取
「- 原文：」以下的引文塊、「- 白話：」以下的縮排塊。
"""
import os, re, json, glob

BASE = os.path.dirname(os.path.abspath(__file__))

DIRS = {
    '五分': 'findings',
    '十誦': 'findings_ss',
    '僧祇': 'findings_mk',
    '根有': 'findings_gu',
}

RE_H3 = re.compile(r'^###\s+(\d+)\.\s+(.+?)\s*$', re.M)
RE_H2 = re.compile(r'^##\s+', re.M)
# 「- 原文：」到「- 白話：」或下一個欄位，或任一標題（## / ###），或區塊尾
BOUND = r'(?=^-\s*(?:白話|補證|位置|四分律對照|五分律對照|十誦律對照|差異說明)\s*[：:]|^#{2,6}\s|\Z)'
RE_ORIG_BLOCK = re.compile(r'^-\s*原文\s*[：:]\s*\n(.*?)' + BOUND, re.M | re.S)
# 白話可接在同行（「- 白話：……」）或次行（縮排塊），
# 標籤後也可能帶夾註（「- 白話（括號內名相略釋）：」），兩種都要吃
RE_PLAIN_BLOCK = re.compile(
    r'^-\s*白話\s*(?:[（(][^）)\n]{0,40}[）)])?\s*[：:][ \t]*\n?(.*?)' + BOUND,
    re.M | re.S)
RE_QUOTE = re.compile(r'^\s*>\s?(.*)$')


def extract_quotes(block):
    """從引文塊取 > 開頭的行"""
    lines = []
    for ln in block.split('\n'):
        m = RE_QUOTE.match(ln)
        if m:
            lines.append(m.group(1).rstrip())
    return '\n'.join(lines).strip()


def extract_plain(block):
    """從白話塊取非空行（去掉縮排）"""
    lines = []
    for ln in block.split('\n'):
        s = ln.strip()
        if s:
            lines.append(s)
    return '\n'.join(lines).strip()


def parse_file(path):
    txt = open(path, encoding='utf-8').read()

    # 只取「## 保留項」至下一個 ## 章節之間的內容；
    # 若無「保留項」標題，則取全文（部分稿直入 ### 項）。
    m_keep = re.search(r'^##\s*保留項\s*$', txt, re.M)
    if m_keep:
        rest = txt[m_keep.end():]
        m_next = re.search(r'^##\s+', rest, re.M)
        body_txt = rest[:m_next.start()] if m_next else rest
    else:
        body_txt = txt

    marks = list(RE_H3.finditer(body_txt))
    out = {}
    for i, m in enumerate(marks):
        no = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body_txt)
        body = body_txt[start:end]

        mo = RE_ORIG_BLOCK.search(body)
        orig = extract_quotes(mo.group(1)) if mo else ''
        mp = RE_PLAIN_BLOCK.search(body)
        plain = extract_plain(mp.group(1)) if mp else ''

        out[no] = {'title': title, 'orig': orig, 'plain': plain}
    return out


def main():
    index = {}
    for canon, d in DIRS.items():
        dpath = os.path.join(BASE, d)
        if not os.path.isdir(dpath):
            continue
        n_items = n_orig = n_plain = 0
        for fp in sorted(glob.glob(os.path.join(dpath, 'vol*.md'))):
            unit = os.path.splitext(os.path.basename(fp))[0]
            parsed = parse_file(fp)
            for no, v in parsed.items():
                index[f'{canon}|{unit}|{no}'] = v
                n_items += 1
                if v['orig']:
                    n_orig += 1
                if v['plain']:
                    n_plain += 1
        print(f'{canon}: {n_items} 項，有原文 {n_orig}，有白話 {n_plain}')

    out = os.path.join(BASE, 'originals_index.json')
    json.dump(index, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'\n已存 {out}（{len(index)} 項）')

    rows = json.load(open(os.path.join(BASE, 'matrix_built.json'), encoding='utf-8'))
    hit = miss = 0
    miss_list = []
    for r in rows:
        k = f"{r['canon']}|{r['unit']}|{r['no']}"
        if k in index and index[k]['orig']:
            hit += 1
        else:
            miss += 1
            if len(miss_list) < 10:
                miss_list.append(k)
    print(f'與矩陣對齊：命中 {hit}，未命中 {miss}（{hit/(hit+miss)*100:.1f}%）')
    print('未命中樣本:', miss_list)

    # 樣本
    print('\n=== 樣本 ===')
    for k in ['五分|vol01|1', '十誦|vol01|1', '僧祇|vol01-02|1', '根有|vol01|1']:
        if k in index:
            v = index[k]
            print(f'[{k}] {v["title"]}')
            print('  原文:', v['orig'][:100].replace('\n', ' / '))
            print('  白話:', v['plain'][:60].replace('\n', ' / '))


if __name__ == '__main__':
    main()
