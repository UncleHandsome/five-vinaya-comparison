# -*- coding: utf-8 -*-
"""Render the deduplicated bilingual edition from _work/assemble_mk.py output.

Usage:  python write_mk.py            (摩訶僧祇律)
        MK_CANON=genben python write_mk.py   (根本說一切有部毘奈耶)
Reads mk_assemble_meta.json plus the findings themselves via assemble_mk's
parser (imported by exec) so quotes stay re-anchored, and writes:
  合冊 / 分冊 / 獨有敘事 / README
"""
import os, re, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

CANON = os.environ.get('MK_CANON', 'sengqi')

C = {
    'sengqi': {
        'name': '摩訶僧祇律',
        'folder': '摩訶僧祇律_去重白話',
        'src_folder': '摩訶僧祇律',
        'units': 'mk_units.json',
        'base_dir': 'sengqi',
        'src': 'findings_mk',
        'n_vol': 40,
        'sub': '大衆部律',
        'trans': '東晉佛陀跋陀羅譯、法顯記',
        'books': [(1, 10), (11, 20), (21, 30), (31, 40)],
        'book_names': ['卷一至卷十', '卷十一至卷二十', '卷二十一至卷三十', '卷三十一至卷四十'],
        'school_note': '四律分屬不同部派：本律屬大眾部，對校三律則皆上座系（法藏、化地、說一切有部）。'
                       '譯語、詳略、次第本有差異，故不以字句異同為去取，而以「戒條／制度／程序／事件／法數清單」為單位。',
        'cmp_why': '以其部派立場與上座系出入較大、可保留之實質增異較多故也',
        'limit1': '1. 本資料夾《四分律》尼律單提法第一至八十六戒僅存戒條列表，緣起從缺，'
                  '此部分以戒條有無與內容異同為準，不以緣起有無判為本律獨有。',
        'limit4': '本律之犍度資料散見於雜誦跋渠，與三律揵度未必一一同次，比對以內容為準，容有漏比；'
                  '凡「遍查未見」皆列查詢詞，可據工作檔覆核。',
    },
    'genben': {
        'name': '根本說一切有部毘奈耶',
        'folder': '根本說一切有部毘奈耶_去重白話',
        'src_folder': '根本說一切有部毗奈耶',
        'units': 'gu_units.json',
        'base_dir': 'genben',
        'src': 'findings_gu',
        'n_vol': 50,
        'sub': '說一切有部律',
        'trans': '唐義淨譯',
        'books': [(1, 10), (11, 20), (21, 35), (36, 50)],
        'book_names': ['卷一至卷十', '卷十一至卷二十', '卷二十一至卷三十五', '卷三十六至卷五十'],
        'school_note': '本律與《十誦律》同屬說一切有部，《四分律》《五分律》則屬法藏部、化地部。'
                       '同部系之重合最易誤判為本律獨有，故凡與《十誦》相應者，優先判為同部詳略而刪略；'
                       '去取以「戒條／制度／程序／事件／法數清單」為單位，不以字句異同為準。',
        'cmp_why': '以本律與《十誦》同屬有部、重合最多，可保留之實質增異最少故也',
        'limit1': '1. 本書只校《經分別》五十卷之苾芻諸學處，未及苾芻尼律；'
                  '對校諸律中亦有僅存戒條列表而緣起從缺之篇（如《四分律》尼律單提法第一至八十六戒），'
                  '此類篇目不引為本書有無之據。',
        'limit4': '本律與《十誦律》同屬有部，二律重合處最易誤判為獨有，故以《十誦》為第一覆核對象；'
                  '凡「遍查未見」皆列查詢詞，可據工作檔覆核。',
    },
}[CANON]

NM = C['name']
OUT = os.environ.get('MK_OUT') or os.path.join(ROOT, C['folder'])
os.makedirs(OUT, exist_ok=True)
UNITS = json.load(open(os.path.join(W, C['units']), encoding='utf-8'))
UTITLE = {u['unit']: u['title'] for u in UNITS}
UVOLS = {u['unit']: u['vols'] for u in UNITS}
meta = json.load(open(os.environ.get('MK_META') or os.path.join(W, 'mk_assemble_meta.json'), encoding='utf-8'))
S = {s['unit']: s for s in meta['stats']}
units_out = json.load(open(os.environ.get('MK_UOUT') or os.path.join(W, 'mk_units_out.json'), encoding='utf-8'))

