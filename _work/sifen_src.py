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

# 戒條正式簡稱表（側邊欄與節題共用）。缺檔時靜默退化為原節題，不補造。
_JIE_PATH = os.path.join(BASE, 'jie_names.json')
JIE_NAMES = json.load(open(_JIE_PATH, encoding='utf-8')) if os.path.exists(_JIE_PATH) else {}


# 尼單提有八節，底本戒末標作「(十)」「(十一)」而無「竟」字，切節時合為一節，
# 致前一戒（掘地、壞生種等）隱於後一戒名下。此處不改節界（免動錨點與白話），
# 僅令標籤併列所含二戒，以存其實。
JIE_MULTI = {(31, 11), (31, 21), (31, 31), (32, 7), (32, 27), (32, 92),
             (33, 1), (35, 41)}


def jie_family(no, u=None):
    """篇號 → 簡稱表之聚類鍵。僅登錄「一戒一節」之聚類。

    眾學（篇 022–024）在本書合為 58 節、滅諍（篇 025）合為 1 節、
    尼提舍尼合為 2 節，一節含多戒，故不登錄，仍用原節題，免以單一戒名冠多戒。
    篇 021 前八節為單提 83–90、段 66 起為四提舍尼；篇 037 末二節為尼提舍尼。
    """
    if 1 <= no <= 2:
        return '比丘波羅夷'
    if 3 <= no <= 6:
        return '比丘僧殘'
    if no == 7:
        return '比丘不定'
    if 8 <= no <= 12:
        return '比丘捨墮'
    if 13 <= no <= 20:
        return '比丘單提'
    if no == 21:
        return '比丘單提' if (u and u.get('a', 0) <= 65) else '比丘提舍尼'
    if no == 26:
        return '尼波羅夷'
    if 27 <= no <= 28:
        return '尼僧殘'
    if 29 <= no <= 30:
        return '尼捨墮'
    if 31 <= no <= 36:
        return '尼單提'
    if no == 37:
        return '尼單提' if (u and u.get('a', 0) <= 140) else None
    return None

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

# 篇題覆定：底本卷首作「人揵度第十二之一」，而全書無「之二」，去其「之一」，
# 免讀者疑有闕卷（校閱報告所指）。
TITLE_FIX = {52: '人揵度第十二'}
TITLE.update(TITLE_FIX)

# 揵度本名別體：059 卷首標「尼揵度竟」，058 作「比丘尼揵度竟」，二者本是一揵度，
# 須合編節次（058 訖於（七），059 當接（八）–（十一）），故併為一名。
FAM_ALIAS = {'尼揵度': '比丘尼揵度'}

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
# 尼單提諸篇尾標或作「(三十)」，或作「(三十竟)」，或於括號後再著句號
# 「(三十)。」；舊式只認第一種，凡作「竟」或帶句號者皆漏切，一節遂含二戒
# （031 段11–12、21–22、31–32，032 段7–8，035 段41–54 皆是）。今並收三式。
RE_TAIL = re.compile(r'[（(]([一二三四五六七八九十百]+)(?:竟)?[）)]\s*[。，、]?\s*$')
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
        # 「若比丘飲酒者」之「者」為戒條句末助詞，非名所須；尼律一路已去之，此處從同
        if len(cl) > 1:
            cl = re.sub(r'者$', '', cl)
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
    for u in out:
        u['cn'] = CN_FIX.get((no, u['a']), u['cn'])
        pre = SEC_PREFIX.get((no, u['a']))
        if pre and u.get('name'):
            u['name'] = pre + u['name']
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
        cut = acc.rfind('，', 6, 17)          # 於逗號處截，不割斷詞句
        if cut <= 0:
            cut = acc.rfind('、', 6, 17)      # 無逗則於頓號處截（如「和尚等、阿闍梨阿闍梨等」）
        acc = acc[:cut] if cut > 0 else acc[:18]
    acc = re.sub(r'[、，；：]$', '', acc)
    return acc


