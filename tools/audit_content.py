#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《五部律差異對照本》內容層自檢（先導掃描）。

與 tools/verify_integrity.py 分工：
  verify_integrity.py 查「結構」——HTML 閉合、項號連續、錨點、三書項數、分卷銜接。
  audit_content.py    查「內容」——引文能否回原典、斷言與狀態是否相合、
                                  「遍查未見」是否可信、分條與體例是否好讀。

本工具只產出「待核清單」，**不自動判定對錯，更不自動改書**。
理由見《原文核校審閱計畫》：前二十一輪的教訓是，凡未經人工回原文判讀者，
一律不得據以改動；尤其「四分無」一類斷言，多半是「無此判語」而非「無此制」。

用法：
  python tools/audit_content.py                    # 印摘要
  python tools/audit_content.py --out 待核清單/     # 另輸出 CSV
  python tools/audit_content.py --only C1,C1B,C3   # 只跑指定關卡
  python tools/audit_content.py --top 30           # 每關列出前 N 例

檢查碼：
  C1   引文回查：ref4/ref5/ref10 之引文首段能否在所屬律原典中逐字命中
  C1B  「遍查未見」複驗：其查詢詞在原典中是否真的 0 見（假性缺載）
  C2   斷言—狀態：diff_full 明言「四分無」而 v4=有者，列為待人工判讀
  C3   未比之部：diff_full 提及某部，而矩陣該部欄位記「未比」
  C4   高風險斷言：法數、罪名、人數、否定、比較——供人工逐條回原文
  C5   差異敘述體例：極短、過長、括號不閉、工作痕、贅尾
  C6   成品分條：極短條、被分條器割裂（以「；」起頭）、引號不閉
  C7   凡例編號：重複或跳號
  C8   術語定義：高頻律學術語是否見於凡例
