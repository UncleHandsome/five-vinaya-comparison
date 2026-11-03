# -*- coding: utf-8 -*-
"""Assemble per-item evidence for filling the 五分 draft's 十誦律對照 column.

Three independent evidence streams:
  A. findings_ss/*.md  — 十誦 retained items, each citing the 五分 paragraph it matches
  B. 十誦律_去重 附錄一 — deletion table, rows citing a 五分 paragraph
  C. ss_cands.json     — lexical (rare n-gram) candidates over the whole 十誦 corpus

Output: _work/ss_evidence/volNN.md, one section per 五分 item.
"""
import glob
import json
import os
import re
from collections import defaultdict

W = os.path.dirname(os.path.abspath(__file__))
ABS = ('遍查未見', '全無', '無此', '未見', '俱無', '皆無')


def norm(s):
    return re.sub(r'[^\u4e00-\u9fff]', '', re.sub(r'[\s　]', '', s))


def items(path):
    txt = open(path, encoding='utf-8').read()
    out = []
    for p in re.split(r'^### ', txt, flags=re.M)[1:]:
        head = p.split('\n', 1)[0]
        m = re.match(r'(\d+)\.\s*(.*)', head)
        if m:
            out.append({'no': int(m.group(1)), 'title': m.group(2).strip(), 'body': p})
    return out


def field(body, name):
    m = re.search(r'^-\s*' + name + r'[：:](.*)$', body, re.M)
    return m.group(1).strip() if m else ''


def load_shisong():
    vols = {}
    for f in sorted(glob.glob(os.path.join(W, 'shisong', 'vol*.txt'))):
        v = int(re.search(r'vol(\d+)', f).group(1))
        d = {}
        for ln in open(f, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if '\t' in ln:
                a, b = ln.split('\t', 1)
                if a.isdigit():
                    d[int(a)] = b
        vols[v] = d
    return vols


def para_span(vols, v, p, before=0, after=1):
    d = vols.get(v, {})
    out = []
    for q in range(p - before, p + after + 1):
        if q in d:
            out.append((q, d[q]))
    return out


def stream_a():
    """(五分vol, 五分para) -> 十誦 item citation records."""
    idx = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(W, 'findings_ss', '*.md'))):
        for it in items(f):
            ref = field(it['body'], '五分律對照')
            pos = field(it['body'], '位置')
            if not ref or any(k in ref[:12] for k in ABS):
                continue
            t = re.sub(r'[^\s，：；、（）]*原文\.txt', '', ref)
            t = re.sub(r'第\d+行', '', t)
            hits = []
            for a, b in re.findall(r'卷\s*(\d{1,2})\s*[·，、]?\s*段\s*(\d{1,3})', t):
                hits.append((int(a), int(b)))
            for m in re.finditer(r'(?<![\d.\-])(\d{1,2})\s*-\s*(\d{1,3})(?![\d])', t):
                hits.append((int(m.group(1)), int(m.group(2))))
            for v, p in hits:
                if 1 <= v <= 30:
                    idx[(v, p)].append({'unit': os.path.basename(f)[:-3], 'no': it['no'],
                                        'title': it['title'], 'pos': pos, 'ref': ref})
    return idx


def main():
    vols = load_shisong()
    ia = stream_a()
    ib = json.load(open(os.path.join(W, 'ss_deleted_index.json'), encoding='utf-8'))
    ic = json.load(open(os.path.join(W, 'ss_cands.json'), encoding='utf-8'))

    outdir = os.path.join(W, 'ss_evidence')
    os.makedirs(outdir, exist_ok=True)

    stats = {'a': 0, 'b': 0, 'c': 0, 'none': 0}
    for f in sorted(glob.glob(os.path.join(W, 'findings', 'vol*.md'))):
        v = int(re.search(r'vol(\d+)', f).group(1))
        lines = ['# 五分卷%d 十誦對照證據' % v, '',
                 '每項列出三路證據。A＝十誦稿保留項所引五分段；B＝十誦刪略總表所記對應；C＝稀有詞檢索候選。',
                 'A、B 為既有校勘紀錄，可信度高；C 僅供起查。', '']
        for it in items(f):
            pos = field(it['body'], '位置')
            ps = set()
            for a, b in re.findall(r'(?<![\d-])(\d{1,3})\s*[-–—]\s*(\d{1,3})(?![\d-])', pos):
                ps.update(range(int(a), int(b) + 1))
            for a in re.findall(r'(?<![\d-])(\d{1,3})(?![\d-])', pos):
                ps.add(int(a))
            lines += ['', '## 第%d項　%s' % (it['no'], it['title']),
                      '- 五分位置：%s' % pos,
                      '- 五分差異說明：%s' % field(it['body'], '差異說明')[:220]]
            seen = set()
            got = False
            for p in sorted(ps):
                for rec in ia.get((v, p), []):
                    got = True
                    stats['a'] += 1
                    key = ('A', rec['unit'], rec['no'])
                    if key in seen:
                        continue
                    seen.add(key)
                    lines.append('- **A** 十誦稿 `%s` 第%d項「%s」（十誦位置 %s）'
                                 % (rec['unit'], rec['no'], rec['title'], rec['pos']))
                    lines.append('  - 其五分對照：%s' % rec['ref'][:180])
                for rec in ib.get('%d-%d' % (v, p), []):
                    got = True
                    stats['b'] += 1
                    key = ('B', rec[0], rec[1])
                    if key in seen:
                        continue
                    seen.add(key)
                    lines.append('- **B** 十誦 卷%d 段%d「%s」（刪略理由：%s）'
                                 % (rec[0], rec[1], rec[2], rec[3]))
                    for q, tx in para_span(vols, rec[0], rec[1], 0, 1):
                        lines.append('  - 卷%d 段%d：%s' % (rec[0], q, tx[:150]))
            cand = ic.get('%d-%d' % (v, it['no']), {}).get('cands', [])
            qtext = field(it['body'], '原文')
            qg5 = {norm(qtext)[i:i + 5] for i in range(len(norm(qtext)) - 4)}
            for c in cand[:3]:
                if c['score'] < 120:
                    continue
                ctext = norm(c['text'])
                shared = any(g in ctext for g in qg5)
                if not shared:
                    continue
                key = ('C', c['vol'], c['para'])
                if key in seen:
                    continue
                seen.add(key)
                got = True
                stats['c'] += 1
                lines.append('- **C** 十誦 卷%d 段%d（相似度 %s）：%s'
                             % (c['vol'], c['para'], c['score'], c['text'][:130]))
            if not got:
                stats['none'] += 1
                lines.append('- 三路皆無候選，須直接檢索。')
        open(os.path.join(outdir, 'vol%02d.md' % v), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(stats)


if __name__ == '__main__':
    main()
