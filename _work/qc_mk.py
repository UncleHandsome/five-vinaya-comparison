# -*- coding: utf-8 -*-
"""QC for the 摩訶僧祇律 / 根本說 edition.

Measures the artefact, not the intent:
  1. 逐字校驗 — every quote line must be found verbatim in the *labelled paragraph*
     of the base text (labels read from the file itself).
  2. 簡化字 — high-confidence simplified-only glyph scan.
  3. 白話 — present, and not shorter than 40% of the quoted 原文 (CJK chars).
  4. 形制 — item numbering, required fields, 段號 coverage per unit.

usage:  python qc_mk.py [findings|edition]
"""
import os, re, sys, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
MODE = sys.argv[1] if len(sys.argv) > 1 else 'findings'
CANON = os.environ.get('MK_CANON', 'sengqi')

C = {'sengqi': {'base': 'sengqi', 'src': 'findings_mk', 'units': 'mk_units.json',
                'folder': '摩訶僧祇律_去重白話', 'n_vol': 40},
     'genben': {'base': 'genben', 'src': 'findings_gu', 'units': 'gu_units.json',
                'folder': '根本說一切有部毘奈耶_去重白話', 'n_vol': 50}}[CANON]

# simplified-only glyphs (shared forms such as 云/制/只/尸/斗/服/面/里/干/于/卻/宁/准
# are deliberately excluded: they are legitimate in a Traditional text)
# Candidate simplified-only glyphs. Anything that actually occurs in the four base
# corpora is dropped at run time (such a glyph may legitimately enter a verbatim
# quote), so the scan can only fire on text we authored. 你／她／它 and 窗 are not
# candidates: they are normal forms in Modern Traditional Chinese prose.
CAND = ('这们时说过还进来对开关门问间长东车马鸟鱼龙风飞书写学觉见观听声义议论証识语话读谁请谢变边达运'
        '远连选阳阴队阶际随隐难页顶项顺须顾顿预领颇颈颊频颗题颜额饭饮饱饿馆驾骑骗鲜鸡鸣鸭鹅鹰麦黄齐齿龄龟'
        '个么儿几头尽层属岁坚夺与处开实宠审灾炉点炼热态总恼惊惧惯战户扑执扩扫扬抚邻赚约记录忆怀显电画'
        '盐红纸线继续编缝让许读针钟钢钩钱铁铜银锡镇阶雾饼馈马鱼鸟麦龄龙专业丛严义乡书买价储场墙节'        '层应录忆怀态总恼惊惧惯战户扑执扩扫扬抚时显炼电画盐红约纸线练绘继续绵绸缎编缝肃节装让记许读赚辑邻酱针钟钢钩钱铁铜银锡'
        '犹补诉诚诺闲闷晓误询简营烛删刻净凑众'
        '经结给该谓还没组织纪级纯纲纳纵纹纺线练细终绍绑绒绕络绝统继续绳维绵综绿缀'
        '订认讨训议讯讲讳讼访设诊证评译诗诞详诬课调谅谈谋谎谜谨谱'
        '贝负贡财责贤败账货质贩贪贫购贯贴贵贷贸费贺贼资宾赐赏赔赖赛赞赠'
        '车轨转轮软轻载较辅辆辈辉辑输闪闭闯闰闲闸闹闻阀阁阅阐阔阙驰驱驳驴驶驹驻驼驾骂骄骇验骏骚骤'
        '鸡鸣鸥鸦鸭鸽鸿鹅鹊鹏鹤鹰鲁鲍鲜鲨鲸鳄纠红纤纱纽组织绎绑绘绪绫绷绽围图圆颠颤飘龉')
# not simplified intrusions but normal in Modern Traditional prose:
SKIP = set('你我她它窗静')
HI = set(c for c in CAND if c not in SKIP and ord(c) > 127)

BASE_GLYPHS = set()
for _f in glob.glob(os.path.join(W, 'sengqi', '*.txt')) + glob.glob(os.path.join(W, 'shisong', '*.txt')) + \
        glob.glob(os.path.join(W, 'wufen', '*.txt')) + glob.glob(os.path.join(W, 'sifen', '*.txt')):
    BASE_GLYPHS.update(open(_f, encoding='utf-8').read())
EXCLUDED = sorted(HI & BASE_GLYPHS)   # may legitimately appear inside verbatim quotes
HI -= BASE_GLYPHS