# paragraph counts of the base text, for the coverage audit
NPARA = {}
for v in range(1, C['n_vol'] + 1):
    p = os.path.join(W, C['base_dir'], 'vol%02d.txt' % v)
    if os.path.exists(p):
        NPARA[v] = max([int(l.split('\t', 1)[0]) for l in open(p, encoding='utf-8')] or [0])


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def nums(s):
    """Paragraph numbers mentioned in a pointer string such as '段26–29、34'."""
    out = set()
    for a, b in re.findall(r'(\d{1,3})\s*[～~－–-]\s*(\d{1,3})', s or ''):
        if 0 < int(a) <= int(b) < 500:
            out.update(range(int(a), int(b) + 1))
    for a in re.findall(r'(?<![\d～~－–-])(\d{1,3})(?![\d～~－–-])', s or ''):
        if 0 < int(a) < 500:
            out.add(int(a))
    return out


def refind(unit):
    """Original findings text for a unit, or None."""
    p = os.path.join(W, C['src'], unit + '.md')
    return open(p, encoding='utf-8').read() if os.path.exists(p) else None


def sections_of(text):
    pos = [(m.start(), m.group(1)) for m in re.finditer(r'^## (.*)$', text, re.M)]
    sec = {}
    for i, (p, name) in enumerate(pos):
        end = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        sec[name.strip()] = text[p:end]
    return sec


def pointers(unit):
    """Paragraph numbers cited in 位置 fields and 刪除表 first column."""
    text = refind(unit)
    if not text:
        return set()
    sec = sections_of(text)
    got = set()
    for m in re.finditer(r'^-\s*位置[：:](.*)$', sec.get('保留項', '') + sec.get('敘事抽取', ''), re.M):
        got |= nums(m.group(1))
    d = ''
    for _k in ('刪除項（彙總）', '刪除項（匯總）', '刪除項'):
        if _k in sec:
            d = sec[_k]
            break
    else:
        for _k in sec:
            if _k.startswith('刪除項'):
                d = sec[_k]
                break
    for ln in d.split('\n'):
        ln = ln.strip()
        if ln.startswith('|'):
            cells = [c.strip() for c in ln.strip('|').split('|')]
            if cells and not set(cells[0]) <= set('-: '):
                got |= nums(cells[0])
        else:
            got |= nums(ln)
    return got


def unit_block(key):
    u = units_out[key]
    s = S[key]
    vols = u['vols']
    vlab = '卷{}'.format('、卷'.join(str(v) for v in vols))
    out = ['<a id="{}"></a>'.format(key),
           '## {}　{}\n'.format(vlab, u['title']),
           '> 底本 %s 字，本編保留 %s 字（%.1f%%），保留 %d 項；另抽取獨有敘事 %d 項（見另檔）。餘與《四分》《五分》《十誦》文意重複，刪略理由見附錄一。\n' % (
               format(s['src'], ','), format(s['kept'], ','), s['ratio'] * 100, s['items'], s['narr'])]
    for it in u['items']:
        out.append(it.strip() + '\n')
    return '\n'.join(out)


def vol_of(key):
    return UVOLS[key][0]


# ---------------------------------------------------------------- statistics
def stat_rows():
    rows = []
    for u in UNITS:
        k = u['unit']
        if k not in S:
            continue
        s = S[k]
        vlab = '、'.join(str(v) for v in u['vols'])
        rows.append((vlab, u['title'], s['src'], s['kept'], s['ratio'], s['items'], s['narr']))
    return rows


def stat_table(rows, cap):
    t = ['| 卷 | 篇目 | 底本字數 | 保留字數 | 比例 | 保留項 | 敘事抽取 |',
         '|---:|---|---:|---:|---:|---:|---:|']
    for r in rows:
        t.append('| {} | {} | {} | {} | {:.1f}% | {} | {} |'.format(
            r[0], r[1], format(r[2], ','), format(r[3], ','), r[4] * 100, r[5], r[6]))
    ts = sum(r[2] for r in rows)
    tk = sum(r[3] for r in rows)
    ti = sum(r[5] for r in rows)
    tn = sum(r[6] for r in rows)
    t.append('| **{}** | {} | **{}** | **{}** | **{:.1f}%** | **{}** | **{}** |'.format(
        '合計', cap, format(ts, ','), format(tk, ','), (tk / ts * 100) if ts else 0, ti, tn))
    return t, ts, tk, ti, tn


