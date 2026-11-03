# -*- coding: utf-8 -*-
"""Harvest cross-references already recorded in the drafts' 刪除項 tables.

Each draft's deletion table names where the deleted passage corresponds in the
other canons, written as `volNN段M`.  Those cells are collision evidence that
the matrix never read, because the extractor only walks 保留項.

For every C item (absent from 四分) this looks up whether another draft pointed
at it, and reports the pointing row.  A hit means: 四分所無，而某律有，且該律
自己已經記下對應 — i.e. the item is not an island.

Output: `_work/crossref.json`
"""
import os, re, json, glob
from collections import defaultdict

W = os.path.dirname(os.path.abspath(__file__))
DIRS = {'五分': 'findings', '十誦': 'findings_ss',
        '僧祇': 'findings_mk', '根有': 'findings_gu'}

REF = re.compile(r'vol(\d{1,2})\s*段\s*(\d{1,3})')

# --- index every volNN段M mention, with its file and line -------------------
idx = defaultdict(list)
for canon, d in DIRS.items():
    for f in sorted(glob.glob(os.path.join(W, d, 'vol*.md'))):
        unit = os.path.basename(f)[:-3]
        for ln in open(f, encoding='utf-8'):
            for m in REF.finditer(ln):
                idx[(int(m.group(1)), int(m.group(2)))].append(
                    (canon, unit, ln.strip()[:180]))

rows = json.load(open(os.path.join(W, 'matrix_rows.json'), encoding='utf-8'))
C = [r for r in rows if r['absent4']]


def own_refs(r):
    """Possible (vol, seg) of this item, from its 位置 field."""
    pos = r['pos'] or ''
    out = []
    if r['canon'] == '五分':
        for m in re.finditer(r'(\d{1,2})\s*[-–]\s*(\d{1,3})', pos):
            out.append((int(m.group(1)), int(m.group(2))))
    elif r['canon'] == '僧祇':
        for m in re.finditer(r'卷(\d{1,2})[·・.]\s*段(\d{1,3})', pos):
            out.append((int(m.group(1)), int(m.group(2))))
    else:
        vols = [int(x) for x in re.findall(r'\d{1,2}', r['unit'])]
        for m in re.finditer(r'段\s*(\d{1,3})', pos):
            for v in vols:
                out.append((v, int(m.group(1))))
    return out


hits = []
for r in C:
    found = []
    for key in own_refs(r):
        for canon, unit, line in idx.get(key, ()):
            if canon == r['canon']:
                continue
            found.append({'by': canon, 'unit': unit, 'ref': 'vol%02d段%d' % key,
                          'line': line})
    if found:
        hits.append({'canon': r['canon'], 'unit': r['unit'], 'no': r['no'],
                     'title': r['title'], 'pos': r['pos'], 'by': found})

json.dump(hits, open(os.path.join(W, 'crossref.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('C items', len(C), ' with cross-reference', len(hits))
print('by canon', {c: sum(1 for h in hits if h['canon'] == c) for c in DIRS})
print('citing canon', {c: sum(1 for h in hits for f in h['by'] if f['by'] == c) for c in DIRS})
