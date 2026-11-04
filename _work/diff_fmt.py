#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""差異說明的可讀性處理。

六件事，都不改事實，只改指代與排版：
  1. expand_refs  —— 「兩律」「三律」「本律」換成具體律名（由五欄判定，可判定率 98%）
  2. tidy_punct   —— 段號用連字號、卷號用波浪號、半形括號改全形
  3. split_sentences —— 依句號斷行，過長者再依分號斷（括號內不斷）
  4. split_by_canon  —— 一句並列數律者，於「，X律」處再分，一律一行
  5. label_of     —— 末句只是「判罪輕重不同」一類的分類語，降為項末小字「異在：…」
  6. bold_canons  —— 律名加粗，便於掃讀

用法：
    from diff_fmt import diff_lines
    lines = diff_lines(row)      # row 為 matrix_built 的一列
"""
import re

CANONS = [('v4', '四分'), ('v5', '五分'), ('v10', '十誦'), ('vMK', '僧祇'), ('vGU', '根有')]
ORDER = ['四分', '五分', '十誦', '僧祇', '根有']
NUM = {'兩': 2, '二': 2, '三': 3, '四': 4}

RE_REF = re.compile(r'([兩二三四])(部)?律')
RE_SELF = re.compile(r'(本律|此律)(首|冠辭|全文|全篇|開頭)?')
RE_CANON = re.compile(r'(四分|五分|十誦|僧祇|根有)(律?)')
RE_SENT = re.compile(r'[^。]*。|[^。]+$')


def _sets(row):
    """回傳（他律清單, 含本律清單），只計已比對者，按傳統次序。"""
    others = [n for k, n in CANONS if n != row.get('canon') and row.get(k) not in ('', '未比')]
    whole = [row.get('canon')] + others
    others.sort(key=ORDER.index)
    whole.sort(key=ORDER.index)
    return others, whole


def expand_refs(text, row):
    """「兩律」→具體律名；「本律」「此律」→本稿律名。無法判定者原樣保留。"""
    others, whole = _sets(row)
    no = sorted([n for k, n in CANONS if n != row.get('canon') and row.get(k) == '無'],
                key=ORDER.index)
    yes = sorted([n for k, n in CANONS if n != row.get('canon') and row.get(k) == '有'],
                 key=ORDER.index)

    def sub(m):
        n = NUM[m.group(1)]
        # 「二部律」為專名（比丘、比丘尼二部之律），不可拆
        if m.group(2) and m.group(1) == '二':
            return m.group(0)
        # 先看本句語氣：句中有「無」「不」者取無此制之律，言「有」「同」者取有之律
        seg = re.split(r'[。；]', text[m.end():])[0]
        if re.search(r'[無不缺乏闕未]', seg) and len(no) == n:
            return '、'.join(no)
        if re.match(r'^[^，。；]{0,4}(有|同)', seg) and len(yes) == n:
            return '、'.join(yes)
        if len(others) == n:
            return '、'.join(others)
        if len(whole) == n:
            return '、'.join(whole)
        # 兩者皆不合，即上下文不足以判定所指，寧存舊文，不可臆斷
        return m.group(0)

    text = RE_REF.sub(sub, text)

    def sub_self(m):
        name = row.get('canon') or '本律'
        tail = m.group(2) or ''
        if tail == '首':
            tail = '篇首'
        elif tail in ('冠辭', '全文', '全篇', '開頭'):
            tail = ''
        return name + tail

    return RE_SELF.sub(sub_self, text)


def bold_canons(text, once=True, skip=()):
    """律名加粗（含其後之「律」字）。已在 ** 內者不重複。

    once=True 時，同一段文字中每部律只標首次，免粗體過密反失焦點。
    skip 為不再加粗之律名（用於承接上條、同一主語之續條）。
    """
    out, i, seen = [], 0, set()
    for m in RE_CANON.finditer(text):
        if text[:m.start()].count('**') % 2 == 1:
            continue
        if once and m.group(1) in seen:
            continue
        seen.add(m.group(1))
        if m.group(1) in skip:
            continue
        out.append(text[i:m.start()])
        out.append('**' + m.group(1) + m.group(2) + '**')
        i = m.end()
    out.append(text[i:])
    return ''.join(out)


def _split_long(s):
    """長句依分號斷，但括號內的分號不算。"""
    depth, cuts = 0, []
    for i, ch in enumerate(s):
        if ch in '（(':
            depth += 1
        elif ch in '）)':
            depth = max(0, depth - 1)
        elif ch == '；' and depth == 0:
            cuts.append(i)
    if not cuts:
        return [s]
    out, prev = [], 0
    for c in cuts:
        out.append(s[prev:c].strip() + '。')
        prev = c + 1
    tail = s[prev:].strip()
    if tail:
        out.append(tail)
    return out


def split_sentences(text, limit=110):
    """依句號斷句；單句超過 limit 字者再依分號斷。

    括號（）與引號「」之內的句號不算句末——舊用正則 `[^。]*。` 會在
    「（……見 M-2102。）」處切斷，把「）」孤懸成一行。
    """
    sents, buf, dq, dp = [], '', 0, 0
    for ch in text:
        if ch in '「『':
            dq += 1
        elif ch in '」』':
            dq = max(0, dq - 1)
        elif ch in '（(':
            dp += 1
        elif ch in '）)':
            dp = max(0, dp - 1)
        buf += ch
        if ch == '。' and dq == 0 and dp == 0:
            sents.append(buf.strip())
            buf = ''
    if buf.strip():
        sents.append(buf.strip())
    out = []
    for s in sents:
        if len(s) > limit:
            out.extend(_split_long(s))
        else:
            out.append(s)
    return out


# ---------- 一律一行 ----------

RE_CANON_HEAD = re.compile(r'(?:亦|又|而|然|但)?(四分|五分|十誦|僧祇|根有)')
RE_NUMBERED = re.compile(r'^[（(]?[一二三四五六七八九十]+[、）)]')


def split_by_canon(s, min_len=6):
    """把一句之內並列諸律者，於「，X律」「；X律」處分為數條，一律一行。

    凡例九所許「各律分述者，每律自成一條」，舊稿多未做到；此處只斷句、
    不改字，故不涉事實。二事不斷：
      · 引號「」與括號（）之內，屬引文或夾註；
      · 前段不足 min_len 字者，斷之則成殘句。
    """
    if RE_NUMBERED.match(s):          # 「一、二、三」自有層次，不拆
        return [s]
    if len(set(RE_CANON.findall(s))) < 2:
        return [s]
    out, buf, dq, dp = [], '', 0, 0
    for i, ch in enumerate(s):
        if ch in '「『':
            dq += 1
        elif ch in '」』':
            dq = max(0, dq - 1)
        elif ch in '（(':
            dp += 1
        elif ch in '）)':
            dp = max(0, dp - 1)
        if ch in '，；' and dq == 0 and dp == 0 and RE_CANON_HEAD.match(s[i + 1:]):
            if len(re.sub(r'\W', '', buf)) >= min_len:
                out.append(buf.rstrip('，；') + '。')
                buf = ''
                continue
        buf += ch
    if buf.strip():
        out.append(buf.strip())
    return out


# ---------- 總結句降為標籤 ----------

RE_LABEL = re.compile(
    r'^(?:故|此|是故|要之|總之)?(.{2,14}?)(?:均|皆|俱|盡|各|互|全)?'
    r'(?:不同|有別|為異|相異|大異|迥異|略異|小異|異)[。]?$')
RE_LABEL2 = re.compile(r'^此為(.{2,18}?)之(?:差|差異|異)[。]?$')


def label_of(s):
    """末句若只是「判罪輕重不同」一類的分類語，取出其分類，改作項末小字。

    此類句不含新事實，只是給前文貼標籤；留作正文則與前句重複，
    降為「異在：…」反便掃讀。非此類者回空字串，原句不動。
    """
    t = s.replace('**', '').strip()
    if len(t) > 18:
        return ''
    m = RE_LABEL.match(t)
    if not m:
        m = RE_LABEL2.match(t)
    if not m:
        return ''
    tag = m.group(1).strip()
    # 只收「判罪輕重」一類的純分類語；含律名、標點、引文者仍屬正文，不動
    if re.search(r'[，、；：「」（）]', tag) or RE_CANON.search(tag):
        return ''
    tag = re.sub(r'(實質|根本|全然|大致|約|略|微|甚|大|小|迥|全|盡)$', '', tag).strip()
    tag = re.sub(r'(之|的|其)$', '', tag).strip()
    return tag


def merge_topic(lines, max_len=14, cap=60):
    """短小的「話題句」併入下一條，免得獨立成行而無所依。

    如「同一六群比丘障難受戒的因緣。」本是下文的前提，獨占一行則讀來
    突兀；併入則成「…因緣，五分律制…」。凡含律名、或以「此、故、是」
    起首者（多為結論句）不併，以免把結論黏到下一事。
    """
    out = []
    for s in lines:
        if (out and out[-1].endswith('。')
                and len(re.sub(r'\W', '', out[-1])) <= max_len
                and not RE_CANON.search(out[-1])
                and not re.match(r'^(此|故|是|然|其|要)', out[-1])
                and RE_CANON_HEAD.match(s)
                and len(out[-1]) + len(s) <= cap):
            out[-1] = out[-1][:-1] + '，' + s
        else:
            out.append(s)
    return out


def tidy_punct(s):
    """段號用連字號（–），卷號用波浪號（～），半形括號改全形。"""
    s = re.sub(r'段(\d+)\s*[-—–~～]\s*(\d+)', r'段\1–\2', s)
    s = re.sub(r'卷(\d+)\s*[-—–~]\s*(\d+)', r'卷\1～\2', s)
    s = re.sub(r'\(([^)（）]*[\u4e00-\u9fff][^)（）]*)\)', r'（\1）', s)
    return s


def merge_tail(lines, max_len=14, cap=120):
    """末條過短者併回前條，免「四分、五分、十誦俱無。」孤懸一行。"""
    if len(lines) > 1 and lines[-1].endswith('。'):
        tail = lines[-1]
        if (len(re.sub(r'\W', '', tail)) <= max_len
                and len(lines[-2]) + len(tail) <= cap):
            lines = lines[:-2] + [lines[-2][:-1] + '，' + tail]
    return lines


RE_LIST_LEAD = re.compile(r'^(?P<lead>[^：，。；]{2,16})：(?P<body>[^。；]+)。$')


def _split_dun(body):
    """依頂層頓號切分（括號、引號內者不切）"""
    out, buf, d = [], '', 0
    for ch in body:
        if ch in '（「『〈《':
            d += 1
        elif ch in '）」』〉》':
            d = max(0, d - 1)
        buf += ch
        if ch == '、' and d == 0:
            out.append(buf[:-1])
            buf = ''
    if buf:
        out.append(buf)
    return out


def listify(line, maxlen=34):
    """把「主句：A、B、C……」之長列舉拆為縮排小列，字句不動。

    一句列二十餘法目，通欄而下則難尋其目；此處只分行，不改一字。
    回傳 (引導行, [小列…]) 或 None（不合此形者原樣）。
    """
    m = RE_LIST_LEAD.match(line)
    if not m:
        return None
    body = m.group('body')
    if body.count('、') < 8:
        return None
    items = _split_dun(body)
    n = len(items)
    k = max(2, (n + 5) // 6)          # 每列約五六目，末列不使孤懸一二目
    base, rem = divmod(n, k)
    chunks, i = [], 0
    for j in range(k):
        size = base + (1 if j < rem else 0)
        chunks.append('、'.join(items[i:i + size]))
        i += size
    if len(chunks) < 2:
        return None
    chunks[-1] += '。'
    return f"- {m.group('lead')}：", [f'  - {c}' for c in chunks]


def diff_lines(row, bold=True, expand=True, limit=110):
    """回傳可直接寫入 Markdown 的行（不含尾隨空行）。"""
    text = (row.get('diff_full') or row.get('diff') or '').replace('\n', ' ').strip()
    if not text:
        return []
    if expand:
        text = expand_refs(text, row)
    text = tidy_punct(text)
    sents = split_sentences(text, limit)

    lines = []
    for s in sents:
        lines.extend(split_by_canon(s))

    tag = ''
    if len(lines) > 1:
        t = label_of(lines[-1])
        if t:
            tag = t
            lines.pop()

    lines = merge_topic(lines)
    lines = merge_tail(lines)

    if bold:
        out_b, prev = [], None
        for s in lines:
            m = RE_CANON_HEAD.match(s)
            lead = m.group(1) if m else None
            # 承接上條、主語仍同者，不再加粗，免得滿篇粗體
            out_b.append(bold_canons(s, skip={lead} if lead and lead == prev else ()))
            prev = lead
        lines = out_b
    if not lines:
        return []
    parts, nested = [], False
    for s in lines:
        lf = listify(s)
        if lf:
            nested = True
            parts.append(lf[0])
            parts.extend(lf[1])
        else:
            parts.append(f'- {s}')
    if len(lines) == 1 and not nested:
        out = [f'**差異**：{lines[0]}']
    else:
        out = ['**差異**'] + parts
    if tag:
        out += ['', f'<sub>異在：{tag}</sub>']
    return out


if __name__ == '__main__':
    import json, os, sys
    base = os.path.dirname(os.path.abspath(__file__))
    rows = json.load(open(os.path.join(base, 'matrix_built.json'), encoding='utf-8'))
    ids = sys.argv[1:] or ['M-0001', 'M-1329', 'M-1707']
    for i in ids:
        r = [x for x in rows if x['id'] == i][0]
        print('=' * 60)
        print(i, r['canon'], r['title'])
        print('原：', r['diff_full'])
        for ln in diff_lines(r):
            print('  ', ln)
