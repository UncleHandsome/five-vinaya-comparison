#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批次三／四：法數與罪名斷言全檢、L2 分層抽樣。

判準（見《原文核校審閱計畫》關二）：
  每一斷言要能回答「原文哪一句支持它」。本工具以「該項 ref／本稿原文」
  為證據範圍，計三項指標：
    A 法數   —— diff_full 明言 N 種／N 法，引文中列舉數是否相稱
    B 罪名   —— diff_full 出现的罪名，是否在同一項引文中可見
    C 引文覆蓋 —— diff_full 中「」內短語，有多少能在同一項引文中找到

抽樣固定 seed=42，可重現；分層為 canon × lv × st，每層抽 10%（至少 2 筆）。

用法：
  python tools/audit_assertions.py
  python tools/audit_assertions.py --out <dir>
"""
import os, re, csv, json, math, random, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
OUT = os.path.join(WORK, '審閱')

CN = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7,
      '八': 8, '九': 9, '十': 10, '十一': 11, '十二': 12, '十三': 13,
      '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18,
      '十九': 19, '二十': 20, '三十': 30, '四十': 40, '五十': 50}

CRIMES = ('波羅夷', '僧伽婆尸沙', '偷蘭遮', '波逸提', '突吉羅',
          '尼薩耆', '滅擯', '摩那埵', '別住', '偷羅遮', '波夜提')

# 「分」不作量詞：三分白、四分僧物皆為份數／部類，非「N 分」之法數。
# 律名（四分律、五分律、十誦律）須先剔除，否則「四分」會被誤讀為 4 分。
RE_NUM = re.compile(r'([一二三四五六七八九十百\d]+)\s*(種|法|事|類|戒|人|日|夜|歲|指|錢)')
RE_CANONNAME = re.compile(r'(?:四分|五分|十誦|僧祇|根有)律?')
RE_ENUM = re.compile(r'[一二三四五六七八九十]+[者、：]')


def numval(s):
    if s.isdigit():
        return int(s)
    if s in CN:
        return CN[s]
    if '十' in s:
        a, _, b = s.partition('十')
        return CN.get(a, 1) * 10 + CN.get(b, 0)
    return None


def refs_of(r, orig_index=None):
    """證據範圍＝各對照欄＋本稿原文＋白話。

    originals_index.json 以「所屬律|卷檔|項序」為鍵，正與矩陣列對應；
    不納入它，會把「法數見於本稿原文而非 ref 節引」誤判為無據。
    """
    s = ' '.join((r.get(k) or '') for k in ('ref4', 'ref5', 'ref10', 'xref'))
    if orig_index:
        k = '%s|%s|%s' % (r.get('canon'), r.get('unit'), r.get('no'))
        v = orig_index.get(k) or {}
        s += ' ' + (v.get('orig') or '') + ' ' + (v.get('plain') or '')
    return s


def enum_count(text):
    """引文中列舉項的最粗估計：數「一者／二者…」或「一、二、…」。"""
    a = len(re.findall(r'[一二三四五六七八九十]+者', text))
    b = len(re.findall(r'[一二三四五六七八九十]+、', text))
    return max(a, b)


def main():
    outdir = OUT
    if '--out' in __import__('sys').argv:
        outdir = __import__('sys').argv[__import__('sys').argv.index('--out') + 1]
    os.makedirs(outdir, exist_ok=True)
    rows = json.load(open(os.path.join(WORK, 'matrix_built.json'), encoding='utf-8'))
    orig_index = json.load(open(os.path.join(WORK, 'originals_index.json'), encoding='utf-8'))

    lines = ['# 斷言全檢與分層抽樣報告', '',
             '> 由 `tools/audit_assertions.py` 產出；seed=42，可重現。', '']
    rec = []

    # ── A 法數斷言全檢 ────────────────────────────────────────────
    lines += ['## 一、法數斷言全檢', '']
    fa = []
    for r in rows:
        t = RE_CANONNAME.sub('', r.get('diff_full') or '')
        nums = [(numval(m.group(1)), m.group(2)) for m in RE_NUM.finditer(t)]
        nums = [(n, u) for n, u in nums if n and n >= 2]
        if not nums:
            continue
        refs = refs_of(r, orig_index)
        ec = enum_count(refs)
        for n, u in nums:
            flag = '可核' if ec and ec >= n else ('引文無列舉' if not ec else '列舉少於所稱')
            fa.append((r['id'], r['canon'], n, u, ec, flag))
    cnt = collections.Counter(x[5] for x in fa)
    lines += ['| 判定 | 筆數 |', '|---|---:|']
    for k, v in cnt.most_common():
        lines.append('| %s | %d |' % (k, v))
    lines += ['', '法數斷言共 **%d** 筆。「引文無列舉」者多因引文為節引、'
              '或法數見於「本稿原文」而非 ref 欄，非必誤；列為人工複核清冊。' % len(fa), '']
    lines += ['### 列舉少於所稱（優先複核）', '']
    short = [x for x in fa if x[5] == '列舉少於所稱']
    for x in short[:40]:
        lines.append('- %s〔%s〕稱 %d %s，引文列舉僅 %d' % x[:5])
    if not short:
        lines.append('- 無')
    lines.append('')
    for x in fa:
        rec.append(('三', r.get('id', ''), '', '法數', 'L1', '④',
                    '', '%d%s' % (x[2], x[3]), '不改' if x[5] == '可核' else '疑',
                    x[5], '人工複核' if x[5] != '可核' else '無'))

    # ── B 罪名斷言 ─────────────────────────────────────────────────
    lines += ['## 二、罪名斷言', '']
    crime_rows = []
    for r in rows:
        t = r.get('diff_full') or ''
        cs = [c for c in CRIMES if c in t]
        if not cs:
            continue
        refs = refs_of(r, orig_index)
        absent = [c for c in cs if c not in refs]
        crime_rows.append((r['id'], r['canon'], ','.join(cs), ','.join(absent)))
    n_abs = sum(1 for x in crime_rows if x[3])
    lines += ['含罪名之差異說明 **%d** 筆；其中罪名未見於同項 ref 引文者 **%d** 筆。' %
              (len(crime_rows), n_abs), '',
              '> 罪名多半記在「本稿原文」欄或由推論得出，ref 為節引，故未見不代表無據；'
              '此數供抽樣時優先挑選。', '']
    for x in [y for y in crime_rows if y[3]][:20]:
        lines.append('- %s〔%s〕缺：%s' % (x[0], x[1], x[3]))
    lines.append('')

    # ── C L2 分層抽樣 ──────────────────────────────────────────────
    lines += ['## 三、L2 分層抽樣（canon × lv × st，每層 10%，seed=42）', '']
    rnd = random.Random(42)
    strata = collections.defaultdict(list)
    for r in rows:
        strata[(r['canon'], r['lv'], r['st'])].append(r)
    sample = []
    for k, v in sorted(strata.items()):
        n = max(2, math.ceil(len(v) * 0.10))
        sample.extend(rnd.sample(v, min(n, len(v))))
    lines += ['分層數 **%d**，抽樣 **%d** 筆（占全書 %.1f%%）。' %
              (len(strata), len(sample), 100 * len(sample) / len(rows)), '']

    low = []
    for r in sample:
        t = r.get('diff_full') or ''
        refs = refs_of(r, orig_index)
        qs = [q for q in re.findall(r'「([^」]{2,14})」', t)]
        hit = sum(1 for q in qs if q in refs)
        cov = (hit / len(qs)) if qs else None
        if cov is not None and cov < 0.5:
            low.append((r['id'], r['canon'], r['st'], len(qs), hit, round(cov, 2), t[:60]))
        rec.append(('四', '', r['id'], '抽樣', 'L2', '④', '', t[:70],
                    '疑' if (cov is not None and cov < 0.5) else '確',
                    '引文覆蓋 %s' % ('%.0f%%' % (cov * 100) if cov is not None else '無引語'),
                    '人工複核' if (cov is not None and cov < 0.5) else '無'))
    lines += ['引語覆蓋率低於 50%% 者 **%d** 筆（占抽樣 %.1f%%）。'
              '此為「差異說明所述是否能在同項引文中逐字找到」之粗標，'
              '低者多為編者綜合推論，宜回原文補證。' %
              (len(low), 100 * len(low) / len(sample)), '']
    lines += ['| 項號 | 律 | 狀態 | 引語數 | 命中 | 覆蓋 | 現文 |',
              '|---|---|---|---:|---:|---:|---|']
    for x in low[:30]:
        lines.append('| %s | %s | %s | %d | %d | %.0f%% | %s |' %
                     (x[0], x[1], x[2], x[3], x[4], x[5] * 100, x[6].replace('|', '／')))
    lines.append('')

    p = os.path.join(outdir, '斷言與抽樣報告.md')
    open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    q = os.path.join(outdir, '斷言抽樣明細.csv')
    with open(q, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(('批次', '篇號', '項號', '檢查碼', '層', '回查點', '原文位置',
                    '現文摘要', '判定', '理由', '處置'))
        w.writerows(rec)
    print('報告：%s' % p)
    print('明細：%s（%d 筆）' % (q, len(rec)))
    print('法數斷言 %d（列舉少於所稱 %d）｜罪名斷言 %d（缺引文 %d）｜'
          '分層 %d／抽樣 %d／低覆蓋 %d' %
          (len(fa), len(short), len(crime_rows), n_abs,
           len(strata), len(sample), len(low)))


if __name__ == '__main__':
    main()