TOT = {v: sum(len(norm(t)) for t in
              (l.rstrip('\n').split('\t', 1)[1] for l in
               open(os.path.join(W, C['base_dir'], 'vol%02d.txt' % v), encoding='utf-8')))
       for v in range(1, C['n_vol'] + 1)}

# --------------------------------------------------------------------- head
rows = stat_rows()
sub_tbl, ts, tk, ti, tn = stat_table(rows, '{} 單位（{} 卷）'.format(len(rows), sum(len(u['vols']) for u in UNITS)))
base_total = sum(TOT.values())
pct = tk / base_total * 100 if base_total else 0
REFS = [('《五分律去重白話》', 11.7), ('《十誦律去重》', 24.5)]


def cmp_sentence(pct, why):
    """比較句須由實算之比例生成，不可寫死（写死者會因比例越界而虛報）。"""
    lo = [n for n, v in REFS if pct > v]
    hi = [n for n, v in REFS if pct <= v]
    pair = '與'.join('%s%g％' % (n, v) for n, v in REFS)
    if not lo:
        head = '低於%s' % pair
    elif not hi:
        head = '高於%s' % pair
    else:
        near = min(REFS, key=lambda t: abs(t[1] - pct))[0]
        head = '介於%s之間，而與%s尤近' % (pair, near)
    return '%s，%s' % (head, why)


cmp_txt = cmp_sentence(pct, C['cmp_why'])

head = []
head.append('# {}去重白話\n'.format(NM))
head.append('以《{nm}》（{sub}，{tr}）為底本，以《四分律》（法藏部）、《五分律》（彌沙塞部）、《十誦律》（薩婆多部）三部上座系律為對校本；凡與三律文意重複者刪略，僅保留本律獨有或具實質增異之內容，並譯為現代繁體中文。\n'.format(
    nm=NM, sub=C['sub'], tr=C['trans']))
head.append('## 凡例\n')
head += [
    '一、底本：《{}》{}卷。據本資料夾 `{}/` 原文，工作檔 `_work/{}/vol01–vol{}.txt`，每卷依原段落編號（段N），引文標「卷N·段M」以便覆核。\n'.format(
        NM, C['n_vol'], C['src_folder'], C['base_dir'], C['n_vol']),
    '二、對校本：《四分律》六十卷、《五分律》三十卷、《十誦律》六十一卷，工作檔各在 `_work/sifen/`、`_work/wufen/`、`_work/shisong/`。' + C['school_note'] + '\n',
    '三、判重口徑：\n1. 三律中任一律有同一戒、同一制度、同一事件、同一法數，且內容實質相同者，視為重複，刪除。\n2. 三律俱無，或同一戒／同一事件中有可指認之實質增異者（判罪輕重、程序羯磨、法數多寡、人物地點數量結局之異，或別具一段獨立情節），保留其增異部分。\n3. 僅屬譯語、詳略、修辭、次第不同，或名相異稱而範疇相當者，不保留。\n4. 每項須能以一話說清差異；界限難定者不強入正文，列於附錄二「存疑」。\n',
    '四、保留比例：底本全書 {bt} 字，本稿保留 {k} 字，約 {p}％（另有獨有敘事 {n} 項抽入另檔，不計）。本稿比例{cmp}。各單位比例見下表；未保留者並非全無價值，而是與三律大體相應，其理由逐單位列於附錄一。\n'.format(
        bt=format(base_total, ','), k=format(tk, ','), p=round(pct, 1), n=tn, cmp=cmp_txt),
    '五、編次：仍依底本卷次。每單位（一卷或相鄰二卷）先標篇目與統計，再列保留項。每項含「位置」「四分律對照」「五分律對照」「十誦律對照」「差異說明」「原文」「白話」七目。原文皆逐字迻錄，並經程式逐句回錨底本，故引文必可對上；段號缺口標「（中略：段X～Y）」，只取一段之部分者為節引。\n',
    '六、本生、譬喻、長篇敘事：不關斷罪要素之故事，即使三律全無，亦不混入正文，一律抽入另檔《{}_去重白話_獨有敘事.md》，記其卷段指針與要旨；原文六百字以下者併錄全文及白話，長篇之原文亦併載該檔（未譯）——或為校勘者逐字抄錄經組稿程式逐句回錨者，或為 `_work/extract_narr.py` 依『位置』段區間自底本整段抽出者；兩途引文俱經 `_work/qc_narr.py` 於產物上逐行覆核，以備另行取用。\n'.format(NM),
    '七、術語：白話中波羅夷、僧殘、波夜提、偷蘭遮、羯磨、布薩、自恣、安居等名相仍其舊，首次出現以括號簡註；人名、地名、職名照原文。全文用繁體。\n',
    '八、資料限制：\n' + C['limit1'] + '\n2. 《四分律》自恣揵度之一未收入本資料夾。\n3. 《十誦律》卷八段百二十至百四十五與段八十至百六內部重出，覆核時須注意。\n4. ' + C['limit4'] + '\n',
]
head.append('## 全書統計\n')
head += sub_tbl
head.append('\n> 字數以中文字計，不含標點、段號與空白。保留字數指本稿引文之字數；同一段分段引用僅計一次。\n')
head.append('## 目錄\n')
for u in UNITS:
    if u['unit'] in S:
        vlab = '、'.join(str(v) for v in u['vols'])
        head.append('- [卷{}　{}](#{})（{} 項）'.format(vlab, u['title'], u['unit'], S[u['unit']]['items']))