# 同名重出、截斷不成詞者，酌改（鍵為「篇號-起段」）
TOPIC_FIX = {
    (39, 1): '異處獨住一比丘自恣',
    (39, 11): '八難來聽略說自恣',
    (39, 32): '舊比丘自恣客來更作',
    (39, 39): '見客不求而作自恣得罪',
    (45, 69): '從波婆城至阿頭摩',
    (60, 24): '與六群比丘白衣家內共食',
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
    (38, 331): '眾僧結制安居共行瘂法',
    (38, 342): '前後安居人雜住，隨上座處自恣',
    # 舊題逕取段首套語（「往至佛所頭面禮足在一面坐」之屬），語意懸空，今正
    (38, 44): '欝鞞羅婆羅門男女施食受二歸',
    (38, 53): '受梵天勸請，觀世間根機',
    (38, 83): '伊羅鉢龍王自陳宿業，問何時脫',
    (38, 108): '得糞掃衣，帝釋成池取石供浣',
    (38, 200): '一住處和合說戒，別部說戒得罪',
    (38, 260): '瓶沙王遣將守護僧園，妨說戒',
}


# 揵度起首而無「(○○揵度竟)」可據者。篇038 段331 起為自恣揵度之一，
# 至卷末而揵度未竟（續見篇039 之二），故於此明定其名，免落篇題「(開頭)」。
KHD_HEAD = {(38, 331): '自恣揵度'}


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
        fam = nm or KHD_HEAD.get((no, a)) or fam0
        fam = FAM_ALIAS.get(fam, fam)
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
    (7, 1): '共女人屏處坐說非法語',
    (9, 23): '居士為比丘辦衣價囑買',
    (12, 1): '殘藥齊七日得服',
    (17, 12): '無病自為身索美食',
    (18, 79): '與衣後不語主還取',
    (21, 19): '作兜羅綿貯床褥',
    (27, 4): '言人，若居士、居士兒',
    (28, 1): '染污心，從男子受食',
    (29, 14): '使織師織衣，自與其價',
    (34, 49): '受請滅諍而不為滅',
    (35, 81): '許授戒，留令勸化',
    (35, 87): '索衣許授具足戒',
    (36, 15): '安居竟不往僧中自恣',
    # 戒條句以條件／時態子句開頭，自動抽取只取首段，遂成「瞋恚故」「共同羯磨已」
    # 之類半句。此八條另定名，取所犯之事為主。
    (5, 1): '瞋恚故以無根波羅夷謗',
    (5, 10): '瞋恚故於異分事取片',
    (19, 26): '鬪諍如法滅已後更發起',
    (19, 46): '作如是語言婬欲非障道',
    (19, 66): '作是言婬欲非障道',
    (20, 20): '共同羯磨已後作如是語',
    (20, 44): '共鬪諍已聽語向彼說',
    (20, 66): '瞋恚故以無根僧殘謗',
}

# 底本第62、67、68戒戒末標記奪「六十」二字，作「(二竟)」「(七竟)」「(八竟)」，
# 致戒號倒退為二、七、八。今據戒次訂正；原文摺疊塊仍存底本之舊，讀者可覆核。
CN_FIX = {(24, 87): '六十二', (24, 92): '六十七', (24, 102): '六十八'}

# 篇021 於九十單提之末逕接四波羅提提舍尼，戒號復從「一」起，易與單提相混。
# 節名冠以法名，使層級自明。
SEC_PREFIX = {(21, 66): '〔波羅提提舍尼〕', (21, 77): '〔波羅提提舍尼〕',
              (21, 85): '〔波羅提提舍尼〕', (21, 95): '〔波羅提提舍尼〕'}

