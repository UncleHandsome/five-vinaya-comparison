# -*- coding: utf-8 -*-
"""Column-aware harvest of the drafts' 刪除項 tables.

The deletion tables carry a column per canon (四分律／五分律／十誦律).  A cell
like `vol18段139` in the 五分律 column means: this deleted passage of the
present canon corresponds to 五分律 卷18 段139.  Read column-wise, the tables
are a ready-made collision record; read line-wise (as `crossref.py` did) they
are noise, because 保留項 comparison lines also mention `volNN段M`.

Output: `_work/crossref.json`
    [{'canon','unit','no','title','pos','by':[{'by','unit','ref','topic',
      'reason','line'}]}]
"""
import os, re, json, glob
from collections import defaultdict

W = os.path.dirname(os.path.abspath(__file__))
DIRS = {'五分': 'findings', '十誦': 'findings_ss',
        '僧祇': 'findings_mk', '根有': 'findings_gu'}
REF = re.compile(r'vol\s*(\d{1,2})\s*段\s*(\d{1,3})')
CANON_OF_COL = [('四分', '四分'), ('五分', '五分'), ('十誦', '十誦')]

idx = defaultdict(list)      # (canon, vol, seg) -> [citation]


def col_canon(name):
    for key, val in CANON_OF_COL:
        if key in name:
            return val
    return None


for canon, d in DIRS.items():
    for f in sorted(glob.glob(os.path.join(W, d, 'vol*.md'))):
        unit = os.path.basename(f)[:-3]
        lines = open(f, encoding='utf-8').read().split('\n')
        cols = None
        for ln in lines:
            s = ln.strip()
            if not s.startswith('|'):
                if cols and not s:
                    cols = None          # table ended
                continue
            cells = [c.strip() for c in s.strip('|').split('|')]
            if cols is None:
                # header row?
                if any('四分' in c for c in cells) and any('段' in c for c in cells):
                    cols = [col_canon(c) for c in cells]
                continue
            if all(set(c) <= set('-: ') for c in cells if c):
                continue                  # separator row
            topic = cells[1] if len(cells) > 1 else ''
            reason = cells[-1]
            for ci, c in enumerate(cells):
                if ci >= len(cols) or not cols[ci] or cols[ci] == '四分':
                    continue
                for m in REF.finditer(c):
                    idx[(cols[ci], int(m.group(1)), int(m.group(2)))].append(
                        {'by': canon, 'unit': unit, 'ref': 'vol%02d段%02d' % (
                            int(m.group(1)), int(m.group(2))),
                         'topic': topic[:60], 'reason': reason[:40],
                         'seg': cells[0][:20]})

rows = json.load(open(os.path.join(W, 'matrix_rows.json'), encoding='utf-8'))
C = [r for r in rows if r['absent4']]


def own_refs(r):
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
    found, seen = [], set()
    for v, s in own_refs(r):
        for cit in idx.get((r['canon'], v, s), ()):
            if cit['by'] == r['canon']:
                continue
            k = (cit['by'], cit['unit'], cit['seg'])
            if k in seen:
                continue
            seen.add(k)
            found.append(cit)
    if found:
        hits.append({'canon': r['canon'], 'unit': r['unit'], 'no': r['no'],
                     'title': r['title'], 'pos': r['pos'], 'by': found})

json.dump(hits, open(os.path.join(W, 'crossref.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('C items', len(C), 'with table cross-reference', len(hits))
print('by canon', {c: sum(1 for h in hits if h['canon'] == c) for c in DIRS})
print('citations', sum(len(h['by']) for h in hits))
print('reasons', __import__('collections').Counter(
    f['reason'] for h in hits for f in h['by']).most_common(12))
