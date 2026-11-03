# -*- coding: utf-8 -*-
"""Extract every retained item from the four deduplication drafts into one table.

The four drafts were built at different times and do not carry the same fields:

    findings/      五分律   - 四分律對照 (+ 十誦 only in prose)
    findings_ss/   十誦律   - 四分律對照, 五分律對照
    findings_mk/   摩訶僧祇 - 四分/五分/十誦
    findings_gu/   根本說有部 - 四分/五分/十誦

So the matrix records, per item, which comparison fields exist and what each
says; it never invents a cell that the draft does not support.
"""
import os, re, json, glob

W = os.path.dirname(os.path.abspath(__file__))
CANONS = [('五分', 'findings', '五分律'), ('十誦', 'findings_ss', '十誦律'),
          ('僧祇', 'findings_mk', '摩訶僧祇律'), ('根有', 'findings_gu', '根本說一切有部毘奈耶')]

FIELDS = ('位置', '所屬', '四分律對照', '五分律對照', '十誦律對照', '三律對照',
          '差異說明', '要旨', '全文收錄')
ABSENT = ('遍查未見', '全無', '無此', '未見', '不見', '無對應', '俱無', '皆無')


def items_of(text):
    """Yield (title, {field: value}) for every ### item under 保留項."""
    m = re.search(r'^## 保留項\s*$', text, re.M)
    if not m:
        return
    rest = text[m.end():]
    nxt = re.search(r'^## ', rest, re.M)
    if nxt:
        rest = rest[:nxt.start()]
    for chunk in re.split(r'^### ', rest, flags=re.M)[1:]:
        ls = chunk.split('\n')
        title = re.sub(r'^[\s\d]+[.、]\s*', '', ls[0].strip())
        if not title:
            continue
        f, cur = {}, None
        for ln in ls[1:]:
            mm = re.match(r'^-\s*([^：:]{1,12})[：:]\s*(.*)$', ln.strip())
            if mm and mm.group(1) in FIELDS:
                cur = mm.group(1)
                f[cur] = mm.group(2).strip()
            elif cur and ln.strip() and not ln.strip().startswith(('#', '>')):
                f[cur] = (f[cur] + ln.strip()).strip()
            elif ln.strip().startswith('- ') or ln.strip().startswith('#'):
                cur = None
        yield title, f


rows = []
for tag, d, name in CANONS:
    for path in sorted(glob.glob(os.path.join(W, d, '*.md'))):
        unit = os.path.basename(path)[:-3]
        # W02a/W02b are superseded drafts of vol02, already folded into vol02.md
        if unit.startswith('W'):
            continue
        text = open(path, encoding='utf-8').read()
        for i, (title, f) in enumerate(items_of(text), 1):
            ref4 = f.get('四分律對照', '') or f.get('三律對照', '')
            ref5 = f.get('五分律對照', '')
            ref10 = f.get('十誦律對照', '')
            # label C: the item is said to be absent from 四分
            absent4 = any(k in ref4 for k in ABSENT) if ref4 else False
            rows.append({
                'canon': tag, 'unit': unit, 'no': i, 'title': title,
                'pos': f.get('位置', ''),
                'ref4': ref4, 'ref5': ref5, 'ref10': ref10,
                'diff': f.get('差異說明', ''),
                'has5': bool(ref5), 'has10': bool(ref10),
                'absent4': absent4,
            })

json.dump(rows, open(os.path.join(W, 'matrix_rows.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

from collections import Counter
c = Counter((r['canon'], r['absent4']) for r in rows)
tot = Counter(r['canon'] for r in rows)
print('items per canon:', dict(tot), 'total', len(rows))
for tag, _d, _n in CANONS:
    a = c[(tag, True)]
    print('  {}: {} items, {} marked 四分所無 ({:.0f}%)'.format(
        tag, tot[tag], a, 100.0 * a / tot[tag] if tot[tag] else 0))
print('field coverage:')
for tag, _d, _n in CANONS:
    sub = [r for r in rows if r['canon'] == tag]
    print('  {}: 五分欄 {}/{}  十誦欄 {}/{}'.format(
        tag, sum(r['has5'] for r in sub), len(sub),
        sum(r['has10'] for r in sub), len(sub)))