# 篇037 同病：一百七十八單提之末逕接八波羅提提舍尼。底本以「(一百七十八波逸提法竟)」
# 結單提，而提舍尼首戒只作「(一)」，無「竟」字可據，切戒時遂將段141–147 併入
# 第一百七十八戒——節名作「使外道女香塗摩身」，而所含已是乞酥戒文。
# 今於段141 補切一刀，冠以法名，與篇021 同例；戒號逕定，不與單提之累加相混。
SEC_SPLIT = {(37, 141): ('〔波羅提提舍尼〕', '乞酥食'),
             # 段149 為四分律尼眾學法之總註（「下眾學戒與大僧戒無異，故不出耳」），
             # 與前節乞油蜜戒不同科。五分尼眾學法之問答（D-0852）附此，別立一節。
             (37, 149): ('〔尼眾學法〕', '四分從略')}
NUM_FIX = {(37, 135): 178, (37, 141): 1}

# ── 四分戒名人工覆定（2026-11-04，第八輪校閱）──────────────────────
# `_crime_name()` 取戒文首句為節名，遇「若比丘婬欲意……」「春殘一月在……」
# 一類開端，則所截者非戒名，或三戒同名，或竟成敘事語。此表以通行戒名正之；
# 其未經確認者不列，寧存原式。
NAME_FIX = {
    # 全書審閱批次一（2026-11-05）：篇31 節名截在引語中者，補定
    (31, '八'): '向未受大戒人說過人法',
    (1, '一'): '犯不淨行',
    (3, '二'): '摩觸女人',
    (4, '三'): '麁惡語',
    (4, '四'): '歎身索供',
    (5, '八'): '無根謗',
    (5, '九'): '假根謗',
    (6, '十一'): '助破僧',
    (8, '三'): '月望衣',
    (8, '四'): '從非親里比丘尼取衣',
    (8, '五'): '使非親里比丘尼浣衣',
    (9, '六'): '從非親里居士乞衣',
    (9, '七'): '過受衣',
    (9, '九'): '二居士各辦衣價',
    (9, '十'): '遣使送衣價',
    (10, '十七'): '使非親里比丘尼浣染擘羊毛',
    (11, '二十三'): '乞縷線使非親里織師織衣',
    (11, '二十四'): '勸織師增價',
    (11, '二十五'): '奪衣',
    (12, '二十七'): '雨浴衣',
    (12, '二十八'): '急施衣',
    (12, '二十九'): '阿蘭若離衣',
    # 以下八條，`_crime_name()` 截在引號之中，節名成「…作如是語：『比丘為飲…」之形，
    # 目錄尤為刺目。今就戒文與各篇篇旨所已用之語補定。
    (15, '二十三'): '譏謗教授比丘尼',
    (17, '四十六'): '許食不與',
    (20, '七十一'): '不學戒',
    (20, '七十二'): '謗毀雜碎戒',
    (20, '七十三'): '說戒時言始知',
    (26, '四'): '大妄語',
    (28, '九'): '教人受染心男子食',
    (28, '十六'): '瞋心捨三寶',
}

# 二不定法第二戒（露處不定）底本無「(二竟)」尾標，切戒時併入前段之緣起，
# 遂使一戒失其節名。今就該段起處補立，節數仍二，惟戒數由一而二。
UNIT_FIX = {(7, 11): {'cn': '二', 'name': '露處不定'}}

# 百眾學法「行／坐」成對，底本於坐戒多省作「坐亦如是」，節名遂空。
# 依前行戒之節名補「坐」字（底本坐戒亦作「…行入白衣舍坐」，仍其舊文）。
_ZUO_PIAN = (22, 23)


def _fill_zuo(no, r):
    if no not in _ZUO_PIAN:
        return r
    prev = ''
    for u in r:
        nm = (u.get('name') or '').strip()
        if not nm and prev:
            u['name'] = prev + '坐'
        prev = (u.get('name') or '').strip() or prev
    return r


