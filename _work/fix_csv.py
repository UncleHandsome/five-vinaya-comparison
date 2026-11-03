#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將勘誤套用至 CSV（就地更新受影響之行，其餘不動）。

CSV 欄位：編號,主稿,證據,層級,狀態,主題,四分,五分,十誦,僧祇,根有,
         位置,實質差異,四分對照,五分對照,十誦對照,補證
"""
import csv, io, os, sys
from errata import ERRATA, dedup_xref, clean_title

W = os.path.dirname(os.path.abspath(__file__))
CSVP = os.path.join(os.path.dirname(W), '03_成品', '五部律綜合異同矩陣.csv')

COL = {'title': '主題', 'diff_full': '實質差異', 'ref4': '四分對照',
       'st': '狀態', 'lv': '層級'}
CELL = {'v4': '四分', 'v5': '五分', 'v10': '十誦', 'vMK': '僧祇', 'vGU': '根有'}


def main():
    raw = open(CSVP, encoding='utf-8-sig').read()
    rd = csv.DictReader(io.StringIO(raw))
    fields = rd.fieldnames
    rows = list(rd)

    n = 0
    for r in rows:
        e = ERRATA.get(r['編號'])
        if not e:
            continue
        for k, col in COL.items():
            if k in e and col in r:
                r[col] = e[k]
        for ck, cv in e.get('cells', {}).items():
            col = CELL.get(ck)
            if col and col in r:
                r[col] = cv
        n += 1

    # 主題列清理（段號後綴、分類標籤、戒號統一）——全部行
    for r in rows:
        if r.get('主題'):
            r['主題'] = clean_title(r['主題'], r['編號'])

    # 補證欄去重（全部行，不限勘誤行）
    for r in rows:
        if '補證' in r and r['補證']:
            r['補證'] = dedup_xref(r['補證'])

    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=fields, lineterminator='\n')
    wr.writeheader()
    wr.writerows(rows)
    open(CSVP, 'w', encoding='utf-8-sig', newline='').write(buf.getvalue())
    print(f'已更新 {n} 行 → {CSVP}')


if __name__ == '__main__':
    main()
