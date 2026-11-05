#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""審閱判讀引擎：把待核逐筆抓回原典上下文，自動分級，產出台帳。

與 audit_content.py 的差別：
  audit_content.py  只列「哪些要核」
  audit_review.py   把每一筆的**原典上下文**抓出來，並做可自動判定者的分級，
                    輸出「判讀材料包」供人工回原文判讀，及五級判定台帳。

用法：
  python tools/audit_review.py                 # 全跑
  python tools/audit_review.py --only 1B,2    # 只跑指定節
  python tools/audit_review.py --out <dir>    # 指定輸出目錄
"""
import os, re, sys, csv, json, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
OUT = os.path.join(ROOT, '03_成品')
sys.path.insert(0, WORK)

CANON_DIR = {
    '四分': '四分律', '五分': '五分律', '十誦': '十誦律',
    '僧祇': '摩訶僧祇律', '根有': '根本說一切有部毘奈耶',
}


def _flat(s):
    return re.sub(r'\s+', '', s or '')


def load_pools():
    raw, flat = {}, {}
    for canon, d in CANON_DIR.items():
        t = ''.join(open(p, encoding='utf-8', errors='ignore').read()
                    for p in sorted(glob.glob(os.path.join(ROOT, '01_原文', d, '*.txt'))))
        raw[canon] = t
        flat[canon] = _flat(t)
    ex = ''.join(open(p, encoding='utf-8', errors='ignore').read()
                 for p in sorted(glob.glob(os.path.join(WORK, 'sifen', '*.txt'))))
    raw['四分'] += ex
    flat['四分'] += _flat(ex)
    flat['原典'] = ''.join(flat[k] for k in CANON_DIR)
    # 凡例三：引文出自各稿 findings 去重合冊。回查池須含稿本層，
    # 否則會把稿本節引誤報為誤引（先導掃描曾誤報 186 筆，加池後全數命中）。
    draft = []
    for pat in ('02_去重稿/*.md', '_work/findings/*.md', '_work/findings_ss/*.md',
                '_work/findings_mk/*.md', '_work/findings_gu/*.md'):
        for p in sorted(glob.glob(os.path.join(ROOT, pat))):
            draft.append(open(p, encoding='utf-8', errors='ignore').read())
    raw['稿本'] = ''.join(draft)
    flat['稿本'] = _flat(raw['稿本'])
    flat['*'] = flat['原典'] + flat['稿本']
    return raw, flat


def context(raw, term, width=90, limit=2):
    """抓詞在原典中出現處之前後文。"""
    hits = []
    for m in list(re.finditer(re.escape(term), raw))[:limit]:
        s = raw[max(0, m.start() - width): m.end() + width]
        hits.append(re.sub(r'\s+', '', s))
    return hits


def quotes(s):
    return [q for q in re.findall(r'「([^」]+)」', s or '') if len(_flat(q)) >= 4]


def query_terms(s):
    m = re.search(r'查詢詞[：:]\s*([^）)]*)', s or '')
    if not m:
        return []
    return [x.strip() for x in re.split(r'[／/、，,；;]', m.group(1)) if len(x.strip()) >= 2]


# ── 分級：C1 引文回查 ──────────────────────────────────────────────

VARIANT = str.maketrans({
    '麁': '麤', '㥲': '瞋', '脚': '腳', '鉢': '缽', '柰': '奈',
    '㝹': '兔', '床': '牀', '著': '着', '污': '汙',
})


def classify_quote(q, flat):
    """回 (級, 理由)。甲逐字、乙節引、丙可解釋、丁真未命中。"""
    raw_q = q
    f = _flat(q)
    if '…' in q:
        parts = [x for x in re.split(r'…+', f) if len(x) >= 4]
        if parts and all(x[:10] in flat['*'] for x in parts[:2]):
            return '乙', '節引，兩端皆命中'
    f2 = f.translate(VARIANT)
    f2 = re.sub(r'\[[^\]]{1,12}\]', '', f2)          # 去組字式
    f2 = re.sub(r'[，。、；：？！「」『』（）()]', '', f2)  # 去標點
    if len(f2) >= 6:
        for n in (12, 10, 8, 6):
            if f2[:n] in flat['*'].translate(VARIANT):
                return '甲', '去異體／標點後命中前 %d 字' % n
        # 改查中段（引文可能含前綴說明）
        for i in range(0, min(len(f2) - 8, 24), 4):
            if f2[i:i + 8] in flat['*'].translate(VARIANT):
                return '甲', '中段第 %d 字起命中' % i
    if re.search(r'\[[^\]]{1,12}\]', raw_q):
        return '丙', '含組字式，原典以造字檔存儲'
    if any(c in raw_q for c in '麁㥲脚鉢㝹'):
        return '丙', '含異體字'
    if '…' in raw_q:
        return '丙', '節引但兩端未能自動對齊'
    return '丁', '五部原典皆未見，疑誤引或張冠李戴'


# ── 台帳 ────────────────────────────────────────────────────────────

LEDGER = ('批次', '篇號', '項號', '檢查碼', '層', '回查點', '原文位置',
          '現文摘要', '判定', '理由', '處置', 'errata鍵', '改動欄位', '複驗')


def main():
    args = sys.argv[1:]
    outdir = os.path.join(WORK, '審閱')
    if '--out' in args:
        outdir = args[args.index('--out') + 1]
    only = None
    if '--only' in args:
        only = set(args[args.index('--only') + 1].split(','))
    os.makedirs(outdir, exist_ok=True)

    rows = json.load(open(os.path.join(WORK, 'matrix_built.json'), encoding='utf-8'))
    byid = {r['id']: r for r in rows}
    raw, flat = load_pools()
    md = open(os.path.join(OUT, '五部律差異對照本.md'), encoding='utf-8').read()
    plain = json.load(open(os.path.join(WORK, 'sifen_plain.json'), encoding='utf-8'))

    material = ['# 審閱判讀材料包', '',
                '> 由 `tools/audit_review.py` 自動抓取原典上下文。**每一級判定仍須回原文讀過才算數。**', '']
    ledger = []
    summary = collections.Counter()

    def add(mat):
        material.append(mat)

    def rec(batch, pno, pid, code, layer, point, loc, excerpt, verdict, reason,
            action, key='', field=''):
        ledger.append((batch, pno, pid, code, layer, point, loc,
                       excerpt[:100], verdict, reason, action, key, field, ''))
        summary[(code, verdict)] += 1

    # ── 1B：假性「遍查未見」 ────────────────────────────────────────
    if not only or '1B' in only:
        add('## 一、C1B　「遍查未見」之精確查詢詞實有（回原文判是否即所尋之制）')
        add('')
        n = 0
        for r in rows:
            for field, canon in (('ref4', '四分'), ('ref5', '五分'), ('ref10', '十誦')):
                s = r.get(field) or ''
                if '遍查未見' not in s:
                    continue
                for t in query_terms(s):
                    q = _flat(t)
                    if len(q) < 4 or q.isdigit():
                        continue
                    c = flat[canon].count(q)
                    if not (1 <= c <= 5):
                        continue
                    n += 1
                    ctx = context(raw[canon], t, 85, 2)
                    add('### %s　%s　查詞「%s」（%s %d 見）' % (r['id'], r['canon'], t, canon, c))
                    add('')
                    add('- 所屬律：%s｜狀態 %s｜欄位 %s' % (r['canon'], r['st'], field))
                    add('- 標題：%s' % r['title'])
                    add('- 該欄原文：%s' % re.sub(r'\s+', '', s)[:180])
                    for i, x in enumerate(ctx, 1):
                        add('- 原典出處 %d：…%s…' % (i, x))
                    add('')
                    rec('一', '', r['id'], 'C1B', 'L1', '③',
                        '%s／%s' % (canon, t), t, '待判', '', '')
        add('> 小計 %d 筆。判準：詞出現不等於「此制存在」；須讀上下文確認是否即該項所尋之制。' % n)
        add('')

    # ── 2：「四分無」而 v4=有 ───────────────────────────────────────
    if not only or '2' in only:
        add('## 二、C2　diff_full 言「四分無」而 v4=有')
        add('')
        pat = re.compile(r'四分(?:律)?(?:並|亦|皆)?(?:無|未見|不載|不立|無此|未有)|本律無')
        n = 0
        for r in rows:
            t = r.get('diff_full') or ''
            if pat.search(t) and r['v4'] == '有':
                n += 1
                add('### %s　〔%s %s〕%s' % (r['id'], r['canon'], r['st'], r['title']))
                add('')
                add('- 差異說明：%s' % t)
                add('- 四分對照（ref4）：%s' % re.sub(r'\s+', '', r.get('ref4') or '')[:200])
                add('- 五欄：v4=%s v5=%s v10=%s vMK=%s vGU=%s' %
                    (r['v4'], r['v5'], r['v10'], r['vMK'], r['vGU']))
                add('')
                rec('一', '', r['id'], 'C2', 'L1', '④⑤', '',
                    t[:80], '待判', '', '')
        add('> 小計 %d 筆。判準：區分「無此制」／「無此判語／細目」；後者非矛盾，改寫法不改資料。' % n)
        add('')

    # ── 3：未比之部 ─────────────────────────────────────────────────
    if not only or '3' in only:
        add('## 三、C3　敘述涉及「未比」之部')
        add('')
        for r in rows:
            t = r.get('diff_full') or ''
            for name, f in (('五分', 'v5'), ('十誦', 'v10'), ('僧祇', 'vMK'), ('根有', 'vGU')):
                if name in t and r.get(f) == '未比':
                    add('- **%s**〔%s〕%s：%s' % (r['id'], r['canon'], f, t[:150]))
                    rec('一', '', r['id'], 'C3', 'L0', '⑤', f, t[:70], '可改',
                        '敘述涉及該部而欄記未比，讀者易誤為「無」', '凡例六補別白；該項對照欄補「未比」')
        add('')

    # ── 1：引文回查分級 ─────────────────────────────────────────────
    if not only or '1' in only:
        add('## 四、C1　引文回查四級判定')
        add('')
        grade = collections.Counter()
        detail = collections.defaultdict(list)
        for r in rows:
            for field in ('ref4', 'ref5', 'ref10'):
                s = r.get(field) or ''
                if '遍查未見' in s:
                    continue
                qs = quotes(s)
                if not qs:
                    continue
                q = max(qs, key=lambda x: len(_flat(x)))
                f = _flat(q)
                # 已在 audit_content 判為命中者，逕記甲
                if len(re.split(r'…+', q)) > 1:
                    parts = [x for x in re.split(r'…+', f) if len(x) >= 4]
                    okk = parts and all(x[:10] in flat['*'] for x in parts[:2])
                else:
                    okk = f[:12] in flat['*']
                if okk:
                    if f[:12] in flat['原典']:
                        g, why = '甲', '逐字命中整卷原典'
                    elif f[:12] in flat['稿本']:
                        g, why = '甲', '逐字命中 findings 去重合冊（稿本層）'
                    else:
                        g, why = '甲', '節引兩端皆命中'
                else:
                    g, why = classify_quote(q, flat)
                grade[g] += 1
                detail[g].append((r['id'], field, r['canon'], f[:48], why))
                rec('二', '', r['id'], 'C1', 'L0', '①②③', field, f[:60],
                    {'甲': '確', '乙': '確', '丙': '不改', '丁': '疑'}[g],
                    why, {'甲': '無', '乙': '無', '丙': '記理由', '丁': '回原典核所屬律與段次'}[g])
        add('| 級 | 筆數 | 意義 |')
        add('|---|---:|---|')
        for g, name in (('甲', '逐字命中'), ('乙', '合法節引'), ('丙', '可解釋未命中'), ('丁', '真未命中')):
            add('| %s | %d | %s |' % (g, grade[g], name))
        add('')
        add('### 丁類明細（須逐筆回原典）')
        add('')
        for x in detail['丁']:
            add('- %s｜%s｜%s｜%s｜%s' % x)
        add('')
        add('### 丙類明細（記理由即可）')
        add('')
        for x in detail['丙'][:60]:
            add('- %s｜%s｜%s｜%s｜%s' % x)
        if len(detail['丙']) > 60:
            add('- … 餘 %d 筆見台帳' % (len(detail['丙']) - 60))
        add('')

    # ── 5：篇級對讀 ─────────────────────────────────────────────────
    if not only or '5' in only:
        add('## 五、L3　七十五篇逐篇對讀（自動全檢）')
        add('')
        try:
            import sifen_src as S
            has_src = True
        except Exception as e:
            has_src = False
            add('> sifen_src 無法載入：%s' % e)
        dcount = collections.Counter(int(x) for x in
                                     re.findall(r'四分 (\d{3}) 段', md))
        add('| 篇 | 節數 | 白話鍵 | 合段(正常) | 孤鍵 | 空節 | 節題異常 | 差異項 |')
        add('|---:|---:|---:|---:|---:|---:|---:|---:|')
        bad = []
        for no in range(0, 75):
            try:
                us = S.units(no) if has_src else []
            except Exception:
                us = []
            segs = set()
            for u in us:
                segs.update(range(u['a'], u['b'] + 1))
            pkeys = set()
            for k in plain:
                if k.startswith('%03d-' % no):
                    try:
                        pkeys.add(int(k.split('-')[1]))
                    except ValueError:
                        pass
            # 凡例十三已明：譯者或合數段為一，故「某段無單獨白話鍵」是合段，非缺漏。
            # 真異常只有三種：白話鍵超出原文段號、整節全無白話、節題截斷。
            merged = sorted(segs - pkeys)
            orphan = sorted(pkeys - segs)
            empty_sec = [u['a'] for u in us
                         if not (set(range(u['a'], u['b'] + 1)) & pkeys)]
            abn = [(u.get('name') or '') for u in us
                   if re.search(r'[：:『』「」]|言$|共$|至阿頭$', u.get('name') or '')]
            nd = dcount.get(no, 0)
            add('| %03d | %d | %d | %d | %d | %d | %d | %d |' %
                (no, len(us), len(pkeys), len(merged), len(orphan),
                 len(empty_sec), len(abn), nd))
            if orphan or empty_sec or abn:
                bad.append((no, orphan[:8], empty_sec[:8], abn[:3]))
            rec('五', '%03d' % no, '', 'L3', 'L3', '①⑤', '%03d' % no,
                '節%d 白話%d 合段%d 孤鍵%d 空節%d 題異常%d' %
                (len(us), len(pkeys), len(merged), len(orphan), len(empty_sec), len(abn)),
                '疑' if (orphan or empty_sec or abn) else '確', '', '')
        add('')
        add('### 異常篇明細')
        add('')
        for no, orphan, empty_sec, abn in bad:
            add('- %03d：孤鍵 %s｜空節 %s｜節題 %s' % (no, orphan, empty_sec, abn))
        add('')

    # ── 寫出 ─────────────────────────────────────────────────────────
    p = os.path.join(outdir, '判讀材料.md')
    open(p, 'w', encoding='utf-8').write('\n'.join(material))
    q = os.path.join(outdir, '審閱台帳.csv')
    with open(q, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(LEDGER)
        w.writerows(ledger)
    print('判讀材料：%s（%d 行）' % (p, len(material)))
    print('審閱台帳：%s（%d 筆）' % (q, len(ledger)))
    print('判定分佈：', dict(summary))


if __name__ == '__main__':
    main()
