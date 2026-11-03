# -*- coding: utf-8 -*-
"""把《獨有敘事》另檔之條目序號改為全書統一（1～N），並將正文中
「見「敘事抽取」X」之單元局部序號改為全局序號，使跨檔指針唯一可查。
usage: python globalize_narr.py <書目錄> [--dry]"""
import io, os, re, sys, hashlib

D = sys.argv[1]
DRY = '--dry' in sys.argv
NA = [f for f in os.listdir(D) if f.endswith('_獨有敘事.md')][0]
nm = re.search(r'^(.*)_去重白話_獨有敘事\.md$', NA).group(1)
na = io.open(os.path.join(D, NA), encoding='utf-8').read()

# 卷次 → 局部序（依另檔現行『### N.』與『- 所屬：卷X』）
items = []
pos = [(m.start(), int(m.group(1)), m.group(2)) for m in re.finditer(r'^### (\d+)\. (.*)$', na, re.M)]
for i, (p, num, title) in enumerate(pos):
    end = pos[i + 1][0] if i + 1 < len(pos) else len(na)
    body = na[p:end]
    m = re.search(r'^-\s*所屬[：:]\s*卷\s*(\d{1,2})', body, re.M)
    items.append({'num': num, 'title': title, 'vol': int(m.group(1)) if m else None,
                  'span': (p, end)})
# 以序號重置處為單元分界（同單元內序號連貫）
units, cur = [], None
for gi, it in enumerate(items, 1):
    it['global'] = gi
    if cur is None or it['num'] != (cur[-1]['num'] + 1):
        cur = []
        units.append(cur)
    cur.append(it)
LOC = {}
for u in units:
    for it in u:
        LOC[(it['vol'], it['num'])] = it['global']
print('另檔 %s｜條目 %d｜單元 %d 組' % (NA, len(items), len(units)))

# 1) 另檔：### 改全局序；目錄加全局序
out = na
new_items = []
for it in items:
    seg = na[it['span'][0]:it['span'][1]]
    seg = re.sub(r'^### \d+\. ', '### %d. ' % it['global'], seg, count=1, flags=re.M)
    new_items.append(seg)
head = na[:items[0]['span'][0]]
toc_lines, gi = [], 1
INTOC = False
for line in head.split('\n'):
    if line.strip().startswith('## 目錄'):
        INTOC = True
        toc_lines.append(line)
        continue
    if INTOC and gi <= len(items) and line.strip().startswith('- '):
        t = line.strip()[2:].strip()
        want = items[gi - 1]['title'].strip()
        if t == want or t.startswith(want[:18]) or want.startswith(t[:18]):
            toc_lines.append('- %d. %s' % (gi, t if re.match(r'^\d+\.', t) else t))
            gi += 1
            continue
    toc_lines.append(line)
tail = '\n'.join(new_items)
new_na = '\n'.join(toc_lines) + tail
print('   目錄編號 %d 條（應等於條目數）' % (gi - 1))

# 2) 正文指針：局部序 → 全局序（以同段『位置：卷X·段Y』定卷）
fixed, unresolved, total = [], [], 0
for f in sorted(os.listdir(D)):
    if not f.endswith('.md') or f == NA:
        continue
    p = os.path.join(D, f)
    md = io.open(p, encoding='utf-8').read()
    lines = md.split('\n')
    vol = None
    n = 0
    for i, l in enumerate(lines):
        m = re.match(r'^## (?:卷)?(\d{1,2})', l.strip())
        if m:
            vol = int(m.group(1))
        m2 = re.search(r'見「敘事抽取」\s*(\d{1,3})', l)
        if m2:
            total += 1
            mv = re.search(r'卷(\d{1,2})', l)
            v = int(mv.group(1)) if mv else vol
            g = LOC.get((v, int(m2.group(1))))
            if g is None:
                unresolved.append((f, i + 1, v, m2.group(1)))
                continue
            lines[i] = l.replace('見「敘事抽取」%s' % m2.group(1),
                                 '見《獨有敘事》第%d條' % g)
            n += 1
    if n and not DRY:
        io.open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    if n:
        fixed.append('%s×%d' % (f.replace(nm + '_去重白話_', ''), n))
print('   指針共 %d 處，改定 %s；未能映射 %s' % (total, ', '.join(fixed) or '0',
                                                unresolved or '無'))
if not DRY:
    io.open(os.path.join(D, NA), 'w', encoding='utf-8').write(new_na)
    print('   已寫另檔 sha %s（%d B）' % (
        hashlib.sha1(new_na.encode('utf-8')).hexdigest()[:10], len(new_na.encode('utf-8'))))
else:
    print('   DRY：未寫')