head += ['- [附錄一：刪略總表](#app1)', '- [附錄二：存疑總表](#app2)',
         '- [附錄三：工作方法與資料限制](#app3)',
         '- 另檔：《{}_去重白話_獨有敘事.md》（三律全無之本生、譬喻、長篇敘事）\n'.format(NM)]

# --------------------------------------------------------------------- body
body = []
n = 0
for u in UNITS:
    k = u['unit']
    if k not in units_out:
        continue
    n += 1
    if n > 1:
        body.append('\n---\n')
    body.append(unit_block(k))
main = '\n'.join(head) + '\n' + '\n'.join(body)

# ---------------------------------------------------------------- appendices
app = ['\n---\n', '<a id="app1"></a>', '# 附錄一：刪略總表\n',
       '逐單位列出未保留之段落及其三律對應。「遍查未見」指已檢索該律全庫未得對應。此表為刪略之審計紀錄，非閱讀正文。\n']
for u in UNITS:
    k = u['unit']
    if k not in units_out or not units_out[k]['deletion']:
        continue
    app.append('\n## 卷{}\u3000{}\n'.format('、'.join(str(v) for v in u['vols']), u['title']))
    app.append(units_out[k]['deletion'] + '\n')
app += ['\n---\n', '<a id="app2"></a>', '# 附錄二：存疑總表\n',
        '以下各條界限難定，暫從刪略，另記待裁。\n']
for u in UNITS:
    k = u['unit']
    if k in units_out and units_out[k]['doubts']:
        app.append('\n## 卷{}\u3000{}\n'.format('、'.join(str(v) for v in u['vols']), u['title']))
        app.append(units_out[k]['doubts'] + '\n')
