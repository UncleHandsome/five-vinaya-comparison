#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《五部律差異對照本》全書掃描：以校閱報告所列問題類型為綱，逐類自查。

用法：
  python tools/audit_book.py            # 印出各類問題
  python tools/audit_book.py --md out   # 另存 markdown 報告
  python tools/audit_book.py --refs     # 另存散文自由引用清單（供人工覆核）

只讀成品 MD，不改書；凡可機械判定者列為「確」，須人判者列為「疑」。
"""
import os, re, sys, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, '03_成品', '五部律差異對照本.md')
WORK = os.path.join(ROOT, '_work')

S = open(MD, encoding='utf-8').read()
LINES = S.split('\n')

# ── 切篇、切節、切項 ─────────────────────────────────────────────
PIAN = []          # [(no, title, text)]
for m in re.finditer(r'^#### (\d{3})　(.+)$', S, re.M):
    PIAN.append([int(m.group(1)), m.group(2).strip(), m.start()])
P2 = S.find('### 第二部')
if P2 < 0:
    P2 = len(S)
for i, p in enumerate(PIAN):
    p[2] = S[p[2]: PIAN[i + 1][2] if i + 1 < len(PIAN) else P2]

ITEM = []          # [(dno, title, meta, text)]
for m in re.finditer(r'^\*\*(D-\d{4})\*\*　(.+)$', S, re.M):
    ITEM.append([m.group(1), m.group(2).strip(), m.start()])
for i, it in enumerate(ITEM):
    it[2] = S[it[2]: ITEM[i + 1][2] if i + 1 < len(ITEM) else P2]

META = {}
for d, t, body in ITEM:
    m = re.search(r'^<sub>(.+?)</sub>$', body, re.M)
    META[d] = m.group(1) if m else ''

issues = collections.defaultdict(list)


def add(kind, msg):
    issues[kind].append(msg)


# ── 一、節題：序號連續、重複、空節 ────────────────────────────────
CN = '一二三四五六七八九十百'
_D = {c: i for i, c in enumerate('一二三四五六七八九', 1)}


def _cn2int(s):
    """中文數字轉整數（一–九百九十九）。"""
    s = s.strip()
    if not s:
        return 0
    if '百' in s:
        a, _, b = s.partition('百')
        v = _D.get(a, 1) * 100
        if b:
            v += _cn2int(b)
        return v
    if '十' in s:
        a, _, b = s.partition('十')
        return (_D.get(a, 1) * 10) + (_D.get(b, 0) if b else 0)
    return _D.get(s, 0)
for no, title, body in PIAN:
    heads = re.findall(r'^##### (.+)$', body, re.M)
    # 序號（一、二、…）連續
    nums = []
    for h in heads:
        if h.startswith('〔'):
            continue
        m = re.match(r'^(?:第)?([%s]+)、' % CN, h)
        if m:
            from_ = m.group(1)
            v = _cn2int(from_)
            nums.append((v, h))
    for (a, ha), (b, hb) in zip(nums, nums[1:]):
        if b != a + 1:
            add('節序不連續', '%03d %s：%s → %s' % (no, title, ha[:14], hb[:14]))
    dup = [h for h, n in collections.Counter(heads).items() if n > 1]
    if dup:
        add('節題重複', '%03d %s：%s' % (no, title, '／'.join(x[:16] for x in dup)))

# 空節：節題下既無「本節差異」亦無原文塊
for no, title, body in PIAN:
    parts = re.split(r'^##### ', body, flags=re.M)[1:]
    for p in parts:
        h = p.split('\n', 1)[0]
        if '<details class="art-src"' not in p and '本節差異' not in p:
            add('空節', '%03d %s：%s' % (no, title, h[:24]))

# ── 二、引號配對（塊級）──────────────────────────────────────────
for d, t, body in ITEM:
    blk = [l for l in body.split('\n') if l.startswith('> ')]
    if not blk:
        continue
    txt = '\n'.join(blk)
    diff = txt.count('「') - txt.count('」')
    if diff:
        add('引號未平', '%s %s（差 %+d）' % (d, t[:26], diff))

# ── 三、工程殘留與體例 ───────────────────────────────────────────
BAD = [
    (r'\bW\d{2}\b', '底稿 W 檔號'),
    (r'sifen/|wufen/|shisong', '資料庫路徑'),
    (r'vol\d+[-#]', '卷檔代號'),
    (r'\d{3}_[^\s，。；）]{1,12}段', '篇檔名'),
    (r'（查詞：|（查：|（查 ', '查詢詞體例'),
    (r'線索所稱|提示詞|待查|TODO', '草稿語'),
]
for d, t, body in ITEM:
    for pat, name in BAD:
        if re.search(pat, body):
            add('工程殘留', '%s %s：%s' % (d, t[:22], name))

# ── 四、標題口吃與重複 ──────────────────────────────────────────
for d, t, body in ITEM:
    parts = re.split(r'　+', t)
    if len(parts) >= 2:
        a, b = parts[0].strip('*'), parts[1]
        if len(a) >= 4 and b.startswith(a):
            add('標題口吃', '%s %s' % (d, t[:40]))
seen = collections.defaultdict(list)
for d, t, body in ITEM:
    # 取 **…** 內的完整主標題（含「戒名　要點」）。同戒二項以要點區別，
    # 如「媒嫁戒　二段結戒」與「媒嫁戒　女男各十種」，體例容許，不算重複。
    m = re.match(r'^\*\*(.+?)\*\*', t)
    core = (m.group(1) if m else re.sub(r'[　 ].*$', '', t)).replace('*', '').strip()
    seen[core].append(d)
for k, v in seen.items():
    if len(v) > 1:
        add('標題重複', '%s：%s' % ('、'.join(v), k[:30]))

# ── 五、狀態與說明矛盾（啟發式）──────────────────────────────────
MORE = r'(別立|另立|增出|分為|詳列|復立|更立|多出)'
LESS = r'(不載|無此|未見|略去|缺|不出|從略)'
for d, t, body in ITEM:
    meta = META.get(d, '')
    m = re.search(r'〔(?:五分|十誦|僧祇|根有) ([ABCD])〕', meta)
    if not m:
        continue
    st = m.group(1)
    diff = body.split('**本稿原文**')[0]
    has_more = bool(re.search(MORE, diff))
    has_less = bool(re.search(LESS, diff))
    if st == 'D' and has_more and not has_less:
        add('狀態疑義', '%s %s：標 D 而說明多「增／立」' % (d, t[:24]))

# ── 六、類欄 ─────────────────────────────────────────────────────
SMETA = {}
for m in re.finditer(r'^\*\*(S-\d{4})\*\*　(.+?)\n\n(<sub>.+?</sub>)', S, re.M | re.S):
    SMETA[m.group(1)] = (m.group(2).strip(), m.group(3))
for sid, (st, meta) in SMETA.items():
    m = re.search(r'類：([^　]+)', meta)
    if not m:
        add('類未標（體例：寧缺勿強配）', '%s %s' % (sid, st[:24]))
        continue
    cls = m.group(1)
    _i = S.find('**%s**' % sid)
    _o = S.find('**本稿原文**', _i)
    _seg = S[_o:_o + 320] if _o > 0 else ''
    if cls.startswith('比丘') and re.search(r'若比丘尼', _seg):
        add('類疑義', '%s %s：類作「%s」而戒文主語為尼' % (sid, st[:20], cls))

# ── 七、篇旨漏戒名 ───────────────────────────────────────────────
for no, title, body in PIAN:
    m = re.search(r'> \*\*篇旨\*\*：(.+)', body)
    if not m:
        continue
    intro = m.group(1)
    heads = re.findall(r'^##### (?:第?[%s]+、)?(.+)$' % CN, body, re.M)
    miss = []
    for h in heads:
        nm = re.sub(r'（.*?）', '', h).strip()
        nm = re.sub(r'^第[%s]+戒[　 ]*' % CN, '', nm)
        if len(nm) < 2:
            continue
        nm = re.sub(r'戒$', '', nm)
        if len(nm) < 2:
            continue
        key = nm[:2]
        if key and key not in intro:
            miss.append(nm[:10])
    # 篇旨為提要，非逐條索引；此項僅供人工覆核，不列入機械報告。
    if False and len(miss) >= 8:
        add('篇旨漏目', '%03d %s：未見 %s' % (no, title, '、'.join(miss[:6])))

# ── 八、互見死鏈 ─────────────────────────────────────────────────
D_SET = set(x[0] for x in ITEM)
S_SET = set(re.findall(r'^\*\*(S-\d{4})\*\*', S, re.M))
for ref in set(re.findall(r'S-\d{4}', S)):
    if ref not in S_SET:
        add('互見死鏈', '引 %s 而無此項' % ref)
for ref in set(re.findall(r'D-\d{4}', S)):
    if ref not in D_SET:
        add('互見死鏈', '引 %s 而無此項' % ref)

# ── 九、篇首節數與實際 ───────────────────────────────────────────
for no, title, body in PIAN:
    m = re.search(r'<sub>本篇 (\d+) 段(?:，分 (\d+) 節)?，差異 (\d+) 項</sub>', body)
    if not m:
        continue
    seg, ns, nd = int(m.group(1)), m.group(2), int(m.group(3))
    heads = len(re.findall(r'^##### ', body, re.M))
    if ns and heads and int(ns) != heads:
        add('節數不符', '%03d %s：篇首 %s 節，實 %d 節' % (no, title, ns, heads))
    real_d = len(re.findall(r'^\*\*D-\d{4}\*\*', body, re.M))
    if real_d != nd:
        add('差異數不符', '%03d %s：篇首 %d 項，實 %d 項' % (no, title, nd, real_d))

# ── 十、數字與列舉（標題 N 種／N 類）──────────────────────────────
CN2N = {'二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15, '十六': 16,
        '十七': 17, '十八': 18, '十九': 19, '二十': 20, '二十一': 21, '二十二': 22,
        '二十三': 23, '二十四': 24, '二十五': 25, '三十': 30}
for d, t, body in ITEM:
    m = re.search(r'([%s]+)\s*(種|類|條|句|事|法|目)' % CN, t)
    if not m:
        continue
    want = CN2N.get(m.group(1))
    if not want or want < 3:
        continue
    # 以頓號列舉數估算
    seg = body.split('**本稿原文**')[0]
    runs = re.findall(r'[^\n，。；：]{1,12}(?:、[^\n，。；：]{1,12}){2,}', seg)
    if not runs:
        continue
    best = max(r.count('、') + 1 for r in runs)
    # 頓號列舉數與題目數字之對應須人判（列舉或散見他處），不列入機械報告。
    if False and abs(best - want) >= 3 and best >= 6:
        add('數字疑義', '%s %s：題作 %s %s，列舉約 %d' % (d, t[:20], m.group(1), m.group(2), best))

# ── 十一、附錄與統計 ─────────────────────────────────────────────
m = re.search(r'按四分律篇次歸位者 \*\*([\d,]+)\*\* 項', S)
if m and m.group(1).replace(',', '') != str(len(D_SET)):
    add('統計不符', '第一部 %s 項，實 %d' % (m.group(1), len(D_SET)))
for lab, pat in [('D 項', r'\*\*D\*\*.*?D 凡 ([\d,]+) 項')]:
    pass

# ── 十二、重複條目（同律同卷同項）────────────────────────────────
seen2 = collections.Counter()
for d, t, body in ITEM:
    m = re.search(r'本稿位置：([^　]+)　出處：([^　<]+)', META.get(d, ''))
    if m:
        seen2[(m.group(2).strip(), m.group(1).strip())] += 1
for k, n in seen2.items():
    if n > 1:
        add('重複條目', '%s ×%d' % (k[0], n))

# ── 十三、散文中的自由引用（供人工覆核，不列為問題）──────────────
# 項號曾因改判歸位而位移；自動生成的目錄連結不會錯，但散文中手寫的
# 「見 D-xxxx」「另見 S-xxxx」可能指到別項。此表列出號碼與該號現指之標題。
if '--refs' in sys.argv:
    _id_title = {m.group(1): m.group(2).replace('*', '').strip()
                 for m in re.finditer(r'^\*\*([DS]-\d{4})\*\*　(.+)$', S, re.M)}
    _rows = []
    for _i, _l in enumerate(LINES, 1):
        if ('](#d-' in _l or '](#s-' in _l or '.html#s-' in _l
                or '.html#d-' in _l or _l.startswith('<a id=')):
            continue
        if re.match(r'^\*\*[DS]-\d{4}\*\*', _l):
            continue
        for _m in re.finditer(r'\b[DS]-\d{4}\b', _l):
            _r = _m.group(0)
            _rows.append('| %d | `%s` | %s | %s |' % (
                _i, _r, (_id_title.get(_r) or '（無此項）')[:44],
                _l.strip().replace('|', '／')[:96]))
    _rp = os.path.join(WORK, '審閱', '自由引用清單.md')
    open(_rp, 'w', encoding='utf-8').write(
        '# 散文中的自由項號引用\n\n'
        '供人工覆核：號碼是否仍指對項目（項號曾因改判歸位而位移）。\n'
        '自動生成的目錄連結（`](#d-…)`）、項號行與錨點不計。\n\n'
        '| 行 | 引用 | 該號現指 | 所在行 |\n|---|---|---|---|\n'
        + '\n'.join(_rows) + '\n')
    print('→ 自由引用 %d 處：%s' % (len(_rows), _rp))

# ── 輸出 ─────────────────────────────────────────────────────────
order = ['節序不連續', '節題重複', '空節', '引號未平', '工程殘留', '標題口吃', '標題重複',
         '狀態疑義', '類未標（體例：寧缺勿強配）', '類疑義', '互見死鏈', '節數不符',
         '差異數不符', '統計不符', '重複條目']
out = []
out.append('# 全書掃描報告')
out.append('')
out.append('書稿：`03_成品/五部律差異對照本.md`（D 項 %d、篇 %d）' % (len(D_SET), len(PIAN)))
out.append('')
out.append('| 類 | 數 |')
out.append('|---|---:|')
for k in order:
    out.append('| %s | %d |' % (k, len(issues.get(k, []))))
out.append('')
for k in order:
    v = issues.get(k, [])
    if not v:
        continue
    out.append('## %s（%d）' % (k, len(v)))
    out.append('')
    for x in v[:40]:
        out.append('- %s' % x)
    if len(v) > 40:
        out.append('- …另有 %d 條' % (len(v) - 40))
    out.append('')

out.append('## 判定說明（非零項之處置）')
out.append('')
out.append('- **引號未平**：皆為嵌套引文（「…「…」…」）與 D-1458 多引文項，人工判為可存，不補字。')
out.append('- **類未標**：體例所定「未分類」，寧缺勿強配，不自動補類。')
out.append('- **類疑義**：S-0252 兼攝比丘三夷與比丘尼四夷，類作「比丘四波羅夷」可通。')
out.append('- **標題重複**：只計 `**…**` 完整主標題全同者；同戒二項以「戒名　要點」區別，不計。')
out.append('- **不列入機械判定**：篇旨漏目（篇旨為提要非逐條索引）、題目數字 vs 列舉數')
out.append('  （列舉常散見他處）——二者硬掃會出數十筆偽陽性，須人判。')
out.append('- **不列入機械判定**：散文中的 D／S 號是否指對項目（錨點皆存在，惟號碼曾位移，')
out.append('  須逐處核語義）。2026-11-07 已人工核過 68 行自由引用，並改寫第三部 G2 說明')
out.append('  與 README 項號說明，使不倚賴易位移之項號。')
out.append('')
_SEED = []
for d, t, body in ITEM:
    if re.search(r'\*\*(?:單提|僧殘|捨墮|波羅夷|提舍尼)\s*\d+', t):
        _SEED.append('- `%s`　%s' % (d, t[:80]))
out.append('## 附：標題中殘留底稿戒號（%d 項，待對勘）' % len(_SEED))
out.append('')
out.extend(_SEED)
out.append('')
out.append('第四批已修報告點名之 8 項，機械掃描另得此 %d 項。此類編號多為五分律底稿戒次，'
           '與四分正式戒號非一一對應（如底稿「單提19／20」與四分「蟲水澆泥草／覆房過三節」互易，'
           '而 11–18 又相合），不宜自動替換，須逐條對勘五分律戒本次第，故留待下輪。' % len(_SEED))
out.append('')

txt = '\n'.join(out)
print(txt)
if '--md' in sys.argv:
    i = sys.argv.index('--md')
    p = sys.argv[i + 1] if i + 1 < len(sys.argv) else os.path.join(WORK, '審閱', '全書掃描報告.md')
    open(p, 'w', encoding='utf-8').write(txt)
    print('\n→', p)