"""
import os, re, csv, sys, json, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
OUT = os.path.join(ROOT, '03_成品')

CANON_DIR = {
    '四分': '四分律',
    '五分': '五分律',
    '十誦': '十誦律',
    '僧祇': '摩訶僧祇律',
    '根有': '根本說一切有部毘奈耶',
}

# ── 讀入 ──────────────────────────────────────────────────────────────

def _norm(s):
    """比對用正規化：去空白、去省略號標記。不改字，避免掩蓋異文。"""
    s = re.sub(r'\s+', '', s or '')
    return s.replace('……', '').replace('…', '')


def load_pools():
    pools = {}
    for canon, dirname in CANON_DIR.items():
        txt = []
        for p in sorted(glob.glob(os.path.join(ROOT, '01_原文', dirname, '*.txt'))):
            txt.append(open(p, encoding='utf-8', errors='ignore').read())
        pools[canon] = _norm(''.join(txt))
    # 四分另加已切片之 75 篇（段級文本，標點可能與整卷檔略異）
    extra = []
    for p in sorted(glob.glob(os.path.join(WORK, 'sifen', '*.txt'))):
        extra.append(open(p, encoding='utf-8', errors='ignore').read())
    pools['四分'] += _norm(''.join(extra))
    pools['*'] = ''.join(pools[k] for k in CANON_DIR)
    return pools


def load_rows():
    return json.load(open(os.path.join(WORK, 'matrix_built.json'), encoding='utf-8'))


def load_md():
    return open(os.path.join(OUT, '五部律差異對照本.md'), encoding='utf-8').read()


# ── 工具 ──────────────────────────────────────────────────────────────

def quotes(s):
    """抽引號內文字，取 ≥4 字者。"""
    return [q for q in re.findall(r'「([^」]+)」', s or '') if len(_norm(q)) >= 4]


def hit(pool, q, n=12):
    """引文是否命中：有省略號者須前後兩段皆命中；否則取前 n 字。"""
    parts = re.split(r'…+', q)
    parts = [_norm(x) for x in parts if len(_norm(x)) >= 4]
    if not parts:
        return False
    if len(parts) > 1:
        return all(x[:min(n, len(x))] in pool for x in parts[:2])
    return parts[0][:n] in pool


def query_terms(s):
    """從「遍查未見（查詢詞：A／B／C）」抽出查詢詞。"""
    m = re.search(r'查詢詞[：:]\s*([^）)]*)', s or '')
    if not m:
        return []
    return [x.strip() for x in re.split(r'[／/、，,；;]', m.group(1)) if len(x.strip()) >= 2]


# ── 各關 ──────────────────────────────────────────────────────────────

def C1(rows, pools):
    """引文回查：只問「這句是否出現在五部原典任一處」。

    不假設 ref4/ref5/ref10 固定對應某部——實測三欄混錄所屬律與對校律之文，
    硬配會製造假警報。所屬律與段次之判定留給人工（見審閱計畫關一）。
    """
    res = []
    for r in rows:
        for field in ('ref4', 'ref5', 'ref10'):
            s = r.get(field) or ''
            if '遍查未見' in s:
                continue
            qs = quotes(s)
            if not qs:
                continue
            q = max(qs, key=lambda x: len(_norm(x)))
            if not hit(pools['*'], q):
                res.append((r['id'], field, r['canon'],
                            _norm(q)[:40], '引文未命中五部原典',
                            '回原典核該句所屬律與段次；或為組字式／異體／節引'))
    return res


def C1B(rows, pools):
    """「遍查未見」複驗——只報兩種真正可疑者。

    凡例四明言：「遍查未見」謂未得**此制**之對應，非謂查詢詞 0 見。
    故常見詞出現百餘次並不足以推翻斷言，不列。
    只列：① 查詢詞過泛或為純數字（無法覆核）；
          ② 精確短語（≥4 字）在該部罕見而實有（1–5 見），最可能是漏檢。
    """
    res = []
    for r in rows:
        for field, canon in (('ref4', '四分'), ('ref5', '五分'), ('ref10', '十誦')):
            s = r.get(field) or ''
            if '遍查未見' not in s:
                continue
            for t in query_terms(s):
                q = _norm(t)
                if len(q) < 3 or q.isdigit():
                    if LOOSE:
                        res.append((r['id'], field, r['canon'], t,
                                    '查詢詞過泛／純數字', '補可覆核之精確詞，或改述所查之制'))
                    continue
                n = pools[canon].count(q)
                if 1 <= n <= 5 and len(q) >= 4:
                    res.append((r['id'], field, r['canon'], t,
                                '精確短語實有 %d 見' % n, '回該處核是否即所尋之制'))
    return res


def C2(rows, pools):
    """diff_full 明言四分無，而 v4=有：待人工判讀，非必錯。"""
    pat = re.compile(r'四分(?:律)?(?:並|亦|皆)?(?:無|未見|不載|不立|無此|未有)|本律無')
    res = []
    for r in rows:
        t = r.get('diff_full') or ''
        if pat.search(t) and r['v4'] == '有':
            m = pat.search(t)
            res.append((r['id'], 'diff_full', r['canon'],
                        t[max(0, m.start() - 18):m.start() + 34],
                        'v4=有', '判讀是「無此制」或「無此細目」；後者非矛盾'))
    return res


def C3(rows, pools):
    """差異敘述提及某部，而矩陣該部記「未比」——讀者易誤為「無」。"""
    pairs = (('五分', 'v5'), ('十誦', 'v10'), ('僧祇', 'vMK'), ('根有', 'vGU'))
    res = []
    for r in rows:
        t = r.get('diff_full') or ''
        for name, field in pairs:
            if name in t and r.get(field) == '未比':
                res.append((r['id'], field, r['canon'], name,
                            '敘述涉及 %s 而欄記未比' % name,
                            '補「未比」之別白，或改敘述使不涉該部'))
    return res


def C4(rows, pools):
    """高風險斷言抽出：法數、罪名、人數、否定、比較。"""
    pats = [
        ('法數', re.compile(r'(?:舉|凡|立|列|別為|分為|有)[一二三四五六七八九十百\d]+(?:種|法|事|類|戒|人|日|夜|歲|指|錢)')),
        ('罪名', re.compile(r'(?:波羅夷|僧殘|偷蘭遮|波逸提|突吉羅|尼薩耆|滅擯|摩那埵|別住)')),
        ('否定', re.compile(r'(?:遍查未見|無此|不載|未見|不立|無有|所無)')),
        ('比較', re.compile(r'(?:所異在|不同|而.{0,8}(?:無|有)|惟|但)')),
    ]
    res = []
    for r in rows:
        t = r.get('diff_full') or ''
        kinds = [n for n, p in pats if p.search(t)]
        if kinds:
            res.append((r['id'], 'diff_full', r['canon'],
                        t[:60], '/'.join(kinds), '回原文核此斷言'))
    return res


def C5(rows, pools):
    """差異敘述體例。"""
    res = []
    for r in rows:
        t = r.get('diff_full') or ''
        L = len(t)
        if L < 25:
            res.append((r['id'], 'diff_full', r['canon'], t[:30], '極短 %d 字' % L, '補足所異之由'))
        if L > 400:
            res.append((r['id'], 'diff_full', r['canon'], t[:40], '過長 %d 字' % L, '考慮分條或移入按語'))
        if t.count('「') != t.count('」'):
            res.append((r['id'], 'diff_full', r['canon'], t[:30], '引號不閉', '補正'))
        for w in ('核定稿', 'TODO', '待補', '待核', '暫存'):
            if w in t:
                res.append((r['id'], 'diff_full', r['canon'], t[:30], '工作痕：' + w, '清除'))
                break
        if re.search(r'-\s*原文[：:]|-\s*白話', t):
            res.append((r['id'], 'diff_full', r['canon'], t[:30], '贅尾', '清除'))
    return res


def C6(rows, pools, md):
    """成品分條品質。"""
    res = []
    lines = [(i + 1, l) for i, l in enumerate(md.split('\n')) if l.startswith('- ')]
    for ln, l in lines:
        body = l[2:].strip()
        if len(body) < 12:
            res.append(('L%d' % ln, '分條', '', body[:30], '極短條', '併入上條或補足'))
        if body.startswith(('；', '，', '。', '、')):
            res.append(('L%d' % ln, '分條', '', body[:30], '疑遭分條器割裂', '改寫引文標點'))
        if body.count('「') != body.count('」'):
            res.append(('L%d' % ln, '分條', '', body[:30], '引號不閉', '補正'))
    return res


def C7(rows, pools, md):
    """凡例編號重複／跳號。"""
    seg = md.split('## 附錄')[0]
    nums = []
    cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
          '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,
          '十八':18,'十九':19,'二十':20}
    for m in re.finditer(r'^([一二三四五六七八九十]+)、\*\*', seg, re.M):
        nums.append((cn.get(m.group(1), 0), m.group(1)))
    res = []
    seen = {}
    for n, s in nums:
        if n in seen:
            res.append(('凡例', '體例', '', '%s、 重出（前見 %s、）' % (s, seen[n]),
                        '編號重複', '改號'))
        seen[n] = s
    return res


def C8(rows, pools, md):
    """高頻術語是否已在凡例定義。"""
    seg = md.split('## 附錄')[0]
    terms = ['明相出', '迦絺那', '摩那埵', '本日治', '說淨', '淨施', '手受',
             '非時漿', '結界', '和合', '別住', '覆藏', '遮說戒', '正食',
             '非正食', '殘食法', '不癡毘尼', '搩手', '四方僧物']
    res = []
    for t in terms:
        n = md.count(t)
        if n >= 20 and t not in seg:
            res.append(('全書', '術語', '', t, '全書 %d 見而凡例未定義' % n,
                        '補入凡例「一字多義」或另立名相表'))
    return res


LOOSE = False   # --loose 時才列出「查詢詞過泛」一類參考性雜訊

CHECKS = {
    'C1': (C1, '引文回查'), 'C1B': (C1B, '遍查未見複驗'),
    'C2': (C2, '斷言—狀態'), 'C3': (C3, '未比之部'),
    'C4': (C4, '高風險斷言'), 'C5': (C5, '差異敘述體例'),
    'C6': (C6, '成品分條'), 'C7': (C7, '凡例編號'), 'C8': (C8, '術語定義'),
}

HEADER = ('項號／位置', '欄位', '所屬律', '現文／詞', '發現', '建議動作')


def main():
    global LOOSE
    args = sys.argv[1:]
    LOOSE = '--loose' in args
    outdir = None
    if '--out' in args:
        outdir = args[args.index('--out') + 1]
    only = None
    if '--only' in args:
        only = set(args[args.index('--only') + 1].split(','))
    top = 8
    if '--top' in args:
        top = int(args[args.index('--top') + 1])

    rows = load_rows()
    pools = load_pools()
    md = load_md()
    print('資料：矩陣 %d 列；原文池 %s 字；對照本 %s 字'
          % (len(rows), format(len(pools['*']), ','), format(len(md), ',')))
    print('（本工具只列「待核」，不判對錯、不改書）\n')

    allrows = []
    for code, (fn, name) in CHECKS.items():
        if only and code not in only:
            continue
        try:
            r = fn(rows, pools, md) if fn.__code__.co_argcount >= 3 else fn(rows, pools)
        except TypeError:
            r = fn(rows, pools)
        tag = '（抽樣母體，非待核）' if code == 'C4' else ''
        print('[%s] %-14s %5d 筆%s' % (code, name, len(r), tag))
        for x in r[:top]:
            print('     ', ' | '.join(str(v)[:44] for v in x))
        if len(r) > top:
            print('      … 餘 %d 筆' % (len(r) - top))
        allrows.extend([(code,) + x for x in r])

    if outdir:
        os.makedirs(outdir, exist_ok=True)
        p = os.path.join(outdir, '內容待核清單.csv')
        with open(p, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(('檢查碼',) + HEADER)
            w.writerows(allrows)
        print('\n已輸出：%s（%d 筆）' % (p, len(allrows)))
        for code in CHECKS:
            sub = [x for x in allrows if x[0] == code]
            if sub and (not only or code in only):
                q = os.path.join(outdir, '待核_%s.csv' % code)
                with open(q, 'w', encoding='utf-8-sig', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(HEADER)
                    w.writerows(x[1:] for x in sub)
    n_wait = sum(1 for x in allrows if x[0] != 'C4')
    n_pool = len(allrows) - n_wait
    print('\n合計待核 %d 筆；另 C4 抽樣母體 %d 筆（供分層抽樣，非逐條待核）。'
          % (n_wait, n_pool))


if __name__ == '__main__':
    main()