def norm(s):
    s = re.sub(r'[\s　]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


_CN = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
       '七': 7, '八': 8, '九': 9, '十': 10, '百': 100}


def cn2num(s):
    s = (s or '').strip()
    if s.isdigit():
        return int(s)
    tot, num, seen = 0, 0, False
    for c in s:
        if c not in _CN:
            return 0
        seen = True
        if c == '十':
            tot += (num or 1) * 10
            num = 0
        elif c == '百':
            tot += (num or 1) * 100
            num = 0
        else:
            num = _CN[c]
    return tot + num if seen else 0


PARA = {}


def para_text(vol, pid):
    key = (vol, pid)
    if key not in PARA:
        p = os.path.join(W, C['base'], 'vol%02d.txt' % vol)
        if not os.path.exists(p):
            return ''
        d = {int(n): t for n, t in
             (l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8'))}
        PARA[vol] = d
    return PARA[vol].get(pid, '')


def npara(vol):
    para_text(vol, 0)
    return max(PARA.get(vol, {0: ''})) if PARA.get(vol) else 0


LABEL = re.compile(r'^\*\*\s*(?:卷\s*(\d{1,2})\s*[·・])?\s*段\s*(\d{1,3})(?:\s*[～~－-]\s*(\d{1,3}))?[^*]*\*\*')
BARE = re.compile(r'^\s*(?:[*（(【〔\[]?\s*卷\s*(\d{1,2})\s*[·・，,\s]\s*段\s*(\d{1,3})\s*'
                  r'(?:[（(][^）)】〕]{1,60}[）)])?\s*(?:[）)】〕\]]|[：:]|$)'
                  r'|段\s*(\d{1,3})\s*(?:[：:]|$))')


def unit_vols(name, units):
    for u in units:
        if u['unit'] == name:
            return u['vols']
    # edition filenames are 卷X至卷Y / 合冊 / 獨有敘事 — map them to their volume span
    m = re.search(r'卷([一二三四五六七八九十百千〇0-9]+)至卷([一二三四五六七八九十百千〇0-9]+)', name)
    if m:
        a, b = cn2num(m.group(1)), cn2num(m.group(2))
        if a and b and a <= b:
            return list(range(a, b + 1))
    if '合冊' in name or '獨有敘事' in name:
        return list(range(1, C['n_vol'] + 1))
    return None


def quotes_of(md):
    """Yield (vol, para, text) for each quote line; vol/para may be None."""
    out = []
    for ln in md.split('\n'):
        k = ln.strip()
        if not k.startswith('>'):
            continue
        body = k.lstrip('>').strip()
        if not body or body.startswith('（中略'):
            continue
        body = re.sub(r'[（(【〔\[]\s*(?:中略|節引|節錄)[^）)】〕\]]*[）)】〕\]]', ' ', body)
        if not body.strip():
            continue
        m = LABEL.match(body)
        if m:
            out.append((int(m.group(1)) if m.group(1) else None, int(m.group(2)),
                        body[m.end():].lstrip('　 ')))
            continue
        m = BARE.match(body)
        if m:
            vol = m.group(1)
            pid = m.group(2) or m.group(3)
            out.append((int(vol) if vol else None, int(pid), body[m.end():].lstrip('：:　 ')))
            continue
        # no label in front: only then drop a leading bold marker (e.g. 「**（節引）**」)
        body = re.sub(r'^\s*\*\*[^*]{0,30}\*\*\s*', '', body)
        if not body:
            continue
        m = LABEL.match(body)
        if m:
            out.append((int(m.group(1)) if m.group(1) else None, int(m.group(2)),
                        body[m.end():].lstrip('　 ')))
            continue
        m = BARE.match(body)
        if m:
            vol = m.group(1)
            pid = m.group(2) or m.group(3)
            out.append((int(vol) if vol else None, int(pid), body[m.end():].lstrip('：:　 ')))
        else:
            out.append((None, None, body))
    return out


def read_label(t):
    """Return (vol, para, text_without_label) for a quote fragment, if it carries one."""
    t = re.sub(r'[（(【〔\[]\s*(?:內?中略|節引|節錄|略)[^）)】〕\]]*[）)】〕\]]', ' ', t)
    for rx in (LABEL, BARE):
        m = rx.match(t.strip())
        if m:
            g = m.groups()
            if rx is LABEL:
                return (int(g[0]) if g[0] else None, int(g[1]), t.strip()[m.end():].strip('　 ：:'))
            vol = g[0]
            pid = g[1] or g[2]
            return (int(vol) if vol else None, int(pid), t.strip()[m.end():].strip('　 ：:'))
    t = re.sub(r'^\s*[*（(【〔\[]?\s*卷\s*\d{1,2}\s*[·・/\s－-]?\s*段?\s*\d{1,3}'
               r'\s*(?:[～~－–]\s*(?:段\s*)?\d{1,3})?'
               r'\s*(?:前段|後段|中段|前半|後半|全段)?\s*[）)】〕\]]?\s*'
               r'(?:[（(][^）)】〕]{1,60}[）)])?\s*[*：:]?\s*', '', t.strip())
    t = re.sub(r'^\s*[（(【〔][^）)】〕]{1,60}[）)】〕]\s*[：:]?\s*', '', t)
    return (None, None, t.strip())


ED_DIR = os.environ.get('MK_ED') or os.path.join(ROOT, C['folder'])
files = (sorted(glob.glob(os.path.join(W, C['src'], '*.md'))) if MODE == 'findings'
         else sorted(glob.glob(os.path.join(ED_DIR, '*_去重白話_*.md'))))
units = json.load(open(os.path.join(W, C['units']), encoding='utf-8'))
UT = {u['unit']: u['vols'] for u in units}

bad_quote, no_label, relabel, n_quote, n_char = [], [], [], 0, 0
sim_hits, short_bai, no_bai, unmapped = [], [], [], []
scope = []
for f in files:
    base = os.path.basename(f)[:-3]
    vols = unit_vols(base, units)
    if vols is None:
        unmapped.append(base)
    md = open(f, encoding='utf-8').read()
    text_all = {v: norm(''.join(t for n, t in
                                (l.rstrip('\n').split('\t', 1)
                                 for l in open(os.path.join(W, C['base'], 'vol%02d.txt' % v),
                                               encoding='utf-8')))) for v in (vols or [])}
    unit_str = ''.join(text_all.get(v, '') for v in (vols or []))
    scope.append((base, len(vols or []), len(unit_str), md.count('\n### ')))
    heads = [(h.start(), [int(x) for x in re.findall(r'卷\s*(\d{1,2})', h.group(1))])
             for h in re.finditer(r'^## (卷[^\n]*)$', md, re.M)]

    def head_vols(pos):
        hv = [v for p, v in heads if p < pos]
        return hv[-1] if hv else []

    for m in re.finditer(r'^### (.*)$', md, re.M):
        title = m.group(1)[:40]
        uvs = head_vols(m.start())
        uv = uvs[0] if len(uvs) == 1 else None
        ends = [md.find(x, m.end()) for x in ('\n### ', '\n## ', '\n---')]
        ends = [e for e in ends if e > 0]
        end = min(ends) if ends else len(md)
        item = md[m.start():end]
        qs = quotes_of(item)
        oc = 0
        for vol, a, txt in qs:
            n = norm(txt)
            if not n:
                continue
            n_quote += 1
            n_char += len(n)
            oc += len(n)
            # verify per sentence: a quote line may join sentences, carry an inline
            # ellipsis, or add the agent's own 「」; the sentence is the atom.
            atoms = [x for x in re.split(r'(?<=[。！？；])', txt) if norm(x)] or [txt]
            if vol is None:
                vol = uv                      # 卷次可由本節「## 卷N」標題推出
            if vol is None and vols and len(vols) > 1:
                no_label.append((base, title, txt[:30]))
            for at0 in atoms:
                v2, p2, at = read_label(at0)
                vv, aa = (v2 or vol), (p2 or a)
                m = norm(at)
                if len(m) < 4:
                    continue
                if m in unit_str:
                    if aa is not None and vv is not None and vols and vv in vols:
                        if m not in norm(para_text(vv, aa)):
                            relabel.append((base, title, '卷{}段{}'.format(vv, aa), at[:36]))
                    continue
                bad_quote.append((base, title,
                                  '段{}'.format(aa) if aa else '無段號',
                                  '卷{}'.format(vv) if vv else '', at[:44]))
        bm = re.search(r'-\s*白話[：:](.*?)(?=\n-\s|\n###|\Z)', item, re.S)
        is_narr = bool(re.search(r'^-\s*(要旨|全文收錄)[：:]', item, re.M))
        if is_narr:
            if not re.search(r'^-\s*要旨[：:]\s*\S', item, re.M):
                no_bai.append((base, title, '敘事無要旨'))
        elif not bm:
            no_bai.append((base, title))
        elif oc and len(norm(bm.group(1))) < 0.4 * oc:
            short_bai.append((base, title, oc, len(norm(bm.group(1)))))
    for i, ch in enumerate(md):
        if ch in HI:
            sim_hits.append((base, ch, md[max(0, i - 12):i + 12].replace('\n', ' ')))

print('mode', MODE, 'files', len(files), 'quotes', n_quote, 'quote chars', n_char)
print('quotes NOT verbatim anywhere in the unit:', len(bad_quote))
for x in bad_quote[:40]:
    print('  BADQ', x)
    if '-v' in sys.argv and x[2].startswith('段') and x[3].startswith('卷'):
        v = int(x[3][1:])
        p = int(x[2][1:])
        print('        底本卷{}段{}：{}'.format(v, p, para_text(v, p)[:90]))
print('label off but text found in unit:', len(relabel))
for x in relabel[:6]:
    print('  RELABEL', x)
print('quotes without usable paragraph label:', len(no_label))
for x in no_label[:6]:
    print('  NOLAB', x)
print('items lacking 白話:', len(no_bai), no_bai[:6])
print('items whose 白話 is under 40% of 原文:', len(short_bai))
for x in short_bai[:8]:
    print('  SHORT', x)
uniq = {}
for b, ch, ctx in sim_hits:
    uniq.setdefault(ch, (b, ctx))
print('scan scope: {} glyphs enforced, {} shared forms excluded ({})'.format(
    len(HI), len(EXCLUDED), ''.join(EXCLUDED)))
print('simplified glyphs:', len(uniq))
for ch, (b, ctx) in sorted(uniq.items()):
    print('  SIM {} U+{:04X} in {} | {}'.format(ch, ord(ch), b, ctx))

# 段號 coverage (single-volume units, edition or findings)
if MODE == 'findings':
    def nums(s):
        out = set()
        for a, b in re.findall(r'(\d{1,3})\s*[～~－\-\u2013\u2014]\s*(\d{1,3})', s or ''):
            if 0 < int(a) <= int(b) < 500:
                out.update(range(int(a), int(b) + 1))
        for a in re.findall(r'(?<![\d～~－\-\u2013\u2014])(\d{1,3})(?![\d～~－\-\u2013\u2014])', s or ''):
            if 0 < int(a) < 500:
                out.add(int(a))
        return out
    for f in files:
        base = os.path.basename(f)[:-3]
        vols = UT.get(base) or []
        if len(vols) != 1:
            continue
        md = open(f, encoding='utf-8').read()
        cited = set()
        for m in re.finditer(r'^-\s*位置[：:](.*)$', md, re.M):
            cited |= nums(m.group(1))
        for m in re.finditer(r'^\>\s*\*\*(?:卷\d+·)?段(\d+)', md, re.M):
            cited.add(int(m.group(1)))
        for ln in md.split('\n'):
            s = ln.strip()
            if s.startswith('|'):
                c = [x.strip() for x in s.strip('|').split('|')]
                if c and not set(c[0]) <= set('-: ') and c[0] != '段號範圍':
                    cited |= nums(c[0])
            else:
                cited |= nums(s)
        tot = npara(vols[0])
        miss = [p for p in range(1, tot + 1) if p not in cited]
        if miss:
            print('COV 卷{} 共 {} 段，無歸屬 {} 段：{}'.format(vols[0], tot, len(miss), miss[:20]))

# 管轄自印 + 退碼：尺若無所管，綠不綠皆不足信
print('管轄：%d 檔 — %s' % (len(files), '; '.join(
    '%s（卷%d、底本%d字、%d項）' % (b, nv, ns, ni) for b, nv, ns, ni in scope)))
if unmapped:
    print('  無法定卷次之檔（此類檔未校）：%s' % ', '.join(unmapped))
hard = [('非逐字之引文', len(bad_quote)), ('段號誤指', len(relabel)),
        ('無段號之引文', len(no_label)), ('缺白話/要旨', len(no_bai)),
        ('白話過短', len(short_bai)), ('簡形', len(sim_hits)),
        ('卷次未定之檔', len(unmapped))]
print('判紅項目：' + '、'.join('%s=%d' % t for t in hard))
sys.exit(1 if any(v for _, v in hard) else 0)