def _split_sec(no, r):
    """於指定段補切一刀，使律末附出之法（如尼律提舍尼）自成一節。"""
    hits = [(a, pre, nm) for (n, a), (pre, nm) in SEC_SPLIT.items() if n == no]
    if not hits:
        return r
    out = []
    for u in r:
        done = False
        for a, pre, nm in hits:
            if u['a'] < a <= u['b']:
                out.append({'a': u['a'], 'b': a - 1,
                            'cn': u.get('cn', ''), 'name': u.get('name', '')})
                out.append({'a': a, 'b': u['b'], 'cn': '', 'name': pre + nm})
                done = True
                break
        if not done:
            out.append(u)
    return out


def _apply_frag(no, r):
    r = _split_sec(no, r)
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
            fx = NUM_FIX.get((no, u.get('a')))
            if fx:
                u['num'] = fx
                st[0], st[1] = fx, 0
                continue
            v = _cn2int(u.get('cn') or '')
            if not v:
                continue
            if st[0] and v <= st[0]:         # 戒號回卷，新起一輪
                st[1] += st[0]
            u['num'] = v + st[1]
            st[0] = v
    # 本分支於 units() 中提前回傳，若不在此補套，尼律諸篇之 NAME_FIX／UNIT_FIX
    # 將永不生效（2026-11-05 全書審閱查出）。戒號已定，此處只改節名，不動 a/b。
    for no in range(26, 38):
        if no in UNITS_CACHE:
            _fix_names(no, UNITS_CACHE[no])
    _NUN_DONE = True


def _fix_names(no, r):
    """套用人工戒名覆定與補節。只改節名，不動 a/b，故節界與編號不更。"""
    for u in r:
        fx = NAME_FIX.get((no, (u.get('cn') or '').strip()))
        if fx:
            u['name'] = fx
        ux = UNIT_FIX.get((no, u.get('a')))
        if ux:
            u.update(ux)
    return r


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
        r = _fill_zuo(no, r)
    r = _apply_frag(no, r)
    _fix_names(no, r)
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
    # 據 CBETA cbeta_gaiji 對照表補（Unicode Ext A／B，通行字體可顯示）
    '[弓*朁]': '㣅', '[斯/瓦]': '㽄', '[月*冓]': '䐟', '[米*番]': '䊩',
    '[糸*耳]': '䋙', '[肖*毛]': '㲖', '[革*卬]': '䩕', '[革*茸]': '䩸',
    '[馬*父]': '䭸', '[麥*弋]': '䴬', '[麥*戈]': '䴰',
    '[卄/告]': '𦮽', '[卄/毦]': '𦶇', '[口*荼]': '𠻬', '[旁*毛]': '𣯟',
    '[木*戈]': '𣏾', '[沙/虫]': '𧋊',
    # 據 cbeta_gaiji 再補（皆 Unicode Ext A，仿宋、雅黑、宋體皆有字形）
    '[泳-永+羨]': '㵪', '[口*集]': '㗱', '[仁-二+達]': '㒓',
    '[革*玄]': '䩙', '[打-丁+沓]': '㧺', '[革*必]': '䩛',
    '[病-丙+貴]': '㿉', '[宋-木+喬]': '㝯', '[仁-二+匡]': '㑌',
    '[叟*毛]': '㲣', '[禾*秀]': '䅎', '[飢-几+(堶-土)]': '䭉',
    '[打-丁+鳥]': '㨶', '[跳-兆+詹]': '䠨', '[鹿*瓦]': '㼾',
    '[打-丁+毛]': '㧌', '[穩-禾+糸]': '䌥', '[仁-二+戾]': '㑦',
    '[打-丁+先]': '㧥', '[糸*爭]': '䋫', '[口*窒]': '㗧',
    '[女*占]': '㚲', '[虫*豕]': '䖶',
    # Unicode Ext B（仿宋無字形，瀏覽器／打印時由系統字體補足）
    '[跳-兆+互]': '𧿟', '[外*男]': '𡖦', '[口*磬]': '𡄇',
    '[怡-台+龍]': '𢤱', '[口*數]': '𡂡', '[革*雍]': '𩍓',
    '[戀-心+廾]': '𢍶', '[口*匿]': '𠽋', '[虫*賴]': '𧔣',
    '[矛*(替-曰+貝)]': '𥎞', '[竺-二+發]': '𥳊', '[這-言+(序-予+手)]': '𨓍',
    '[歹*斯]': '𣩠', '[竺-二+處]': '𥱿', '[王*車]': '𤥭',
    '[袖-由+未]': '𧙕', '[金*纂]': '𨰭', '[序-予+禾]': '𢇲',
    '[皮*宿]': '𥀝', '[起-巳+厥]': '𧽸', '[金*葛]': '𨭛',
    '[病-丙+干]': '𤴲', '[門@視]': '𨶳',
    # 據 CBETA 造字對照表：CB01738 即 U+246C6「𤛆」，義同「犛」。
    # 全角括號一形係舊稿錄入時所生，一併收之。
    '[牧/(厂@牛)]': '犛', '[牧/（厂@牛）]': '犛',
}

