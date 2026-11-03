# -*- coding: utf-8 -*-
"""Pull the full 原文 of every narrative item out of the base text.

The 獨有敘事 appendix currently holds, for long stories, only a pointer
(「全文收錄：長篇，未譯，留指針」).  This script replaces that line with the
verbatim paragraphs named in the item's 位置 field — whole paragraphs, cut only
where the pointer itself names a bound (「至『X』」／「『X』以下」) — and says so
per item when 判文／制文 come along or when only half a paragraph was claimed.

usage: python extract_narr.py [--dry]     env: NARR_TARGET, NARR_BASE
"""
import os, re, io, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
TARGET = os.environ.get('NARR_TARGET') or os.path.join(
    ROOT, '根本說一切有部毘奈耶_去重白話',
    '根本說一切有部毘奈耶_去重白話_獨有敘事.md')
BASE = os.environ.get('NARR_BASE') or os.path.join(W, 'genben')
DRY = '--dry' in sys.argv

P = {}


def paras(v):
    if v not in P:
        f = os.path.join(BASE, 'vol%02d.txt' % v)
        if not os.path.exists(f):
            return None
        P[v] = {}
        for line in io.open(f, encoding='utf-8'):
            parts = line.rstrip('\n').split('\t', 1)
            if len(parts) != 2 or not parts[0].strip().isdigit():
                continue
            P[v][int(parts[0])] = parts[1]
    return P[v]


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def cjk(s):
    return len(norm(s))


VOL_RE = re.compile(r'^-\s*所屬[：:]\s*卷\s*(\d{1,2})', re.M)
POS_RE = re.compile(r'^-\s*位置[：:](.*)$', re.M)
FULL_RE = re.compile(r'^-\s*全文收錄[：:].*(?:\n(?![->#])]*)?', re.M)
KEEP_RE = re.compile(r'長篇|未譯|留指針|只存指針')
# 卷N·段M  /  段M  /  段M～N  inside quotes
Q_RE = re.compile(r'^\s*(?:[*（(【〔\[]?\s*(?:卷\s*(\d{1,2})\s*[·・]\s*)?段\s*(\d{1,3})'
                  r'(?:\s*[～~－–]\s*(?:段\s*)?\d{1,3})?[^*）)】〕\]]*\*\*\s*)'
                  r'(?:[（(【〔]?\s*(?:卷\s*(\d{1,2})\s*[·・]\s*)?段\s*(\d{1,3})[^）)】〕]*[）)】〕]?)?\s*'
                  r'(?:卷\s*(\d{1,2})\s*[·・]\s*)?段?\s*(\d{1,3})?\s*(?:[（(]?[：:])?\s*(.*)$')


MOD_TAIL = re.compile(r'除|不含|至『|至「|前半|前段|末段判|判文|制文|節引|以下')
MOD_HEAD = re.compile(r'後半|中段|以下')
RANGE_RE = re.compile(r'段\s*(\d{1,3})\s*(?:[～~－–]\s*(?:段\s*)?(\d{1,3}))?')


def strip_brackets(s):
    for pat in (r'「[^」]*」', r'『[^』]*』', r'〔[^〕]*〕', r'【[^】]*】',
                r'\([^)]*\)', r'（[^）]*）'):
        for _ in range(3):
            new = re.sub(pat, '', s)
            if new == s:
                break
            s = new
    return s


def pos_ranges(s):
    """Return ([(a, b)], start_mod, stop_mod, stated)."""
    clean = strip_brackets(s)
    clean = re.sub(r'字數約?\s*[\d,，]{2,8}\s*字?', '', clean)
    clean = re.sub(r'約\s*[\d,，]{2,8}\s*字', '', clean)
    rs = []
    for seg in re.split(r'[、,，;；\s]+', clean):
        m = re.search(r'段\s*(\d{1,3})\s*(?:[～~－–]\s*(?:段\s*)?(\d{1,3}))?', seg)
        if m:
            rs.append((int(m.group(1)), int(m.group(2) or m.group(1))))
        elif re.fullmatch(r'\d{1,3}', seg):
            rs.append((int(seg), int(seg)))
    rs = [(a, b) for a, b in rs if b >= a and a >= 1]
    merged = []
    for a, b in rs:
        if merged and a <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    start_mod = bool(MOD_HEAD.search(s))
    stop_mod = bool(MOD_TAIL.search(s))
    st = re.search(r'字數約?\s*([\d,，]{2,8})\s*字?', s)
    stated = int(re.sub(r'[,，]', '', st.group(1))) if st else 0
    return merged, start_mod, stop_mod, stated


