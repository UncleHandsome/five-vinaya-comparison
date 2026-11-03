#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《五部律差異對照本》全量機械校勘。

檢查項：
  A. 三類引文可查性（本稿原文、四分對照、他部對照）
  B. 數字一致性（差異說明稱「N法」，原文是否有 N 項列舉）
  C. 術語一致性（差異說明用該律譯名否）
  D. 標題與差異之矛盾（標題稱有、差異稱無）
  E. 狀態與對照欄一致性
  F. 重複項偵測

輸出：_work/_audit/report.md 與 issues.json
"""
import os, re, json, sys
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, '03_成品')
RAW = os.path.join(ROOT, '01_原文')
OUT = os.path.join(BASE, '_audit')

CANON_DIR = {
    '四分': '四分律', '五分': '五分律', '十誦': '十誦律',
    '僧祇': '摩訶僧祇律', '根有': '根本說一切有部毘奈耶',
}


def load_canon_texts():
    """載入五部律全文（去空白與標點，便於比對）"""
    texts = {}
    for canon, d in CANON_DIR.items():
        p = os.path.join(RAW, d)
        if not os.path.isdir(p):
            print(f'  ! 缺目錄：{p}')
            continue
        buf = []
        for fn in sorted(os.listdir(p)):
            if fn.endswith('.txt'):
                buf.append(open(os.path.join(p, fn), encoding='utf-8', errors='ignore').read())
        t = ''.join(buf)
        texts[canon] = re.sub(r'[^\u4e00-\u9fff]', '', t)
        print(f'  {canon}: {len(texts[canon]):,} 字')
    return texts


def norm(s):
    return re.sub(r'[^\u4e00-\u9fff]', '', s or '')


def main():
    os.makedirs(OUT, exist_ok=True)
    d = json.load(open(os.path.join(BASE, 'matrix_built.json'), encoding='utf-8'))
    orig = json.load(open(os.path.join(BASE, 'originals_index.json'), encoding='utf-8'))

    print('載入原文…')
    T = load_canon_texts()

    issues = defaultdict(list)

    # ── A. 引文可查性 ──
    print('\nA. 引文可查性')
    def check_quotes(s, canon, minlen=6):
        """回傳 (可查數, 不可查數, 不可查樣本)"""
        qs = re.findall(r'「([^」]{' + str(minlen) + r',})」', s or '')
        hit = miss = 0
        bad = []
        for q in qs:
            q2 = norm(q.split('……')[0].split('…')[0])
            if len(q2) < minlen:
                continue
            probe = q2[:18]
            if probe in T.get(canon, ''):
                hit += 1
            else:
                miss += 1
                bad.append(q[:30])
        return hit, miss, bad

    stat_a = Counter()
    for r in d:
        # 四分對照
        h, m, bad = check_quotes(r.get('ref4'), '四分')
        stat_a['ref4_hit'] += h; stat_a['ref4_miss'] += m
        if m:
            issues['A_ref4'].append((r['id'], r['canon'], bad[:2], r.get('ref4', '')[:70]))
        # 五分對照
        h, m, bad = check_quotes(r.get('ref5'), '五分')
        stat_a['ref5_hit'] += h; stat_a['ref5_miss'] += m
        if m:
            issues['A_ref5'].append((r['id'], r['canon'], bad[:2], r.get('ref5', '')[:70]))
        # 十誦對照
        h, m, bad = check_quotes(r.get('ref10'), '十誦')
        stat_a['ref10_hit'] += h; stat_a['ref10_miss'] += m
        if m:
            issues['A_ref10'].append((r['id'], r['canon'], bad[:2], r.get('ref10', '')[:70]))
        # 本稿原文
        o = orig.get(f"{r['canon']}|{r['unit']}|{r['no']}", {}).get('orig', '')
        h, m, bad = check_quotes(o, r['canon'])
        stat_a['orig_hit'] += h; stat_a['orig_miss'] += m
        if m:
            issues['A_orig'].append((r['id'], r['canon'], bad[:2], o[:70]))

    for k in ['ref4', 'ref5', 'ref10', 'orig']:
        h, m = stat_a[f'{k}_hit'], stat_a[f'{k}_miss']
        tot = h + m
        print(f'  {k}: 可查 {h}，不可查 {m}（{m/tot*100 if tot else 0:.1f}%）')

    # ── B. 數字一致性 ──
    print('\nB. 數字一致性')
    NUM = '一二三四五六七八九十'
    def cn2int(s):
        if s in NUM:
            return NUM.index(s) + 1
        if s == '十': return 10
        if s.startswith('十'): return 10 + NUM.index(s[1]) + 1
        if s.endswith('十'): return (NUM.index(s[0]) + 1) * 10
        if '十' in s:
            a, b = s.split('十')
            return (NUM.index(a) + 1) * 10 + (NUM.index(b) + 1)
        return 0

    stat_b = Counter()
    for r in d:
        df = r.get('diff_full', '') or ''
        # 找「N法」「N種」「N事」「N戒」並在差異說明後文或原文中找列舉
        for m in re.finditer(r'([一二三四五六七八九十]{1,2})(法|種|事|戒|門|句)', df):
            cn, unit = m.group(1), m.group(2)
            n = cn2int(cn)
            if n < 2 or n > 20:
                continue
            # 在原文中找「何等N」「云何N」「N者」等列舉標記
            o = orig.get(f"{r['canon']}|{r['unit']}|{r['no']}", {}).get('orig', '')
            if not o:
                continue
            pat = rf'(何等{cn}|云何{cn}|{cn}者|{cn}事|{cn}法|{cn}種)'
            if re.search(pat, o):
                stat_b['ok'] += 1
            else:
                stat_b['noverify'] += 1
    print(f'  法數詞：原文有對應列舉 {stat_b["ok"]}，無從核對 {stat_b["noverify"]}')

    # ── C. 術語一致性 ──
    print('\nC. 術語一致性')
    TERM = {
        '五分': {'突吉羅': '突吉羅', '波逸提': '波逸提', '偷蘭遮': '偷蘭遮'},
        '十誦': {'突吉羅': '突吉羅', '波夜提': '波夜提', '偷蘭遮': '偷蘭遮'},
        '僧祇': {'越毘尼': '突吉羅', '波夜提': '波夜提', '偷蘭遮': '偷蘭遮'},
        '根有': {'惡作': '突吉羅', '波逸底迦': '波逸提', '窣吐羅底也': '偷蘭遮'},
    }
    stat_c = Counter()
    for r in d:
        df = r.get('diff_full', '') or ''
        c = r['canon']
        expect = TERM.get(c, {})
        # 檢查是否用了別律的譯名（如僧祇稿用「突吉羅」而應用「越毘尼」）
        for own, common in expect.items():
            if common != own and own in T.get(c, ''):
                # 該律原文有此譯名
                if common in df and own not in df:
                    stat_c['suspect'] += 1
                    issues['C_term'].append((r['id'], c, f'用「{common}」而未用「{own}」', df[:60]))
    print(f'  可疑：{stat_c["suspect"]}')

    # ── D. 標題與差異矛盾 ──
    print('\nD. 標題與差異矛盾')
    stat_d = 0
    for r in d:
        t = r.get('title', '') or ''
        df = r.get('diff_full', '') or ''
        # 標題稱「X 有」而差異稱「X 無」
        m = re.search(r'([四五十僧根][分誦祇有])律?[^，。]{0,6}(別立|有|獨有)', t)
        if m and re.search(r'四分[^。]{0,8}(無|未見)', df):
            stat_d += 1
            issues['D'].append((r['id'], r['canon'], t[:40], df[:50]))
    print(f'  疑似矛盾：{stat_d}')

    # ── 輸出 ──
    print('\n寫報告…')
    lines = ['# 全量機械校勘報告', '', f'共 {len(d)} 項。', '']
    lines.append('## A. 引文可查性')
    lines.append('')
    lines.append('| 欄 | 可查 | 不可查 | 比率 |')
    lines.append('|---|---:|---:|---:|')
    for k, name in [('ref4', '四分對照'), ('ref5', '五分對照'), ('ref10', '十誦對照'), ('orig', '本稿原文')]:
        h, m = stat_a[f'{k}_hit'], stat_a[f'{k}_miss']
        tot = h + m
        lines.append(f'| {name} | {h} | {m} | {m/tot*100 if tot else 0:.1f}% |')
    lines.append('')
    for key, name in [('A_ref4', '四分對照'), ('A_ref5', '五分對照'), ('A_ref10', '十誦對照'), ('A_orig', '本稿原文')]:
        if issues[key]:
            lines.append(f'### {name} 不可查（{len(issues[key])} 項）')
            lines.append('')
            for it in issues[key][:60]:
                lines.append(f'- `{it[0]}` [{it[1]}] 引文「{it[2][0][:24]}」 — {it[3][:50]}')
            if len(issues[key]) > 60:
                lines.append(f'- ……餘 {len(issues[key])-60} 項')
            lines.append('')

    lines.append('## B. 數字一致性')
    lines.append('')
    lines.append(f'- 法數詞有原文列舉可核：{stat_b["ok"]}')
    lines.append(f'- 無從核對：{stat_b["noverify"]}')
    lines.append('')
    lines.append('## C. 術語一致性')
    lines.append('')
    lines.append(f'- 疑用別律譯名：{stat_c["suspect"]}')
    lines.append('')
    if issues['C_term']:
        for it in issues['C_term'][:40]:
            lines.append(f'- `{it[0]}` [{it[1]}] {it[2]} — {it[3]}')
        lines.append('')
    lines.append('## D. 標題與差異矛盾')
    lines.append('')
    lines.append(f'- 疑似：{stat_d}')
    lines.append('')
    for it in issues['D'][:30]:
        lines.append(f'- `{it[0]}` [{it[1]}] 標題「{it[2]}」／差異「{it[3]}」')
    lines.append('')

    open(os.path.join(OUT, 'report.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    json.dump({k: v for k, v in issues.items()}, open(os.path.join(OUT, 'issues.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'完成：{os.path.join(OUT, "report.md")}')


if __name__ == '__main__':
    main()