app.append('\n---\n<a id="app3"></a>\n# 附錄三：工作方法與資料限制\n')
app.append('''
## 一、流程

1. 將《{nm}》{nv} 卷切分、編號；《四分律》切篇（七十五檔），《五分律》切三十卷，《十誦律》切六十一卷，各依原文段落標號，以便對照與回錨。
2. 以一卷或相鄰二卷為一單位，先按「戒條／制度／事件」與三律逐一對齊（四律次第多不相應，一按內容對齊），再逐段判定重複與否。
3. 每項須能以一話說清與三律之實質差異；不能者歸入刪略或存疑。
4. 引文自工作檔逐字摘錄，再由組稿程式逐句回錨底本，凡無法對上者一律不收；跨段引用標「（中略：段X～Y）」。
5. 白話逐句對應原文，不增不減；術語保留，人名、地名照原文。
6. 不關斷罪要素之本生、譬喻、長篇敘事，三律全無者抽入另檔，記其指針與要旨；長篇之原文再依『位置』段區間自底本逐字抽出，整段錄出，不作節略。

## 二、校驗

- 引文逐字：以程式比對，本稿每一句引文均可在底本工作檔中依序尋得；未能回錨者另記清單，回查後或改或刪。
- 段落覆蓋：各單位之保留項「位置」與刪除表合併後，覆核該單位全部段號有歸屬。
- 形制齊備：每一保留項皆具「位置／四分律對照／五分律對照／十誦律對照／差異說明／原文／白話」七目，編號連貫。
- 簡化字：以高置信簡形表掃描全稿，未發現簡化字（「云、制、只、尸、斗、服、面、里、干、于、卻、宁、准、注、脚、角、污、烟、虫、猪、踊、揵、攀、搬、擿、愍、沓、刮」等兩律共用之形不列入，以免誤判）。

## 三、限制與風險

1. 四律部派不同，判罪名相、戒條次第本有系統差異；本稿所稱「重複」指內容實質相同，非字句相同。去取含編者判斷，覆核者宜依段號回查原文。
2. 「遍查未見」只證明在所收錄之工作檔與檢索詞範圍內未得對應，不等於該律全本必然無此文。
3. 犍度、雜誦部分材料散出，同一制度在四律分屬不同篇章，對齊未必周延，容有過刪或過留。
4. 白話為現代語譯，重在達意，非學術定本；引用佛典原文仍應以底本為準。

---

*本稿完成於 {d}。*
'''.format(nm=NM, nv=C['n_vol'], d=datetime.date.today().isoformat()))

open(os.path.join(OUT, '{}_去重白話_合冊.md'.format(NM)), 'w', encoding='utf-8') \
    .write(main + '\n' + '\n'.join(app))


