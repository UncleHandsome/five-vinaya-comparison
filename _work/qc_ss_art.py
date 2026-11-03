# -*- coding: utf-8 -*-
"""量《十誦律去重》產物之引文忠實度（分冊＋合冊）：
   嚴則——每條引用行（去標點空白後）須為其所標『卷N·段M』底本段文之連續子串，
              或為數段相連之子串（行內跨段者以『段M』標首段，故亦驗跨段拼接）。
   寬則——行內每一句（以。！？；斷）須能在該卷全文中尋得。
   凡嚴則不合者，印出多餘之字（拼接過界）或缺失之字，以定病灶。"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, '十誦律_去重')
BASE = os.path.join(ROOT, '_work', 'shisong')


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


PARA, VOL = {}, {}
for fn in os.listdir(BASE):
    if not (fn.startswith('vol') and fn.endswith('.txt')):
        continue
    v = int(fn[3:5])
    d = {}
    for ln in io.open(os.path.join(BASE, fn), encoding='utf-8'):
        a, sep, b = ln.rstrip('\n').partition('\t')
        if sep and a.strip().isdigit():
            d[int(a)] = b.strip()
    PARA[v] = d
    VOL[v] = norm(''.join(d[n] for n in sorted(d)))

Q = re.compile(r'^> \*\*(?:卷(\d{1,2})·)?段(\d{1,3})\*\*　(.*)$', re.M)
# 另檢「回捲」：同一項內段號序列須不遞退（舊尺漏 re.M 曾虛報 0，故此处立為硬判）
QLAB = re.compile(r'^> \*\*(?:卷\d{1,2}·)?段(\d{1,3})\*\*', re.M)
files = [f for f in sorted(os.listdir(D)) if f.endswith('.md') and f != 'README.md']
strict_bad, loose_bad, total = [], [], 0
regress = []
for f in files:
    md = io.open(os.path.join(D, f), encoding='utf-8').read()
    heads = [(m.start(), [int(x) for x in re.findall(r'卷\s*(\d{1,2})', m.group(1))])
             for m in re.finditer(r'^## (卷[^\n]*)$', md, re.M)]

    def hv(pos):
        c = [v for p, v in heads if p < pos]
        return c[-1] if c else []
    for m in re.finditer(r'^### .*$', md, re.M):
        tv = hv(m.start())
        end = [md.find(x, m.end()) for x in ('\n### ', '\n## ', '\n---')]
        end = [e for e in end if e > 0]
        item = md[m.start():min(end) if end else len(md)]
        nums = [int(x) for x in QLAB.findall(item)]
        back = [(a, b) for a, b in zip(nums, nums[1:]) if b < a]
        if back:
            regress.append((f, m.group(0)[:38], nums[:12], back[:2]))
        for ln in item.split('\n'):
            g = Q.match(ln.strip())
            if not g:
                continue
            v = int(g.group(1)) if g.group(1) else (tv[0] if len(tv) == 1 else None)
            p, txt = int(g.group(2)), g.group(3)
            total += 1
            a = norm(txt)
            if not a:
                continue
            src = norm(PARA.get(v, {}).get(p, '')) if v else ''
            ok = bool(src) and a in src
            if not ok and v:
                # 跨段拼接：自本段起向後串接，容行內含連續數段
                acc = ''
                for n in sorted(x for x in PARA[v] if x >= p):
                    acc += norm(PARA[v][n])
                    if a in acc:
                        ok = True
                        break
                    if len(acc) > 3 * len(a):
                        break
            if not ok:
                strict_bad.append((f, v, p, txt[:56], len(a), len(src)))
            for at in [x for x in re.split(r'(?<=[。！？；])', txt) if norm(x)]:
                if v and norm(at) not in VOL[v]:
                    loose_bad.append((f, v, p, at[:40]))

print('檔 %d｜引用行 %d' % (len(files), total))
print('嚴則（整行須在本段或連續數段內）不合：%d' % len(strict_bad))
for x in strict_bad[:12]:
    print('  %s 卷%s段%s｜產%d字/段%d字｜%s' % (
        x[0].replace('十誦律_去重_', ''), x[1], x[2], x[4], x[5], x[3]))
print('寬則（逐句須在本卷內）不合：%d' % len(loose_bad))
for x in loose_bad[:8]:
    print('  %s 卷%s段%s｜%s' % (x[0].replace('十誦律_去重_', ''), x[1], x[2], x[3]))
print('回捲（同一項內段號遞退）之項：%d' % len(regress))
for x in regress[:10]:
    print('  %s｜%s｜序列 %s｜退 %s' % (x[0].replace('十誦律_去重_', ''), x[1], x[2], x[3]))
sys.exit(1 if strict_bad or loose_bad or regress else 0)
