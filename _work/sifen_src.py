#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四分律原文與白話的「節」切分與渲染。

節（unit）＝對照本插入原文／白話的最小單位：
  前三十卷  依戒條（四分原文每戒末標「(一竟)」「(二竟)」…；尼單提諸篇標「(一)」「(二)」…）
  卷三十一至六十  依揵度與子題；過長者再依事件起首切成小段

資料來源：
  sifen/NNN_*.txt        段分好的四分律原文（段號\t文字）
  sifen_plain.json       段 → 白話（由 align_sifen2.py 產生）
"""
import os, re, glob, json, math

BASE = os.path.dirname(os.path.abspath(__file__))
SIFEN_DIR = os.path.join(BASE, 'sifen')
PLAIN_JSON = os.path.join(BASE, 'sifen_plain.json')

# ---------- 載入 ----------
SEG = {}      # 篇號 -> [(段號, 文字), ...]
for _f in sorted(glob.glob(os.path.join(SIFEN_DIR, '*.txt'))):
    _no = int(os.path.basename(_f)[:3])
    _lst = []
    for _l in open(_f, encoding='utf-8', errors='ignore'):
        _l = _l.rstrip('\n')
        if not _l.strip():
            continue
        _m = re.match(r'^(\d+)\t(.*)$', _l)
        if _m:
            _lst.append((int(_m.group(1)), _m.group(2)))
    SEG[_no] = _lst

PLAIN = {}
if os.path.exists(PLAIN_JSON):
    PLAIN = json.load(open(PLAIN_JSON, encoding='utf-8'))

RE_JING = re.compile(r'[（(]([一二三四五六七八九十百]+)竟[)）]?')
RE_TAIL = re.compile(r'[（(]([一二三四五六七八九十百]+)[）)]\s*$')
RE_NIAN = re.compile(r'[（(]([^（()）]{1,10}(?:揵度|犍度)[^（()）]{0,4}竟)[)）]')

# 事件起首（供長篇切點吸附）
RE_START = re.compile(r'^(爾時|時有|時，|時世|佛在|佛告|若比丘|優波離|諸比丘|告諸比丘|彼時|世尊)')


def _cn2int(s):
    """中文數字轉整數，支援「一百七十八」"""
    D = {'〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
         '六': 6, '七': 7, '八': 8, '九': 9}
    U = {'十': 10, '百': 100, '千': 1000}
    total, cur = 0, 0
    for ch in s:
        if ch in D:
            cur = D[ch]
        elif ch in U:
            cur = (cur or 1) * U[ch]
            total += cur
            cur = 0
        else:
            return 0
    return total + cur


def _jie_name(s):
    """從戒條句提取短名：去「若比丘」等主語，略去「若在村落」之類條件句"""
    s = re.sub(r'^[「『]?若(?:比丘|比丘尼)[，,]?', '', s or '')
    s = re.sub(r'[，,]?(尼薩耆波逸提|僧伽婆尸沙|波羅夷|波逸提|波羅提提舍尼|突吉羅).*$', '', s)
    s = re.sub(r'^衣已竟[，,]?迦絺那衣已[出捨][，,]?', '', s)
    for cl in re.split(r'[，,；;]', s):
        cl = cl.strip('，,。 「」『』')
        if not cl or re.match(r'^若|^除|^有|^復', cl):
            continue
        return cl[:14] + ('…' if len(cl) > 14 else '')
    return ''


def _units_jing(no):
    """依「(N竟)」切戒"""
    segs = SEG[no]
    marks = []
    for n, t in segs:
        m = RE_JING.search(t)
        if m:
            marks.append((n, m.group(1)))
    out, prev = [], 0
    for n, cn in marks:
        body = '\n'.join(t for k, t in segs if prev < k <= n)
        m = re.search(r'當如是說[：:]\s*([^\n。]{8,120})', body)
        out.append({'a': prev + 1, 'b': n, 'cn': cn, 'name': _jie_name(m.group(1)) if m else ''})
        prev = n
    if prev < segs[-1][0]:
        out.append({'a': prev + 1, 'b': segs[-1][0], 'cn': '', 'name': ''})
    return out


def _crime_name(body):
    """從戒條段找「……者，波逸提」的定罪句，取前面的罪名短語"""
    m = re.search(r'([^，。；：！？「」『』（）()]{2,18})[，,]?\s*(?:波羅夷|僧伽婆尸沙|僧殘|偷蘭遮|波逸提|波羅提提舍尼|突吉羅)', body)
    if not m:
        return ''
    s = re.sub(r'\s+', '', m.group(1))
    s = re.split(r'[，,、]', s)[-1]
    s = re.sub(r'^(彼|若|此|諸|有)?(比丘尼?|沙彌尼?)?[，,]?', '', s)
    return s[:14] + ('…' if len(s) > 14 else '')


def _units_tail(no):
    """依「(N)」尾標切戒（尼單提諸篇）"""
    segs = SEG[no]
    marks = [(n, m.group(1)) for n, t in segs if (m := RE_TAIL.search(t))]
    out, prev = [], 0
    for n, cn in marks:
        body = '\n'.join(t for k, t in segs if prev < k <= n)
        out.append({'a': prev + 1, 'b': n, 'cn': cn, 'name': _crime_name(body)})
        prev = n
    if prev < segs[-1][0]:
        out.append({'a': prev + 1, 'b': segs[-1][0], 'cn': '', 'name': ''})
    return out


def _split_budget(segs, a, b, budget=3600, maxseg=48):
    """把 [a,b] 依字數預算切成若干段，切點吸附到事件起首"""
    idx = [k for k in range(len(segs)) if a <= segs[k][0] <= b]
    if not idx:
        return []
    total = sum(len(segs[k][1]) for k in idx)
    if len(idx) <= maxseg and total <= budget:
        return [(a, b)]
    want = max(2, math.ceil(total / budget), math.ceil(len(idx) / maxseg))
    cuts, cur, acc, target = [], a, 0, total / want
    for pos, k in enumerate(idx):
        acc += len(segs[k][1])
        if acc >= target * (len(cuts) + 1) and pos < len(idx) - 1:
            # 往後找最近的事件起首
            cand = None
            for k2 in idx[pos:min(pos + 6, len(idx))]:
                if RE_START.match(segs[k2][1]):
                    cand = segs[k2][0]
                    break
            cuts.append(cand if cand and cand > cur else segs[k][0])
            cur = cuts[-1]
    out, prev = [], a
    for c in cuts:
        if c > prev:
            out.append((prev, c - 1))
            prev = c
    out.append((prev, b))
    return [(x, y) for x, y in out if y >= x]


_CN = '一二三四五六七八九十'


def _units_qian(no):
    """揵度諸篇：先依「(○○揵度竟)」切，過長再依預算細分"""
    segs = SEG[no]
    marks = [(n, m.group(1)) for n, t in segs if (m := RE_NIAN.search(t))]
    blocks, prev = [], 0
    for n, nm in marks:
        blocks.append((prev + 1, n, nm))
        prev = n
    if prev < segs[-1][0]:
        blocks.append((prev + 1, segs[-1][0], ''))
    out = []
    for a, b, nm in blocks:
        nm = re.sub(r'(?:具足)?竟$', '', nm)
        parts = _split_budget(segs, a, b)
        for k, (x, y) in enumerate(parts):
            if nm and len(parts) > 1:
                name = '%s（%s）' % (nm, _CN[k] if k < len(_CN) else k + 1)
            elif nm:
                name = nm
            else:
                name = ''
            out.append({'a': x, 'b': y, 'cn': '', 'name': name})
    return out


UNITS_CACHE = {}


def units(no):
    """回傳 [{a,b,cn,name}, ...]，保證覆蓋全篇且無重疊"""
    if no in UNITS_CACHE:
        return UNITS_CACHE[no]
    segs = SEG[no]
    if not segs:
        r = []
    elif no == 0 or len(segs) == 1:
        r = [{'a': segs[0][0], 'b': segs[-1][0], 'cn': '', 'name': ''}]
    elif 31 <= no <= 37:
        r = _units_tail(no)
    elif no >= 38:
        r = _units_qian(no)
    else:
        r = _units_jing(no)
    UNITS_CACHE[no] = r
    return r


def seg_text(no, n):
    for k, t in SEG[no]:
        if k == n:
            return t
    return ''


def plain_text(no, a, b):
    """取 [a,b] 段的白話，按段序串接"""
    out = []
    for n in range(a, b + 1):
        s = PLAIN.get('%03d-%d' % (no, n))
        if s:
            out.append(s)
    return out


def unit_label(u):
    """節的顯示名（不含段範圍）"""
    if u.get('cn'):
        h = f'第{u["cn"]}戒'
        if u.get('name'):
            h += f'　{u["name"]}'
        return h
    if u.get('name'):
        return u['name']
    return ''
