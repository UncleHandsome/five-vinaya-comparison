# -*- coding: utf-8 -*-
"""Insert （中略：段N） markers where a 五分 draft quote skips source text.

The five drafts mark omissions as （中略：段X）, but a handful of quotes jump
across one or more 段 without any marker, so the quotation reads as continuous
when it is not.  This script finds those jumps and inserts the marker.

Idempotent: skips a block whose break line is already followed by 中略.
"""
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
    src, pos, cur = '', [], 0
    for ln in open(os.path.join(W, 'wufen/vol%02d.txt' % v), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' not in ln:
            continue
        n, t = ln.split('\t', 1)
        if not n.isdigit():
            continue
        s = norm(t)
        pos.append((cur, cur + len(s), int(n)))
        src += s
        cur += len(s)
    return src, pos


def seg_at(pos, i):
    for a, b, n in pos:
        if a <= i < b:
            return n
    return None


def txt(raw):
    return norm(clean(raw.strip().lstrip('>').strip()))


for v, needles in TARGET.items():
    src, pos = load(v)
    path = os.path.join(W, 'findings/vol%02d.md' % v)
    for needle in needles:
        lines = open(path, encoding='utf-8').read().split('\n')
        start = None
        for i, ln in enumerate(lines):
            if ln.strip().startswith('>') and needle in ln:
                start = i
                break
        if start is None:
            print('BLOCK NOT FOUND', v, needle)
            continue
        end = start
        while end + 1 < len(lines) and lines[end + 1].strip().startswith('>'):
            end += 1
        blk = lines[start:end + 1]

        target_idx = None
        for j in range(1, len(blk)):
            joined = ''.join(txt(x) for x in blk[:j + 1])
            if joined and joined not in src:
                target_idx = j
                break
        if target_idx is None:
            print('NO BREAK', v, needle)
            continue
        # already marked?
        if target_idx + 1 < len(blk) and '中略' in blk[target_idx + 1]:
            print('ALREADY MARKED', v, needle)
            continue

        joined_prev = ''.join(txt(x) for x in blk[:target_idx])
        p = src.find(joined_prev)
        if p < 0:
            print('PREFIX NOT FOUND', v, needle)
            continue
        i_end = p + len(joined_prev)
        nxt = txt(blk[target_idx])
        i_bad = src.find(nxt)
        if i_bad < 0:
            # the break may sit inside this line; fall back to the head of the line
            i_bad = i_end
        a, b = seg_at(pos, max(i_end - 1, 0)), seg_at(pos, i_bad)
        if a is None or b is None:
            print('SEG UNRESOLVED', v, needle, a, b)
            continue
        mark = '（中略：段%d）' % a if a == b else '（中略：段%d～%d）' % (a, b)
        lines.insert(start + target_idx + 1, '  > ' + mark)
        open(path, 'w', encoding='utf-8').write('\n'.join(lines))
        print('INSERT vol%02d line %d: %s   [%s]' % (v, start + target_idx + 1, mark, needle))
