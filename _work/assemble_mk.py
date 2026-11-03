# -*- coding: utf-8 -*-
"""摩訶僧祇律去重白話 edition assembler.

Re-anchors every 原文 quote to the base text (verbatim guarantee), keeps the
白話 / 差異 / 對照 fields as authored, and splits 敘事抽取 into a separate file.
Run after _work/findings_mk/*.md are produced."""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
OUT = os.path.join(ROOT, '摩訶僧祇律_去重白話')

SRC_DIR = os.environ.get('MK_SRC') or os.path.join(W, 'findings_mk')
UNITS = json.load(open(os.path.join(W, os.environ.get('MK_UNITS', 'mk_units.json')), encoding='utf-8'))

FIELDS = ['位置', '所屬', '四分律對照', '五分律對照', '十誦律對照', '三律對照',
          '差異說明', '要旨', '全文收錄']
META_START = ('底本', '對校本', '對照本', '凡例', '口徑', '說明：', '原文欄', '體例',
              '校勘', '本卷字數', '以下各條', '查詢詞：本')


def strip_head(s):
    return re.sub(r'^#+ .*$', '', (s or '').strip(), flags=re.M).strip()


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def fmt(raw):
    """'段15–26、31' -> '第15～26段、第31段'; anything odder is left untouched."""
    if not raw:
        return ''
    out = []
    for seg in re.split(r'[,，]', raw):
        seg = seg.strip()
        m = re.match(r'^(\d{1,3})\s*[～~－-–]\s*(\d{1,3})$', seg)
        if m:
            out.append('第{}～{}段'.format(m.group(1), m.group(2)))
        elif re.match(r'^\d{1,3}$', seg):
            out.append('第{}段'.format(seg))
        else:
            return raw
    return '、'.join(out)


PARAS = {}
BASE_DIR = os.environ.get('MK_BASE') or os.path.join(W, 'sengqi')