Q_PATS = [
    r'^\*\*\s*(?:卷\s*(\d{1,2})\s*[·・]\s*)?段\s*(\d{1,3})[^*]{0,14}\*\*\s*[　:：]?\s*(.*)$',
    r'^[（(【〔\[]\s*(?:卷\s*(\d{1,2})\s*[·・]\s*)?段\s*(\d{1,3})[^）)】〕\]]{0,14}[）)】〕\]]\s*[：:]?\s*(.*)$',
    r'^\s*(?:卷\s*(\d{1,2})\s*[·・]\s*)?段\s*(\d{1,3})\s*[：:]\s*(.*)$',
    r'^\s*(?:卷\s*(\d{1,2})\s*[·・]\s*)?第\s*(\d{1,3})\s*段\s*[：:]?\s*(.*)$',
    r'^\s*(?:卷\s*(\d{1,2})\s*[·・]\s*)?段\s*(\d{1,3})\s*[　\s]*(.*)$',
]


def split_q(line):
    """(vol, para, text) if the quote line starts with a paragraph label."""
    body = line.lstrip('>').strip()
    if not body or body.startswith('（中略') or body.startswith('(中略'):
        return None
    for p in Q_PATS:
        m = re.match(p, body, re.S)
        if m:
            v = m.group(1)
            return (int(v) if v else None, int(m.group(2)), m.group(3).strip())
    return None


def item_quotes(block):
    """(para, sentence-text) pairs actually quoted inside an item."""
    out = []
    for line in block.split('\n'):
        s = line.strip()
        if not s.startswith('>'):
            continue
        q = split_q(s)
        if q and norm(q[2]):
            out.append((q[0], q[1], q[2]))
    return out


def cut_start(text, first_q):
    if not first_q:
        return text
    n_first = norm(first_q)
    if not n_first:
        return text
    # walk the original text, keeping a map from normalised index to raw index
    idx, raw_at = [], []
    for i, ch in enumerate(text):
        if norm(ch):
            raw_at.append(i)
            idx.append(ch)
    joined = ''.join(idx)
    p = joined.find(n_first)
    if p < 0:
        return text
    return text[raw_at[p]:]


def cut_end(text, last_q):
    if not last_q:
        return text
    n_last = norm(last_q)
    if not n_last:
        return text
    raw_at, idx = [], []
    for i, ch in enumerate(text):
        if norm(ch):
            raw_at.append(i)
            idx.append(ch)
    joined = ''.join(idx)
    p = joined.find(n_last)
    if p < 0:
        return text
    end = raw_at[min(p + len(n_last) - 1, len(raw_at) - 1)]
    # extend to the closing punctuation of that sentence
    tail = text[end:]
    m = re.search(r'^[^。！？]*[。！？]?[」』)）]?', tail)
    stop = end + (m.end() if m else 1)
    return text[:stop]


def render(vol, ranges, chunks, note_tag=''):
    span = '、'.join('段{}～{}'.format(a, b) if b > a else '段{}'.format(a) for a, b in ranges)
    lines = ['- 全文收錄（卷{}·{} 逐字抽出，未譯{}）：'.format(vol, span, note_tag), '']
    for v, p, t in chunks:
        if p is None:
            lines.append('> {}'.format(t))
        else:
            lines.append('> **卷{}·段{}**　{}'.format(v, p, t.strip()))
    return '\n'.join(lines)


src = io.open(TARGET, encoding='utf-8').read()
head, tail = src.split('## 目錄', 1)
items = re.split(r'(?m)^(### )', tail)
# rebuild: items[0] is the preamble after 目錄
blocks = [items[0]] + [items[i] + items[i + 1] for i in range(1, len(items) - 1, 2)]

