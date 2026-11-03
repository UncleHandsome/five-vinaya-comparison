#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""差異說明的可讀性處理。

四件事，都不改事實，只改指代與排版：
  1. expand_refs  —— 「兩律」「三律」「本律」換成具體律名（由五欄判定，可判定率 98%）
  2. bold_canons  —— 律名加粗，便於掃讀
  3. split_sentences —— 依句號斷行，過長者再依分號斷（括號內不斷）
  4. diff_lines   —— 輸出 Markdown 行

用法：
    from diff_fmt import diff_lines
    lines = diff_lines(row)      # row 為 matrix_built 的一列
"""
import re

CANONS = [('v4', '四分'), ('v5', '五分'), ('v10', '十誦'), ('vMK', '僧祇'), ('vGU', '根有')]
ORDER = ['四分', '五分', '十誦', '僧祇', '根有']
NUM = {'兩': 2, '二': 2, '三': 3, '四': 4}

RE_REF = re.compile(r'([兩二三四])(部)?律')
RE_SELF = re.compile(r'(本律|此律)(首|冠辭|全文|全篇|開頭)?')
RE_CANON = re.compile(r'(四分|五分|十誦|僧祇|根有)(律?)')
RE_SENT = re.compile(r'[^。]*。|[^。]+$')


def _sets(row):
    """回傳（他律清單, 含本律清單），只計已比對者，按傳統次序。"""
    others = [n for k, n in CANONS if n != row.get('canon') and row.get(k) not in ('', '未比')]
    whole = [row.get('canon')] + others
    others.sort(key=ORDER.index)
    whole.sort(key=ORDER.index)
    return others, whole


def expand_refs(text, row):
    """「兩律」→具體律名；「本律」「此律」→本稿律名。無法判定者原樣保留。"""
    others, whole = _sets(row)

    def sub(m):
        n = NUM[m.group(1)]
        # 「二部律」為專名（比丘、比丘尼二部之律），不可拆
        if m.group(2) and m.group(1) == '二':
            return m.group(0)
        if len(others) == n:
            return '、'.join(others)
        if len(whole) == n:
            return '、'.join(whole)
        # 兩者皆不合，即上下文不足以判定所指，寧存舊文，不可臆斷
        return m.group(0)

    text = RE_REF.sub(sub, text)

    def sub_self(m):
        name = row.get('canon') or '本律'
        tail = m.group(2) or ''
        if tail == '首':
            tail = '篇首'
        elif tail in ('冠辭', '全文', '全篇', '開頭'):
            tail = ''
        return name + tail

    return RE_SELF.sub(sub_self, text)


def bold_canons(text, once=True):
    """律名加粗（含其後之「律」字）。已在 ** 內者不重複。

    once=True 時，同一段文字中每部律只標首次，免粗體過密反失焦點。
    """
    out, i, seen = [], 0, set()
    for m in RE_CANON.finditer(text):
        if text[:m.start()].count('**') % 2 == 1:
            continue
        if once and m.group(1) in seen:
            continue
        seen.add(m.group(1))
        out.append(text[i:m.start()])
        out.append('**' + m.group(1) + m.group(2) + '**')
        i = m.end()
    out.append(text[i:])
    return ''.join(out)


def _split_long(s):
    """長句依分號斷，但括號內的分號不算。"""
    depth, cuts = 0, []
    for i, ch in enumerate(s):
        if ch in '（(':
            depth += 1
        elif ch in '）)':
            depth = max(0, depth - 1)
        elif ch == '；' and depth == 0:
            cuts.append(i)
    if not cuts:
        return [s]
    out, prev = [], 0
    for c in cuts:
        out.append(s[prev:c].strip() + '。')
        prev = c + 1
    tail = s[prev:].strip()
    if tail:
        out.append(tail)
    return out


def split_sentences(text, limit=110):
    """依句號斷句；單句超過 limit 字者再依分號斷。"""
    sents = [s.strip() for s in RE_SENT.findall(text) if s.strip()]
    out = []
    for s in sents:
        if len(s) > limit:
            out.extend(_split_long(s))
        else:
            out.append(s)
    return out


def diff_lines(row, bold=True, expand=True, limit=110):
    """回傳可直接寫入 Markdown 的行（不含尾隨空行）。"""
    text = (row.get('diff_full') or row.get('diff') or '').replace('\n', ' ').strip()
    if not text:
        return []
    if expand:
        text = expand_refs(text, row)
    sents = split_sentences(text, limit)
    if bold:
        sents = [bold_canons(s) for s in sents]
    if len(sents) <= 1:
        return [f'**差異**：{sents[0] if sents else text}']
    return ['**差異**'] + [f'- {s}' for s in sents]


if __name__ == '__main__':
    import json, os, sys
    base = os.path.dirname(os.path.abspath(__file__))
    rows = json.load(open(os.path.join(base, 'matrix_built.json'), encoding='utf-8'))
    ids = sys.argv[1:] or ['M-0001', 'M-1329', 'M-1707']
    for i in ids:
        r = [x for x in rows if x['id'] == i][0]
        print('=' * 60)
        print(i, r['canon'], r['title'])
        print('原：', r['diff_full'])
        for ln in diff_lines(r):
            print('  ', ln)
