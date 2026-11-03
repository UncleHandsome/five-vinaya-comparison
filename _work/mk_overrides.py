# -*- coding: utf-8 -*-
"""Turn the harvested cross-references into matrix cell overrides.

A citation is accepted only when the citing draft names a 卷段 in the item's own
canon and gives a reason in the same row.  It fills the citing canon's cell with
「有」 and records the evidence, so the cell stops being 「未比」 without anyone
guessing.
"""
import os, json

W = os.path.dirname(os.path.abspath(__file__))
hits = json.load(open(os.path.join(W, 'crossref.json'), encoding='utf-8'))
built = json.load(open(os.path.join(W, 'matrix_built.json'), encoding='utf-8'))
cur = {(r['canon'], r['unit'], r['no']): r for r in built}

ov, log = {}, []
for h in hits:
    key = '%s|%s|%d' % (h['canon'], h['unit'], h['no'])
    r = cur.get((h['canon'], h['unit'], h['no']))
    for cit in h['by']:
        cellname = cit['by']
        field = {'僧祇': 'vMK', '根有': 'vGU', '五分': 'v5', '十誦': 'v10'}.get(cellname)
        if not field or not r:
            continue
        before = r[field]
        ov.setdefault(key, {})[field] = '有'
        log.append({'key': key, 'cell': field, 'before': before,
                    'ref': cit['ref'], 'by': cit['by'], 'unit': cit['unit'],
                    'topic': cit['topic'], 'reason': cit['reason']})

json.dump(ov, open(os.path.join(W, 'cell_overrides.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(log, open(os.path.join(W, 'cell_xref_log.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('rows overridden', len(ov), ' cells', len(log))
print('filled from 未比', sum(1 for x in log if x['before'] == '未比'))
