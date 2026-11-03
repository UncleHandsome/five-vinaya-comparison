# -*- coding: utf-8 -*-
"""Dump each broken quote block plus the skipped source span, for hand-writing markers."""
import re, os

W = os.path.dirname(os.path.abspath(__file__))
TARGET = {24: ['此比丘犯罪，非不犯罪'],
          25: ['時羅睺羅至那羅聚落'],
          28: ['爾時拘舍彌有一長者'],
          29: ['時有一婬女名半迦尸', '有比丘尼產一男兒']}


def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def clean(q):
    for _ in range(3):
        q = re.sub(r'[（(〔]\s*段\s*\d+[^）)〕]{0,24}[）)〕]', '', q)
        q = re.sub(r'\*\*\s*段\s*\d+[^*]{0,12}\*\*', '', q)
        q = re.sub(r'[（(]\s*(?:節引|節錄|後段|中段|前段|末句|僅引[^）)]{0,12})[）)]', '', q)
        q = re.sub(r'段\s*\d+\s*(?:[～~\-–]\s*\d+\s*)?[：:]', '', q)
    return q


def load(v):
    rows, cur = [], 0
    src, pos = '', []
    for ln in open(os.path.join(W, 'wufen/vol%02d.txt' % v), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' not in ln:
            continue
        n, t = ln.split('\t', 1)
        if not n.isdigit():
            continue
        rows.append((int(n), t))
        s = norm(t)
        pos.append((cur, cur + len(s), int(n)))
        src += s
        cur += len(s)
    return src, pos, rows


def seg_at(pos, i):
    for a, b, n in pos:
        if a <= i < b:
            return n
    return None


def txt(raw):
    return norm(clean(raw.strip().lstrip('>').strip()))


for v, needles in TARGET.items():
    src, pos, rows = load(v)
    path = os.path.join(W, 'findings/vol%02d.md' % v)
    lines = open(path, encoding='utf-8').read().split('\n')
    for needle in needles:
        start = None
        for i, ln in enumerate(lines):
            if ln.strip().startswith('>') and needle in ln:
                start = i
                break
        if start is None:
            print('NOT FOUND', v, needle)
            continue
        end = start
        while end + 1 < len(lines) and lines[end + 1].strip().startswith('>'):
            end += 1
        blk = lines[start:end + 1]
        print('=' * 70)
        print('vol%02d  needle=%s' % (v, needle))
        for k, x in enumerate(blk):
            print('  [%d] %s' % (k, x))
        tj = None
        for j in range(1, len(blk)):
            if ''.join(txt(x) for x in blk[:j + 1]) not in src:
                tj = j
                break
        print('  --> break at blk[%d]: %s' % (tj, blk[tj]))
        prev = ''.join(txt(x) for x in blk[:tj])
        p = src.find(prev)
        i_end = p + len(prev)
        a = seg_at(pos, i_end - 1)
        b = seg_at(pos, src.find(txt(blk[tj])))
        print('  --> prev ends in 段%s, next starts in 段%s' % (a, b))
        lo, hi = (a if a else b), (b if b else a)
        for n, t in rows:
            if lo <= n <= hi:
                print('    段%d: %s' % (n, t[:300]))
