# -*- coding: utf-8 -*-
import json, re
rows = json.load(open('matrix_rows.json', encoding='utf-8'))
pat = re.compile(r'(\d{3}_[^`\s]*?\.txt)[^0-9]{0,14}(?:第)?(\d+)(?:[～~\-–](\d+))?段')

def anch(r):
    m = pat.search(r['ref4'] or '')
    return (m.group(1), int(m.group(2))) if m else None

print('with anchor', sum(1 for r in rows if anch(r)), 'of', len(rows))
c = json.load(open('wufen_C_items.json', encoding='utf-8'))
cs = {(x['vol'], x['no']) for x in c}
for r in rows:
    if r['canon'] == '五分' and r['absent4']:
        v = int(r['unit'][3:5])
        if (v, r['no']) not in cs:
            print('EXTRA', r['unit'], r['no'], r['title'][:40], '|', r['ref4'][:70])
