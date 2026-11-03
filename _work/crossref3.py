# -*- coding: utf-8 -*-
"""Audit the 五分稿's 十誦 verdicts against 十誦's own deletion table.

The 十誦 draft lists, for every passage it deleted, which 四分 and 五分 paragraph
it duplicates, written as `五分1-28～1-41`.  So if 十誦's table names 五分 18-139,
十誦 did have that content — even when the 五分 draft recorded 「十誦遍查未見」.

This turns 935 recorded correspondences into a check on the 85 「遍查未見」
claims that the 十誦 column of the 五分 draft rests on.

Output: `_work/audit_ss.json`
"""
import os, re, json, glob
from collections import defaultdict

W = os.path.dirname(os.path.abspath(__file__))
REF = re.compile(r'五分\s*(\d{1,2})\s*[-–]\s*(\d{1,3})(?:\s*[～~]\s*(?:五分)?\s*(\d{1,2})\s*[-–]\s*(\d{1,3}))?')

idx = defaultdict(list)
for f in sorted(glob.glob(os.path.join(W, 'findings_ss', 'vol*.md'))):
    unit = os.path.basename(f)[:-3]
    for ln in open(f, encoding='utf-8'):
        s = ln.strip()
        if not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if len(cells) < 4:
            continue
        for m in REF.finditer(s):
            v, a = int(m.group(1)), int(m.group(2))
            b = int(m.group(4)) if m.group(4) and int(m.group(3)) == v else a
            for seg in range(a, b + 1):
                idx[(v, seg)].append({'unit': unit, 'seg': cells[0],
                                      'topic': cells[1][:40], 'reason': cells[-1][:30]})

rows = json.load(open(os.path.join(W, 'matrix_rows.json'), encoding='utf-8'))
five = [r for r in rows if r['canon'] == '五分']

def span(pos):
    m = re.match(r'\s*(\d{1,2})-(\d{1,3})(?:\s*[～~]\s*(?:\d{1,2}-)?(\d{1,3}))?', pos or '')
    if not m:
        return None
    a = int(m.group(1)); lo = int(m.group(2))
    hi = int(m.group(3)) if m.group(3) else lo
    return a, lo, hi

hits = []
for r in five:
    sp = span(r['pos'])
    if not sp:
        continue
    v, lo, hi = sp
    found = {}
    for seg in range(lo, hi + 1):
        for c in idx.get((v, seg), ()):
            found[(c['unit'], c['seg'])] = c
    if not found:
        continue
    verdict = '十誦遍查未見' if '遍查未見' in (r['ref10'] or '') else '十誦對照已記'
    hits.append({'unit': r['unit'], 'no': r['no'], 'title': r['title'],
                 'pos': r['pos'], 'ref10': (r['ref10'] or '')[:70],
                 'verdict': verdict,
                 'by': [{'unit': k[0], 'seg': k[1], 'topic': c['topic'],
                         'reason': c['reason']} for k, c in list(found.items())[:3]]})

json.dump(hits, open(os.path.join(W, 'audit_ss.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
from collections import Counter
print('五分項被十誦刪除表引用：', len(hits))
print(Counter(h['verdict'] for h in hits))
print('其中原記「遍查未見」而實有引用者：',
      sum(1 for h in hits if h['verdict'] == '十誦遍查未見'))
