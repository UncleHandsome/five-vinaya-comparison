# -*- coding: utf-8 -*-
"""十誦律去重 edition assembler: re-anchors every quote to the base text,
drops metadata lines, rebuilds items with paragraph labels and 中略 markers."""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
OUT = os.path.join(ROOT, '02_去重稿', '十誦律_去重白話')
os.makedirs(OUT, exist_ok=True)

UNITS = json.load(open(os.path.join(W, 'ss_units.json'), encoding='utf-8'))

def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)

PARAS = {}
for v in range(1, 62):
    p = os.path.join(W, 'shisong', 'vol%02d.txt' % v)
    PARAS[v] = [(int(n), t) for n, t in
                (l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8'))]

META_START = ('底本', '對校本', '對照本', '凡例', '口徑', '說明', '原文欄', '四分律引檔',
              '五分律引', '體例', '校勘', '本卷字數', '以下各條')

def src_index(vols, rng):
    """Return (normstr, list of (norm_pos, vol, para_id, raw_start, raw_end))."""
    ns = []
    spans = []
    for v in vols:
        for pid, t in PARAS[v]:
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
    parts = re.split(r'(?<=[。！？：])', q)
    return [p for p in parts if norm(p)]

def recover(seg, src):
    n = norm(seg)
    if not n:
        return None
    i = src.find(n)
    if i >= 0:
        return (i, i + len(n))
    # tolerate a few divergent chars: longest common block via sliding window
    for L in range(len(n), 8, -1):
        if L < 10:
            break
        i = src.find(n[:L])
        if i >= 0:
            return (i, i + L)
    return None

def reanchor(q, src, spans, vlist, rng):
    """Return list of (para_id|'gap', text, vol) verbatim blocks; plus unrecovered fragments."""
    q = re.sub(r'^\s*\*\*[^*]{0,40}\*\*\s*', '', q)
    q = re.sub(r'^\s*〔[^〕]{0,20}〕\s*', '', q)
    q = re.sub(r'^\s*[（(][^）)]{0,24}[）)][：:]?\s*', '', q)
    q = re.sub(r'^\s*卷?\s*\d{1,2}\s*[-－]\s*段?\s*\d{1,3}\s*[：:]\s*', '', q)
    q = re.sub(r'^\s*(?:段|卷)\s*\d{1,3}(?:[～~\-－]\s*\d{1,3})?\s*(?:前段|後段|中段)?\s*[：:]\s*', '', q)
    q = re.sub(r'^\s*【[^】]{1,12}】\s*', '', q)
    found = []
    lost = []
    for sent in sentences(q):
        if len(norm(sent)) < 4:
            continue
        hit = recover(sent, src)
        if not hit:
            lost.append(sent.strip()[:60])
            continue
        a, b = hit
        va, pa = locate(a, spans)
        vb, pb = locate(max(a, b - 1), spans)
        found.append([a, b, pa, pb, va or vb, sent.strip()])
    found.sort(key=lambda x: x[0])
    blocks = []
    last_para = None
    for a, b, pa, pb, vv, txt in found:
        if last_para is not None and pa > last_para + 1:
            lo, hi = last_para + 1, pa - 1
            gap = '（中略：段%d～%d）' % (lo, hi) if hi > lo else '（中略：段%d）' % lo
            blocks.append(('gap', gap, None))
        if blocks and blocks[-1][0] != 'gap' and blocks[-1][0] == pa:
            blocks[-1] = (pa, blocks[-1][1] + txt, vv)
        else:
            blocks.append((pa, txt, vv))
        last_para = pb or last_para
    return blocks, lost

def quote_blocks(text):
    """Yield (kind, payload) for a findings file's 保留項 section."""
    out = []
    cur = None
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('>'):
            body = s.lstrip('>').strip()
            if not body:
                continue
            if any(body.startswith(m) for m in META_START):
                continue
            out.append(('q', body))
    return out

def parse_items(keep_sec):
    items = []
    for chunk in re.split(r'^### ', keep_sec, flags=re.M)[1:]:
        lines = chunk.split('\n')
        title = lines[0].strip()
        title = re.sub(r'^\d+\s*[.、]\s*', '', title)
        if not title or title.startswith(('已知線索', '定稿補記')):
            continue
        items.append((title, '\n'.join(lines[1:])))
    return items

FIELDS = ['位置', '四分律對照', '五分律對照', '差異說明']


def extract_plain(body):
    """取「- 白話：」以下之縮排塊（可多段，段落各占一行）"""
    out, on = [], False
    for ln in body.split('\n'):
        if not on:
            m = re.match(r'^-\s*白話[^：:]{0,8}[：:]\s*(.*)$', ln)
            if m:
                on = True
                if m.group(1).strip():
                    out.append(m.group(1).strip())
            continue
        if re.match(r'^-\s', ln) or re.match(r'^#{1,6}\s', ln):
            break
        s = ln.rstrip()
        out.append('' if not s.strip() else re.sub(r'^ {1,4}', '', s))
    while out and not out[-1].strip():
        out.pop()
    return out

units_out = []
all_lost = []
stats = []
for u in UNITS:
    f = os.path.join(W, 'findings_ss', u['unit'] + '.md')
    text = open(f, encoding='utf-8').read()
    pos = [(m.start(), m.group(1)) for m in re.finditer(r'^## (.*)$', text, re.M)]
    sections = {}
    for i, (p, name) in enumerate(pos):
        end = pos[i+1][0] if i+1 < len(pos) else len(text)
        sections[name.strip()] = text[p:end]
    keep = sections.get('保留項', '')
    src, spans = src_index(u['vols'], tuple(u['rng']) if u['rng'] else None)
    items_md = []
    n_items = 0
    kept_chars = 0
    for idx, (title, body) in enumerate(parse_items(keep), 1):
        n_items += 1
        flds = {}
        for fl in body.split('\n'):
            m = re.match(r'^-\s*([^：]{1,12})[：:](.*)$', fl.strip())
            if m and m.group(1) in FIELDS:
                flds[m.group(1)] = m.group(2).strip()
        qs = [b for k, b in quote_blocks(body)]
        blocks, lost = [], []
        for q in qs:
            bl, lo = reanchor(q, src, spans, u['vols'], u['rng'])
            blocks.extend(bl)
            lost.extend(lo)
        if lost:
            all_lost.append({'unit': u['unit'], 'item': title, 'lost': lost})
        vlabel = '' if len(u['vols']) == 1 else ''
        out = ['### %d. %s' % (idx, title), '']
        for k in FIELDS:
            if flds.get(k):
                out.append('- %s：%s' % (k, flds[k]))
        if blocks:
            out.append('- 原文：')
            out.append('')
            for pid, txt, vv in blocks:
                if pid == 'gap':
                    out.append('> %s' % txt)
                else:
                    tag = ('卷%d·' % vv) if vv and len(u['vols']) > 1 else ''
                    out.append('> **%s段%s**　%s' % (tag, pid, txt))
                    kept_chars += len(norm(txt))
        plain = extract_plain(body)
        if plain:
            out.append('- 白話：')
            for ln in plain:
                out.append('  ' + ln if ln else '')
        items_md.append('\n'.join(out))
    stats.append({'unit': u['unit'], 'title': u['title'], 'items': n_items,
                  'src': len(src), 'kept': kept_chars,
                  'ratio': kept_chars/len(src) if src else 0})
    units_out.append({'unit': u['unit'], 'title': u['title'],
                      'items': items_md,
                      'deletion': re.sub(r'^## .*$', '', sections.get('刪除項（彙總）') or sections.get('刪除項') or '', flags=re.M).strip(),
                      'doubts': re.sub(r'^## .*$', '', sections.get('存疑', ''), flags=re.M).strip()})

json.dump({'stats': stats, 'lost': all_lost}, open(os.path.join(W, 'ss_assemble_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
tot_src = sum(s['src'] for s in stats)
tot_kept = sum(s['kept'] for s in stats)
tot_items = sum(s['items'] for s in stats)
print('units', len(stats), 'items', tot_items, 'src', tot_src, 'kept', tot_kept, 'ratio', round(tot_kept/tot_src*100, 1))
print('items with unrecovered fragments:', len(all_lost))
for x in all_lost[:10]:
    print(' ', x['unit'], x['item'][:40], '->', x['lost'][:2])
