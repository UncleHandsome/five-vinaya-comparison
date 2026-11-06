#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精簡版：抽掉全部白話與每節所附的四分律原文。

原書每一節有三層：
  1. 本節差異一覽（art-diff）
  2. 四分律原文（art-src）—— 每節所附，段 1–N
  3. 各差異項：差異條列、本稿原文、白話（details summary 白話）

精簡版只去第 2 層與白話，保留篇名、節名、差異一覽、差異條列與本稿原文。
產出：
  03_成品/五部律差異對照本_精簡.md
  08_PDF_精簡/五部律差異對照本_精簡_Chrome.pdf
  08_PDF_精簡/五部律差異對照本_精簡_LaTeX.pdf

用法：
  python tools/build_lean.py --md       # 只產 MD
  python tools/build_lean.py --chrome   # MD + Chrome PDF
  python tools/build_lean.py --tex      # MD + LaTeX PDF
  python tools/build_lean.py            # 全部
"""
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
SRC = os.path.join(ROOT, '03_成品')
OUT = os.path.join(ROOT, '08_PDF_精簡')
sys.path.insert(0, WORK)

FULL = '五部律差異對照本.md'
LEAN = '五部律差異對照本_精簡.md'


def strip_lean(md):
    """回傳（精簡後文字, 移除的 art-src 數, 移除的白話數）。"""
    n_src = len(re.findall(r'<details[^>]*\bclass="art-src"', md))
    n_plain = len(re.findall(r'<summary>\s*白話\s*</summary>', md))

    # 每節所附四分律原文
    md = re.sub(r'<details[^>]*\bclass="art-src"[^>]*>.*?</details>\s*', '', md, flags=re.S)
    # 節級白話（art-plain）
    md = re.sub(r'<details[^>]*\bclass="art-plain"[^>]*>.*?</details>\s*', '', md, flags=re.S)
    # 項級白話（<details><summary>白話</summary>…）
    md = re.sub(r'<details[^>]*>\s*<summary>\s*白話\s*</summary>.*?</details>\s*', '', md, flags=re.S)
    # 節級「白話從缺」小字
    md = re.sub(r'<sub>\s*本節白話從缺\s*</sub>\s*', '', md)

    # 移除區塊後留下的連續空行
    md = re.sub(r'\n[ \t]*\n[ \t]*\n+', '\n\n', md)

    # 卷首加本版說明，並在書名標明版本
    note = ('> **本版說明**：本版為「精簡版」，已抽去全書白話，以及每節所附的'
            '四分律原文（凡例所稱之二摺疊塊），只存篇旨、節題、本節差異一覽、'
            '差異條列與本稿原文。欲讀原文與白話，請用完整版。\n')
    md = md.replace('# 五部律差異對照本\n',
                    '# 五部律差異對照本（精簡版）\n\n' + note, 1)
    return md, n_src, n_plain


def main():
    t0 = time.time()
    src = os.path.join(SRC, FULL)
    if not os.path.exists(src):
        print('找不到', src)
        sys.exit(1)

    raw = open(src, encoding='utf-8').read()
    lean, n_src, n_plain = strip_lean(raw)
    lean_path = os.path.join(SRC, LEAN)
    with open(lean_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(lean)

    left_plain = len(re.findall(r'白話', lean))
    left_src = len(re.findall(r'四分律原文', lean))
    print('原 %d 字／%.1f MB' % (len(raw), len(raw.encode('utf-8')) / 1e6))
    print('精簡 %d 字／%.1f MB（%.0f%%）' %
          (len(lean), len(lean.encode('utf-8')) / 1e6,
           100 * len(lean.encode('utf-8')) / len(raw.encode('utf-8'))))
    print('移除：四分律原文 %d 塊、白話 %d 處；殘留「白話」%d、「四分律原文」%d' %
          (n_src, n_plain, left_plain, left_src))

    if '--md' in sys.argv:
        return
    os.makedirs(OUT, exist_ok=True)
    title = '五部律差異對照本（精簡版）'

    if '--tex' not in sys.argv:
        import build_pdf as P
        out = os.path.join(OUT, '五部律差異對照本_精簡_Chrome.pdf')
        print('Chrome PDF …', end=' ', flush=True)
        t = time.time()
        ok = P.md_to_pdf(lean_path, out, title, md_text=lean,
                         subtitle='精簡版　去白話、去四分律原文',
                         meta_lines=['— 精簡版 —',
                                     '只存差異條列與本稿原文，不附白話與四分律原文',
                                     'A4 · 內文 12pt · 緊湊排版'])
        print(('%.1f MB（%.0fs）' % (os.path.getsize(out) / 1e6, time.time() - t))
              if ok else '失敗')

    if '--chrome' not in sys.argv:
        import build_tex as T
        out = os.path.join(OUT, '五部律差異對照本_精簡_LaTeX.pdf')
        print('LaTeX PDF …', end=' ', flush=True)
        t = time.time()
        ok = T.build(lean_path, out, title)
        print(('%.1f MB（%.0fs）' % (os.path.getsize(out) / 1e6, time.time() - t))
              if ok else '失敗')

    print('完成，共 %.0f 秒。' % (time.time() - t0))


if __name__ == '__main__':
    main()
