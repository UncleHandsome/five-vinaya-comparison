#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產出《五部律差異對照本》——以四分律為閱讀主線。

結構：
  卷首：題解、凡例、五部律部派、統計、讀法
  第一部：四分律有對應處之差異（1,440 項，按四分律 75 篇次第）
  第二部：四分律所無之制度（669 項，按主稿分）
  第三部：歸併組（甲表 7 組、乙表 3 組）
  附錄：無法歸位、統計、卷次對照

輸出：
  五部律差異對照本.md（合冊）
  五部律差異對照本_卷一至卷十.md 等 6 個分卷檔
"""
import json, re, os, glob
from collections import defaultdict, Counter, OrderedDict
from norm_ref import normalize as norm_ref
from section_intro import INTRO as SEC_INTRO

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
OUT = os.path.join(ROOT, '03_成品')   # 成品統一輸出於此

# ---------- 載入 ----------
si = {x['n']: x for x in json.load(open(os.path.join(BASE, 'sifen_index.json'), encoding='utf-8'))}
rows = json.load(open(os.path.join(BASE, 'matrix_built.json'), encoding='utf-8'))
loc = json.load(open(os.path.join(BASE, '_locate.json'), encoding='utf-8'))
ORIG = json.load(open(os.path.join(BASE, 'originals_index.json'), encoding='utf-8'))

ID2ROW = {r['id']: r for r in rows}
PLACED = {p['id']: p for p in loc['placed']}
ABSENT = set(loc['absent'])
UNPLACED = loc['unplaced']

# 勘誤改判者：原判「四分所無」，覆核後實有對應，改入第一部
ERRATA_POS = {'M-1913': (0, 3)}
for _rid, (_n, _seg) in ERRATA_POS.items():
    if _rid not in PLACED:
        PLACED[_rid] = {'id': _rid, 'n': _n, 'seg': _seg, 'how': 'errata'}
    ABSENT.discard(_rid)

# G/T 歸併組（自矩陣 md 提取，此處硬編，來源見 _work/gt_groups.json）
GT_PATH = os.path.join(BASE, 'gt_groups.json')
if os.path.exists(GT_PATH):
    GT = json.load(open(GT_PATH, encoding='utf-8'))
else:
    GT = {
        'G1': ['M-0071', 'M-1524'], 'G2': ['M-0067', 'M-0508'],
        'G3': ['M-0093', 'M-1594'], 'G4': ['M-0088', 'M-2102'],
        'G5': ['M-1682', 'M-2124'], 'G6': ['M-1169', 'M-1666'],
        'G7': ['M-1088', 'M-2105'], 'T1': ['M-0228', 'M-1692'],
        'T2': ['M-1725', 'M-1976'], 'T3': ['M-0322', 'M-1809'],
    }
ID2GT = {}
for g, ids in GT.items():
    for i in ids:
        ID2GT[i] = g

GT_INFO = {
    'G1': ('未獲許可入比丘尼住處', '五分 vol07#1（僧差）／僧祇 vol14-15#26（白）',
           '以五分戒文為主，僧祇之「白」法與「為尼作唄」四判入程序差異欄'),
    'G2': ('作大房過量', '五分 vol06#11（三重為限）／十誦 vol11-12#9（三種不犯緣）',
           '以五分戒文與犯相為主，十誦板覆、鳥翅覆、草根覆三句入開緣欄'),
    'G3': ('知檀越欲與僧物迴與餘人', '五分 vol09#1／僧祇 vol20-21#18',
           '以五分戒文為主，僧祇五層遞減判入判罪欄'),
    'G4': ('輕師／不恭敬', '五分 vol08#10／根有 vol42-43#1',
           '**判罪權重相反**，兩存其判，不強合'),
    'G5': ('七佛戒經偈', '僧祇 vol27-28#12／根有 vol50#7',
           '七偈一一對應；根有結勸偈另註'),
    'G6': ('波羅夷與學行法', '十誦 vol56#32／僧祇 vol25-26#24',
           '條件一一對應；同室宿、布薩自恣之許否兩存'),
    'G7': ('食前食後至餘家', '十誦 vol54#26／根有 vol42-43#4',
           '三稿各記一側面：十誦立不犯緣、根有立犯界'),
    'T1': ('比丘為官所執時之布薩', '五分 vol18#11／僧祇 vol27-28#22',
           '五分取清淨欲、就彼布薩、出界三層；僧祇分時集與羯磨欲、非時集與清淨欲'),
    'T2': ('大目連被判妄語', '僧祇 vol29-30#19／根有 vol10-11#4',
           '僧祇四則逐一判；根有以攝頌總標五事'),
    'T3': ('災起時全僧共收', '五分 vol25#9／僧祇 vol33#14',
           '五分收僧房臥具、不助得突吉羅；僧祇收塔與枝提幡蓋、違者越毘尼'),
}

ST_NAME = {'A': '同條增異', 'B': '同條開緣', 'C': '四分所無', 'D': '同條減略'}

# 同制重出：同一制度在原稿中兩處收錄（多因底本不同章節重出），互註以免讀者以為二事
SAME_TOPIC = {
    'M-1068': 'M-0617', 'M-0617': 'M-1068',   # 未結界僧坊界量
    'M-0600': 'M-0756', 'M-0756': 'M-0600',   # 布草除偷蘭白衣相應罪
    'M-0531': 'M-0582', 'M-0582': 'M-0531',   # 五似食
}

from errata import apply as apply_errata


# 篇名覆寫：原檔 038 名為「(開頭)」，實含受戒至自恣四揵度，且括號會壞目錄錨點
TITLE_FIX = {0: '卷首譯款與通序偈', 38: '受戒・說戒・安居・自恣諸揵度（卷31–37）'}


def ptitle(n):
    return TITLE_FIX.get(n, si[n]['title'])


def anchor(n):
    return f'p{n:03d}'
ST_ORDER = {'A': 0, 'B': 1, 'C': 2, 'D': 3}

# 分卷（依四分律原檔六檔）
JUAN_SEGS = [
    ('卷一至卷十', list(range(0, 13)), '01-10原文.txt'),
    ('卷十一至卷二十一', list(range(13, 26)), '11-21 原文.txt'),
    ('卷二十二至卷三十', list(range(26, 38)), '22-30 原文.txt'),
    ('卷三十一至卷三十七', [38], '31-37 原文.txt'),
    ('卷三十八至卷四十九', list(range(39, 61)), '38-49 原文.txt'),
    ('卷五十至卷六十', list(range(61, 75)), '50-60 原文.txt'),
]

# ---------- 清理工具 ----------
RE_TXT_TAG = re.compile(r'`?(\d{3})[_A-Za-z\u4e00-\u9fff]*\.txt`?')
RE_CHUNK_TAG = re.compile(r'`?[\w/]*(shoujie|shuojie|anju|zizi)[_\d]*\.txt`?')


def dedup_xref(x):
    """補證欄常有「……（同樣內容）」的重複，去其重複括號（可多處）"""
    if not x:
        return x
    out = x
    for _ in range(6):
        changed = False
        for m in re.finditer(r'（([^（）]{12,})）', out):
            inner = m.group(1)
            if inner[:20] in out[:m.start()]:
                out = out[:m.start()] + out[m.end():]
                changed = True
                break
        if not changed:
            break
    return re.sub(r'\s+', ' ', out).strip()


def fix_ref4_loc(ref4, p_):
    """用歸位結果修正 ref4 的定位前綴：行號引用與裸段號補上篇號"""
    if not ref4 or not p_:
        return ref4
    tag = f'`{p_["n"]:03d}`'
    # 原始檔行號引用：四分律01-10原文.txt 第196行馬麥段 → `001` 段2
    if '原文.txt' in ref4:
        new = re.sub(r'^[^：:「]{0,26}原文\.txt\s*(?:第\d+行)?[^：:「]{0,14}',
                     f'{tag} 段{p_["seg"]}', ref4, count=1)
        return new
    # 裸段號：段7 → `001` 段7
    m = re.match(r'^段(\d{1,4})', ref4)
    if m:
        return f'{tag} 段{m.group(1)}' + ref4[m.end():]
    return ref4


def clean_ref(s, kind='四分'):
    """把引用標記統一為讀者可用之形式（見 norm_ref.py）"""
    return norm_ref(s, kind)


def esc(s):
    """表格/標題用：去掉會破壞結構的字元"""
    return (s or '').replace('|', '｜').strip()


def one_line(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()


FULLNAME = {'五分': '五分律', '十誦': '十誦律', '僧祇': '僧祇律', '根有': '根有律'}
ORIG_LIMIT = 1500   # 原文超過此數即節引，免長篇打斷閱讀


def clip_orig(orig, r):
    """超長原文截斷，標明節引與全文出處"""
    if len(orig) <= ORIG_LIMIT:
        return orig, False
    cut = orig[:ORIG_LIMIT]
    # 儘量切在段末
    nl = cut.rfind('\n')
    if nl > ORIG_LIMIT * 0.7:
        cut = cut[:nl]
    return cut, True


def fix_terms(diff, canon):
    """把「本律」「此律」換為具體律名，免讀者回頭查主稿"""
    if not diff:
        return diff
    name = FULLNAME.get(canon, canon)
    d = diff.replace('本律', name).replace('此律', name)
    return d


def clean_orig(t):
    """清理原文中的重複標點與工作殘留"""
    if not t:
        return ''
    t = t.replace('〕〕', '〕').replace('】】', '】').replace('〔〔', '〔')
    t = t.replace('。。', '。').replace('，，', '，')
    return t.strip()


# ---------- 主體：按四分律篇次分組 ----------
by_seg = defaultdict(list)   # 篇號 -> [(seg, row)]
for rid, p in PLACED.items():
    by_seg[p['n']].append((p['seg'], ID2ROW[rid]))

for n in by_seg:
    by_seg[n].sort(key=lambda x: (x[0], ST_ORDER.get(x[1]['st'], 9), x[1]['id']))


# ---------- 戒條分節 ----------
# 四分律原文每戒末標「(一竟)」「(二竟)」…，據此切分篇內戒條。
JIE = {}   # 篇號 -> [(起段, 迄段, 序, 戒名), ...]


def _jie_name(s):
    """從戒條句提取短名"""
    s = re.sub(r'^若比丘[，,]?', '', s or '')
    s = re.sub(r'[，,]?(尼薩耆波逸提|僧伽婆尸沙|波羅夷|波逸提|波羅提提舍尼|突吉羅).*$', '', s)
    s = re.sub(r'^衣已竟[，,]?迦絺那衣已[出捨][，,]?', '', s)
    s = s.strip('，,。 ')
    return s[:12] + ('…' if len(s) > 12 else '')


def load_jie():
    d = os.path.join(BASE, 'sifen')
    if not os.path.isdir(d):
        return
    for f in glob.glob(os.path.join(d, '*.txt')):
        try:
            no = int(os.path.basename(f)[:3])
        except ValueError:
            continue
        lines = open(f, encoding='utf-8', errors='ignore').read().split('\n')
        marks = []
        for i, l in enumerate(lines):
            m = re.search(r'\(([一二三四五六七八九十百]+)竟[)）]?', l)
            if m:
                marks.append((i + 1, m.group(1)))
        if not marks:
            continue
        jies, prev = [], 0
        for seg, cn in marks:
            seg_text = '\n'.join(lines[prev:seg])
            m = re.search(r'當如是說[：:]\s*([^\n。]{8,120})', seg_text)
            jies.append((prev + 1, seg, cn, _jie_name(m.group(1)) if m else ''))
            prev = seg
        JIE[no] = jies


load_jie()

# 序號
D_NO = {}
k = 0
for n in sorted(by_seg):
    for seg, r in by_seg[n]:
        k += 1
        D_NO[r['id']] = f'D-{k:04d}'

# ---------- 第二部：C 項按主稿 ----------
absent_rows = [ID2ROW[i] for i in ABSENT]
# G/T 組成員合併：每組只出現一次，取第一項為主，第二項附註
gt_primary = {}
gt_secondary = {}
for g, ids in GT.items():
    live = [i for i in ids if i in ABSENT]
    if not live:
        continue
    gt_primary[g] = live[0]
    for i in live[1:]:
        gt_secondary[i] = g

by_canon_absent = defaultdict(list)
for r in absent_rows:
    if r['id'] in gt_secondary:
        continue
    by_canon_absent[r['canon']].append(r)
for c in by_canon_absent:
    by_canon_absent[c].sort(key=lambda r: (ST_ORDER.get(r['st'], 9), r['unit'], r['no']))

# S 編號須依「實際輸出順序」分配（先主稿、再層級、後原序），否則文中編號跳躍
S_NO = {}
k = 0
for c in ['五分', '十誦', '僧祇', '根有']:
    _bylv = defaultdict(list)
    for r in by_canon_absent.get(c, []):
        _bylv[r.get('lv', '其他')].append(r)
    for lv in ['戒條', '制度', '法數', '事件', '其他']:
        for r in _bylv.get(lv, []):
            k += 1
            S_NO[r['id']] = f'S-{k:04d}'


# ---------- 單項渲染 ----------
def render_item(r, no_prefix, compact=False):
    """渲染一項"""
    r = apply_errata(r)
    g = ID2GT.get(r['id'])
    _aid = no_prefix.lower()
    tag = f'〔{r["canon"]} {r["st"]}〕'
    gt_tag = f'　[`{g}`](#gt-{g})' if g else ''
    lines = []
    lines.append(f'<a id="{_aid}"></a>')
    lines.append('')
    lines.append(f'**{no_prefix}**　{fix_terms(r["title"], r["canon"])}{gt_tag}')
    lines.append('')
    p_ = PLACED.get(r['id'])
    loc_tag = f'四分 {p_["n"]:03d} 段{p_["seg"]}' if p_ else '四分所無'
    lines.append(f'<sub>{tag}　層級：{r.get("lv","")}　{loc_tag}　本稿位置：{esc(r.get("pos",""))}　出處：{r["canon"]} {r["unit"]}#{r["no"]}</sub>')
    lines.append('')
    # 差異
    diff = fix_terms(one_line(r.get('diff_full') or r.get('diff') or ''), r['canon'])
    if diff:
        _mate = SAME_TOPIC.get(r['id'])
        if _mate:
            _mno = D_NO.get(_mate) or S_NO.get(_mate)
            if _mno:
                diff += f'　〔同制另見 [`{_mno}`](#{_mno.lower()})〕'
        lines.append(f'**差異**：{diff}')
        lines.append('')
    if compact:
        # 簡版：錄原文與白話（折疊），不錄他部對照
        o = ORIG.get(f"{r['canon']}|{r['unit']}|{r['no']}", {})
        orig = clean_orig((o.get('orig') or '').strip())
        plain = fix_terms(clean_orig((o.get('plain') or '').strip()), r['canon'])
        if orig:
            body, clipped = clip_orig(orig, r)
            lines.append(f'**本稿原文**（{r["canon"]}）：')
            lines.append('')
            for ln in body.split('\n'):
                lines.append(f'> {ln}')
            if clipped:
                lines.append('>')
                lines.append(f'> 〔節引，原文共 {len(orig):,} 字；全文見 {r["canon"]} {r["unit"]}#{r["no"]}〕')
            lines.append('')
        if plain:
            lines.append('<details><summary>白話</summary>')
            lines.append('')
            for ln in plain.split('\n'):
                lines.append(ln)
                lines.append('')
            lines.append('</details>')
            lines.append('')
        ref4 = clean_ref(r.get('ref4', ''), '四分')
        if ref4:
            lines.append(f'- **四分對照**：{ref4}')
            lines.append('')
        # 補證（簡版亦須出，凡例八目之一）
        _xref = dedup_xref(one_line(r.get('xref', '')))
        if _xref:
            lines.append(f'- **補證**：{_xref}')
            lines.append('')
        return '\n'.join(lines)

    # 本稿原文
    o = ORIG.get(f"{r['canon']}|{r['unit']}|{r['no']}", {})
    orig = clean_orig((o.get('orig') or '').strip())
    plain = fix_terms(clean_orig((o.get('plain') or '').strip()), r['canon'])
    if orig:
        body, clipped = clip_orig(orig, r)
        lines.append(f'**本稿原文**（{r["canon"]}）：')
        lines.append('')
        for ln in body.split('\n'):
            lines.append(f'> {ln}')
        if clipped:
            lines.append(f'>')
            lines.append(f'> 〔節引，原文共 {len(orig):,} 字；全文見 {r["canon"]} {r["unit"]}#{r["no"]}〕')
        lines.append('')
    if plain:
        lines.append('<details><summary>白話</summary>')
        lines.append('')
        for ln in plain.split('\n'):
            lines.append(f'{ln}')
            lines.append('')
        lines.append('</details>')
        lines.append('')

    # 他部對照
    p_loc = PLACED.get(r['id'])
    ref4 = fix_ref4_loc(clean_ref(r.get('ref4', ''), '四分'), p_loc)
    ref5 = clean_ref(r.get('ref5', ''), '五分')
    ref10 = clean_ref(r.get('ref10', ''), '十誦')

    if r['canon'] == '五分':
        pairs = [('四分', ref4), ('十誦', ref10)]
    elif r['canon'] == '十誦':
        pairs = [('四分', ref4), ('五分', ref5)]
    else:  # 僧祇、根有
        pairs = [('四分', ref4), ('五分', ref5), ('十誦', ref10)]

    shown = False
    for name, ref in pairs:
        if ref and ref not in ('', '—'):
            lines.append(f'- **{name}對照**：{ref}')
            shown = True
    if shown:
        lines.append('')

    # 補證
    xref = dedup_xref(one_line(r.get('xref', '')))
    if xref:
        lines.append(f'- **補證**：{xref}')
        lines.append('')

    return '\n'.join(lines)


def render_gt_block(g, ids):
    """渲染一個 G/T 歸併組"""
    title, ev, handle = GT_INFO.get(g, ('', '', ''))
    kind = '同條' if g.startswith('G') else '同題異制'
    out = [f'<a id="gt-{g}"></a>', '', f'#### `{g}`　{title}', '',
           f'<sub>{kind}　證據：{ev}</sub>', '',
           f'**處理**：{handle}', '']
    for i in ids:
        r = ID2ROW.get(i)
        if not r:
            continue
        r = apply_errata(r)
        _ref = D_NO.get(i) or S_NO.get(i)
        _link = f'　[`{_ref}`](#{_ref.lower()})' if _ref else ''
        out.append(f'##### {r["canon"]}　{r["title"]}{_link}')
        out.append('')
        p_ = PLACED.get(r['id'])
        loc_tag = f'四分 {p_["n"]:03d} 段{p_["seg"]}' if p_ else '四分所無'
        out.append(f'<sub>〔{r["canon"]} {r["st"]}〕　{loc_tag}　本稿位置：{esc(r.get("pos",""))}　出處：{r["canon"]} {r["unit"]}#{r["no"]}</sub>')
        out.append('')
        diff = fix_terms(one_line(r.get('diff_full') or r.get('diff') or ''), r['canon'])
        if diff:
            out.append(f'**差異**：{diff}')
            out.append('')
        o = ORIG.get(f"{r['canon']}|{r['unit']}|{r['no']}", {})
        orig = clean_orig((o.get('orig') or '').strip())
        if orig:
            body, clipped = clip_orig(orig, r)
            out.append(f'**本稿原文**（{r["canon"]}）：')
            out.append('')
            for ln in body.split('\n'):
                out.append(f'> {ln}')
            if clipped:
                out.append('>')
                out.append(f'> 〔節引，原文共 {len(orig):,} 字；全文見 {r["canon"]} {r["unit"]}#{r["no"]}〕')
            out.append('')
        ref4 = clean_ref(r.get('ref4', ''), '四分')
        if ref4:
            out.append(f'- **四分對照**：{ref4}')
            out.append('')
    return '\n'.join(out)


# ---------- 卷首 ----------
def build_front():
    _er = [apply_errata(r) for r in rows]
    tot = len(_er)
    st_cnt = Counter(r['st'] for r in _er)
    canon_cnt = Counter(r['canon'] for r in _er)
    lv_cnt = Counter(r.get('lv', '') for r in _er)

    L = []
    L.append('# 五部律差異對照本')
    L.append('')
    L.append('> **以《四分律》為閱讀主線，一冊在手，遍知五部之異同。**')
    L.append('>')
    L.append('> 讀《四分律》至某篇某戒，翻至本書同篇，即見其餘四部於此處有何增、減、開、異；')
    L.append('> 讀畢全律，再覽第二部，即知四分律所未載而他部獨有者何事。')
    L.append('')
    L.append('---')
    L.append('')

    # 題解
    L.append('## 卷首　題解')
    L.append('')
    L.append('<a id="front1"></a>'); L.append(''); L.append('### 一、本書之為用')
    L.append('')
    L.append('五部律同出一源而分流五派，各持己誦，歷數百年而後寫定。其同者，戒條之大體也；'
             '其異者，判罪之輕重、開緣之寬狹、法數之多寡、羯磨之程序、緣起之人物結局也。'
             '昔人校律，多循「以一本為底，餘本互註」之法；本書則倒其軸——**以四分律為軸，餘四部為輪**。')
    L.append('')
    L.append('所以然者，讀律者恒自一部入手。入手既畢，所急者不在「我讀了什麼」，而在'
             '「我漏了什麼、我讀的這一句在別本作何解」。本書即應此問：')
    L.append('')
    L.append('- **按篇檢索**：讀至四分律某篇，翻至本書同篇，該處所有差異依段號排列，一覽可盡。')
    L.append('- **按部檢索**：欲知某部（如十誦）獨有何制，翻至第二部該部之節。')
    L.append('- **按組檢索**：同一制度兩部各記一次者，已歸併為 `G#`／`T#` 組，見第三部。')
    L.append('')
    L.append('<a id="front2"></a>'); L.append(''); L.append('### 二、五部律與部派')
    L.append('')
    L.append('| 律本 | 部派 | 卷數 | 譯者 | 年代 | 本書代號 |')
    L.append('|---|---|---:|---|---|---|')
    L.append('| 四分律 | 法藏部（曇無德部） | 60 | 佛陀耶舍、竺佛念 | 姚秦弘始十二年前後 | 四分 |')
    L.append('| 五分律 | 彌沙塞部（化地部） | 30 | 佛陀什、竺道生 | 劉宋景平元年 | 五分 |')
    L.append('| 十誦律 | 說一切有部（薩婆多部） | 61 | 弗若多羅、鳩摩羅什 | 姚秦弘始年間 | 十誦 |')
    L.append('| 摩訶僧祇律 | 大眾部 | 40 | 佛陀跋陀羅、法顯 | 東晉義熙十四年 | 僧祇 |')
    L.append('| 根本說一切有部毘奈耶 | 根本說一切有部 | 50 | 義淨 | 唐長安年間 | 根有 |')
    L.append('')
    L.append('> 五部之中，四分、五分屬上座系分別說部之流，十誦、根有同屬說一切有部（根有為其「根本」一支），'
             '僧祇屬大眾部。部派既異，則同一戒條之輕重、同一羯磨之程序，往往分途。')
    L.append('')
    L.append('> **底本**：五部原文據大正藏電子文本，編號依次為 T22 no. 1428、T22 no. 1421、'
             'T23 no. 1435、T22 no. 1425、T23 no. 1442。組字式（如 `[卄/告]`）與校記字形照錄，'
             '頁碼欄標記從略，以便閱讀。')
    L.append('')
    L.append('<a id="front3"></a>'); L.append(''); L.append('### 三、統計全貌')
    L.append('')
    L.append(f'本書收錄 **{tot:,}** 項差異，皆為各去重稿所保留、經五部對校而可指認者。')
    L.append('')
    L.append('| 主稿 | 項數 | A 同條增異 | B 同條開緣 | C 四分所無 | D 同條減略 |')
    L.append('|---|---:|---:|---:|---:|---:|')
    for c in ['五分', '十誦', '僧祇', '根有']:
        sub = [r for r in _er if r['canon'] == c]
        cc = Counter(r['st'] for r in sub)
        L.append(f'| {c} | {len(sub)} | {cc["A"]} | {cc["B"]} | {cc["C"]} | {cc["D"]} |')
    L.append(f'| **合計** | **{tot:,}** | **{st_cnt["A"]}** | **{st_cnt["B"]}** | **{st_cnt["C"]}** | **{st_cnt["D"]}** |')
    L.append('')
    L.append('> **項數不等於差異量**。各稿項數取決於底本規模與去重比例：底本大而與他部重合少者，'
             '保留比例高、項數亦多。四稿之去重比例如下，可與上表參看。')
    L.append('')
    L.append('| 主稿 | 底本字數 | 保留字數 | 保留比例 | 項數 |')
    L.append('|---|---:|---:|---:|---:|')
    _cnt_by_canon = Counter(r['canon'] for r in _er)
    L.append(f'| 五分 | 341,000 許 | 40,000 許 | 11.7% | {_cnt_by_canon["五分"]} |')
    L.append(f'| 十誦 | 658,969 | 161,403 | 24.5% | {_cnt_by_canon["十誦"]} |')
    L.append(f'| 僧祇 | 451,943 | 119,952 | 26.5% | {_cnt_by_canon["僧祇"]} |')
    L.append(f'| 根有 | 387,935 | 36,839 | 9.5% | {_cnt_by_canon["根有"]} |')
    L.append('')
    L.append('> 根有項數最少，非其差異最少，乃因其與十誦同屬有部、重合最多，可保留者僅 9.5%；'
             '僧祇比例最高，則因大眾部立場與上座系出入最大。')
    L.append('')
    L.append('| 層級 | 項數 |')
    L.append('|---|---:|')
    for lv in ['戒條', '制度', '法數', '事件']:
        L.append(f'| {lv} | {lv_cnt.get(lv,0)} |')
    L.append('')
    L.append('按四分律篇次歸位者 **{:,}** 項（第一部），四分律所無者 **{:,}** 項（第二部），'
             '二者合 **{:,}** 項，即全數歸位，無遺漏（歸位方法見附錄一）。'
             '其中 9 項因與他稿同一制度而併入第三部之 `G#`／`T#` 組，'
             '故第一部、第二部正文共見 **{:,}** 項。'.format(
                 len(PLACED), len(ABSENT), len(PLACED) + len(ABSENT),
                 len(PLACED) + len(by_canon_absent.get('五分', [])) + len(by_canon_absent.get('十誦', []))
                 + len(by_canon_absent.get('僧祇', [])) + len(by_canon_absent.get('根有', []))))
    L.append('')
    L.append('<a id="front4"></a>'); L.append(''); L.append('### 四、狀態代號')
    L.append('')
    L.append('| 代號 | 名目 | 釋義 |')
    L.append('|---|---|---|')
    L.append('| **A** | 同條增異 | 同一戒條或制度，本稿有他部所無之實質增異（判罪輕重、程序、法數、人物結局） |')
    L.append('| **B** | 同條開緣 | 同一戒條，本稿另立開緣（新增開許或新增限制） |')
    L.append('| **C** | 四分所無 | 四分律無此戒此制，而他部有之 |')
    L.append('| **D** | 同條減略 | 同一戒條，本稿較他部為略 |')
    L.append('')
    L.append('`G#` 為同條歸併組，`T#` 為同題異制組，詳第三部。')
    L.append('')
    L.append('<a id="front5"></a>'); L.append(''); L.append('### 五、凡例')
    L.append('')
    L.append('一、**編次**：第一部依《四分律》六十卷、七十五篇之次第。篇名與段號依四分律原檔'
             '（按篇切成七十五檔，自 000 至 074），段號為該篇內之自然段序，'
             '如「`026` 段12」即第 026 篇〈八波羅夷法〉第十二段。')
    L.append('')
    L.append('二、**篇旨與每項八目**：每篇之首標「篇旨」，述該篇在四分律中所載之戒目、制度或體例，'
             '俾讀者未讀其文先知其略。篇旨之下，每項八目：序號、標題（差異事由）、狀態與出處、'
             '差異說明、本稿原文、白話、他部對照、補證。'
             '序號 `D-` 屬第一部（按四分篇次），`S-` 屬第二部（按主稿）。白話以摺疊塊呈現，不佔篇幅。'
             '十誦稿原未譯白話，故十誦諸項無此目，非本書之闕。')
    L.append('')
    L.append('三、**引文**：本稿原文錄主稿（該項所屬之律）之文，四分對照錄四分律之文，他部對照錄該部之文，'
             '皆逐字迻錄，出自各稿 findings，已經程式回錨底本，逐句可覆核。'
             '引文過長者存其要，以「……」標省略；跨段者段前標段號。')
    L.append('')
    L.append('> 須辨者：「差異說明」中夾引之文，或為逐字，或為節引，或為概括（如列舉戒目時撮舉其要），'
             '不盡與原文相符；其逐字者以「本稿原文」及「對照」二目為準。')
    L.append('')
    L.append('四、**「遍查未見」**：四分對照作「遍查未見」者，謂該稿作者遍檢四分律而未得**此制**之對應，'
             '並附查詢詞以備覆核。此為文獻學斷言，非工作進度之闕漏。')
    L.append('')
    L.append('> 須辨者：查詢詞或單見於四分律他處，然不成此制，故仍判未見。'
             '如「稽首」二字四分律或有，而卷首偈頌之序則無；「壞色」四分律屢見，'
             '而受施白疊捽破壞色之制則無。讀者覆核時，當驗其**制**，不當只驗其**詞**。')
    L.append('')
    L.append('五、**出處**：`五分 vol07#1` 謂五分稿第七校勘單位第一項；'
             '原文全文見各稿去重合冊（《十誦律_去重》《五分律_去重白話》'
             '《摩訶僧祇律_去重白話》《根本說一切有部毘奈耶_去重白話》）。')
    L.append('')
    L.append('六、**不補造**：凡一稿未設對照欄者，本書不作推斷，於矩陣記「未比」。'
             '本書為對照本，非裁決本；兩存其說者，並列不強合。')
    L.append('')
    L.append('七、**項號與引用**：`D-0001` 至 `D-1456` 為第一部（按四分篇段），'
             '`S-0001` 至 `S-0659` 為第二部（按主稿），`G1`–`G7`／`T1`–`T3` 為第三部歸併組。'
             '項號全書唯一且連續，可徑引作「《五部律差異對照本》D-0450」。'
             '每項皆有錨點，`D-0450` 與 `[D-0450](#d-0450)` 相通。')
    L.append('')
    L.append('八、**與矩陣之關係**：本書為《五部律綜合異同矩陣》之閱讀本。矩陣重證據（五欄有無、逐列可查），'
             '本書重閱讀（按四分篇次、一處一覽）。二者同源，編號可互查：矩陣 `M-####`，本書 `D-####`／`S-####`。')
    L.append('')
    L.append('九、**稱謂**：各稿原以「本律」自稱、「兩律」「三律」稱其對校本。本書已將「差異說明」與'
             '「標題」中的「本律」「此律」逕換為具體律名（如「僧祇律」），免讀者回頭查主稿；'
             '惟「本稿原文」保留底本自稱，該處「本律」即指此項所屬之律，不另改。「兩律」「三律」'
             '仍存其舊，所指隨主稿而異，列表如下。凡此類語，皆就該項所屬之律立說，非就本書之五部立說。')
    L.append('')
    L.append('| 主稿 | 「兩律」所指 | 「三律」所指 | 出現次數 |')
    L.append('|---|---|---|---|')
    L.append('| 五分 | 四分、五分 | —（未用） | 兩律 31 |')
    L.append('| 十誦 | 四分、五分 | 四分、五分、十誦 | 兩律 528、三律 9 |')
    L.append('| 僧祇 | —（未用） | 四分、五分、十誦 | 三律 660 |')
    L.append('| 根有 | 四分、五分 | 四分、五分、十誦 | 兩律 1、三律 202 |')
    L.append('')
    L.append('> **參差之辨**：十誦稿之「三律」含本律（如「三律賊數各異：四分二賊、五分五賊、'
             '十誦三賊」），而「兩律」則否（如「兩律戒文皆無」，指四分、五分）；'
             '僧祇、根有之「三律」則為對校本，不含本律。此原稿用語之不一，'
             '讀者當按上下文自辨。')
    L.append('')
    L.append('十、**資料限制**：四分律自恣揵度之一未入庫（卷37末），此處以全庫檢索及他部對照為據；'
             '四分律尼律單提第一至八十六戒僅存戒條列表，緣起從缺。')
    L.append('')
    L.append('<a id="front6"></a>'); L.append(''); L.append('### 六、五部律罪名異譯對照')
    L.append('')
    L.append('同一罪階，五部譯名不同；同一譯名，五部所指亦未必盡同。讀他部之文，'
             '先識其名，乃可對照。下表所列異譯，皆見於本書引文，可據以互檢。')
    L.append('')
    L.append('| 罪階 | 四分 | 五分 | 十誦 | 僧祇 | 根有 |')
    L.append('|---|---|---|---|---|---|')
    L.append('| 極惡 | 波羅夷 | 波羅夷 | 波羅夷 | 波羅夷 | 波羅夷／**波羅市迦** |')
    L.append('| 次重 | 僧殘／僧伽婆尸沙 | 僧殘／僧伽婆尸沙 | 僧殘／僧伽婆尸沙 | 僧殘／僧伽婆尸沙 | 僧殘 |')
    L.append('| 捨財 | 尼薩耆波逸提／捨墮 | 尼薩耆波逸提／捨墮 | **尼薩耆波夜提** | **尼薩耆波夜提** | **尼薩耆波逸底迦**／捨墮 |')
    L.append('| 墮落 | 波逸提 | 波逸提 | **波夜提** | **波夜提** | **波逸底迦** |')
    L.append('| 提舍尼 | 提舍尼 | 提舍尼 | 提舍尼 | 提舍尼 | 提舍尼／**悔過法** |')
    L.append('| 眾學 | 式叉迦羅尼 | 眾學 | 眾學 | 眾學 | 眾學 |')
    L.append('| 滅諍 | 滅諍 | 滅諍 | 滅諍 | 滅諍 | 滅諍 |')
    L.append('| 輕罪 | 突吉羅 | 突吉羅 | 突吉羅 | **越毘尼** | **惡作** |')
    L.append('| 重罪未遂 | 偷蘭遮 | 偷蘭遮／**偷羅遮** | 偷蘭遮 | 偷蘭遮 | **窣吐羅底也** |')
    L.append('')
    L.append('> 三處最易誤讀：')
    L.append('>')
    L.append('> 一、**越毘尼**。僧祇律以此稱突吉羅，非「越過毘尼」之謂，乃其譯語。'
             '本書僧祇諸項每見「得越毘尼罪」，即四分律之突吉羅。')
    L.append('>')
    L.append('> 二、**惡作**。根有律以此稱突吉羅（義淨譯），與「惡說」相對——'
             '惡作為身口之過，惡說為語言之過，二者同階。')
    L.append('>')
    L.append('> 三、**窣吐羅底也**。根有律以此稱偷蘭遮，音譯之異，非別有罪名。')
    L.append('')
    L.append('> 又，五部同用「波羅夷」而判罪範圍有異者，如四分「人作非人想，偷蘭遮」'
             '而十誦判波羅夷，此非譯名之別，乃實質之異，詳見第一部諸項。')
    L.append('')
    L.append('<a id="front7"></a>'); L.append(''); L.append('### 七、讀法示例')
    L.append('')
    L.append('設讀四分律卷二十二「八波羅夷法」，欲知他部異同：')
    L.append('')
    _ids26 = [r['id'] for _s, r in by_seg.get(26, [])]
    if _ids26:
        _lo, _hi, _c26 = D_NO[_ids26[0]], D_NO[_ids26[-1]], len(_ids26)
        L.append(f'1. 查目錄，得「026　八波羅夷法」在卷二十二之首，計 {_c26} 項。')
        L.append('2. 先讀該篇「篇旨」，知此篇所載者何事；次讀「狀態」一行，知差異之構成。')
        L.append(f'3. 次見 `{_lo}` 至 `{_hi}`，依四分段號排列；段1、段3、段7……各有差異。')
    else:
        L.append('1. 查目錄，得「026　八波羅夷法」在卷二十二之首。')
        L.append('2. 翻至該篇，諸項依四分段號排列。')
    L.append('4. 每項先讀「差異」一句，知異在何處；再讀「四分對照」，知四分原文作何；'
             '終讀他部對照，知彼部作何。')
    L.append('5. 若該項標 `G#`／`T#`，則同一制度他部亦記一次，可翻第三部見兩稿全文並列。')
    L.append('6. 讀畢該篇，若欲知「四分律於此完全沒有什麼」，翻第二部相應主稿之節。')
    L.append('')
    L.append('---')
    L.append('')
    return '\n'.join(L)


# ---------- 目錄 ----------
def build_toc():
    L = ['## 目錄', '']
    L.append('### 卷首')
    L.append('')
    L.append('- [一、本書之為用](#front1)')
    L.append('- [二、五部律與部派](#front2)')
    L.append('- [三、統計全貌](#front3)')
    L.append('- [四、狀態代號](#front4)')
    L.append('- [五、凡例](#front5)')
    L.append('- [六、五部律罪名異譯對照](#front6)')
    L.append('- [七、讀法示例](#front7)')
    L.append('')
    L.append('### 第一部　四分律有對應處之差異')
    L.append('')
    for jname, segs, _f in JUAN_SEGS:
        L.append(f'**{jname}**')
        L.append('')
        for n in segs:
            if n in by_seg and by_seg[n]:
                t = ptitle(n)
                cnt = len(by_seg[n])
                L.append(f'- [{n:03d}　{t}](#{anchor(n)})　{cnt} 項')
            elif n in SEC_INTRO:
                L.append(f'- [{n:03d}　{ptitle(n)}](#{anchor(n)})　無差異')
        L.append('')
    L.append('### 第二部　四分律所無之制度')
    L.append('')
    for c in ['五分', '十誦', '僧祇', '根有']:
        cnt = len(by_canon_absent.get(c, []))
        L.append(f'- [{c}所增](#add{c})　{cnt} 項')
    L.append('')
    L.append('### 第三部　歸併組')
    L.append('')
    L.append('- [甲、同條歸併七組](#gt-g)')
    L.append('- [乙、同題異制三組](#gt-t)')
    L.append('')
    L.append('### 附錄')
    L.append('')
    L.append('- [一、歸位方法與覆核](#ap1)')
    L.append('- [二、分部統計](#ap2)')
    L.append('- [三、四分律篇目卷次對照](#ap3)')
    L.append('')
    L.append('---')
    L.append('')
    return '\n'.join(L)


# ---------- 第一部 ----------
def build_part1(seg_filter=None):
    L = []
    if seg_filter is None:
        L.append('## 第一部　四分律有對應處之差異')
        L.append('')
        L.append('> 依四分律七十五篇次第。每篇先標篇名、段數與差異項數，再依段號列項。')
        L.append('> 一項之內，先「差異」一句明其異，次「四分對照」錄四分原文，'
                 '終錄他部對照與補證。')
        L.append('')
    for jname, segs, fname in JUAN_SEGS:
        if seg_filter is not None and jname != seg_filter:
            continue
        if seg_filter is not None:
            # 分卷檔：加書名與導語
            L.insert(0, f'# 五部律差異對照本　{jname}')
            L.insert(1, '')
            L.insert(2, '> 本檔為《五部律差異對照本》第一部之' + jname + '部分，'
                         '依四分律篇次排列。卷首題解、目錄、第二部（四分所無）、'
                         '第三部（歸併組）及附錄見合冊 `五部律差異對照本.md`。')
            L.insert(3, '')
            L.insert(4, '---')
            L.insert(5, '')
        L.append(f'### {jname}')
        L.append('')
        L.append(f'<sub>四分律原檔：{fname.replace("原文.txt", "卷").replace("-", "–").replace(" 卷", "卷")}</sub>')
        L.append('')
        for n in segs:
            _has = bool(by_seg.get(n))
            if not _has and n not in SEC_INTRO:
                continue
            info = si[n]
            L.append(f'<a id="{anchor(n)}"></a>')
            L.append('')
            L.append(f'#### {n:03d}　{ptitle(n)}')
            L.append('')
            if n in SEC_INTRO:
                L.append(f'> **篇旨**：{SEC_INTRO[n]}')
                L.append('')
            extra = '（含受戒、說戒、安居、自恣四揵度，段1–330）' if n == 38 else ''
            _cnt_n = len(by_seg.get(n, []))
            if _cnt_n:
                L.append(f'<sub>本篇 {info["paras"]} 段{extra}，差異 {_cnt_n} 項</sub>')
            else:
                L.append(f'<sub>本篇 {info["paras"]} 段{extra}，**無差異項**</sub>')
            L.append('')
            if not _cnt_n:
                L.append('> 本篇諸部皆同，無可指認之實質差異，故不列項。')
                L.append('')
                continue
            # 概覽：狀態分布與主稿分布
            _rows_n = [apply_errata(r) for _s, r in by_seg.get(n, [])]
            stc = Counter(r['st'] for r in _rows_n)
            cnc = Counter(r['canon'] for r in _rows_n)
            st_parts = '・'.join(f'{k} {stc[k]}' for k in ['A', 'B', 'C', 'D'] if stc.get(k))
            cn_parts = '、'.join(f'{c} {cnc[c]}' for c in ['十誦', '五分', '僧祇', '根有'] if cnc.get(c))
            L.append(f'<sub>狀態：{st_parts}　｜　主稿：{cn_parts}</sub>')
            L.append('')
            # 本篇目錄（項數多者，便於篇內跳轉）
            _items = by_seg.get(n, [])
            if len(_items) >= 15:
                L.append(f'<details class="art-toc"><summary>本篇目錄（{len(_items)} 項）</summary>')
                L.append('')
                for _s2, _r2 in _items:
                    _no2 = D_NO[_r2['id']]
                    L.append(f'- [`{_no2}`](#{_no2.lower()})　{esc(_r2["title"][:38])}')
                L.append('')
                L.append('</details>')
                L.append('')
            _jies = JIE.get(n)
            if _jies:
                for (_s1, _s2, _cn, _nm) in _jies:
                    _grp = [(s, r) for s, r in by_seg[n] if _s1 <= s <= _s2]
                    if not _grp:
                        continue
                    _h = f'第{_cn}戒' + (f'　{_nm}' if _nm else '')
                    L.append(f'##### {_h}　（段{_s1}–{_s2}）')
                    L.append('')
                    for seg, r in _grp:
                        L.append(render_item(r, D_NO[r['id']]))
                _rest = [(s, r) for s, r in by_seg[n] if s > _jies[-1][1]]
                if _rest:
                    L.append('##### 其餘')
                    L.append('')
                    for seg, r in _rest:
                        L.append(render_item(r, D_NO[r['id']]))
            else:
                for seg, r in by_seg[n]:
                    L.append(render_item(r, D_NO[r['id']]))
            L.append('')
    return '\n'.join(L)


# ---------- 第二部 ----------
def build_part2():
    L = []
    L.append('## 第二部　四分律所無之制度')
    L.append('')
    L.append('> 此部所收，皆四分律遍查未見而他部有之者。四分律既無對應之處，'
             '故不能按篇次歸位，改依主稿分節。')
    L.append('>')
    L.append('> 讀法：欲知某部於四分律之外別有何制，逕翻該部之節。各節內依層級分組，'
             '組內依原稿項次排列。')
    L.append('>')
    L.append('> **層級之限**：戒條、制度、法數、事件四目，依原稿標題與差異說明判定，'
             '界限本有交叉——如同一緣起既繫於戒條，亦可歸於事件；同一法數既為制度之目，'
             '亦可獨立成類。此分組僅供瀏覽，非嚴格分類，尋項時宜兼顧相鄰諸組。')
    L.append('')
    L.append('| 主稿 | 項數 | 說明 |')
    L.append('|---|---:|---|')
    desc = {
        '五分': '五分律獨有或增出之戒條、制度。五分稿原以四分為主要對校，此類多為四分九十單提、百眾學法所無。',
        '十誦': '十誦律獨有或增出者，數量最多。十誦與四分同屬廣律，結構相近而細節繁密，故增異亦夥。',
        '僧祇': '僧祇律獨有者。僧祇屬大眾部，律制自成體系，與上座系諸律距離最遠。',
        '根有': '根有律獨有者。根有與十誦同屬有部，與十誦重合最多，故此類最少。',
    }
    for c in ['五分', '十誦', '僧祇', '根有']:
        L.append(f'| {c} | {len(by_canon_absent.get(c, []))} | {desc[c]} |')
    n_merged = sum(1 for i in loc['absent'] if i in gt_secondary)
    L.append('')
    L.append(f'> 表列共 {sum(len(v) for v in by_canon_absent.values())} 項，另有 {n_merged} 項已併入第三部之 `G#`／`T#` 組'
             f'（同組他稿重出者，不於此重列），合 {len(ABSENT)} 項，即四分律所無之全數。')
    L.append('')
    for c in ['五分', '十誦', '僧祇', '根有']:
        sub = by_canon_absent.get(c, [])
        if not sub:
            continue
        L.append(f'<a id="add{c}"></a>')
        L.append('')
        L.append(f'### {c}所增')
        L.append('')
        _cc = Counter(r.get('lv', '') for r in sub)
        _lv_s = '、'.join(f'{k} {_cc[k]}' for k in ['戒條', '制度', '法數', '事件'] if _cc.get(k))
        _fn = FULLNAME.get(c, c)
        L.append(f'> **節旨**：此節 {len(sub)} 項，皆{_fn}於四分律之外別有之制。'
                 f'內含：{_lv_s}。')
        L.append('')
        L.append(f'<sub>共 {len(sub)} 項</sub>')
        L.append('')
        # 按層級分組
        bylv = defaultdict(list)
        for r in sub:
            bylv[r.get('lv', '其他')].append(r)
        for lv in ['戒條', '制度', '法數', '事件', '其他']:
            if lv not in bylv:
                continue
            L.append(f'#### {c}·{lv}（{len(bylv[lv])} 項）')
            L.append('')
            for r in bylv[lv]:
                L.append(render_item(r, S_NO[r['id']], compact=True))
        L.append('')
    return '\n'.join(L)


# ---------- 第三部 ----------
def build_part3():
    L = []
    L.append('## 第三部　歸併組')
    L.append('')
    L.append('> 同一制度，兩稿各記一次者，合為一組。矩陣中該二列並列同一 `G#`／`T#`。'
             '本部所收十組，皆經逐條回讀確認，非機械配對。')
    L.append('')
    L.append('<a id="gt-g"></a>')
    L.append('')
    L.append('### 甲、同條歸併七組')
    L.append('')
    L.append('兩稿各記一次同一戒或同一制度者。')
    L.append('')
    for g in ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7']:
        L.append(render_gt_block(g, GT[g]))
        L.append('')
    L.append('<a id="gt-t"></a>')
    L.append('')
    L.append('### 乙、同題異制三組')
    L.append('')
    L.append('主題相近而規制不同，並存互註，不減項。')
    L.append('')
    for g in ['T1', 'T2', 'T3']:
        L.append(render_gt_block(g, GT[g]))
        L.append('')
    return '\n'.join(L)


# ---------- 附錄 ----------
def build_appendix():
    L = []
    L.append('## 附錄')
    L.append('')

    # 一、歸位說明
    L.append('<a id="ap1"></a>')
    L.append('')
    L.append('### 附錄一　歸位方法與覆核')
    L.append('')
    L.append('本書第一部按四分律篇段編次，其歸位之法有六，依可靠程度為序：')
    L.append('')
    L.append('| 法 | 依據 | 項數 | 說明 |')
    L.append('|---|---|---:|---|')
    how_name = {
        'file': '對照欄明記檔名與段號',
        'name_seg': '對照欄明記篇名與段號',
        'name_dash': '對照欄明記篇名與段號',
        'bare': '對照欄明記篇號與段號',
        'dash': '對照欄明記篇號與段號',
        'dot': '對照欄明記篇號與段號',
        'num_seg': '對照欄明記篇號與段號',
        'sifen_prefix': '對照欄明記篇號與段號',
        'loose': '對照欄明記篇號與段號',
        'chunk': '受戒揵度分塊檔，歸 038 篇',
        'file_only': '對照欄僅記篇名，段號從缺',
        'quote': '引文檢索（以「」內引文回四分原文定位）',
        'force': '語義判定（引文未入庫者）',
    }
    cnt_how = Counter(p['how'] for p in loc['placed'])
    for how in ['file', 'name_seg', 'name_dash', 'bare', 'dash', 'dot', 'num_seg', 'sifen_prefix', 'loose',
                'chunk', 'file_only', 'quote', 'force']:
        if cnt_how.get(how):
            L.append(f'| `{how}` | {how_name.get(how,"")} | {cnt_how[how]} | — |')
    L.append(f'| | **合計** | **{len(loc["placed"])}** | |')
    L.append('')
    if UNPLACED:
        L.append(f'#### 未能歸位者（{len(UNPLACED)} 項）')
        L.append('')
        L.append('| 編號 | 主稿 | 狀態 | 標題 | 四分對照 |')
        L.append('|---|---|---|---|---|')
        for i in UNPLACED:
            r = ID2ROW[i]
            L.append(f'| {i} | {r["canon"]} | {r["st"]} | {esc(r["title"])} | {esc(clean_ref(r.get("ref4",""), '四分')[:90])} |')
        L.append('')
    else:
        L.append('> 全部 1,455 項皆已歸位，無遺漏。其中 `file_only` 十八項僅知篇而不知段，'
                 '依篇次列於該篇之首；`quote` 十二項以引文回原文定位，已逐項覆核；'
                 '`force` 三項引文未入庫（四分律卷37自恣揵度之一、妄語戒名相），依語義定其篇。')
        L.append('')
    L.append('**覆核之法**：任取一項，以其「四分對照」所引之文，回四分律原檔同篇同段比對，字句當合。'
             '若不合，則歸位有誤，可據段號修正。')
    L.append('')

    # 二、統計
    L.append('<a id="ap2"></a>')
    L.append('')
    L.append('### 附錄二　分部統計')
    L.append('')
    L.append('#### 按四分律篇次')
    L.append('')
    L.append('| 篇 | 篇名 | 段數 | 差異項 |')
    L.append('|---|---|---:|---:|')
    for n in sorted(si):
        cnt = len(by_seg.get(n, []))
        L.append(f'| {n:03d} | {ptitle(n)} | {si[n]["paras"]} | {cnt} |')
    L.append('')
    tot_seg = sum(len(v) for v in by_seg.values())
    _n_with = len([n for n in by_seg if by_seg[n]])
    _n_all = len([n for n in si if n in sum([s2 for _j, s2, _f in JUAN_SEGS], [])])
    _no = [n for n in si if n in sum([s2 for _j, s2, _f in JUAN_SEGS], []) and not by_seg.get(n)]
    _tail = (f'；其中 { "、".join(f"{n:03d}" for n in _no) } 諸部皆同，無差異項'
             if _no else '')
    L.append(f'**合計**：{_n_all} 篇，{tot_seg} 項；有差異者 {_n_with} 篇{_tail}。')
    L.append('')

    # 三、卷次對照
    L.append('<a id="ap3"></a>')
    L.append('')
    # 差異密度排行
    L.append('#### 差異密度：每百段之項數')
    L.append('')
    L.append('<sub>密度高者，非必差異大，乃該篇段數少而差異集中。讀者可據此優先細讀。</sub>')
    L.append('')
    dens = []
    for n in sorted(si):
        if n == 0 or not by_seg.get(n):
            continue
        d = len(by_seg[n]) / si[n]['paras'] * 100
        dens.append((d, n, len(by_seg[n]), si[n]['paras']))
    dens.sort(reverse=True)
    L.append('| 序 | 篇 | 篇名 | 項數 | 段數 | 每百段 |')
    L.append('|---:|---|---|---:|---:|---:|')
    for i, (d, n, cnt, paras) in enumerate(dens[:15], 1):
        L.append(f'| {i} | {n:03d} | {ptitle(n)} | {cnt} | {paras} | {d:.1f} |')
    L.append('')
    _tot_paras = sum(si[n]['paras'] for n in by_seg)
    L.append(f'<sub>全書平均：{len(PLACED) / _tot_paras * 100:.1f} 項／百段'
             f'（{len(PLACED):,} 項 ÷ {_tot_paras:,} 段）。</sub>')
    L.append('')

    # 第二部二維分布
    L.append('#### 四分所無：主稿 × 層級')
    L.append('')
    L.append('| 主稿 | 戒條 | 制度 | 法數 | 事件 | 合計 |')
    L.append('|---|---:|---:|---:|---:|---:|')
    for c in ['五分', '十誦', '僧祇', '根有']:
        sub = by_canon_absent.get(c, [])
        cc = Counter(r.get('lv', '') for r in sub)
        L.append(f'| {c} | {cc.get("戒條",0)} | {cc.get("制度",0)} | {cc.get("法數",0)} | {cc.get("事件",0)} | {len(sub)} |')
    allsub = [r for c in ['五分', '十誦', '僧祇', '根有'] for r in by_canon_absent.get(c, [])]
    ac = Counter(r.get('lv', '') for r in allsub)
    L.append(f'| **合計** | **{ac.get("戒條",0)}** | **{ac.get("制度",0)}** | **{ac.get("法數",0)}** | **{ac.get("事件",0)}** | **{len(allsub)}** |')
    L.append('')
    L.append('> 讀法：戒條一欄多者，該部於四分律之外別有戒目；制度、法數多者，'
             '其異在羯磨程序與名相組織，非別立新戒。')
    L.append('')

    L.append('### 附錄三　四分律篇目卷次對照')
    L.append('')
    L.append('| 卷次 | 原檔 | 篇號範圍 | 篇數 |')
    L.append('|---|---|---|---:|')
    for jname, segs, fname in JUAN_SEGS:
        _fn = fname.replace(' ', '')
        _rng = f'{segs[0]:03d}' if len(segs) == 1 else f'{segs[0]:03d}–{segs[-1]:03d}'
        L.append(f'| {jname} | `{_fn}` | {_rng} | {len(segs)} |')
    L.append('')
    L.append('---')
    L.append('')
    L.append('*本書據《五部律綜合異同矩陣》2,124 項、四分律七十五篇索引及歸位表機械生成，'
             'G/T 十組自矩陣正文提取。凡引文皆逐字迻錄自各稿 findings，可回底本覆核。*')
    L.append('')
    return '\n'.join(L)


# ---------- 輸出 ----------
def main():
    front = build_front()
    toc = build_toc()

    parts = {}
    parts['卷一至卷十'] = build_part1('卷一至卷十')
    parts['卷十一至卷二十一'] = build_part1('卷十一至卷二十一')
    parts['卷二十二至卷三十'] = build_part1('卷二十二至卷三十')
    parts['卷三十一至卷三十七'] = build_part1('卷三十一至卷三十七')
    parts['卷三十八至卷四十九'] = build_part1('卷三十八至卷四十九')
    parts['卷五十至卷六十'] = build_part1('卷五十至卷六十')

    part2 = build_part2()
    part3 = build_part3()
    appendix = build_appendix()

    # 合冊
    full = '\n'.join([front, toc, part2, part3, appendix])
    # 第一部插在目錄之後
    p1 = build_part1(None)
    full = '\n'.join([front, toc, p1, part2, part3, appendix])

    out_full = os.path.join(OUT, '五部律差異對照本.md')
    open(out_full, 'w', encoding='utf-8').write(full)
    print(f'合冊：{out_full}　{len(full):,} 字')

    # 分卷
    for jname, txt in parts.items():
        out = os.path.join(OUT, f'五部律差異對照本_{jname}.md')
        open(out, 'w', encoding='utf-8').write(txt)
        print(f'  {jname}：{len(txt):,} 字')

    # 第二、三部 + 附錄另存
    out2 = os.path.join(OUT, '五部律差異對照本_四分所無與歸併組.md')
    open(out2, 'w', encoding='utf-8').write('\n'.join([part2, part3, appendix]))
    print(f'  四分所無與歸併組：{len(part2)+len(part3)+len(appendix):,} 字')


if __name__ == '__main__':
    main()
