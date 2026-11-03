# -*- coding: utf-8 -*-
"""Render `collide.json` as a working report for hand adjudication."""
import os, json, re

W = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(W, 'collide.json'), encoding='utf-8'))
rows = json.load(open(os.path.join(W, 'matrix_rows.json'), encoding='utf-8'))
by = {(r['canon'], r['unit'], r['no']): r for r in rows}


def clip(s, n=150):
    s = re.sub(r'\s+', '', s or '')
    return s[:n] + ('…' if len(s) > n else '')


strong = [x for x in res if x['vs'][0]['score'] >= 2]
weak = [x for x in res if x['vs'][0]['score'] < 2]
strong.sort(key=lambda x: (-x['vs'][0]['score'], -x['vs'][0]['cover']))

L = ['# 四分所無（C 項）的語料碰撞候選', '',
     '以各稿「差異說明」與標題中之稀有詞（在目標律中出現 ≤40 段者）逐段比對，'
     '合併重疊命中為跨度，去重計分。得分 = 該段中獨立命中之稀有字串數。', '',
     '## 一、強候選（≥2 個獨立命中）', '',
     '| # | 主稿 | 項 | 題 | 對律 | 卷段 | 分 | 命中字串 |', '|---:|---|---:|---|---|---|---:|---|']
for i, x in enumerate(strong, 1):
    v = x['vs'][0]
    L.append('| %d | %s | %s#%s | %s | %s | 卷%d段%d | %d | %s |' % (
        i, x['canon'], x['unit'], x['no'], clip(x['title'], 26),
        v['canon'], v['vol'], v['seg'], v['score'], '／'.join(v['terms'])))
L += ['', '## 二、弱候選（單一長字串，多為人名地名）', '',
      '| # | 主稿 | 項 | 題 | 對律 | 卷段 | 命中字串 |', '|---:|---|---:|---|---|---|---|']
for i, x in enumerate(weak, 1):
    v = x['vs'][0]
    L.append('| %d | %s | %s#%s | %s | %s | 卷%d段%d | %s |' % (
        i, x['canon'], x['unit'], x['no'], clip(x['title'], 26),
        v['canon'], v['vol'], v['seg'], '／'.join(v['terms'])))

L += ['', '## 三、強候選逐條（含對律原文）', '']
for i, x in enumerate(strong, 1):
    r = by.get((x['canon'], x['unit'], x['no']), {})
    L.append('### %d. %s %s#%s　%s' % (i, x['canon'], x['unit'], x['no'], x['title']))
    L.append('')
    L.append('- 本稿差異說明：%s' % clip(r.get('diff'), 220))
    L.append('- 位置：%s' % clip(r.get('pos'), 60))
    for v in x['vs'][:2]:
        L.append('- 對律 %s 卷%d段%d（分 %d，命中 %s）：' % (
            v['canon'], v['vol'], v['seg'], v['score'], '／'.join(v['terms'])))
        L.append('  > %s' % v['snip'])
    L.append('')

open(os.path.join(W, 'collide_report.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('strong', len(strong), 'weak', len(weak), '-> collide_report.md')
