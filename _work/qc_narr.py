# -*- coding: utf-8 -*-
"""核驗《根本說一切有部毘奈耶_去重白話_獨有敘事.md》（只讀產物與底本，不改檔）

甲、標「逐字抽出」之區塊：引文行須與底本該段逐字相同。
    區塊自註「自『X』起」只容許首段左截、「至『X』止」只容許末段右截，
    且截斷之界須與自註點名之文句一字不差。
乙、舊有節引（未標抽出）：引文行須為底本該段之連續子串。
丙、覆蓋：條目數、有無引文、中略指針是否越界。
"""
import os, re, io, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
F = os.environ.get('NARR_F') or os.path.join(
    ROOT, '根本說一切有部毘奈耶_去重白話',
    '根本說一切有部毘奈耶_去重白話_獨有敘事.md')
BASE = os.environ.get('NARR_BASE') or os.path.join(W, 'genben')


def rd(p):
    return io.open(p, encoding='utf-8').read()


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


CN = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
      '六': 6, '七': 7, '八': 8, '九': 9}
UN = {'十': 10, '百': 100, '千': 1000}


def cn2num(s):
    s = re.sub(r'[^\u4e00-\u9fff0-9]', '', s or '')
    if s.isdigit():
        return int(s)
    tot, num = 0, 0
    for c in s:
        if c in CN:
            num = CN[c]
        elif c in UN:
            tot += (num or 1) * UN[c]
            num = 0
    return tot + num


PS = {}
for fn in sorted(os.listdir(BASE)):
    if not (fn.startswith('vol') and fn.endswith('.txt')):
        continue
    d = {}
    for ln in rd(os.path.join(BASE, fn)).split('\n'):
        k, sep, t = ln.partition('\t')
        m = re.match(r'^段?\s*(\d+)$', k.strip()) if sep else None
        if m and t.strip():
            d[int(m.group(1))] = t.strip()
    PS[int(fn[3:5])] = d

md = rd(F)
ip = [m.start() for m in re.finditer(r'^### ', md, re.M)] + [len(md)]
Q = re.compile(r'^> \*\*卷(\d+)·段(\d+)\*\*　(.*)$')
GAP = re.compile(r'^> （中略：段(\d+)(?:～(\d+))?')
ANN = re.compile(r'^- 全文收錄（(.*)）：$')

strict_n = loose_n = 0
bad, nofil, items_no_q = [], [], []
ex_blocks = 0

for i in range(len(ip) - 1):
    body = md[ip[i]:ip[i + 1]]
    title = re.sub(r'^### \d+\. ', '', body.split('\n')[0]).strip()

    # 第一遍：把條目切成「區塊」（舊節引 / 逐字抽出），各帶其自註
    blocks, cur = [], None
    for ln in body.split('\n'):
        s = ln.strip()
        a = ANN.match(s)
        if a or s.startswith('- 全文收錄：') or s == '- 原文：':
            ann = a.group(1) if a else ''
            cur = {'ex': '逐字抽出' in ann, 'ann': ann, 'q': []}
            blocks.append(cur)
            if cur['ex']:
                ex_blocks += 1
            continue
        g = Q.match(s)
        if g and cur is not None:
            cur['q'].append((int(g.group(1)), int(g.group(2)), g.group(3)))
    if not any(b['q'] for b in blocks):
        items_no_q.append(title[:24])

    # 第二遍：逐區塊核驗
    for b in blocks:
        cut_from = cut_to = None
        if b['ex']:
            m = re.search(r'自「(.+?)」起', b['ann'])
            cut_from = norm(m.group(1)) if m else None
            m = re.search(r'至「(.+?)」(?:止）?)?', b['ann'])
            cut_to = norm(m.group(1)) if m else None
        for k, (v, p, t) in enumerate(b['q']):
            src = PS.get(v, {}).get(p, '')
            if not src:
                nofil.append((title[:20], v, p))
                continue
            a, n = norm(t), norm(src)
            if not b['ex']:
                loose_n += 1
                # 節引可行內跳引（「……」），逐節須為子串且次序相符
                # 跳引號在 norm 後即消失，故先切原文再歸形
                pieces = [norm(x) for x in re.split(r'…{2,}|。{3,}', t) if norm(x)] or [a]
                at, ok = 0, bool(a)
                for pc in pieces:
                    j = n.find(pc, at)
                    if not pc or j < 0:
                        ok = False
                        break
                    at = j + len(pc)
                if not ok:
                    bad.append(('乙', title[:20], v, p, a[:28], n[:28]))
                continue
            strict_n += 1
            ok = (a == n)
            if not ok and cut_from and k == 0 and cut_from in n:
                ok = (a == n[n.find(cut_from):])
            if not ok and cut_to and k == len(b['q']) - 1 and cut_to in n:
                ok = (a == n[:n.find(cut_to) + len(cut_to)])
            if not ok and cut_from and cut_to and cut_from in n and cut_to in n:
                i0, i1 = n.find(cut_from), n.find(cut_to)
                ok = i0 < i1 and len(b['q']) == 1 and a == n[i0:i1 + len(cut_to)]
            if not ok:
                bad.append(('甲', title[:20], v, p,
                            a[:24] + '｜' + a[-12:], n[:24] + '｜' + n[-12:]))
    for s in (x.strip() for x in body.split('\n')):
        g = GAP.match(s)
        if g:
            hi = int(g.group(2) or g.group(1))
            av = {int(x) for x in re.findall(r'^> \*\*卷(\d+)·', body, re.M)}
            if av and hi > max(PS[min(av)]):
                bad.append(('丙', title[:20], min(av), hi, '中略越界', max(PS[min(av)])))

nj = len([x for x in bad if x[0] == '甲'])
# 自證：本檔凡例所報之數須與實測相符
claim = {}
for m in re.finditer(r'引文(.{1,9}?)行已逐行覆核', md):
    claim['total'] = cn2num(m.group(1))
for m in re.finditer(r'者(.{1,9}?)行與底本該段全段相同', md):
    claim['jia'] = cn2num(m.group(1))
for m in re.finditer(r'舊有節引(.{1,9}?)行俱為', md):
    claim['yi'] = cn2num(m.group(1))
meas = {'total': strict_n + loose_n, 'jia': strict_n, 'yi': loose_n}
claimed = any(k in claim for k in meas)
claim_bad = [(k, claim.get(k), v) for k, v in meas.items() if claim.get(k) != v] if claimed \
    else []

print('底本：卷 %d，段 %d' % (len(PS), sum(len(d) for d in PS.values())))
print('條目 %d；「逐字抽出」區塊 %d' % (len(ip) - 1, ex_blocks))
print('甲（抽出：全段逐字，或依自註於首/末段截斷）引文行 %d，不合 %d' % (strict_n, nj))
print('乙（舊有節引：須為底本子串）引文行 %d，不合 %d' % (loose_n, len(bad) - nj))
print('查無此段 %d；全無引文之條目 %d' % (len(nofil), len(items_no_q)))
print('凡例自報之數 %s／實測 %s → 不合 %d%s' % (
    {k: claim.get(k) for k in ('total', 'jia', 'yi')}, meas, len(claim_bad),
    '' if claimed else '（本檔凡例未報數，不對帳）'))
for x in claim_bad:
    print('  自報『%s』%s，實測 %s' % x)
for x in nofil[:6]:
    print('  查無', x)
for x in items_no_q[:6]:
    print('  無引文', x)
for x in bad[:12]:
    print('  %s %s 卷%s段%s\n    產物：%s\n    底本：%s' % x)
sys.exit(1 if bad or nofil or items_no_q or claim_bad else 0)
