# -*- coding: utf-8 -*-
"""Verify the rendered 五分律 edition against its base text.

The 五分 draft uses two label conventions, so this checker handles both:

    A.  > **段37**　TEXT          (label and text on the same quoted line)
    B.    **段37**                (label alone, indented)
        > TEXT                    (text on the following quoted lines)

Labels seen in practice: 段N, 段N–M, 段N～M, N-M, 段N（節錄）, 段N（節引）,
段N後段, 段N（末）, 段N（首）, N-M（節引）.  Each resolves to a volume and a
paragraph; the paragraph is where the fragment must *start*.

Checks per fragment:
  1. contiguity - occurs verbatim as a contiguous run inside that volume;
  2. anchoring  - starts inside the labelled paragraph (or, for a range, in
                  one of its paragraphs).

Usage:  python qc_book_wufen.py
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
BOOK = os.path.join(ROOT, '五分律_去重白話', '五分律_去重白話_合冊.md')


def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


# ---- base text ------------------------------------------------------------
paras, starts = {}, {}
for v in range(1, 31):
    d, order = {}, []
    for ln in open(os.path.join(W, 'wufen', 'vol%02d.txt' % v), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' in ln:
            a, b = ln.split('\t', 1)
            if a.isdigit():
                d[int(a)] = b
                order.append(int(a))
    paras[v] = d
    full, off, pos = [], {}, 0
    for p in order:
        n = norm(d[p])
        off[p] = (pos, pos + len(n))
        full.append(n)
        pos += len(n)
    starts[v] = (''.join(full), off)


def label_range(lab, cur):
    """Resolve a label to (volume, first paragraph, last paragraph).

        段37            -> (cur, 37, 37)
        段37～40        -> (cur, 37, 40)
        2-185           -> (2, 185, 185)      volume-prefixed form
        2-185～2-203    -> (2, 185, 203)
    """
    s = lab.lstrip('段')
    nums = [int(x) for x in re.findall(r'\d+', s)]
    m = re.match(r'^(\d+)\s*[-–~～]\s*(\d+)', s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if lab.startswith('段'):
            return cur, a, b
        return a, b, (nums[3] if len(nums) >= 4 else b)
    return cur, nums[0], nums[0]


cur = None
blocks = []          # (volume, first paragraph, last paragraph, text)
pend = None          # pending standalone label
allow_cont = False   # only the line right after a label may extend a block
for ln in open(BOOK, encoding='utf-8'):
    s = ln.rstrip('\n')
    st = s.strip()
    h = re.match(r'^##\s*卷(\d+)', st)
    if h:
        cur = int(h.group(1))
        pend, allow_cont = None, False
        continue
    if not st:
        continue
    # A: label and text on one quoted line
    m = re.match(r'^>\s*\*\*([^*]{1,16})\*\*\s*(.*)$', st)
    if m:
        lab, txt = m.group(1), m.group(2)
        if not re.match(r'^(?:段)?\d', lab):
            allow_cont = False
            continue
        vh, lo, hi = label_range(lab, cur)
        blocks.append([vh, lo, hi, txt])
        pend, allow_cont = None, True
        continue
    # B: standalone indented label
    m = re.match(r'^\s{2,}\*\*([^*]{1,16})\*\*\s*$', s)
    if m and re.match(r'^(?:段)?\d', m.group(1)):
        pend, allow_cont = m.group(1), False
        continue
    # quoted text lines
    if st.startswith('>'):
        body = st.lstrip('>').strip()
        if body.startswith(('全卷', '範圍：', '比對範圍', '本卷', '字數以中文字計',
                            '底本：', '對校本：', '以《')):
            allow_cont = False
            continue
        if pend:
            vh, lo, hi = label_range(pend, cur)
            blocks.append([vh, lo, hi, body])
            pend, allow_cont = None, True
        elif allow_cont and blocks:
            blocks[-1][3] += body
        continue
    pend, allow_cont = None, False

tot = bad_contig = bad_anchor = 0
problems = []
for v, lo, hi, txt in blocks:
    txt = re.sub(r'（中略[^）]*）', '', txt)
    if not txt.strip():
        continue
    tot += 1
    if v is None:
        problems.append(('NO-VOL', lo, txt[:30]))
        bad_anchor += 1
        continue
    full, off = starts[v]
    for frag in re.split(r'…+|\.{3,}', txt):
        n = norm(frag)
        if len(n) < 4:
            continue
        i = full.find(n)
        if i < 0:
            bad_contig += 1
            problems.append(('CONTIG', v, lo, frag[:36]))
            break
        ok = any(off.get(p) and off[p][0] <= i < off[p][1] for p in range(lo, hi + 1))
        if not ok:
            if any(n in norm(paras[v].get(p, '')) for p in range(lo, hi + 1)):
                continue
            bad_anchor += 1
            problems.append(('ANCHOR', v, lo, frag[:36]))
            break

print('blocks', tot)
print('fragments not contiguous in volume:', bad_contig)
print('fragments not starting in the labelled paragraph:', bad_anchor)
for x in problems[:20]:
    print('  ', x)
sys.exit(1 if (bad_contig or bad_anchor) else 0)
