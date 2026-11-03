#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把代理產出的白話 JSON 併回 findings 各檔。

用法：
    python _work/_plain_apply.py _work/_plain_out/*.json
    python _work/_plain_apply.py --check          # 只檢查，不寫檔

JSON 格式（一檔一物件）：
    {"vol01": {"1": "白話…", "2": "白話…"}, "vol02": {...}}
鍵為 findings 檔名去 .md，值為 {項號: 白話}。
"""
import json, re, sys, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
DIRS = {
    'ss': os.path.join(BASE, 'findings_ss'),
    'gu': os.path.join(BASE, 'findings_gu'),
    'wf': os.path.join(BASE, 'findings'),
    'mk': os.path.join(BASE, 'findings_mk'),
}
RE_H2_KEEP = re.compile(r'^##\s*保留項\s*$')
RE_H2 = re.compile(r'^##\s+')
RE_H3 = re.compile(r'^###\s+(\d+)\.\s')


def find_keep_range(lines):
    """回傳 (start, end) 行索引區間（不含標題行）"""
    s = None
    for i, ln in enumerate(lines):
        if RE_H2_KEEP.match(ln):
            s = i + 1
            break
    if s is None:
        return None
    e = len(lines)
    for j in range(s, len(lines)):
        if RE_H2.match(lines[j]):
            e = j
            break
    return s, e


def apply_file(path, plains, write=True):
    lines = open(path, encoding='utf-8').read().split('\n')
    rng = find_keep_range(lines)
    if rng is None:
        return {'file': path, 'err': 'no 保留項 section'}
    s, e = rng

    # 收集項目邊界
    marks = [(i, int(RE_H3.match(lines[i]).group(1))) for i in range(s, e) if RE_H3.match(lines[i])]
    done, missing, extra = [], [], []

    # 由後往前改，索引不亂
    for k in range(len(marks) - 1, -1, -1):
        i, no = marks[k]
        end = marks[k + 1][0] if k + 1 < len(marks) else e
        txt = plains.get(str(no))
        if txt is None:
            missing.append(no)
            continue

        # 找 - 原文： 與其後的引文行
        qi = None
        for j in range(i, end):
            if lines[j].lstrip().startswith('- 原文'):
                qi = j
                break
        if qi is None:
            extra.append((no, 'no 原文'))
            continue
        last_q = qi
        j = qi + 1
        while j < end:
            st = lines[j].strip()
            if st.startswith('>'):
                last_q = j
                j += 1
            elif st == '' and j + 1 < end and lines[j + 1].strip().startswith('>'):
                j += 1
            else:
                break

        # 移除既有白話區塊
        cut = last_q + 1
        while cut < end:
            st = lines[cut].strip()
            if st.startswith('- 白話'):
                nxt = cut + 1
                while nxt < end and lines[nxt].strip() and not lines[nxt].lstrip().startswith('- ') \
                        and not lines[nxt].startswith('###') and not lines[nxt].startswith('##'):
                    nxt += 1
                del lines[cut:nxt]
                break
            if st == '':
                cut += 1
                continue
            break

        body = [('  ' + l) if l.strip() else '' for l in txt.strip().split('\n')]
        lines[last_q + 1:last_q + 1] = ['- 白話：'] + body
        done.append(no)

    if write:
        open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    return {'file': os.path.basename(path), 'done': len(done), 'missing': missing, 'extra': extra}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    merged = {}
    for fp in args:
        d = json.load(open(fp, encoding='utf-8'))
        for unit, plains in d.items():
            merged.setdefault(unit, {}).update(plains)

    tot_done = tot_miss = 0
    for unit, plains in sorted(merged.items()):
        path = None
        for tag, dd in DIRS.items():
            p = os.path.join(dd, unit + '.md')
            if os.path.exists(p):
                path = p
                break
        if not path:
            print('!! 找不到', unit)
            continue
        r = apply_file(path, plains, write=not check)
        tot_done += r.get('done', 0)
        tot_miss += len(r.get('missing', []))
        flag = '' if not r.get('missing') and not r.get('extra') else '  <-- 檢查'
        print(f"{r['file']:16s} 寫入 {r.get('done',0):3d} 缺 {len(r.get('missing',[])):2d}{flag}")
        if r.get('missing'):
            print('   缺:', r['missing'][:20])
        if r.get('extra'):
            print('   異:', r['extra'][:10])
    print(f'\n合計寫入 {tot_done} 項，JSON 未對應 {tot_miss} 項' + ('（--check 未寫檔）' if check else ''))


if __name__ == '__main__':
    main()