def paras(v):
    if v not in PARAS:
        p = os.path.join(BASE_DIR, 'vol%02d.txt' % v)
        PARAS[v] = [(int(n), t) for n, t in
                    (l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8'))]
    return PARAS[v]


def src_index(vols, rng):
    ns, spans = [], []
    for v in vols:
        for pid, t in paras(v):
            if rng and not (rng[0] <= pid <= rng[1]):
                continue
            start = len(''.join(ns))
            n = norm(t)
            ns.append(n)
            spans.append((start, start + len(n), v, pid, t))
    return ''.join(ns), spans


def locate(pos, spans):
    for a, b, v, pid, t in spans:
        if a <= pos < b:
            return v, pid
    return None, None


def sentences(q):
    return [p for p in re.split(r'(?<=[。！？：])', q) if norm(p)]


def recover(seg, src, start=0):
    """Locate seg at or after start. Monotonic: never matches before start."""
    n = norm(seg)
    if not n:
        return None
    i = src.find(n, start)
    if i >= 0:
        return (i, i + len(n))
    for L in range(len(n), 8, -1):
        if L < 10:
            break
        i = src.find(n[:L], start)
        if i >= 0:
            return (i, i + L)
    return None


def clean_label(q):
    q = re.sub(r'^\s*\*\*[^*]{0,40}\*\*\s*', '', q)
    q = re.sub(r'^\s*〔[^〕]{0,40}〕\s*', '', q)
    q = re.sub(r'^\s*【[^】]{1,40}】\s*', '', q)
    q = re.sub(r'^\s*卷\s*\d{1,2}\s*[·・/－-]\s*$', '', q)
    q = re.sub(r'^\s*[*（(【〔\[]?\s*卷\s*\d{1,2}\s*[·・/\s－-]?\s*段?\s*\d{1,3}'
               r'\s*(?:[～~－–]\s*(?:段\s*)?\d{1,3})?'
               r'\s*(?:前段|後段|中段|前半|後半|全段)?\s*[）)】〕\]]?\s*'
               r'(?:[（(]\s*(?:節引|節錄|有刪節|原文)\s*[）)])?\s*[*：:]?\s*', '', q)
    q = re.sub(r'^\s*[*（(【〔\[]?\s*(?:段|品)\s*\d{1,3}\s*(?:[～~－–]\s*(?:段\s*)?\d{1,3})?'
               r'\s*(?:前段|後段|中段|前半|後半)?\s*[）)】〕\]]?\s*[*：:]?\s*', '', q)
    q = re.sub(r'^\s*(?:段|品)\s*\d{1,3}\s*(?:[～~－-]\s*\d{1,3})?\s*(?:前段|後段|中段)?[^：:]{0,6}[：:]\s*', '', q)
    q = re.sub(r'^\s*[（(【〔][^）)】〕]{1,60}[）)】〕]\s*[：:]?\s*', '', q)
    return q


def reanchor(q, src, spans, multi, state=None):
    q = re.sub(r'[（(【〔\[]\s*(?:內?中略|節引|節錄|略)[^）)】〕\]]*[）)】〕\]]', ' ', q)
    q = clean_label(clean_label(q))
    found, lost = [], []
    cur = (state or {}).get('pos', 0)
    n = norm(q)
    # 1) whole-quote match first: a continuous quote must not be split into
    #    sentences, or short clauses like 「唯願世尊」 re-anchor to an earlier
    #    occurrence and the quote comes out scrambled.
    whole = None
    if len(n) >= 6:
        i = src.find(n, cur)
        if i < 0 and cur:
            i = src.find(n)
        if i >= 0:
            va, pa = locate(i, spans)
            vb, pb = locate(max(i, i + len(n) - 1), spans)
            # src 為各段相連，連續匹配可能跨段；跨段者改採逐句回錨，
            # 否則一行只掛首段之段號而內含他段文字，標籤即與內容不合。
            if pa == pb:
                whole = (i, i + len(n), q.strip())
    if whole:
        a, b, txt = whole
        va, pa = locate(a, spans)
        vb, pb = locate(max(a, b - 1), spans)
        found.append([a, b, pa, pb or pa, va or vb, txt])
    else:
        cursor = cur
        for sent0 in sentences(q):
            for piece in re.split(r'…+|\.{3,}', sent0):
                sent = clean_label(clean_label(piece))
                if len(norm(sent)) < 4:
                    continue
                hit = recover(sent, src, cursor)
                if not hit:
                    lost.append(sent.strip()[:60])
                    continue
                cursor = hit[1]
                a, b = hit
                va, pa = locate(a, spans)
                vb, pb = locate(max(a, b - 1), spans)
                found.append([a, b, pa, pb or pa, va or vb, sent.strip()])
    found.sort(key=lambda x: x[0])
    blocks = []
    last_para = state['para'] if state else None
    last_vol = state['vol'] if state else None
    prev_end = None
    for a, b, pa, pb, vv, txt in found:
        if last_para is not None and pa is not None and vv == last_vol and pa > last_para + 1:
            lo, hi = last_para + 1, pa - 1
            gap = '（中略：段{}～{}）'.format(lo, hi) if hi > lo else '（中略：段{}）'.format(lo)
            blocks.append(('gap', gap, None))
        if blocks and blocks[-1][0] != 'gap' and blocks[-1][0] == pa and blocks[-1][2] == vv:
            # never stitch non-adjacent text into one continuous-looking quote:
            # an intra-paragraph skip must be marked with an ellipsis.
            sep = '' if (prev_end is not None and a <= prev_end) else '……'
            blocks[-1] = (pa, blocks[-1][1] + sep + txt, vv)
        else:
            blocks.append((pa, txt, vv))
        prev_end = b
        last_para, last_vol = pb, vv
    if state:
        state['para'], state['vol'] = last_para, last_vol
        if found:
            state['pos'] = max(x[1] for x in found)
    rendered = []
    chars = 0
    for pid, txt, vv in blocks:
        if pid == 'gap':
            rendered.append('> ' + txt)
        else:
            tag = ('卷{}·'.format(vv)) if (vv and multi) else ''
            rendered.append('> **{}段{}**　{}'.format(tag, pid, txt))
            chars += len(norm(txt))
    return rendered, lost, chars


def render_item(title, body, src, spans, multi):
    """Emit one item: fields verbatim, 原文 block re-anchored, 白話 preserved."""
    lines = body.split('\n')
    out = [title.strip(), '']
    i, chars, lost, saw_quote = 0, 0, [], False
    state = {'para': None, 'vol': None, 'pos': 0}
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        m = re.match(r'^-\s*([^：:]{1,12})[：:]\s*(.*)$', s)
        key = m.group(1).strip() if m else None
        val = m.group(2).strip() if m else None
        if key in ('原文',):
            out.append('- 原文：')
            out.append('')
            state['para'] = None
            state['pos'] = 0
            i += 1
            qs = []
            if val.startswith('>'):
                qs.append(val.lstrip('>').strip())
            while i < len(lines):
                t = lines[i].strip()
                if t.startswith('>'):
                    b = t.lstrip('>').strip()
                    if b and not any(b.startswith(mm) for mm in META_START):
                        qs.append(b)
                    i += 1
                elif not t:
                    i += 1
                else:
                    break
            rl = []
            for q in qs:
                r2, lo, ch = reanchor(q, src, spans, multi, state)
                rl.extend(r2)
                chars += ch
                lost.extend(lo)
            out.extend(rl)
            if rl:
                out.append('')
            saw_quote = True
            continue
        if key in ('全文收錄',):
            # 短敘事之全文亦回錨加標籤；字數不另計（同段已计入 原文 欄），
            # 其後之「白話」續行由主圈原樣抄出。
            out.append('- 全文收錄：')
            out.append('')
            state['para'] = None
            state['pos'] = 0
            i += 1
            qs = []
            if val.startswith('>'):
                qs.append(val.lstrip('>').strip())
            while i < len(lines):
                t = lines[i].strip()
                if t.startswith('>'):
                    b = t.lstrip('>').strip()
                    if b and not any(b.startswith(mm) for mm in META_START):
                        qs.append(b)
                    i += 1
                elif not t:
                    i += 1
                else:
                    break
            rl = []
            for q in qs:
                r2, lo, ch = reanchor(q, src, spans, multi, state)
                rl.extend(r2)
                lost.extend(lo)
            out.extend(rl)
            if rl:
                out.append('')
            continue
        if key == '白話':
            out.append('- 白話：')
            i += 1
            if val:
                out.append('  ' + val)
            while i < len(lines):
                t = lines[i].strip()
                if not t:
                    i += 1
                    continue
                if re.match(r'^-\s*[^：:]{1,12}[：:]', t) or t.startswith('#'):
                    break
                out.append('  ' + t.lstrip('>').strip() if t.startswith('>') else '  ' + t)
                i += 1
            continue
        if key in FIELDS:
            out.append('- {}：{}'.format(key, val))
            i += 1
            continue
        if s.startswith('>'):
            if not saw_quote:
                out.append('- 原文：')
                out.append('')
                state['para'] = None
                state['pos'] = 0
            b = s.lstrip('>').strip()
            i += 1
            if b and not any(b.startswith(mm) for mm in META_START):
                rl, lo, ch = reanchor(b, src, spans, multi, state)
                out.extend(rl)
                chars += ch
                lost.extend(lo)
            saw_quote = True
            continue
        if s.startswith('#'):
            break
        if s:
            out.append('  ' + s)
        i += 1
    txt = '\n'.join(out)
    txt = re.sub(r'\n{3,}', '\n\n', txt).strip()
    return txt, chars, lost


def del_sec(sec):
    """Deletion table section, tolerating 彙總/匯總 and a bare 刪除項 heading."""
    for k in ('刪除項（彙總）', '刪除項（匯總）', '刪除項'):
        if k in sec:
            return sec[k]
    for k in sec:
        if k.startswith('刪除項'):
            return sec[k]
    return ''


def quote_lines(md):
    """Verbatim quote bodies inside an item's 原文 block (gap markers excluded)."""
    qs, on = [], False
    for ln in md.split('\n'):
        k = ln.strip()
        if re.match(r'^-\s*原文[：:]', k):
            on = True
            continue
        if not on:
            continue
        if k.startswith('- ') or k.startswith('#'):
            break
        if k.startswith('>'):
            b = re.sub(r'^\*\*[^*]+\*\*\s*', '', k.lstrip('>').strip())
            if b and not b.startswith('（中略'):
                qs.append(b)
    return qs


def para_ids(md):
    """Paragraph numbers actually quoted (or skipped over) in an item."""
    out = set()
    for ln in md.split('\n'):
        k = ln.strip()
        if not k.startswith('>'):
            continue
        body = k.lstrip('>').strip()
        m = re.match(r'^\*\*(?:卷\d+·)?段(\d+)(?:～(\d+))?\*\*', body)
        if m:
            a = int(m.group(1))
            out.update(range(a, int(m.group(2) or a) + 1))
        elif body.startswith('（中略'):
            for x in re.findall(r'段(\d+)(?:～段?(\d+))?', body):
                a = int(x[0])
                out.update(range(a, int(x[1] or a) + 1))
    return out


def sections_of(text):
    pos = [(m.start(), m.group(1)) for m in re.finditer(r'^## (.*)$', text, re.M)]
    sec, intro = {}, text[:pos[0][0]] if pos else text
    for i, (p, name) in enumerate(pos):
        end = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        sec[name.strip()] = text[p:end]
    return sec, re.sub(r'^# .*$', '', intro, flags=re.M).strip()


def items_of(section):
    res = []
    for chunk in re.split(r'^### ', section, flags=re.M)[1:]:
        ls = chunk.split('\n')
        t = re.sub(r'^[\s\d]+[.、]\s*', '', ls[0].strip())
        if not t or t.startswith(('已知線索', '定稿補記')):
            continue
        if len(t) <= 14 and re.match(r'^(無|此卷無|本卷無|暫無)', t):
            continue
        res.append((t, '\n'.join(ls[1:])))
    return res


PILOT = bool(os.environ.get('MK_GU'))
META_F = os.path.join(W, os.environ.get('MK_META', 'mk_pilot_meta.json' if PILOT else 'mk_assemble_meta.json'))
UOUT_F = os.path.join(W, os.environ.get('MK_UOUT', 'mk_pilot_units.json' if PILOT else 'mk_units_out.json'))

units_out, stats, all_lost, missing = [], [], [], []
for u in ([] if os.environ.get('MK_PILOT') else UNITS):
    f = os.path.join(SRC_DIR, u['unit'] + '.md')
    if not os.path.exists(f):
        missing.append(u['unit'])
        continue
    text = open(f, encoding='utf-8').read()
    sec, intro = sections_of(text)
    src, spans = src_index(u['vols'], tuple(u['rng']) if u.get('rng') else None)
    multi = len(u['vols']) > 1
    keep, narr = [], []
    ck = nc = 0
    for n, (t, b) in enumerate(items_of(sec.get('保留項', '')), 1):
        r, ch, lo = render_item('### {}. {}'.format(n, t), b, src, spans, multi)
        keep.append(r)
        ck += ch
        if lo:
            all_lost.append({'unit': u['unit'], 'kind': 'keep', 'item': t[:30], 'lost': lo})
    for n, (t, b) in enumerate(items_of(sec.get('敘事抽取', '')), 1):
        # 敘事項入另檔，另檔混列各單位，故一律標「卷N·段M」使每行自定位
        r, ch, lo = render_item('### {}. {}'.format(n, t), b, src, spans, True)
        narr.append({'unit': u['unit'], 'title': u['title'], 'vols': u['vols'], 'md': r, 'chars': ch})
        nc += ch
        if lo:
            all_lost.append({'unit': u['unit'], 'kind': 'narr', 'item': t[:30], 'lost': lo})
    stats.append({'unit': u['unit'], 'title': u['title'], 'vols': u['vols'],
                  'items': len(keep), 'src': len(src), 'kept': ck,
                  'narr': len(narr), 'narr_chars': nc,
                  'ratio': ck / len(src) if src else 0})
    units_out.append({'unit': u['unit'], 'title': u['title'], 'vols': u['vols'],
                      'items': keep, 'narr': narr,
                      'deletion': strip_head(del_sec(sec)),
                      'doubts': strip_head(sec.get('存疑', '')),
                      'intro': intro})

GF = os.path.join(W, 'findings_gu')
GU = json.load(open(os.path.join(W, 'gu_units.json'), encoding='utf-8'))
for u in GU:
    if (not os.environ.get('MK_GU') or u['unit'] != 'vol01'
            or not os.path.isdir(GF) or any(x['unit'] == 'vol01' for x in units_out)):
        continue
    text = open(os.path.join(GF, 'vol01.md'), encoding='utf-8').read()
    sec, _ = sections_of(text)
    src, spans = src_index([1], None)
    keep, narr, ck, nc = [], [], 0, 0
    for n, (t, b) in enumerate(items_of(sec.get('保留項', '')), 1):
        r, ch, lo = render_item('### {}. {}'.format(n, t), b, src, spans, False)
        keep.append(r)
        ck += ch
        if lo:
            all_lost.append({'unit': 'vol01', 'kind': 'keep', 'item': t[:30], 'lost': lo})
    for n, (t, b) in enumerate(items_of(sec.get('敘事抽取', '')), 1):
        r, ch, lo = render_item('### {}. {}'.format(n, t), b, src, spans, True)
        narr.append({'unit': 'vol01', 'title': u['title'], 'vols': [1], 'md': r, 'chars': ch})
        nc += ch
        if lo:
            all_lost.append({'unit': 'vol01', 'kind': 'narr', 'item': t[:30], 'lost': lo})
    stats.append({'unit': 'vol01', 'title': u['title'], 'vols': [1], 'items': len(keep),
                  'src': len(src), 'kept': ck, 'narr': len(narr), 'narr_chars': nc,
                  'ratio': ck / len(src) if src else 0})
    units_out.append({'unit': 'vol01', 'title': u['title'], 'vols': [1], 'items': keep,
                      'narr': narr,
                      'deletion': strip_head(del_sec(sec)),
                      'doubts': strip_head(sec.get('存疑', '')),
                      'intro': ''})
    break

json.dump({'stats': stats, 'lost': all_lost},
          open(META_F, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump({u['unit']: u for u in units_out},
          open(UOUT_F, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

ts = sum(s['src'] for s in stats)
tk = sum(s['kept'] for s in stats)
tn = sum(s['narr'] for s in stats)
tnk = sum(s['narr_chars'] for s in stats)
ti = sum(s['items'] for s in stats)
print('units', len(stats), '/', len(UNITS), 'missing:', missing)
print('items', ti, 'src', ts, 'kept', tk, 'ratio', round(tk / ts * 100, 1) if ts else 0)
print('narrative items', tn, 'quote chars', tnk)
print('unrecovered fragments in', len(all_lost), 'items')
for x in all_lost[:12]:
    print(' ', x['unit'], x['kind'], x['item'], '->', x['lost'][:1])

CORE = ['位置', '差異說明', '原文', '白話']
REFS = ['四分律對照', '五分律對照', '十誦律對照']
bad, refmiss = [], []
for u in units_out:
    n = len(u['items'])
    for i, md in enumerate(u['items'], 1):
        miss = [f for f in CORE if not re.search(r'^-\s*' + f + r'[：:]', md, re.M)]
        if not re.match(r'^### ' + str(i) + r'\. ', md):
            miss.append('序號')
        if not quote_lines(md):
            miss.append('原文無引文')
        if miss:
            bad.append({'unit': u['unit'], 'no': i, 'title': md.split('\n')[0][:30], 'miss': miss})
    short = [(f, sum(1 for md in u['items'] if re.search(r'^-\s*' + f + r'[：:]', md, re.M)))
             for f in REFS]
    if any(c < n for f, c in short):
        refmiss.append({'unit': u['unit'], 'items': n, 'have': dict(short)})
print('items missing core fields:', len(bad))
for x in bad[:10]:
    print('  FIELD', x['unit'], x['no'], x['miss'], x['title'])
print('units with fewer 對照 lines than items:', len(refmiss))
for x in refmiss[:6]:
    print('  REFS', x['unit'], x['items'], x['have'])
json.dump({'lost': all_lost, 'bad_fields': bad, 'refmiss': refmiss},
          open(os.path.join(W, 'mk_lost.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

if os.environ.get('MK_GU'):
    n = [u for u in units_out if u['unit'] == 'vol01']
    if n:
        parts = ['\n\n'.join(n[0]['items'][:4])]
        if n[0]['narr']:
            parts.append('\n\n'.join(x['md'] for x in n[0]['narr'][:2]))
        open(os.path.join(W, 'mk_pilot_out.md'), 'w', encoding='utf-8').write('\n\n---\n\n'.join(parts))
        print('pilot dump written: mk_pilot_out.md')
