# -*- coding: utf-8 -*-
"""產物級覆核尺（第二把，補舊尺之盲）：
  甲、按『卷』硬判段號覆蓋：底本全段 = 正文位置 ∪ 另檔位置 ∪ 附錄一刪略表 ∪ 正文中略標記者；
      缺者列名。舊尺只對單卷單位跑覆蓋（雙卷僅示意），故雙卷之漏素曾 unchecked。
  乙、逐字：每條「> **卷N·段M**　」行須為底本該段之連續子串（行內『……』跳引者逐節核，且須同序）。
  丙、回捲：同一項內段號不得遞退。
  自印管轄：各卷底本段數與四源之命中數俱印；零命中即紅。
usage: python qc_cov.py <書目錄> <底本子目錄> <卷數>
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, '根本說一切有部毘奈耶_去重白話')
BD = os.path.join(ROOT, '_work', sys.argv[2] if len(sys.argv) > 2 else 'genben')
NVOL = int(sys.argv[3]) if len(sys.argv) > 3 else 50


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def rng(s):
    # 位置欄常見「段39（『乃往古昔』以下）～46」之插語，先剝括注使範圍相連
    s = re.sub(r'[（(][^）)]{0,40}[）)]', '', s or '')
    out = set()
    for a, b in re.findall(r'(\d{1,3})\s*[～~－–\-—]\s*(\d{1,3})', s):
        if int(a) <= int(b) < 900:
            out.update(range(int(a), int(b) + 1))
    for x in re.findall(r'(?<![\d～~－–\-—])(\d{1,3})(?![\d～~－–\-—])', s):
        if 0 < int(x) < 900:
            out.add(int(x))
    return out


PARA = {}
for fn in os.listdir(BD):
    if fn.startswith('vol') and fn.endswith('.txt'):
        d = {}
        for ln in io.open(os.path.join(BD, fn), encoding='utf-8'):
            a, sep, b = ln.rstrip('\n').partition('\t')
            if sep and a.strip().isdigit():
                d[int(a)] = b.strip()
        PARA[int(fn[3:5])] = d

books = {}
for f in sorted(os.listdir(D)):
    if f.endswith('.md') and f != 'README.md':
        books[f] = io.open(os.path.join(D, f), encoding='utf-8').read()
合名 = [k for k in books if '合冊' in k][0]
合 = books[合名]
另名 = [k for k in books if '獨有敘事' in k]
另 = books[另名[0]] if 另名 else ''
a1 = 合[合.find('# 附錄一'):合.find('# 附錄二')] if '# 附錄一' in 合 else ''
body = 合[:合.find('# 附錄一')] if '# 附錄一' in 合 else 合

# 以「單位」為域：位置欄未帶卷號者屬疑標，計入該單位各卷（並另計其數）
UNITS = []
ms = [m for m in re.finditer(r'^## (卷[0-9、卷\s]+)　[^\n]*$', body, re.M)]
for i, m in enumerate(ms):
    vs = [int(x) for x in re.findall(r'\d{1,2}', m.group(1))]
    end = ms[i + 1].start() if i + 1 < len(ms) else len(body)
    UNITS.append((vs, m.end(), end))
amb = {v: set() for v in PARA}
kept = {v: set() for v in PARA}
gapmk = {v: set() for v in PARA}
for vs, a, b in UNITS:
    seg = body[a:b]
    def put(dst, nums, explicit_vol):
        for n in nums:
            if explicit_vol and explicit_vol in PARA:
                if n <= len(PARA[explicit_vol]):
                    dst[explicit_vol].add(n)
                continue
            for v in vs:
                if n <= len(PARA[v]):
                    dst[v].add(n)
                    amb[v].add(n)
    for pm in re.finditer(r'^- 位置[：:](.*|[\s\S]*?)(?=\n-\s|\n###|\Z)', seg, re.M):
        t = pm.group(1)
        mv = re.search(r'卷(\d{1,2})', t)
        put(kept, rng(t), int(mv.group(1)) if mv else None)
    for gm in re.finditer(r'（中略：段(\d{1,3})(?:[～~\-–](\d{1,3}))?', seg):
        x, y = int(gm.group(1)), int(gm.group(2)) if gm.group(2) else int(gm.group(1))
        pre = seg[max(0, gm.start() - 260):gm.start()]
        mv = re.findall(r'卷(\d{1,2})', pre)
        put(gapmk, set(range(x, y + 1)), int(mv[-1]) if len(set(mv)) == 1 else None)
# 另檔
for m in re.finditer(r'^-\s*所屬[：:]\s*卷\s*(\d{1,2})[^\n]*\n-\s*位置[：:](.*)$', 另, re.M):
    v = int(m.group(1))
    if v in PARA:
        kept[v].update(x for x in rng(m.group(2)) if x <= len(PARA[v]))
# 附錄一：依其單位標題跟走
delrows = {v: set() for v in PARA}
cur = []
lines = a1.split('\n')
pos = 合.find('# 附錄一')
for l in lines:
    hm = re.match(r'^## (卷[0-9、卷\s]+)　', l)
    if hm:
        cur = [int(x) for x in re.findall(r'\d{1,2}', hm.group(1))]
        continue
    if not l.strip().startswith('|'):
        continue
    c = l.strip().strip('|').split('|')
    first, rest = c[0].strip(), '|'.join(c[1:])
    mv = re.match(r'^卷(\d{1,2})', first)
    nums = rng(re.sub(r'^卷\d{1,2}[·]?\s*段?', '', first))
    if mv:
        v = int(mv.group(1))
        if v in PARA:
            delrows[v].update(x for x in nums if x <= len(PARA[v]))
    elif cur:
        for v in cur:
            sel = set(x for x in nums if x <= len(PARA[v]))
            delrows[v] |= sel
            amb[v] |= sel
miss_tot = amb_tot = 0
print('甲｜按卷覆蓋（底本｜明標保留｜疑標｜敘事｜刪表｜中略｜缺）')
for v in sorted(PARA):
    mx = len(PARA[v])
    if not mx:
        continue
    cov = kept[v] | delrows[v] | gapmk[v]
    miss = sorted(set(range(1, mx + 1)) - cov)
    miss_tot += len(miss)
    amb_tot += len(amb[v] & cov)
    if miss:
        print('  卷%-3d %-5d %-5d %-5d %-5d %-5d %-5d 缺 %d：%s' % (
            v, mx, len(kept[v] - amb[v]), len(amb[v]), len(delrows[v]), len(gapmk[v]),
            len(amb[v] & cov), len(miss), miss[:16]))
print('  全書無歸屬段合計：%d｜其中屬『疑標（位置欄未帶卷號）』而覆蓋者：%d' % (miss_tot, amb_tot))

# 乙、逐字
Q = re.compile(r'^> \*\*(?:卷(\d{1,2})·)?段(\d{1,3})\*\*　(.*)$', re.M)
badq = 0
samples = []
for f, md in books.items():
    heads = [(m.start(), [int(x) for x in re.findall(r'卷\s*(\d{1,2})', m.group(1))])
             for m in re.finditer(r'^## (卷[^\n]*)$', md, re.M)]
    for m in re.finditer(r'^### .*$', md, re.M):
        hv = [v for p, v in heads if p < m.start()]
        uv = hv[-1] if hv else []
        item = md[m.start():m.start() + (md.find('\n### ', m.end()) - m.start() if md.find('\n### ', m.end()) > 0 else 10 ** 7)]
        for q in Q.finditer(item):
            v = int(q.group(1)) if q.group(1) else (uv[0] if len(uv) == 1 else None)
            p, txt = int(q.group(2)), q.group(3)
            if not v or v not in PARA or p not in PARA[v]:
                badq += 1
                samples.append((f, v, p, '查無此段', txt[:34]))
                continue
            n = norm(PARA[v][p])
            pieces = [norm(x) for x in re.split(r'…{2,}|。{3,}', txt) if norm(x)] or [norm(txt)]
            at, ok = 0, True
            for pc in pieces:
                j = n.find(pc, at)
                if j < 0:
                    ok = False
                    break
                at = j + len(pc)
            if not ok:
                badq += 1
                if len(samples) < 12:
                    samples.append((f, v, p, '非底本連續文', txt[:44]))
print('\n乙｜逐字不合：%d 行' % badq)
for s in samples[:10]:
    print('  %s 卷%s段%s｜%s｜%s' % (str(s[0]).replace('根本說一切有部毘奈耶_去重白話_', ''), s[1], s[2], s[3], s[4]))

# 丙、同段引文之真病：文同重貼／片段次序倒退（標籤重複本身非病）
LAB = re.compile(r'^> \*\*(?:卷(\d{1,2})·)?段(\d{1,3})\*\*　(.*)$', re.M)
dup = outof = amb = 0
dupsamp, outsamp = [], []
for f, md in books.items():
    heads = [(m.start(), [int(x) for x in re.findall(r'卷\s*(\d{1,2})', m.group(1))])
             for m in re.finditer(r'^## (卷[^' + chr(10) + r']*)$', md, re.M)]
    stop = md.find(chr(10) + '# 附錄一')
    ip = [m.start() for m in re.finditer(r'^### ', md, re.M) if m.start() < (stop if stop > 0 else len(md))]
    ip.append(stop if stop > 0 else len(md))
    for i in range(len(ip) - 1):
        seg = md[ip[i]:ip[i + 1]]
        hv = [v for pnt, v in heads if pnt < ip[i]]
        uv = hv[-1] if hv else []
        rows = []
        for q in LAB.finditer(seg):
            v = int(q.group(1)) if q.group(1) else (uv[0] if len(uv) == 1 else None)
            if q.group(1) is None and len(uv) != 1:
                amb += 1
            if not v:
                continue
            n = norm(q.group(3))
            src = norm(PARA[v].get(int(q.group(2)), ''))
            rows.append((v, int(q.group(2)), n, src.find(n[:24]) if n else -1))
        grp = {}
        for v, pp, n, idx in rows:
            grp.setdefault((v, pp), []).append((n, idx))
        for k, lst in grp.items():
            if len(lst) < 2:
                continue
            if len(set(x[0] for x in lst)) == 1:
                dup += 1
                if len(dupsamp) < 5:
                    dupsamp.append((f.replace('根本說一切有部毘奈耶_去重白話_', ''),
                                    seg.split(chr(10))[0][:32], k))
            pos = [x[1] for x in lst if x[1] >= 0]
            if any(b < a for a, b in zip(pos, pos[1:])):
                outof += 1
                if len(outsamp) < 6:
                    outsamp.append('倒退 %s｜%s｜卷%s段%s｜位%s｜%s' % (
                        f.replace('根本說一切有部毘奈耶_去重白話_', ''),
                        seg.split(chr(10))[0][:28], k[0], k[1], pos[:4],
                        '／'.join(x[0][:14] for x in lst[:3])))
print('丙｜同段而文句全同之重貼：%d 組｜同段而片段次序倒退：%d 組｜卷次待推之標籤行：%d' % (dup, outof, amb))
for x in dupsamp[:5]:
    print('   重貼 %s｜%s｜卷%s段%s' % (x[0], x[1], x[2][0], x[2][1]))
for x in outsamp[:6]:
    print('   倒退 %s｜%s｜卷%s段%s｜位%s｜%s' % x)
sys.exit(1 if miss_tot or badq or dup or outof else 0)