report, done, skipped, failed = [], 0, 0, []
out_blocks = [blocks[0]]
for blk in blocks[1:]:
    title = blk.split('\n')[0].lstrip('# ').strip()
    fm = FULL_RE.search(blk)
    if not fm or not KEEP_RE.search(fm.group(0)):
        skipped += 1
        out_blocks.append(blk)
        continue
    vm = VOL_RE.search(blk)
    pm = POS_RE.search(blk)
    if not vm or not pm:
        failed.append((title[:30], '無所屬或位置'))
        out_blocks.append(blk)
        continue
    vol = int(vm.group(1))
    ranges, start_mod, stop_mod, stated = pos_ranges(pm.group(1))
    if not ranges:
        failed.append((title[:30], '位置不可解析:' + pm.group(1)[:24]))
        out_blocks.append(blk)
        continue
    ps = paras(vol)
    if ps is None:
        failed.append((title[:30], '無底本卷{}'.format(vol)))
        out_blocks.append(blk)
        continue
    pos = pm.group(1)
    # boundaries the pointer itself names (「X」以下 / 至「X」) — nothing else is trimmed,
    # so trailing 判文／制文 come along and the header says so.
    m_from = re.search(r'[「『]([^」』]{2,30})[」』]\s*以下', pos)
    m_to = re.search(r'至[「『]([^」』]{2,40})[」』]', pos)
    note = []
    if m_to:
        note.append('至「{}」止'.format(m_to.group(1)))
    if m_from:
        note.append('自「{}」起'.format(m_from.group(1)))
    if not note:
        if re.search(r'前半|前段', pos):
            note.append('位置只取其前半，此處全段抽出')
        elif re.search(r'後半|中段', pos):
            note.append('位置只取其後半，此處全段抽出')
        elif stop_mod:
            note.append('末段判文、制文亦帶出')
    chunks, miss = [], []
    prev_b = None
    for ri, (a, b) in enumerate(ranges):
        if b - a > 80:
            b = a + 80
        if prev_b is not None and a > prev_b + 1:
            chunks.append((vol, None, '（中略：段{}～{}，非本事）'.format(prev_b + 1, a - 1)))
        prev_b = b
        for p in range(a, b + 1):
            t = ps.get(p)
            if t is None:
                miss.append(p)
                continue
            if p == a and m_from:
                t = cut_start(t, m_from.group(1))
            if p == b and m_to:
                t = cut_end(t, m_to.group(1))
            chunks.append((vol, p, t))
    note_tag = '；' + '；'.join(note) if note else ''
    if not chunks:
        failed.append((title[:30], '段區無正文'))
        out_blocks.append(blk)
        continue
    got = sum(cjk(t) for _, _, t in chunks)
    raw = sum(cjk(ps[p]) for p in range(ranges[0][0], ranges[-1][1] + 1) if p in ps)
    new = render(vol, ranges, chunks, note_tag)
    blk2 = blk[:fm.start()] + new + blk[fm.end():]
    out_blocks.append(blk2)
    done += 1
    span = '、'.join('{}～{}'.format(a, b) if b > a else str(a) for a, b in ranges)
    flags = []
    if got < raw:
        flags.append('依指針斷取，省{:,}字'.format(raw - got))
    if stated and not (0.55 * stated <= raw <= 1.3 * stated):
        flags.append('自報{:,}與底本{:,}不合'.format(stated, raw))
    report.append('{}|卷{}段{}|抽出{:,}字|底本{:,}字|自報{:,}字|{}段{}{}'.format(
        title[:26], vol, span, got, raw, stated, len(chunks), miss and '|漏段{}'.format(miss) or '',
        ('  << ' + '；'.join(flags)) if flags else ''))
    if flags:
        print('  DEBUG', title[:26], '| 位置:', pos[:60])
        print('        ranges', ranges, 'note', note_tag)
    if miss:
        failed.append((title[:30], '漏段 {}'.format(miss)))

new_src = head + '## 目錄' + ''.join(out_blocks)
# renumber per-volume headings stay as they are; just note the change in 凡例
note = ('\n> 抽出口徑：依各條『位置』所記段區間，自底本 `_work/%s/volNN.txt` 整段逐字錄出，不作節略。'
        '僅當指針自註「至『X』」或「『X』以下」時方於該處斷取；與本事同段之判文、制文不獲已而帶出者，'
        '逐條註「末段判文、制文亦帶出」；指針只取段之前半或後半而此處全段錄出者，'
        '註「位置只取其前半／後半，此處全段抽出」；段區間內非本事之段，'
        '以「（中略：段X～Y，非本事）」跳過。只錄原文，未譯白話；'
        '引文行數與逐字之核，由 `_work/qc_narr.py` 於產物上實測。\n') % os.path.basename(BASE)
if '抽出口徑' not in new_src.split('## 目錄')[0]:
    new_src = new_src.replace('便於另行取用。\n', '便於另行取用。\n' + note, 1)

print('items', len(out_blocks) - 1, 'filled', done, 'already full/skip', skipped, 'failed', len(failed))
print('added CJK chars', sum(cjk(b) for b in out_blocks) - sum(cjk(b) for b in blocks))
for f in failed:
    print('  FAIL', f)
odd = [r for r in report if '<<' in r]
print('flagged items:', len(odd))
for r in odd[:20]:
    print('  ', r)
if not DRY:
    io.open(TARGET, 'w', encoding='utf-8').write(new_src)
    print('written', TARGET, len(new_src), 'sha1', hashlib.sha1(new_src.encode('utf-8')).hexdigest()[:12])
else:
    print('dry run, nothing written')
    for r in report[:12]:
        print('   ', r)