GLYPH_TITLE = GLYPH_MAP


def glyph_fix(s):
    """組字式代通行字；未收者仍存原式，以存底本之真。

    存原式者，其「*」代以全角「＊」——否則 * 前後成對，會被 Markdown
    當作強調標記，`[肖*毛]` 遂渲染為「[肖」＋斜體「毛]」。
    """
    if not s or '[' not in s:
        return s
    for k, v in GLYPH_MAP.items():
        if k in s:
            s = s.replace(k, v)
    s = re.sub(r'\[([^\[\]]{1,24})\]', lambda m: '[' + m.group(1).replace('*', '＊') + ']', s)
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


_NI_JIE = None


def _ni_jie_map():
    """尼單提節 → 戒名（內容對位，見 tools/build_ni_jie.py）。

    戒本 178 名與廣律 170 節次序不同，不能按節序套；此表逐節按戒文對位。
    """
    global _NI_JIE
    if _NI_JIE is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'ni_jie_map.json')
        try:
            with open(p, encoding='utf-8') as f:
                _NI_JIE = json.load(f)
        except Exception:
            _NI_JIE = {}
    return _NI_JIE


def unit_label(u, no=None):
    """節的顯示名（不含段範圍）。

    no 為篇號；若該聚類已登錄正式簡稱，則優先回傳之
    （如篇 010 第十九戒 →「十九、貿錢寶戒」）。未登錄者仍用原節題。
    """
    if no is not None:
        # 尼單提：節序與戒本次序不同，須按內容對位表取名（不限 fam，
        # 少數節 jie_family 未判而仍屬尼單提）
        _v = _ni_jie_map().get(f'{no}|{u["a"]}')
        if _v:
            # 尼單提亦冠戒號（1–178 連續），與比丘「十九、蟲水澆泥草戒」同例。
            # 名表本身不含號，故取該節的 num；缺 num 時退回中文節序。
            _seq = u.get('num') or _cn2int((u.get('cn') or '').strip())
            _pre = f'{_cn_num(_seq)}、' if _seq else ''
            return _pre + '／'.join(_v)
        fam = jie_family(no, u)
        if fam:
            # 尼單提用續編號 num（戒序 1–178）；比丘用 cn 轉數字
            seq = u.get('num') or _cn2int((u.get('cn') or '').strip())
            if seq and (no, u['a']) in JIE_MULTI:
                _a = JIE_NAMES.get(fam + '|' + str(seq - 1))
                _b = JIE_NAMES.get(fam + '|' + str(seq))
                if _a and _b:
                    return _a + '／' + _b
            if seq and (fam + '|' + str(seq)) in JIE_NAMES:
                _nm = JIE_NAMES[fam + '|' + str(seq)]
                # 提舍尼自成一聚，戒號復從「一」起；篇旨已言「節名冠以
                # 〔波羅提提舍尼〕以別之」，此處補冠，免與單提末戒混序。
                if fam == '比丘提舍尼':
                    _nm = '〔波羅提提舍尼〕' + _nm
                return _nm
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
