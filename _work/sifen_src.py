#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四分律原文與白話的「節」切分與渲染。

節（unit）＝對照本插入原文／白話的最小單位：
  前三十卷  依戒條（四分原文每戒末標「(一竟)」「(二竟)」…；尼單提諸篇標「(一)」「(二)」…）
  卷三十一至六十  依揵度與子題；過長者再依事件起首切成小段

資料來源：
  sifen/NNN_*.txt        段分好的四分律原文（段號\t文字）
  sifen_plain.json       段 → 白話（由 align_sifen2.py 產生）
"""
import os, re, glob, json, math, bisect

BASE = os.path.dirname(os.path.abspath(__file__))
SIFEN_DIR = os.path.join(BASE, 'sifen')
PLAIN_JSON = os.path.join(BASE, 'sifen_plain.json')

# ---------- 載入 ----------
SEG = {}      # 篇號 -> [(段號, 文字), ...]
TITLE = {}    # 篇號 -> 篇題（取自檔名，如「衣揵度之二」）
for _f in sorted(glob.glob(os.path.join(SIFEN_DIR, '*.txt'))):
    _no = int(os.path.basename(_f)[:3])
    TITLE[_no] = re.sub(r'^_+|_+$', '', os.path.basename(_f)[4:-4])
    _lst = []
    for _l in open(_f, encoding='utf-8', errors='ignore'):
        _l = _l.rstrip('\n')
        if not _l.strip():
            continue
        _m = re.match(r'^(\d+)\t(.*)$', _l)
        if _m:
            _lst.append((int(_m.group(1)), _m.group(2)))
    SEG[_no] = _lst

PLAIN = {}
if os.path.exists(PLAIN_JSON):
    PLAIN = json.load(open(PLAIN_JSON, encoding='utf-8'))


def _fix_dup034():
    """篇034（四分律卷二十七）底本重出：段1–136 之後復見卷首（段137–141）與
    同一卷全文（段142–277），段278–281 方為真尾。存前段、刪重出、綴真尾，
    並同步搬移白話鍵。"""
    segs = SEG.get(34) or []
    if not segs or segs[-1][0] < 280:
        return
    head = [(n, t) for n, t in segs if n <= 136]
    tail = [(n - 141, t) for n, t in segs if n >= 278]
    SEG[34] = head + tail
    for n in range(137, 278):
        PLAIN.pop('034-%d' % n, None)
    for n in range(278, 282):
        v = PLAIN.pop('034-%d' % n, None)
        if v:
            PLAIN['034-%d' % (n - 141)] = v


_fix_dup034()

RE_JING = re.compile(r'[（(]([一二三四五六七八九十百]+)竟[)）]?')
RE_TAIL = re.compile(r'[（(]([一二三四五六七八九十百]+)[）)]\s*$')
RE_NIAN = re.compile(r'[（(]([^（()）]{1,10}(?:揵度|犍度)[^（()）]{0,4}竟)[)）]')

# 事件起首（供長篇切點吸附）
RE_START = re.compile(r'^(爾時|時有|時，|時世|佛在|佛告|若比丘|優波離|諸比丘|告諸比丘|彼時|世尊)')


def _cn2int(s):
    """中文數字轉整數，支援「一百七十八」"""
    D = {'〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
         '六': 6, '七': 7, '八': 8, '九': 9}
    U = {'十': 10, '百': 100, '千': 1000}
    total, cur = 0, 0
    for ch in s:
        if ch in D:
            cur = D[ch]
        elif ch in U:
            cur = (cur or 1) * U[ch]
            total += cur
            cur = 0
        else:
            return 0
    return total + cur


def _cn_num(n):
    """整數轉中文（1–999），供節序「（十七）」「第一百零五戒」"""
    D = '〇一二三四五六七八九'
    if n < 10:
        return D[n]
    if n < 20:
        return '十' + (D[n % 10] if n % 10 else '')
    if n < 100:
        return D[n // 10] + '十' + (D[n % 10] if n % 10 else '')
    h, r = n // 100, n % 100
    if r == 0:
        return D[h] + '百'
    if r < 10:
        return D[h] + '百零' + D[r]
    return D[h] + '百' + _cn_num(r)


RE_TITLE_NUM = re.compile(r'第[一二三四五六七八九十百]+(?:之[一二三四五六七八九十]+)?$')
RE_TITLE_ZHI = re.compile(r'之[一二三四五六七八九十]+$')
RE_TITLE_TAIL = re.compile(r'(?:之[餘初末]|[初餘])$')


def _base_title(t):
    """篇題去尾碼，得揵度本名：「呵責揵度第十一之一」→「呵責揵度」"""
    t = (t or '').strip()
    if not t or t == '開頭':
        return ''
    t = RE_TITLE_NUM.sub('', t)
    t = RE_TITLE_ZHI.sub('', t)
    t = RE_TITLE_TAIL.sub('', t)
    return t


def _jie_name(s):
    """從戒條句提取短名：去「若比丘」等主語，略去「若在村落」之類條件句"""
    s = s or ''
    _nun = bool(re.match(r'^[「『]?若比丘尼', s))
    # 尼律諸篇主語作「若比丘尼」，須先匹配長者，否則「比丘」先吞，餘「尼…」
    s = re.sub(r'^[「『]?若(?:比丘尼|比丘|沙彌尼|沙彌)[，,]?', '', s)
    s = re.sub(r'[，,]?(尼薩耆波逸提|僧伽婆尸沙|波羅夷|波逸提|波羅提提舍尼|突吉羅).*$', '', s)
    s = re.sub(r'^衣已竟[、，,]?迦絺那衣已[出捨][、，,]?', '', s)
    if _nun:
        # 尼戒條多先標處所、條件（「在聚落若空處」「有染污心」），首句未必是所犯之事
        acc = ''
        for cl in re.split(r'[，,；;。]', s):
            cl = cl.strip('，,。 、「」『』')
            if not cl or re.match(r'^(?:在|於|若|除|衣已竟|迦絺那衣)', cl) and len(cl) <= 14:
                continue
            if len(cl) > 17:      # 一句過長（多為頓號列舉），於頓號處截，免斷字成詞
                k = max(cl.rfind('、', 0, 18), cl.rfind('，', 0, 18))
                cl = cl[:k] if k > 0 else cl[:17]
            if acc and len(acc) + 1 + len(cl) > 17:
                break
            acc = (acc + '，' + cl) if acc else cl
            if len(acc) >= 6:
                break
        acc = re.sub(r'(得持|得畜|得用)$', '', acc)
        return re.sub(r'(者|故|已|時|而)$', '', acc)
    for cl in re.split(r'[，,；;]', s):
        cl = cl.strip('，,。 「」『』')
        if not cl or re.match(r'^若|^除|^有|^復', cl):
            continue
        return cl[:14] + ('…' if len(cl) > 14 else '')
    return ''


def _units_jing(no):
    """依「(N竟)」切戒"""
    segs = SEG[no]
    marks = []
    for n, t in segs:
        m = RE_JING.search(t)
        if m:
            marks.append((n, m.group(1)))
    out, prev = [], 0
    for n, cn in marks:
        body = '\n'.join(t for k, t in segs if prev < k <= n)
        # 底本或作「當如是說」，或作「當如此說」，或但列戒文而無發語
        m = re.search(r'當如[是此]說[：:]\s*[『「]?([^\n。]{8,120})', body)
        if m:
            name = _jie_name(m.group(1))
        else:
            name = _crime_name(body)
        out.append({'a': prev + 1, 'b': n, 'cn': cn, 'name': name})
        prev = n
    if prev < segs[-1][0]:
        out.append({'a': prev + 1, 'b': segs[-1][0], 'cn': '', 'name': ''})
    return out


RE_CRIME = r'(?:波羅夷|僧伽婆尸沙|僧殘|偷蘭遮|波逸提|波羅提提舍尼|突吉羅)'
RE_NUN = re.compile(r'若(?:比丘尼|比丘|沙彌尼|沙彌)[，,]?\s*')


def _crime_name(body):
    """取戒條短名：於「若比丘尼…，某罪」中，取主語以下第一、二句。

    舊法取罪名關鍵詞前十八字、再切末句，於尼律適得其反——戒條長者，末句
    往往只是「是比丘尼犯」，故滿目「尼」「尼染污心」。今改取首句。
    """
    m = RE_NUN.search(body)
    if m:
        rest = body[m.end():]
        mm = re.search(RE_CRIME, rest)
        seg = rest[:mm.start()] if mm else rest[:60]
    else:
        mm = re.search(RE_CRIME, body)
        if not mm:
            return ''
        seg = body[:mm.start()]
    acc = ''
    for cl in re.split(r'[。；，：！？]', seg):
        cl = cl.strip('「」『』（）()　 ')
        cl = re.sub(r'^(?:是|彼|此|諸|有|復|若|而|即)+', '', cl)
        cl = re.sub(r'^(?:比丘尼|比丘|沙彌尼|沙彌)', '', cl)
        if len(cl) < 2:
            continue
        # 捨墮諸戒皆冠以「衣已竟、迦絺那衣已捨」，非所犯之事
        if re.match(r'^(?:衣已竟|迦絺那衣|除僧羯磨|除餘時)', cl):
            continue
        acc = (acc + '，' + cl) if acc else cl
        if len(acc) >= 6:
            break
    acc = re.sub(r'(者|故|已|時|而|得持)$', '', acc)
    if len(acc) > 18:
        k = max(acc.rfind('、', 0, 19), acc.rfind('，', 0, 19))
        acc = acc[:k] if k > 0 else acc[:18]
    return acc


def _units_tail(no):
    """依「(N)」尾標切戒（尼單提諸篇）"""
    segs = SEG[no]
    marks = [(n, m.group(1)) for n, t in segs if (m := RE_TAIL.search(t))]
    out, prev = [], 0
    for n, cn in marks:
        body = '\n'.join(t for k, t in segs if prev < k <= n)
        out.append({'a': prev + 1, 'b': n, 'cn': cn, 'name': _crime_name(body)})
        prev = n
    if prev < segs[-1][0]:
        out.append({'a': prev + 1, 'b': segs[-1][0], 'cn': '', 'name': ''})
    return out


def _split_budget(segs, a, b, budget=1000, maxseg=16, minsize=320):
    """把 [a,b] 依字數預算切成若干段，切點吸附到事件起首。

    揵度部長篇動輒數千字，原以 3600 字為節，較戒條部粗三四倍；今降為 1000 字，
    使一節之量與一戒相若，讀者不必在單一標題下讀數千字。

    舊法邊切邊累加，切點前跳至事件起首後未同步累計量，致多重門檻虛高、
    長篇只落一刀（如受戒揵度段139–144 六段 6,599 字成一節）。今改前綴和定位。
    """
    idx = [k for k in range(len(segs)) if a <= segs[k][0] <= b]
    if not idx:
        return []
    txt = [segs[k][1] for k in idx]
    nums = [segs[k][0] for k in idx]
    n = len(idx)
    total = sum(len(t) for t in txt)
    if n <= maxseg and total <= budget:
        return [(a, b)]
    want = max(2, math.ceil(total / budget), math.ceil(n / maxseg))
    target = total / want
    pre = [0]
    for t in txt:
        pre.append(pre[-1] + len(t))
    cuts = []
    for i in range(1, want):
        goal = target * i
        j = bisect.bisect_left(pre, goal)
        j = min(max(j, (cuts[-1] + 1) if cuts else 1), n - 1)
        # 吸附到往後三段內的事件起首，惟溢量不過半節
        best = j
        for j2 in range(j, min(j + 3, n)):
            if RE_START.match(txt[j2]) and pre[j2] <= goal + target * 0.5:
                best = j2
                break
        if best > (cuts[-1] if cuts else 0):
            cuts.append(best)
    bounds = [0] + cuts + [n]
    out = [(nums[x], nums[y - 1]) for x, y in zip(bounds, bounds[1:]) if y > x]
    # 過短之節併入前節；首節過短則併入次節
    size = {nums[i]: len(txt[i]) for i in range(n)}
    def _len(p):
        return sum(size[k] for k in range(p[0], p[1] + 1) if k in size)
    merged = []
    for p in out:
        if merged and _len(p) < minsize:
            merged[-1] = (merged[-1][0], p[1])
        else:
            merged.append(p)
    if len(merged) > 1 and _len(merged[0]) < minsize:
        merged[1] = (merged[0][0], merged[1][1])
        merged.pop(0)
    return merged


def _split_events(segs, a, b, minlen=500, maxlen=2200):
    """依緣起事件切節：段首作「爾時」「時有」「佛在」等即為新事件之始。

    短於 minlen 者併入前節（首節併入次節），長於 maxlen 者於段界再斷一刀，
    以免單節過鉅。切點皆落於段界，故不割裂文句。
    """
    idx = [k for k in range(len(segs)) if a <= segs[k][0] <= b]
    if not idx:
        return []
    size = {segs[k][0]: len(segs[k][1]) for k in idx}
    units, cur, acc = [], [], 0
    for k in idx:
        if cur and ((RE_START.match(segs[k][1]) and acc >= minlen) or acc >= maxlen):
            units.append(cur)
            cur, acc = [], 0
        cur.append(segs[k][0])
        acc += size[segs[k][0]]
    if cur:
        units.append(cur)
    merged = []
    for u in units:
        L = sum(size[x] for x in u)
        if merged and L < minlen:
            merged[-1] += u
        else:
            merged.append(list(u))
    if len(merged) > 1 and sum(size[x] for x in merged[0]) < minlen:
        merged[1] = merged[0] + merged[1]
        merged.pop(0)
    return [(u[0], u[-1]) for u in merged]


RE_TOPIC_LEAD = re.compile(
    r'^(?:爾時|時有|時，|時|佛在|佛告|彼時|世尊|告諸比丘|諸比丘|優波離|若比丘|'
    r'即從坐起|從坐起|偏露右肩|偏袒右肩|右膝著地|頭面禮足|却住一面|在一面坐|却坐一面|'
    r'合掌|白世尊言|白佛言|白言)+[，、。：]?')
RE_TOPIC_LOC = re.compile(
    r'^(?:(?:世尊|佛|菩薩)(?:在|於|至|往)|在|於)?[^，。]{0,16}(?:國|城|邑|聚落|村|園|林|苑|山中|住|中)$')
RE_TOPIC_PLACE = re.compile(r'^[^，。]{1,8}(?:國|城|邑|聚落|村|園|林|苑)$')


RE_TOPIC_SKIP = re.compile(
    r'^(?:即?從坐起|偏露右肩|偏袒右肩|右膝著地|頭面禮足|却住一面|在一面坐|却坐一面|'
    r'白佛言|白言|作是念|作如是念|而作是言|如是言|如是我聞)')


def _topic(s):
    """取一節之首事件為節名：去「爾時」等發端語、去遊行處所與儀軌套語，撮其行事。"""
    acc = ''
    for cl in re.split(r'[。；，：！？]', s or ''):
        cl = cl.strip('「」『』（）()　 ')
        for _ in range(2):
            cl = RE_TOPIC_LEAD.sub('', cl)
        if not cl or len(cl) < 3:
            continue
        if not acc and (RE_TOPIC_LOC.match(cl) or RE_TOPIC_PLACE.match(cl)
                        or re.match(r'^(?:在|於)[^，。]{0,12}(?:國|城|邑|聚落|村|園|林|苑|中|所|處|間|前)$', cl)
                        or (cl[0] == '在' and len(cl) <= 8)
                        or RE_TOPIC_SKIP.match(cl)
                        or cl.endswith(('如是說', '如是言'))):
            continue
        acc = (acc + '，' + cl) if acc else cl
        if len(acc) >= 8:
            break
    acc = re.sub(r'(者|故|已|時|而|言|爾)$', '', acc)
    acc = re.sub(r'\[[^\]]*$', '', acc)      # 去截斷之組字式殘片（如「波羅[木*奈」）
    acc = acc.rstrip('、，；：')
    if len(acc) > 18:
        cut = acc.rfind('，', 6, 17)          # 於頓號處截，不割斷詞句
        acc = acc[:cut] if cut > 0 else acc[:16]
    acc = re.sub(r'[、，；：]$', '', acc)
    return acc


# 同名重出、截斷不成詞者，酌改（鍵為「篇號-起段」）
TOPIC_FIX = {
    (39, 1): '異處獨住一比丘自恣',
    (39, 11): '八難來聽略說自恣',
    (39, 32): '舊比丘自恣客來更作',
    (39, 39): '見客不求而作自恣得罪',
    (44, 1): '多知識比丘亡財物眾多',
    (44, 21): '亡者三衣與瞻病人',
    (69, 92): '目連見針毛眾生',
    (69, 95): '目連見身爛眾生',
    (74, 25): '莫數舉他罪：身威儀',
    (74, 42): '莫數舉他罪：口命多聞',
    (38, 62): '耶輸伽出家',
    (38, 67): '同友五十人出家',
    (38, 27): '定光如來本生',
    (38, 35): '彌却摩納本生',
    (42, 15): '塚間得皮繩床木床',
    (45, 27): '顛狂比丘食生肉飲血',
    (71, 1): '增一法初，囑聽受持',
}


def _units_qian(no):
    """揵度諸篇：先依「(○○揵度竟)」切，再依緣起事件細分。

    戒條部一戒一節，界畫分明；揵度部無戒名可依，舊法按字數硬切，遂成
    「段139–144」一類無名之節。今改以事件為界——凡段首作「爾時」「時有」
    「佛在」者，即一新緣起；短者併於前節，長者（逾 2,200 字）再斷。

    每節帶 'fam'（所屬揵度本名）與 'topic'（首事件旨要），供跨篇連續編號
    與命名——如藥揵度分見篇045、046，二篇之節合編為「藥揵度（一）…」。
    """
    segs = SEG[no]
    marks = [(n, m.group(1)) for n, t in segs if (m := RE_NIAN.search(t))]
    blocks, prev = [], 0
    for n, nm in marks:
        blocks.append((prev + 1, n, nm))
        prev = n
    if prev < segs[-1][0]:
        blocks.append((prev + 1, segs[-1][0], ''))
    fam0 = _base_title(TITLE.get(no, ''))
    out = []
    for a, b, nm in blocks:
        nm = re.sub(r'(?:具足)?竟$', '', nm)
        fam = nm or fam0
        for x, y in _split_events(segs, a, b):
            head = [t for k, t in segs if x <= k <= y][:2]   # 首二段合觀，免以發端語為名
            out.append({'a': x, 'b': y, 'cn': '', 'name': '', 'fam': fam,
                        'topic': TOPIC_FIX.get((no, x)) or _topic('。'.join(head))})
    return out
    return out


UNITS_CACHE = {}
_QIEN_DONE = False
_NUN_DONE = False

# 卷末殘段（戒文跨卷而斷，或但餘總標）無「(N竟)」可據，另予短名
FRAG_NAME = {
    (4, 85): '沓婆摩羅子為僧知事',
    (5, 17): '阿那律等釋種出家',
    (7, 11): '迦留陀夷與齋優婆私',
    (25, 1): '七滅諍法',
    (34, 140): '度盲瞎癃躄病者',
    (37, 148): '乞油蜜等戒同乞酥',
}

# 自動命名過短、截斷或同名重出者，另予覆寫
JIE_FIX = {
    (27, 4): '言人，若居士、居士兒',
    (28, 1): '染污心，從男子受食',
    (29, 14): '使織師織衣，自與其價',
    (34, 49): '受請滅諍而不為滅',
    (35, 81): '許授戒，留令勸化',
    (35, 87): '索衣許授具足戒',
    (36, 15): '安居竟不往僧中自恣',
}


def _apply_frag(no, r):
    for u in r:
        fix = JIE_FIX.get((no, u['a']))
        if fix:
            u['name'] = fix
        elif not u.get('name') and not u.get('cn'):
            nm = FRAG_NAME.get((no, u['a']))
            if nm:
                u['name'] = nm
    return r


def _name_qian():
    """卷三十一至六十諸篇一次切齊，同一揵度跨篇連續編號。

    須先全數切完再命名，否則篇045、046 各自從「（一）」起算，同名重出。
    """
    cnt = {}
    for no in range(38, 75):
        if no not in SEG:
            continue
        if no not in UNITS_CACHE:
            UNITS_CACHE[no] = _units_qian(no)
        for u in UNITS_CACHE[no]:
            fam = u.get('fam') or ''
            if fam:
                cnt[fam] = cnt.get(fam, 0) + 1
    seq = {}
    for no in range(38, 75):
        for u in UNITS_CACHE.get(no) or []:
            fam = u.get('fam') or ''
            if not fam:
                continue
            seq[fam] = seq.get(fam, 0) + 1
            u['name'] = fam if cnt.get(fam, 1) <= 1 else '%s（%s）' % (fam, _cn_num(seq[fam]))


def _renumber_nun():
    """尼戒諸篇戒號續編。

    底本於卷中重起戒號（如單提「第一百戒」之後復作「第一戒」），致同一戒類
    前後兩見、卷二十七又自「第五戒」起，觀者茫然。今依重起之處累加位移，
    使一類之中戒號蟬聯：第一百零一戒、第一百零二戒……
    """
    global _NUN_DONE
    for no in range(26, 38):
        if no not in SEG or no in UNITS_CACHE:
            continue
        UNITS_CACHE[no] = _apply_frag(no, _units_tail(no) if no >= 31 else _units_jing(no))
    state = {}
    for no in range(26, 38):
        fam = _base_title(TITLE.get(no, ''))
        st = state.setdefault(fam, [0, 0])   # [上一原始戒號, 累計位移]
        for u in UNITS_CACHE.get(no) or []:
            v = _cn2int(u.get('cn') or '')
            if not v:
                continue
            if st[0] and v <= st[0]:         # 戒號回卷，新起一輪
                st[1] += st[0]
            u['num'] = v + st[1]
            st[0] = v
    _NUN_DONE = True


def units(no):
    """回傳 [{a,b,cn,name}, ...]，保證覆蓋全篇且無重疊"""
    global _QIEN_DONE, _NUN_DONE
    if not _QIEN_DONE:
        _name_qian()
        _QIEN_DONE = True
    if 26 <= no <= 37 and not _NUN_DONE:
        _renumber_nun()
        return UNITS_CACHE.get(no) or []
    if no in UNITS_CACHE:
        return UNITS_CACHE[no]
    segs = SEG[no]
    if not segs:
        r = []
    elif no == 0 or len(segs) == 1:
        r = [{'a': segs[0][0], 'b': segs[-1][0], 'cn': '', 'name': ''}]
    elif 31 <= no <= 37:
        r = _units_tail(no)
    elif no >= 38:
        r = _units_qian(no)
    else:
        r = _units_jing(no)
    r = _apply_frag(no, r)
    UNITS_CACHE[no] = r
    return r


def seg_text(no, n):
    for k, t in SEG[no]:
        if k == n:
            return t
    return ''


def plain_text(no, a, b):
    """取 [a,b] 段的白話，按段序串接"""
    out = []
    for n in range(a, b + 1):
        s = PLAIN.get('%03d-%d' % (no, n))
        if s:
            out.append(s)
    return out


# 組字式（CBETA 造字）→ 通行字。底本無 Unicode 之字，以六書之方合成方括，
# 如「[木*奈]」即木旁加奈。此表所收，皆與通行字同字或義定無疑者。
GLYPH_MAP = {
    '[木*奈]': '柰', '[木*柰]': '柰', '[真/心]': '瞋', '[少/兔]': '㝹',
    '[跍*月]': '胡', '[疊*毛]': '氎', '[穀-禾+卵]': '殼', '[禾*會]': '糩',
    '[薜/米]': '糵', '[口*弟]': '涕', '[門@龠]': '鑰', '[袖-由+宁]': '紵',
    '[蹲-酋+(十/田/ㄙ)]': '蹲', '[簿-尃+卑]': '箄', '[口*(隹/乃)]': '嘴',
    '[(殼-一)/牛]': '擠', '[穀-禾+牛]': '擠', '[泳-永+瓦]': '瓶',
    '[酉*卑]': '毘', '[毯-炎+登]': '㲪', '[利-禾+皮]': '剝', '[病-丙+帶]': '帶',
    '[土*廷]': '埏', '[夌*欠]': '陵', '[馬*奔]': '奔', '[金*咨]': '鎡',
    '[金*慈]': '鎡', '[卄/積]': '積', '[貝*為]': '賭', '[土*瓦]': '罐',
    '[竺-二+韋]': '葦', '[口*束]': '吮',
}

GLYPH_TITLE = GLYPH_MAP


def glyph_fix(s):
    """組字式代通行字；未收者仍存原式，以存底本之真。"""
    if not s or '[' not in s:
        return s
    for k, v in GLYPH_MAP.items():
        if k in s:
            s = s.replace(k, v)
    return s


def _title_glyph(s):
    """節題用字清理：組字式代通行字、去未閉合之引號括號。"""
    s = glyph_fix(s)
    s = re.sub(r'\[[^\]]*$', '', s)          # 去截斷之組字式殘片
    s = re.sub(r'\[[^\]]{1,12}\]', '', s)
    for a, b in ('「」', '『』', '（）', '〈〉', '《》'):
        if s.count(a) > s.count(b) and s.rfind(a) > 0:
            s = s[:s.rfind(a)]
    return re.sub(r'[，、；：]$', '', s)


def unit_label(u):
    """節的顯示名（不含段範圍）"""
    if u.get('num'):
        h = f'第{_cn_num(u["num"])}戒'
        if u.get('name'):
            h += f'　{_title_glyph(u["name"])}'
        return h
    if u.get('cn'):
        h = f'第{u["cn"]}戒'
        if u.get('name'):
            h += f'　{_title_glyph(u["name"])}'
        return h
    return '　'.join(_title_glyph(x) for x in (u.get('name'), u.get('topic')) if x)
