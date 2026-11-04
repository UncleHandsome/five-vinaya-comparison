#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 全量導出（不再「就地打補丁」）。

來源：matrix_built.json → errata.apply → 映射為 CSV 欄位。
如此 MD 與 CSV 同源，不會出現「MD 已改、CSV 仍舊」之弊。

CSV 欄位：編號,主稿,證據,層級,狀態,主題,四分,五分,十誦,僧祇,根有,
         位置,實質差異,四分對照,五分對照,十誦對照,補證

註：本檔含 UTF-8 BOM（EF BB BF），以便 Excel 直接雙擊開啟不亂碼。
    Python 讀取請用 encoding='utf-8-sig'。
"""
import csv, io, json, os, re

from errata import apply as apply_errata, clean_title, dedup_xref
from diff_fmt import expand_refs
from sifen_src import glyph_fix

W = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(W)
SRC = os.path.join(W, 'matrix_built.json')
GT_PATH = os.path.join(W, 'gt_groups.json')
OUT = os.path.join(ROOT, '03_成品', '五部律綜合異同矩陣.csv')

FIELDS = ['編號', '主稿', '證據', '層級', '狀態', '主題', '四分', '五分', '十誦',
          '僧祇', '根有', '位置', '實質差異', '四分對照', '五分對照', '十誦對照', '補證']
CELL = [('v4', '四分'), ('v5', '五分'), ('v10', '十誦'), ('vMK', '僧祇'), ('vGU', '根有')]

GT = json.load(open(GT_PATH, encoding='utf-8')) if os.path.exists(GT_PATH) else {}
ID2GT = {i: g for g, ids in GT.items() for i in ids}


def fix_pos(r, orig):
    """僧祇稿部分項僅記段號，卷次自原文「卷N·段M」或 unit 補出（與 MD 一致）。"""
    pos = r.get('pos') or ''
    if r.get('canon') == '僧祇' and pos.startswith('段'):
        m = re.search(r'卷(\d+)[·・]段', orig or '')
        if m:
            return f'卷{m.group(1)}·{pos}'
        mu = re.match(r'vol(\d+)', r.get('unit') or '')
        if mu:
            return f'卷{int(mu.group(1))}·{pos}'
    return pos


def main():
    rows = json.load(open(SRC, encoding='utf-8'))
    oi_path = os.path.join(W, 'originals_index.json')
    OI = json.load(open(oi_path, encoding='utf-8')) if os.path.exists(oi_path) else {}

    out = []
    for raw in rows:
        r = apply_errata(raw)
        o = OI.get(f"{r['canon']}|{r['unit']}|{r['no']}", {})
        orig = o.get('orig') or ''
        ev = f"{r['unit']}#{r['no']}"
        g = ID2GT.get(r['id'])
        if g:
            ev += ' ' + g
        rec = {
            '編號': r['id'],
            '主稿': r['canon'],
            '證據': ev,
            '層級': r.get('lv', ''),
            '狀態': r.get('st', ''),
            '主題': clean_title(r.get('title', ''), r['id']),
            '位置': fix_pos(r, orig),
            '實質差異': expand_refs((r.get('diff_full') or '').replace('\n', ' '), r),
            '四分對照': (r.get('ref4') or '').replace('\n', ' '),
            '五分對照': (r.get('ref5') or '').replace('\n', ' '),
            '十誦對照': (r.get('ref10') or '').replace('\n', ' '),
            '補證': dedup_xref(r.get('xref', '')) or '',
        }
        for k, col in CELL:
            rec[col] = r.get(k, '未比')
        # 組字式代通行字，與對照本、矩陣一致
        for k in rec:
            if isinstance(rec[k], str):
                rec[k] = glyph_fix(rec[k])
        out.append(rec)

    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator='\n')
    wr.writeheader()
    wr.writerows(out)
    open(OUT, 'w', encoding='utf-8-sig', newline='').write(buf.getvalue())
    print(f'全量導出 {len(out)} 行 → {OUT}')


if __name__ == '__main__':
    main()