# ---------------------------------------------------------------- split books
def cnv(n):
    d = '零一二三四五六七八九'
    if n < 10:
        return d[n]
    if n == 10:
        return '十'
    if n < 20:
        return '十' + d[n % 10]
    return d[n // 10] + '十' + (d[n % 10] if n % 10 else '')


def build_subset(a, b, name):
    sub = [r for r in rows if a <= int(re.match(r'\d+', r[0]).group()) <= b]
    if not sub:
        return
    inc = [u for u in UNITS
           if u['unit'] in units_out
           and a <= int(re.match(r'\d+', '、'.join(str(x) for x in u['vols'])).group()) <= b]
    vs = sorted({v for u in inc for v in u['vols']})
    name = '卷{}至卷{}'.format(cnv(vs[0]), cnv(vs[-1])) if vs else name
    hl = ['# {}去重白話　{}\n'.format(NM, name),
          '> 本冊為《{}去重白話》之分冊，收卷{}至卷{}（以單位為界，相鄰二卷之單位不拆）。凡例、判重口徑與資料限制見合冊本。\n'.format(
              NM, cnv(vs[0]), cnv(vs[-1])),
          '## 本冊統計\n']
    tbl, sts, skp, sip, snp = stat_table(sub, '{} 個單位'.format(len(sub)))
    hl += tbl
    hl.append('\n> 字數以中文字計，不含標點、段號與空白。\n')
    parts = ['\n'.join(hl)]
    k = 0
    for u in inc:
        uu = u['unit']
        k += 1
        if k > 1:
            parts.append('\n---\n')
        parts.append(unit_block(uu))
    open(os.path.join(OUT, '{}_去重白話_{}.md'.format(NM, name)), 'w', encoding='utf-8') \
        .write('\n'.join(parts))
    print('分冊 {}：{}（{} 單位，卷 {}～{}）'.format(name, uu, len(inc), vs[0], vs[-1]))


for (a, b), nm in zip(C['books'], C['book_names']):
    build_subset(a, b, nm)

# ---------------------------------------------------------------- narratives
nn = [x for u in UNITS if u['unit'] in units_out for x in units_out[u['unit']]['narr']]
nl = ['# {}去重白話　獨有敘事（本生・譬喻・長篇）\n'.format(NM),
      '> 本檔為《{}去重白話》之另檔。凡不關斷罪要素之本生、譬喻、長篇敘事，而《四分律》《五分律》《十誦律》三書俱無者，不入正文，抽錄於此：記其卷段指針與要旨；原文六百字以下者併錄全文及白話，長篇之原文亦併載本檔（未譯）——或為校勘者逐字抄錄經組稿程式逐句回錨者，或為 `_work/extract_narr.py` 依『位置』段區間自底本整段抽出者，便於另行取用。\n'.format(NM),
      '## 目錄\n']
for i, x in enumerate(nn, 1):
    nl.append('- {}'.format(re.sub(r'^###\s*\d+\.\s*', '', x['md'].split('\n')[0])))
nl.append('')
if not nn:
    nl.append('本次校勘未抽得三律全無之獨立敘事；各單位所記故事類文字，或與三律相應而刪，或已入正文之差異項。\n')
for i, x in enumerate(nn, 1):
    if i > 1:
        nl.append('\n---\n')
    nl.append(x['md'].strip() + '\n')
open(os.path.join(OUT, '{}_去重白話_獨有敘事.md'.format(NM)), 'w', encoding='utf-8') \
    .write('\n'.join(nl))

# -------------------------------------------------------------------- README
rdl = ['# {}去重白話\n'.format(NM),
       '《{}》（{}，{}）去重今譯。凡與《四分律》《五分律》《十誦律》文意重複者刪略，獨有或具實質增異者保留並譯為白話；引文逐字回錨底本，段號可覆核。\n'.format(
           NM, C['sub'], C['trans']),
       '## 檔目\n',
       '| 檔 | 內容 | 大小 |', '|---|---|---:|']
for fn in sorted(os.listdir(OUT)):
    sz = os.path.getsize(os.path.join(OUT, fn))
    if fn.startswith('README'):
        desc = '本說明'
    elif '_去重白話_合冊.md' in fn:
        desc = '正文＋凡例統計目錄＋三附錄'
    elif '獨有敘事' in fn:
        desc = '三律全無之本生、譬喻、長篇敘事另檔'
    else:
        desc = '分冊（依卷次，以單位為界）'
    rdl.append('| {} | {} | {:.0f} KB |'.format(fn, desc, sz / 1024))
rdl.append('\n## 主要數字\n')
rdl.append('- 底本：{} 卷，{:,} 字'.format(C['n_vol'], base_total))
rdl.append('- 保留：{:,.0f} 字（{:.1f}％），{} 項'.format(tk, tk / base_total * 100 if base_total else 0, ti))
rdl.append('- 另檔抽取獨有敘事：{} 項'.format(tn))
rdl.append('- 單位數：{}（已完成）／{}（總）'.format(len(rows), len(UNITS)))
rdl.append('\n## 如何使用\n')
rdl.append('1. 先讀合冊本「凡例」與「全書統計」，了解取捨標準與各單位比例。\n'
           '2. 欲知某段為何刪除，查附錄一該單位刪略表；欲知某項為何保留，看正文該項「差異說明」與三律對照。\n'
           '3. 欲查故事材料，開《{}_去重白話_獨有敘事.md》。\n'
           '4. 引用時請附段號（如「{}卷5，段37」），工作檔在 `_work/{}/`。\n'.format(NM, NM, C['base_dir']))
rdl.append('\n## 覆核要點\n')
rdl.append('- 「遍查未見」指所收工作檔與所列檢索詞之內未得對應，非斷言該律全本必無。\n'
           '- 四律次第多不相應，比對以內容為準；部派見解之異，本稿只記其實質差異，不判優劣。\n')
open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write('\n'.join(rdl))

# ---------------------------------------------------------------- audit print
uncov, multi = [], []
for u in UNITS:
    k = u['unit']
    if k not in units_out:
        continue
    total = sum(NPARA.get(v, 0) for v in u['vols'])
    if not total:
        continue
    cited = pointers(k)
    if len(u['vols']) > 1:
        multi.append((k, len(cited), total))
    elif len(cited) < total * 0.8:
        uncov.append((k, len(cited), total))
print('wrote', OUT)
print('units', len(units_out), '/', len(UNITS), 'items', ti, 'kept', tk, 'narr', tn)
print('single-volume units with 段號 coverage under 80%:', len(uncov))
for x in uncov[:10]:
    print('  COV', x)
print('multi-volume units (coverage indicative only):', len(multi))
