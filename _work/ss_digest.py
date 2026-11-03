# -*- coding: utf-8 -*-
"""Compact evidence digest for the 110 五分 items whose 四分 counterpart is absent.

For each such item we must decide whether 十誦 has the same institution.  The
digest shows the 五分 item plus the strongest pointers into 十誦:
  A  a 十誦 retained item that cites this very 五分 paragraph
  B  a row of the 十誦 deletion table that cites it
  R  rare-term co-occurrence candidate
"""
import glob
import json
import os
import re
from collections import defaultdict

W = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    return re.sub(r'[^\u4e00-\u9fff]', '', re.sub(r'[\s　]', '', s))


def items(path):
    txt = open(path, encoding='utf-8').read()
    out = []
    for p in re.split(r'^### ', txt, flags=re.M)[1:]:
        h = p.split('\n', 1)[0]
        m = re.match(r'(\d+)\.\s*(.*)', h)
        if m:
            out.append({'no': int(m.group(1)), 'title': m.group(2).strip(), 'body': p})
    return out


def field(b, n):
    m = re.search(r'^-\s*' + n + r'[：:](.*)$', b, re.M)
    return m.group(1).strip() if m else ''


def block(b, n):
    m = re.search(r'^-\s*' + n + r'[：:][^\n]*\n(.*?)(?=^-\s*\S+[：:]|\Z)', b, re.M | re.S)
    if not m:
        return field(b, n)
    t = re.sub(r'^>\s*\*\*[^*]*\*\*\s*', '', m.group(1), flags=re.M)
    t = re.sub(r'^>\s*', '', t, flags=re.M)
    return re.sub(r'\s+', '', t)


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


ABS = ('遍查未見', '全無', '無此戒', '俱無', '皆無', '未見')


def main():
    vols = load_shisong()
    ia = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(W, 'findings_ss', '*.md'))):
        for it in items(f):
            ref = field(it['body'], '五分律對照')
            if not ref or any(k in ref[:12] for k in ('遍查未見', '全無', '無此')):
                continue
            t = re.sub(r'[^\s，：；、（）]*原文\.txt', '', ref)
            t = re.sub(r'第\d+行', '', t)
            hits = [(int(a), int(b)) for a, b in
                    re.findall(r'卷\s*(\d{1,2})\s*[·，、]?\s*段\s*(\d{1,3})', t)]
            hits += [(int(m.group(1)), int(m.group(2))) for m in
                     re.finditer(r'(?<![\d.\-])(\d{1,2})\s*-\s*(\d{1,3})(?![\d])', t)]
            for v, p in hits:
                if 1 <= v <= 30:
                    ia[(v, p)].append({'unit': os.path.basename(f)[:-3], 'no': it['no'],
                                       'title': it['title'], 'pos': field(it['body'], '位置'),
                                       'ref': ref})
    ib = json.load(open(os.path.join(W, 'ss_deleted_index.json'), encoding='utf-8'))
    ir = json.load(open(os.path.join(W, 'ss_rare.json'), encoding='utf-8'))

    lines = ['# 五分「四分所無」項 × 十誦 判定摘要', '']
    n = 0
    for f in sorted(glob.glob(os.path.join(W, 'findings', 'vol*.md'))):
        v = int(re.search(r'vol(\d+)', f).group(1))
        for it in items(f):
            if not any(k in field(it['body'], '四分律對照') for k in ABS):
                continue
            n += 1
            pos = field(it['body'], '位置')
            ps = set()
            for a, b in re.findall(r'(?<![\d-])(\d{1,3})\s*[-–—]\s*(\d{1,3})(?![\d-])', pos):
                ps.update(range(int(a), int(b) + 1))
            for a in re.findall(r'(?<![\d-])(\d{1,3})(?![\d-])', pos):
                ps.add(int(a))
            lines += ['', '## %d-%d　%s' % (v, it['no'], it['title']),
                      '- 五分位置：%s' % pos,
                      '- 五分原文：%s' % block(it['body'], '原文')[:300]]
            seen = set()
            for p in sorted(ps):
                for rec in ia.get((v, p), []):
                    k = ('A', rec['unit'], rec['no'])
                    if k in seen:
                        continue
                    seen.add(k)
                    lines.append('- A 十誦稿 `%s`#%d「%s」位置 %s' % (rec['unit'], rec['no'], rec['title'], rec['pos']))
                    lines.append('   - 其五分欄：%s' % rec['ref'][:140])
            for c in ir.get('%d-%d' % (v, it['no']), {}).get('cands', [])[:2]:
                k = ('R', c['vol'], c['para'])
                if k in seen or c['hits'] < 3:
                    continue
                seen.add(k)
                lines.append('- R 十誦 卷%d 段%d（共現 %d 詞：%s）' % (c['vol'], c['para'], c['hits'], '／'.join(c['terms'][:4])))
                lines.append('   - 原文：%s' % c['text'][:130])
            if not seen:
                lines.append('- 三路皆無，須直接檢索')
    open(os.path.join(W, 'wufen_C_digest.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('items', n)


if __name__ == '__main__':
    main()
