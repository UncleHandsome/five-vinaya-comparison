# -*- coding: utf-8 -*-
"""把《根本說一切有部毘奈耶_去重白話》之分冊改成「名實相符」：
檔名與檔內自述之卷區間，一律依該冊實際所收之卷（由 ## 卷N 標題量得）。
usage: python fix_books.py [--dry]"""
import io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, '根本說一切有部毘奈耶_去重白話')
NM = '根本說一切有部毘奈耶'
DRY = '--dry' in __import__('sys').argv


def cnv(n):
    d = '零一二三四五六七八九'
    if n < 10:
        return d[n]
    if n == 10:
        return '十'
    if n < 20:
        return '十' + d[n % 10]
    return d[n // 10] + '十' + (d[n % 10] if n % 10 else '')


def vols_of(md):
    hs = [h for h in re.findall(r'^## .*$', md, re.M) if not h.startswith('## 本冊統計')]
    return sorted({int(x) for h in hs for x in re.findall(r'卷\s*(\d{1,2})', h)})


rows, rd = [], []
for fn in sorted(os.listdir(D)):
    if not fn.startswith(NM + '_去重白話_卷') or not fn.endswith('.md'):
        continue
    p = os.path.join(D, fn)
    md = io.open(p, encoding='utf-8').read()
    vs = vols_of(md)
    if not vs:
        print('無卷次標題，跳過', fn)
        continue
    name = '卷%s至卷%s' % (cnv(vs[0]), cnv(vs[-1]))
    old = fn.split('_去重白話_')[-1][:-3]
    md2 = re.sub(r'^# %s去重白話　.*$' % NM, '# {}去重白話　{}'.format(NM, name), md, count=1, flags=re.M)
    md2 = re.sub(r'^> 本冊為《[^》]*》之分冊，收卷.*?。',
                 '> 本冊為《{}去重白話》之分冊，收卷{}至卷{}（以單位為界，相鄰二卷之單位不拆）。'.format(
                     NM, cnv(vs[0]), cnv(vs[-1])), md2, count=1, flags=re.M)
    new = '{}_去重白話_{}.md'.format(NM, name)
    if md2 != md or new != fn:
        if not DRY:
            io.open(os.path.join(D, new), 'w', encoding='utf-8').write(md2)
            if new != fn:
                os.remove(p)
    rows.append((new, os.path.getsize(os.path.join(D, new)) if not DRY else 0, vs[0], vs[-1]))
    rd.append('%s：%d～%d（原%s）' % (new, vs[0], vs[-1], old))
print('\n'.join(rd))

rp = os.path.join(D, 'README.md')
s = io.open(rp, encoding='utf-8').read()
rows_s = sorted(rows, key=lambda r: r[2])
new_lines, done = [], False
for l in s.split('\n'):
    if re.match(r'^\| %s_去重白話_卷[^|]*\.md \| 分冊' % NM, l.strip()):
        if not done:
            for nm, sz, a, b in rows_s:
                new_lines.append('| %s.md | 分冊（依卷次，名實相符） | %d KB |' % (nm[:-3], round(sz / 1024)))
            done = True
        continue
    new_lines.append(l)
new_tab = '\n'.join(new_lines)
print('README 檔目重建：%d 列分冊%s' % (len(rows_s), '（未變）' if new_tab == s else ''))
if new_tab != s and not DRY:
    io.open(rp, 'w', encoding='utf-8').write(new_tab)
