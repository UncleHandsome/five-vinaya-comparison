#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精簡版：抽掉全部白話與每節所附的四分律原文，並分卷產出。

原書每一節有三層：
  1. 本節差異一覽（art-diff）
  2. 四分律原文（art-src）—— 每節所附，段 1–N
  3. 各差異項：差異條列、本稿原文、白話（details summary 白話）

精簡版只去第 2 層與白話，保留篇名、節名、差異一覽、差異條列與本稿原文。
產出：
  03_成品/五部律差異對照本_精簡.md                 （合冊原稿）
  08_PDF_精簡/五部律差異對照本_精簡_Chrome.pdf       （合冊）
  08_PDF_精簡/五部律差異對照本_精簡_LaTeX.pdf
  08_PDF_精簡/五部律差異對照本_精簡_卷一至卷十_Chrome.pdf
  … 七冊，Chrome／LaTeX 各一套

用法：
  python tools/build_lean.py --md          # 只產合冊 MD
  python tools/build_lean.py --chrome      # 合冊＋分卷，Chrome 版
  python tools/build_lean.py --tex         # 合冊＋分卷，LaTeX 版
  python tools/build_lean.py --skip-full   # 只產分卷（合冊已存在時）
  python tools/build_lean.py               # 全部
"""
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
SRC = os.path.join(ROOT, '03_成品')
OUT = os.path.join(ROOT, '08_PDF_精簡')
TMP = os.path.join(WORK, '_lean_tmp')
sys.path.insert(0, WORK)

FULL = '五部律差異對照本.md'
LEAN = '五部律差異對照本_精簡.md'

NOTE = ('> **本版說明**：本版為「精簡版」，已抽去全書白話，以及每節所附的'
        '四分律原文（凡例所稱之二摺疊塊），只存篇旨、節題、本節差異一覽、'
        '差異條列與本稿原文。欲讀原文與白話，請用完整版。')


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

    # 書名標明版本；有 h1 者在其後插本版說明，無 h1 者插於檔首
    md = re.sub(r'^# 五部律差異對照本(?!（精簡版）)',
                '# 五部律差異對照本（精簡版）', md, count=1, flags=re.M)
    lines = md.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('# '):
            lines.insert(i + 1, '\n' + NOTE + '\n')
            return '\n'.join(lines), n_src, n_plain
    return NOTE + '\n\n' + md, n_src, n_plain


def report(name, raw, lean, n_src, n_plain):
    print('%-14s 原 %.1f MB → 精簡 %.1f MB（%.0f%%）；四分原文 %d 塊、白話 %d 處' %
          (name, len(raw.encode('utf-8')) / 1e6, len(lean.encode('utf-8')) / 1e6,
           100 * len(lean.encode('utf-8')) / max(1, len(raw.encode('utf-8'))),
           n_src, n_plain))


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
    report('合冊', raw, lean, n_src, n_plain)
    print('  殘留「白話」%d、「四分律原文」%d（皆凡例文字）' %
          (len(re.findall(r'白話', lean)), len(re.findall(r'四分律原文', lean))))

    if '--md' in sys.argv:
        return

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    do_chrome = '--tex' not in sys.argv
    do_tex = '--chrome' not in sys.argv
    skip_full = '--skip-full' in sys.argv
    title = '五部律差異對照本（精簡版）'
    subtitle = '精簡版　去白話、去四分律原文'

    P = None
    T = None
    if do_chrome or do_tex:
        import build_pdf as P
    if do_tex:
        import build_tex as T

    if not skip_full:
        if do_chrome:
            out = os.path.join(OUT, '五部律差異對照本_精簡_Chrome.pdf')
            print('Chrome 合冊 …', end=' ', flush=True)
            t = time.time()
            ok = P.md_to_pdf(lean_path, out, title, md_text=lean, subtitle=subtitle,
                             meta_lines=['— 精簡版 —',
                                         '只存差異條列與本稿原文，不附白話與四分律原文',
                                         'A4 · 內文 12pt · 緊湊排版'])
            print(('%.1f MB（%.0fs）' % (os.path.getsize(out) / 1e6, time.time() - t))
                  if ok else '失敗')
        if do_tex:
            out = os.path.join(OUT, '五部律差異對照本_精簡_LaTeX.pdf')
            print('LaTeX 合冊 …', end=' ', flush=True)
            t = time.time()
            ok = T.build(lean_path, out, title)
            print(('%.1f MB（%.0fs）' % (os.path.getsize(out) / 1e6, time.time() - t))
                  if ok else '失敗')

    # 分卷：以 build_pdf.JUAN 為準（兩支腳本清單相同）
    for jname, fn in P.JUAN:
        src = os.path.join(SRC, fn)
        if not os.path.exists(src):
            print('  跳過（缺檔）', fn)
            continue
        raw = open(src, encoding='utf-8').read()
        lean, n_src, n_plain = strip_lean(raw)
        tmp = os.path.join(TMP, fn)
        with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(lean)
        report(jname, raw, lean, n_src, n_plain)

        if do_chrome:
            out = os.path.join(OUT, '五部律差異對照本_精簡_%s_Chrome.pdf' % jname)
            print('  Chrome %s …' % jname, end=' ', flush=True)
            t = time.time()
            ok = P.md_to_pdf(tmp, out, '%s　%s' % (title, jname), md_text=lean,
                             subtitle=subtitle,
                             meta_lines=['— 精簡版・%s —' % jname,
                                         '只存差異條列與本稿原文',
                                         'A4 · 內文 12pt · 緊湊排版'])
            print(('%.1f MB（%.0fs）' % (os.path.getsize(out) / 1e6, time.time() - t))
                  if ok else '失敗')
        if do_tex:
            out = os.path.join(OUT, '五部律差異對照本_精簡_%s_LaTeX.pdf' % jname)
            print('  LaTeX %s …' % jname, end=' ', flush=True)
            t = time.time()
            ok = T.build(tmp, out, '%s　%s' % (title, jname))
            print(('%.1f MB（%.0fs）' % (os.path.getsize(out) / 1e6, time.time() - t))
                  if ok else '失敗')

    print('完成，共 %.0f 秒。' % (time.time() - t0))


if __name__ == '__main__':
    main()
