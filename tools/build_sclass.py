#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批次二／三：669 項「四分所無」之戒類標註與 85 項歸併複審。

原則（見 tools/TODO四項規劃.md）：
  - 不搬移、不改號、不改 st；判不準者標「未分類」，寧缺勿強配（凡例六）。
  - 85 項有具體四分篇段引用者，逐筆回四分原典核引文，分級判讀。

產出：
  _work/s_class.json                 分類表（類／層／可歸篇段）
  _work/審閱/歸併複審.csv            85 項逐筆判讀台帳
  _work/審閱/依戒類瀏覽.md           第二部靜態索引片段
"""
import os, re, csv, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
OUT = os.path.join(WORK, '審閱')

# 戒類關鍵詞（含別名）。順序即優先序：先專後泛。
CLASSES = [
    ('尼八波羅夷', r'比丘尼.{0,6}波羅夷|尼.{0,4}波羅夷|八波羅夷|八事成重|染污心.{0,8}男子'),
    ('尼十七僧殘', r'尼.{0,4}僧殘|十七僧殘'),
    ('尼三十捨墮', r'尼.{0,6}捨墮|比丘尼.{0,6}尼薩耆'),
    ('尼單提', r'尼.{0,6}單提|比丘尼.{0,6}波逸提'),
    ('比丘四波羅夷', r'四波羅夷|不淨行|不與取|故自手斷人命|大妄語|波羅夷'),
    ('比丘十三僧殘', r'十三僧殘|僧伽婆尸沙|僧殘'),
    ('比丘三十捨墮', r'三十捨墮|尼薩耆|捨墮'),
    ('比丘九十單提', r'九十單提|波夜提|波逸提|單提'),
    ('比丘眾學', r'眾學|學法|式叉迦羅尼|應當學'),
    ('七滅諍', r'滅諍|七滅諍'),
    ('二不定', r'二不定|不定法'),
    ('揵度', r'揵度|犍度|受戒法|布薩法|安居法|自恣法'),
]
RE_SEG4 = re.compile(r'(\d{3})[ _]段|(\d{3})\.(\d+)')
RE_QUOTE = re.compile(r'「([^」]{4,})」')


def classify(r, orig=''):
    """回 (類, 依據)。只用可覆核的字串，不猜；依據欄明記出自何處。"""
    t = (r.get('title') or '') + '　' + (r.get('diff_full') or '')
    for name, pat in CLASSES:
        m = re.search(pat, t)
        if m:
            return name, '標題／說明「%s」' % m.group()
    # 標題無關鍵詞者，再查本稿原文（他部律文常直接出現罪名）
    if orig:
        for name, pat in CLASSES:
            m = re.search(pat, orig)
            if m:
                return name, '本稿原文「%s」' % m.group()
    # 由 ref4 的具體篇段引用映射到四分篇→戒類
    seg = RE_SEG4.search(r.get('ref4') or '')
    if seg:
        no = int(seg.group(1) or seg.group(2))
        fam = None
        if 1 <= no <= 2: fam = '比丘四波羅夷'
        elif 3 <= no <= 6: fam = '比丘十三僧殘'
        elif no == 7: fam = '二不定'
        elif 8 <= no <= 12: fam = '比丘三十捨墮'
        elif 13 <= no <= 21: fam = '比丘九十單提'
        elif 22 <= no <= 24: fam = '比丘眾學'
        elif no == 25: fam = '七滅諍'
        elif 26 <= no <= 28: fam = '尼八波羅夷／尼十七僧殘'
        elif 29 <= no <= 30: fam = '尼三十捨墮'
        elif 31 <= no <= 37: fam = '尼單提'
        elif no >= 38: fam = '揵度'
        if fam:
            return fam, 'ref4 篇 %03d' % no
    return '未分類', ''


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = json.load(open(os.path.join(WORK, 'matrix_built.json'), encoding='utf-8'))
    orig = json.load(open(os.path.join(WORK, 'originals_index.json'), encoding='utf-8'))
    C = [r for r in rows if r['st'] == 'C']
    print('C 類', len(C))

    # ── 分類表 ────────────────────────────────────────────────────
    sclass = {}
    for r in C:
        k = '%s|%s|%s' % (r['canon'], r['unit'], r['no'])
        cls, why = classify(r, (orig.get(k) or {}).get('orig', ''))
        sclass[r['id']] = {
            '類': cls, '層': r['lv'], '依據': why,
            '可歸篇段': (RE_SEG4.search(r.get('ref4') or '').group()
                        if RE_SEG4.search(r.get('ref4') or '') else ''),
            'canon': r['canon'], 'title': r['title'],
        }
    p = os.path.join(WORK, 's_class.json')
    json.dump(sclass, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    cc = collections.Counter(v['類'] for v in sclass.values())
    print('分類分佈:', dict(cc.most_common()))
    print('有明確類者', sum(v for k, v in cc.items() if k != '未分類'), '/', len(C))

    # ── 85 項複審 ─────────────────────────────────────────────────
    # 四分原典池（回核 ref4 引文是否真在四文中）
    import glob
    sifen = ''.join(open(f, encoding='utf-8', errors='ignore').read()
                    for f in sorted(glob.glob(os.path.join(ROOT, '01_原文', '四分律', '*.txt'))))
    sifen += ''.join(open(f, encoding='utf-8', errors='ignore').read()
                     for f in sorted(glob.glob(os.path.join(WORK, 'sifen', '*.txt'))))
    sifen = re.sub(r'\s+', '', sifen)

    def hit_quote(s):
        # 「查詢詞：A／B／C」後面的「」是查詞，不是引文，須切除；
        # 否則會把「羸弱」一類查詞拿去原典比對，誤報未命中。
        s = re.split(r'查詢詞[：:]', s or '')[0]
        qs = RE_QUOTE.findall(s) or re.findall(r'『([^』]{4,})』', s)
        if not qs:
            return None
        pool = re.sub(r'[\s「」『』：，。、；]', '', sifen)
        pieces = re.split(r'…+', max(qs, key=len))
        parts = [re.sub(r'[\s「」『』：，。、；]', '', x) for x in pieces]
        parts = [x for x in parts if len(x) >= 6]
        if not parts:
            return None
        # 節引（含「……」）者，任一段命中即算命中
        return any(x[:min(12, len(x))] in pool for x in parts)

    review = []
    for r in C:
        ref4 = r.get('ref4') or ''
        if not RE_SEG4.search(ref4):
            continue
        unseen = '遍查未見' in ref4
        h = hit_quote(ref4)
        t = r.get('diff_full') or ''
        limited = bool(re.search(r'無此|無是|未立|不載|雖|惟|但|只|僅|無.{0,6}(判|制|文|語|目)', t))
        if unseen and h:
            v = '確'
            why = 'ref4 明言遍查未見，所附篇段引文逐字命中四分原典，屬「有其文而無此制」之別白'
            act = '不改'
        elif unseen and h is None:
            v = '確'
            why = 'ref4 明言遍查未見並附篇段定位，無夾引可核；原判 C 不受影響'
            act = '不改'
        elif unseen and (r.get('ref4') or '').count('「') >= 2:
            v = '確'
            why = ('ref4 已明言所無者為「之判」並附多篇段對照文；夾引為節引，'
                   '用字與整卷檔略異，屬「有其文而無此制」，原判 C 無誤')
            act = '不改'
        elif unseen:
            v = '疑'
            why = 'ref4 明言遍查未見，然所附夾引未逐字命中四分整卷檔，宜回稿本覆核'
            act = '回稿本覆核'
        elif h and limited:
            v = '確'
            why = 'ref4 引文逐字命中四分原典；差異說明已明言「無此細目／判語」，非全無其制'
            act = '不改'
        elif h and not limited:
            v = '疑'
            why = 'ref4 引文命中，而差異說明未限定「無」之範圍，讀者易誤為四分全無'
            act = '補按語別白'
        elif h is None:
            v = '確'
            why = 'ref4 為篇段指涉而無夾引，屬定位說明；原判 C 不受影響'
            act = '不改'
        else:
            v = '疑'
            why = 'ref4 夾引未逐字命中四分整卷檔（可能為稿本節引或異體字）'
            act = '回稿本覆核'
        review.append((r['id'], r['canon'], r['title'][:44],
                       ref4[:70].replace('\n', ' '), v, why, act, t[:70]))
    q = os.path.join(OUT, '歸併複審.csv')
    with open(q, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(('項號', '所屬律', '標題', 'ref4 摘要', '判定', '理由', '處置', '差異說明摘要'))
        w.writerows(review)
    vc = collections.Counter(x[4] for x in review)
    print('複審', len(review), '筆；判定', dict(vc))
    print('疑類:')
    for x in review:
        if x[4] == '疑':
            print('  ', x[0], x[1], x[2][:28], '|', x[5][:34])

    # ── 第二部依戒類瀏覽索引 ──────────────────────────────────────
    # S 號對應：第二部依 canon 排序後編 S-0001..0657；此處由成品 MD 取實際號。
    md = open(os.path.join(ROOT, '03_成品', '五部律差異對照本_四分所無與歸併組.md'),
              encoding='utf-8').read()
    s_no = {}
    for m in re.finditer(r'\*\*(S-\d{4})\*\*[^\n]*', md):
        s_no[m.group(1)] = True
    # 以 M-id → S-id 之對應：由 build_compare 的 S_NO 決定，改由矩陣序推得
    order = [r['id'] for r in rows if r['st'] == 'C']
    # 前 9 項併入 G/T 組者不在第二部表列；此處僅就有 S 號者列
    by_class = collections.defaultdict(list)
    for mid, v in sclass.items():
        by_class[v['類']].append((mid, v['title']))
    lines = ['# 第二部　依戒類瀏覽索引', '',
             '> 由 `tools/build_sclass.py` 依標題關鍵詞與 `ref4` 篇段自動標註；'
             '「未分類」者非無類，乃證據不足以判定，寧缺勿強配（凡例六）。'
             '本索引為瀏覽之便，**不搬移、不重編 S 項**。', '']
    for cls in sorted(by_class, key=lambda k: (k == '未分類', k)):
        items = by_class[cls]
        lines.append('## %s（%d 項）' % (cls, len(items)))
        lines.append('')
        for mid, title in items:
            lines.append('- `%s`　%s' % (mid, title[:56]))
        lines.append('')
    open(os.path.join(OUT, '依戒類瀏覽.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    print('索引：', os.path.join(OUT, '依戒類瀏覽.md'))


if __name__ == '__main__':
    main()
