# -*- coding: utf-8 -*-
"""Repair mechanical defects in _work/findings_mk/*.md and findings_gu/*.md.

  1. 簡化字 — replace simplified-only glyphs (none of which occur in the base corpora,
     so a verbatim quote can never legitimately contain them).
  2. 缺段號 — a quote line with no 〔卷N·段M〕 label: locate the paragraph that contains
     it and prepend the label.
  3. 敘事引文 — '首句：'/'末句：' prefixes and mid-sentence truncation break verbatim
     matching: replace with a real verbatim fragment (<=44 chars) from the paragraph.

usage:  python fix_mk.py [sengqi|genben] [--dry]
"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
CANON = 'genben' if 'genben' in sys.argv else 'sengqi'
DRY = '--dry' in sys.argv

C = {'sengqi': {'base': 'sengqi', 'src': 'findings_mk', 'units': 'mk_units.json'},
     'genben': {'base': 'genben', 'src': 'findings_gu', 'units': 'gu_units.json'}}[CANON]

SIM = dict(zip(
    '与么价处头对应当开录怀户扩时来约节装让论话说还这进门随项须风龄'
    '见观听读请谢变边达运远连选阳阴队阶际隐难页顶顺顾预领颇颈颊频颗题颜额饭饮饱饿馆驾骑鲜鸡鸣鸭鹅鹰麦黄齐齿龟'
    '个儿几尽层属岁坚夺实宠审灾炉点炼热总恼惊惧惯战扑执扫扬抚邻赚忆显画盐红线继续编缝许针钟钢钩钱铁铜银锡镇雾饼馈专业丛严乡书买储场墙买卖钱银铁长门开闭关问间闻东车马鸟鱼龙风飞书写学觉见观听声义议论识语读谁请谢变边达运远连选阳阴队阶际随隐难页顶项顺须顾顿预领颇颈颊频颗题颜额饭饮饱饿馆驾骑骗鲜鸡鸣鸭鹅鹰麦黄齐齿龄龟'
    '犹补诉诚诺闲闷晓误询简营烛删净凑',
    '與麼價處頭對應當開錄懷戶擴時來約節裝讓論話說還這進門隨項須風齡'
    '見觀聽讀請謝變邊達運遠連選陽陰隊階際隱難頁頂順顧預領頗頸頰頻顆題顏額飯飲飽餓館駕騎鮮雞鳴鴨鵝鷹麥黃齊齒龜'
    '個兒幾盡層屬歲堅奪實寵審災爐點煉熱總惱驚懼慣戰撲執掃揚撫鄰賺憶顯畫鹽紅線繼續編縫許針鐘鋼鉤錢鐵銅銀錫鎮霧餅饋專業叢嚴鄉書買儲場牆買賣錢銀鐵長門開閉關問間聞東車馬鳥魚龍風飛書寫學覺見觀聽聲義議論識語讀誰請謝變邊達運遠連選陽陰隊階際隨隱難頁頂項順須顧頓預領頗頸頰頻顆題顏額飯飲飽餓館駕騎騙鮮雞鳴鴨鵝鷹麥黃齊齒齡龜'
    '猶補訴誠諾閒悶曉誤詢簡營燭刪淨湊'))
SIM = {k: v for k, v in SIM.items() if k != v}


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


PARA = {}


def load(vol):
    if vol not in PARA:
        p = os.path.join(W, C['base'], 'vol%02d.txt' % vol)
        PARA[vol] = ({int(n): t for n, t in
                      (l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8'))}
                     if os.path.exists(p) else {})
    return PARA[vol]


LBL = re.compile(r'^\s*[〔【（(]?\s*(?:卷\s*(\d{1,2})\s*[·・]\s*)?段\s*(\d{1,3})')


def has_label(body):
    return bool(LBL.match(body))


def locate(vols, raw):
    """Return (vol, pid, offset_in_raw_para) for the first paragraph containing raw."""
    probe = norm(raw)[:12]
    if len(probe) < 5:
        return None
    cands = []
    for v in vols:
        for pid, txt in load(v).items():
            n = norm(txt)
            i = n.find(probe)
            if i >= 0:
                cands.append((v, pid, txt))
                if len(cands) > 1:
                    return cands[0]
    return cands[0] if cands else None


def verbatim_from(txt, raw, limit=44):
    """Cut a <=limit-char verbatim fragment from txt starting at raw's opening."""
    probe = norm(raw)[:8]
    if len(probe) < 4:
        return None
    # walk txt, build a norm->raw index map
    idx, buf = [], []
    for ch in txt:
        if re.match(r'[\u4e00-\u9fff]', ch):
            idx.append(len(buf))
            buf.append(ch)
    n = ''.join(buf)
    i = n.find(probe)
    if i < 0:
        return None
    start = idx[i]
    seg = txt[start:start + limit + 20]
    m = re.search(r'[。！？；]', seg[limit // 2:])
    if m:
        seg = seg[:limit // 2 + m.end()]
    else:
        seg = seg[:limit]
    return seg.strip()


def unit_label(vols, v, pid):
    return '〔卷{}·段{}〕'.format(v, pid) if len(vols) > 1 else '〔段{}〕'.format(pid)


stats = {'sim': 0, 'lab': 0, 'narr': 0, 'files': 0, 'fail': []}

for f in sorted(glob.glob(os.path.join(W, C['src'], '*.md'))):
    base = os.path.basename(f)[:-3]
    units = {u['unit']: u['vols'] for u in
             __import__('json').load(open(os.path.join(W, C['units']), encoding='utf-8'))}
    vols = units.get(base)
    if not vols:
        continue
    stats['files'] += 1
    md = open(f, encoding='utf-8').read()
    out = []
    for ln in md.split('\n'):
        s = ln.strip()
        # 1. simplified glyphs (outside fenced/quote bodies is unnecessary: none exist in base)
        if any(ch in SIM for ch in ln):
            for k, v in SIM.items():
                if k in ln:
                    ln = ln.replace(k, v)
                    stats['sim'] += 1
        if not s.startswith('>'):
            out.append(ln)
            continue
        body = s.lstrip('>').strip()
        if not body or body.startswith('（中略'):
            out.append(ln)
            continue
        # 3. narrative quote: 首句／末句 prefix
        m = re.match(r'^(首句|末句)[：:]\s*(.*)$', body)
        if m:
            raw = m.group(2).strip()
            hit = locate(vols, raw)
            if hit:
                v, pid, txt = hit
                seg = verbatim_from(txt, raw)
                if seg:
                    out.append('> {}{}'.format(unit_label(vols, v, pid), seg))
                    stats['narr'] += 1
                    continue
            stats['fail'].append((base, 'narr', raw[:26]))
            out.append(ln)
            continue
        # 3b. editorial parenthetical inside a quote is not verbatim text
        cleaned = re.sub(r'[（(]\s*(?:段\s*\d[^）)]*|中略[^）)]*|節[引錄][^）)]*'
                         r'|[^）)]{0,20}(?:不具引|不錄|下略)[^）)]*)[）)]', '', body).strip()
        if cleaned != body and norm(cleaned):
            body = cleaned
            s = '>' + cleaned
        # 2. missing paragraph label, or a 段N label with no 卷 in a multi-vol unit
        m = LBL.match(body)
        need = (not m) or (len(vols) > 1 and not m.group(1))
        if need:
            raw = re.sub(r'^\*\*[^*]{0,30}\*\*\s*', '', body)
            raw = LBL.sub('', raw).strip('　 ：:')
            hit = locate(vols, raw)
            if hit:
                v, pid, _ = hit
                out.append('> {}{}'.format(unit_label(vols, v, pid), raw))
                stats['lab'] += 1
                continue
            stats['fail'].append((base, 'lab', raw[:26]))
        out.append(s if s.startswith('>') else ln)
    new = '\n'.join(out)
    if not DRY and new != md:
        open(f, 'w', encoding='utf-8').write(new)

print('files', stats['files'], 'simplified', stats['sim'],
      'labels added', stats['lab'], 'narrative fixed', stats['narr'],
      'unresolved', len(stats['fail']))
for x in stats['fail'][:15]:
    print('  FAIL', x)
