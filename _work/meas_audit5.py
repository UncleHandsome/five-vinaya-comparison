# -*- coding: utf-8 -*-
"""量《五分律去重白話》合冊與分冊：
  1 裸 '>' 續行、獨標段號之引用行（排版之病之範圍）
  2 附錄一口徑：「遍查未見」配「小事／細節／從略／待考」之數與所在卷
  3 白話是否照錄名相（等學／不餘學／惡說／澤枯羹）
  4 跪姿異體之譯法是否一致
  5 統計宣稱之勾稽（379／382／39,967／341,320／11.7％／各卷區間）
"""
import io, os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, '五分律_去重白話')
ED = os.path.join(D, '五分律_去重白話_合冊.md')
s = io.open(ED, encoding='utf-8').read()
lines = s.split('\n')

# 1 ---------------------------------------------------------------- 排版
bare = [i + 1 for i, l in enumerate(lines) if l.strip() == '>']
solo = [i + 1 for i, l in enumerate(lines)
        if re.match(r'^> \*\*段[^*]*\*\*[：:]?$', l.strip())]
print('1｜裸 > 行：%d 處 %s' % (len(bare), bare[:14]))
print('   獨標段號之行：%d 處 %s' % (len(solo), solo[:14]))

# 分冊是否同病
for fn in sorted(os.listdir(D)):
    if fn.endswith('.md') and fn != os.path.basename(ED):
        t = io.open(os.path.join(D, fn), encoding='utf-8').read().split('\n')
        b = [i + 1 for i, l in enumerate(t) if l.strip() == '>']
        o = [i + 1 for i, l in enumerate(t)
             if re.match(r'^> \*\*段[^*]*\*\*[：:]?$', l.strip())]
        print('   %-30s 裸> %d／獨標 %d' % (fn.replace('五分律_去重白話_', ''), len(b), len(o)))


def vol_at(idx):
    v = ''
    for i in range(idx, 0, -1):
        m = re.match(r'^## (卷\d+)', lines[i - 1])
        if m:
            v = m.group(1)
            break
    return v


# 2 ---------------------------------------------------------------- 附錄一口徑
rows = []
for i, l in enumerate(lines, 1):
    if not l.strip().startswith('|'):
        continue
    c = [x.strip() for x in l.strip().strip('|').split('|')]
    if len(c) < 4 or set(c[0]) <= set('-: ') or c[0].startswith('段'):
        continue
    rows.append((i, c))
soft = ['小事', '細節', '從略', '待考', '瑣']
pairs = [(i, vol_at(i), c) for i, c in rows
         if '遍查未見' in ''.join(c) and any(k in c[-1] for k in soft)]
print('\n2｜附錄一列數 %d；「遍查未見」而理由含『小事／細節／從略／待考／瑣』者 %d 列'
      % (len(rows), len(pairs)))
for i, v, c in pairs[:14]:
    print('   L%-5d %s｜%s｜%s｜%s' % (i, v, c[0], c[1][:26], c[-1][:26]))

# 3 ---------------------------------------------------------------- 名相照錄
def baihua_of(needle):
    out = []
    for i, l in enumerate(lines):
        if needle in l:
            j = i
            while j < len(lines) and not lines[j].strip().startswith('- 白話'):
                j += 1
            bh = []
            k = j + 1
            while k < len(lines) and (lines[k].startswith('  ') or not lines[k].strip()):
                if lines[k].strip():
                    bh.append(lines[k].strip())
                k += 1
            out.append((i + 1, ' '.join(bh)[:120]))
    return out


print('\n3｜白話是否照錄名相')
for nd in ['共一學、等學、不等學、不餘學', '突吉羅、惡說不', '澤枯羹']:
    print('   「%s」' % nd[:16])
    for ln, bh in baihua_of(nd)[:3]:
        print('      L%-5d 白話：%s' % (ln, bh))

# 4 ---------------------------------------------------------------- 跪
print('\n4｜跪姿異體之譯法')
for g in ['[跍*月]跪', '䠒跪', '胡跪']:
    hit = [(i + 1, vol_at(i + 1)) for i, l in enumerate(lines) if g in l]
    print('   %-10s %d 處：%s' % (g, len(hit), hit[:10]))
for g in ['[跍*月]跪', '䠒跪']:
    for ln, bh in baihua_of(g)[:8]:
        kw = [k for k in ('胡跪', '長跪', '屈膝', '横膝', '跪') if k in bh]
        print('      L%-5d 譯：%s｜%s' % (ln, kw, bh[:56]))

# 5 ---------------------------------------------------------------- 統計
print('\n5｜統計勾稽')
m = re.search(r'保留項[：:]\s*([\d,]+)\s*項（正文\s*([\d,]+)\s*項', s)
print('   附錄四自述：', m.group(0)[:60] if m else '未找到')
n_items = len(re.findall(r'^### \d+\. ', s, re.M))
n_h2 = len(re.findall(r'^## 卷\d+', s, re.M))
print('   合冊 ### 計 %d（含附錄內之小題）；## 卷 %d 節' % (n_items, n_h2))
per = re.findall(r'^> 全卷 ([\d,]+) 字，本稿保留 ([\d,]+) 字（([\d.]+)%），保留 (\d+) 項', s, re.M)
body = [p for p in per if True]
print('   卷首自述 %d 節；字數合计 %s／保留合计 %s；項数合计 %d' % (
    len(body), format(sum(int(x[0].replace(',', '')) for x in body), ','),
    format(sum(int(x[1].replace(',', '')) for x in body), ','),
    sum(int(x[3]) for x in body)))
if body:
    rr = [(float(x[2]), i) for i, x in enumerate(body)]
    print('   最低 %.1f%%／最高 %.1f%%' % (min(rr)[0], max(rr)[0]))
