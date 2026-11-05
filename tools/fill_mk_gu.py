#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""開遮表補比：僧祇、根有兩欄。

原則：只補「有」，不補「無」。
  - 根有：原典每條學處皆冠「學處第N」，其編次與四分戒序可對（捨墮末五條有調動，
    另立對照）。凡矩陣某列為戒條、且可定位到四分某戒者，根有必有此學處，
    據此補「有」，並記學處序。
  - 僧祇：原典無學處編號，不能憑序對位。改以該列 ref4 所載「查詢詞」回原典檢索，
    須同時滿足：詞長 ≥3、非泛詞、出現 ≤12 次、上下文見制戒語（若比丘／波夜提／
    佛言／制戒…）。檢得者補「有」，記卷次與檢得詞；檢不得者仍標「未比」，
    **不據以斷無**。

產出：_work/mk_gu_fill.json、_work/審閱/僧祇根有補比.csv
"""
import os, re, sys, json, glob, bisect, csv, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
sys.path.insert(0, WORK)
OUT = os.path.join(WORK, '審閱')

CN = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
      '六': 6, '七': 7, '八': 8, '九': 9}


def cn2i(x):
    if '百' in x:
        h, _, r = x.partition('百')
        n = (CN.get(h, 1) if h else 1) * 100
        if r.startswith('零'):
            r = r[1:]
        if not r:
            return n
        if '十' in r:
            a, _, o = r.partition('十')
            return n + (CN.get(a, 1) if a else 1) * 10 + (CN.get(o, 0) if o else 0)
        return n + CN.get(r, 0)
    if '十' in x:
        a, _, o = x.partition('十')
        return (CN.get(a, 1) if a else 1) * 10 + (CN.get(o, 0) if o else 0)
    return CN.get(x, 0)


def load(dirname, head):
    files = sorted(glob.glob(os.path.join(ROOT, '01_原文', dirname, '*.txt')))
    text = re.sub(r'\s+', '', ''.join(
        open(f, encoding='utf-8', errors='ignore').read() for f in files))
    pos = []
    for m in re.finditer(head + r'卷(?:第)?([零一二三四五六七八九十百]+)', text):
        v = cn2i(m.group(1))
        if v and (not pos or pos[-1][1] != v):
            pos.append((m.start(), v))
    return text, pos


def vol_of(pos, idx):
    ps = [p for p, _ in pos]
    i = bisect.bisect_right(ps, idx) - 1
    return pos[i][1] if i >= 0 else (pos[0][1] if pos else 0)


# 根有學處：四分戒序 → 根有學處序。
# 波羅夷、僧殘、提舍尼同序；捨墮末五條調動；單提次序大異，逐條對位。
# 單提 44、66、71、74 四條未能確定，不強配。
GU_MAP = {
    '波羅夷': {i: i for i in range(1, 5)},
    '僧殘': {i: i for i in range(1, 14)},
    '捨墮': {**{i: i for i in range(1, 26)},
             **{26: 30, 27: 28, 28: 26, 29: 27, 30: 29}},
    '提舍尼': {i: i for i in range(1, 5)},
    '單提': {
        1: 1, 2: 2, 3: 3, 4: 65, 5: 54, 6: 6, 7: 7, 8: 8, 9: 5, 10: 73,
        11: 11, 12: 13, 13: 12, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18,
        19: 19, 20: 20, 21: 21, 22: 22, 23: 23, 24: 24, 25: 25, 26: 29,
        27: 26, 28: 27, 29: 30, 30: 70, 31: 32, 32: 31, 33: 36, 34: 33,
        35: 34, 36: 35, 37: 37, 38: 38, 39: 39, 40: 40, 41: 44, 42: 81,
        43: 42, 45: 28, 46: 51, 47: 74, 48: 45, 49: 46, 50: 47, 51: 79,
        52: 64, 53: 63, 54: 78, 55: 66, 56: 60, 57: 52, 58: 67, 59: 68,
        60: 58, 61: 61, 62: 41, 63: 62, 64: 50, 65: 72, 67: 71, 68: 55,
        69: 56, 70: 57, 72: 10, 73: 83, 75: 77, 76: 53, 77: 76, 78: 48,
        79: 49, 80: 69, 81: 82, 82: 59, 83: 80, 84: 85, 85: 86, 86: 84,
        87: 87, 88: 88, 89: 89, 90: 90,
    },
}

# 僧祇：機器檢得者逐條覆核，僅留上下文確為制戒語者（其餘寧缺）
MK_OK = {'M-0138', 'M-0567', 'M-0627', 'M-0880', 'M-0962', 'M-0963',
         'M-1043', 'M-1050', 'M-1055', 'M-1059', 'M-1100', 'M-1147',
         'M-1160', 'M-1212', 'M-1293', 'M-1307', 'M-1309', 'M-1313',
         'M-2036', 'M-2049', 'M-2076', 'M-0278'}

GEN = set('比丘 比丘尼 沙彌 沙彌尼 式叉摩那 世尊 如來 佛 僧 大眾 眾人 居士 白衣 '
          '王 賊 罪 戒 犯 不犯 開 遮 制 聽 許 白 羯磨 布薩 自恣 安居 衣 鉢 食 藥 '
          '房 屋 牀 坐 臥 行 住 語 說 事 法 人 時 處 中 上 下 一 二 三 四 五 六 七 八 九 十 '
          '爾時 一時 佛言 答言 白佛 突吉羅 偷蘭遮 波逸提 波羅夷 僧殘 僧伽 沙門 '
          '婆羅門 四真諦 五百歲 如小兒 現前僧'.split())
BAD = re.compile(r'[日歲由旬拘盧舍肘弓里步錢兩斗升]|者$|時$|處$|中$|故$')
RULE = re.compile(r'若比丘|若苾芻|波夜提|波逸提|僧伽婆尸沙|佛言|制戒|不應|應如是')


def query_terms(r):
    out = []
    m = re.search(r'查詢詞[：:]\s*([^）)]*)', r.get('ref4') or '')
    if m:
        for x in re.split(r'[／/、，,；;]', m.group(1)):
            x = re.sub(r'[^\u4e00-\u9fff]', '', x)
            if 3 <= len(x) <= 8:
                out.append(x)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    import sifen_src as S

    names = json.load(open(os.path.join(WORK, 'jie_names.json'), encoding='utf-8'))
    rev = {}
    for k, v in names.items():
        if k.startswith('_'):
            continue
        fam, _, i = k.partition('|')
        nm = re.sub(r'戒$', '', re.sub(r'^[一二三四五六七八九十百]+、', '', v))
        rev[(fam, nm)] = int(i)

    loc = json.load(open(os.path.join(WORK, '_locate.json'), encoding='utf-8'))
    place = {x['id']: (x['n'], x['seg']) for x in loc['placed']}
    rows = json.load(open(os.path.join(WORK, 'matrix_built.json'), encoding='utf-8'))

    def jie_name(no, seg):
        for u in S.units(no):
            if u['a'] <= seg <= u['b']:
                lb = S.unit_label(u, no) or ''
                for part in re.split(r'／', lb):
                    nm = re.sub(r'戒$', '', re.sub(r'^[一二三四五六七八九十百]+、', '', part))
                    if nm:
                        return nm
        return None

    FAMS = {'波羅夷': '比丘波羅夷', '僧殘': '比丘僧殘', '捨墮': '比丘捨墮',
            '單提': '比丘單提', '提舍尼': '比丘提舍尼'}

    MK, MP = load('摩訶僧祇律', '摩訶僧祇律')
    GU, GP = load('根本說一切有部毘奈耶', '根本說一切有部毘奈耶')
    # 根有學處位置：須分罪類，否則「學處第11」會取到僧殘十一而非單提十一
    GU_SECS = [(994, '波羅夷'), (90319, '僧殘'), (141655, '捨墮'),
               (225205, '單提'), (454069, '提舍尼')]
    gu_pos = {}
    for _i, (_st, _nm) in enumerate(GU_SECS):
        _en = GU_SECS[_i + 1][0] if _i + 1 < len(GU_SECS) else len(GU)
        for m in re.finditer(r'學處第([一二三四五六七八九十百零]+)', GU):
            _p = m.start()
            if _st <= _p < _en:
                _n = cn2i(m.group(1))
                if _n and (_nm, _n) not in gu_pos:
                    gu_pos[(_nm, _n)] = _p

    fill, ledger = {}, []
    for r in rows:
        need = [k for k in ('vMK', 'vGU') if r.get(k) == '未比']
        if not need:
            continue
        # 根有：戒條且可定位者，按學處序補有
        if 'vGU' in need and r.get('lv') == '戒條' and r['id'] in place:
            nm = jie_name(*place[r['id']])
            for fam, pref in FAMS.items():
                if (pref, nm) in rev:
                    i = rev[(pref, nm)]
                    j = GU_MAP.get(fam, {}).get(i)
                    if j and (fam, j) in gu_pos:
                        _p = gu_pos[(fam, j)]
                        fill.setdefault(r['id'], {})['vGU'] = {
                            'v': '有', 'cite': '根有 卷%d' % vol_of(GP, _p),
                            'term': '學處第%d' % j,
                            'ctx': GU[max(0, _p - 16):_p + 8]}
                    break
        # 僧祇：查詢詞回檢
        if 'vMK' in need and r['id'] in MK_OK:
            for t in query_terms(r):
                if t in GEN or BAD.search(t):
                    continue
                n = MK.count(t)
                if not (1 <= n <= 12):
                    continue
                i = MK.find(t)
                ctx = MK[max(0, i - 60):i + len(t) + 60]
                if not RULE.search(ctx):
                    continue
                fill.setdefault(r['id'], {})['vMK'] = {
                    'v': '有', 'cite': '僧祇 卷%d' % vol_of(MP, i),
                    'term': t, 'ctx': ctx}
                break

    json.dump(fill, open(os.path.join(WORK, 'mk_gu_fill.json'), 'w',
                         encoding='utf-8'), ensure_ascii=False, indent=1)
    for mid, d in sorted(fill.items()):
        r = next(x for x in rows if x['id'] == mid)
        for k in ('vMK', 'vGU'):
            if k in d:
                ledger.append((mid, r['canon'], r['title'][:46], k,
                               d[k]['v'], d[k]['cite'], d[k]['term'],
                               d[k]['ctx'][:48]))
    q = os.path.join(OUT, '僧祇根有補比.csv')
    with open(q, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(('項號', '所屬律', '標題', '欄位', '補值', '出處', '檢得詞', '上下文'))
        w.writerows(ledger)

    c = collections.Counter(x[3] for x in ledger)
    print('補比 %d 格（僧祇 %d、根有 %d）' % (len(ledger), c['vMK'], c['vGU']))


if __name__ == '__main__':
    main()
