#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一鍵重建全部成品。

順序有依賴，不可調換：
  1. 附錄表資料     ← tools/build_appendices.py 產出 appendix5/6.md
  2. 對照本 MD      ← matrix_built.json + _locate.json + originals_index.json（並讀附錄表）
  3. 矩陣 MD        ← matrix_built.json（套 errata）
  4. 矩陣 CSV       ← 套 errata 至既有 CSV
  5. 對照本 HTML    ← 對照本 MD
  6. 矩陣 HTML      ← 矩陣 MD
  7. 專題表 HTML    ← tools/build_tables_html.py 讀 appendix5/6.md
  8. PDF 分卷       ← 對照本 MD
  9. PDF 合冊       ← 對照本 MD

用法：
  python rebuild_all.py             # 全部
  python rebuild_all.py --no-pdf    # 略過 PDF（省時）
  python rebuild_all.py --only 1,2  # 只跑指定步
"""
import os, subprocess, sys, time

W = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(W)
TOOLS = os.path.join(ROOT, 'tools')

STEPS = [
    ('附錄表資料', [sys.executable, os.path.join(TOOLS, 'build_appendices.py')]),
    ('對照本 MD', [sys.executable, 'build_compare.py']),
    ('矩陣 MD', [sys.executable, 'matrix_md.py']),
    ('矩陣 CSV', [sys.executable, 'fix_csv.py']),
    ('對照本 HTML', [sys.executable, 'build_html.py']),
    ('矩陣 HTML', [sys.executable, 'build_matrix_html.py']),
    ('專題表 HTML', [sys.executable, os.path.join(TOOLS, 'build_tables_html.py')]),
    ('PDF 分卷', [sys.executable, 'build_pdf.py']),
    ('PDF 合冊', [sys.executable, '-c',
                  "import build_pdf as P, os, shutil;"
                  "P.md_to_pdf(os.path.join(P.SRC, P.FULL),"
                  " os.path.join(P.OUT, P.FULL.replace('.md', '.pdf')), '五部律差異對照本');"
                  "shutil.rmtree(P.TMP, ignore_errors=True) if os.path.isdir(P.TMP) else None"]),
]


def main():
    only = None
    skip_pdf = '--no-pdf' in sys.argv
    for a in sys.argv:
        if a.startswith('--only'):
            only = set(int(x) for x in a.split('=')[-1].split(','))

    t0 = time.time()
    for i, (name, cmd) in enumerate(STEPS, 1):
        if only and i not in only:
            continue
        if skip_pdf and name.startswith('PDF'):
            continue
        print(f'[{i}/{len(STEPS)}] {name} …', flush=True)
        t = time.time()
        r = subprocess.run(cmd, cwd=W, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if r.returncode != 0:
            print(f'   ✗ 失敗（{time.time()-t:.1f}s）')
            print('   ' + (r.stderr or '').strip()[:400].replace('\n', '\n   '))
            sys.exit(1)
        # 只印最後一行摘要
        tail = [x for x in (r.stdout or '').strip().split('\n') if x.strip()]
        if tail:
            print(f'   {tail[-1].strip()[:110]}  （{time.time()-t:.1f}s）')
        else:
            print(f'   ✓（{time.time()-t:.1f}s）')

    print(f'\n完成，共 {time.time()-t0:.0f} 秒。')


if __name__ == '__main__':
    main()
