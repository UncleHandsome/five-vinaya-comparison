#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《五部律差異對照本》LaTeX 版 PDF 生成。

相比 Chrome 版，補上：
  - 頁碼（頁腳居中）
  - PDF 書籤（章節可跳轉）
  - 頁眉（書名／卷次）

要點：
  1. 文檔類用 ctexart（article 在 xelatex 下不生成書籤）
  2. 跨檔錨點（如 S-0208 在別卷）須先轉為純文本，否則 LaTeX 報 undefined
  3. 仿宋缺「・」（U+30FB），以「·」替代
  4. details 白話塊轉為普通段落

用法：
  python build_tex.py --test          # 只做卷三十一至三十七
  python build_tex.py                 # 全部分卷
  python build_tex.py --full          # 另做合冊
"""
import os, re, subprocess, sys, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, '03_成品')
OUT = os.path.join(ROOT, '07_PDF_LaTeX')
TMP = os.path.join(BASE, '_tex_tmp')

# TeX 路徑：可用環境變量 TEXBIN 覆蓋
TEXBIN = os.environ.get('TEXBIN') or r'C:\texlive\2026\bin\windows'

JUAN = [
    ('卷一至卷十', '五部律差異對照本_卷一至卷十.md'),
    ('卷十一至卷二十一', '五部律差異對照本_卷十一至卷二十一.md'),
    ('卷二十二至卷三十', '五部律差異對照本_卷二十二至卷三十.md'),
    ('卷三十一至卷三十七', '五部律差異對照本_卷三十一至卷三十七.md'),
    ('卷三十八至卷四十九', '五部律差異對照本_卷三十八至卷四十九.md'),
    ('卷五十至卷六十', '五部律差異對照本_卷五十至卷六十.md'),
    ('四分所無與歸併組', '五部律差異對照本_四分所無與歸併組.md'),
]
FULL = '五部律差異對照本.md'


def prep(md):
    """轉為 LaTeX 友善的 Markdown"""
    # 本篇目錄在 PDF 無用，整段移除
    md = re.sub(r'<details class="art-toc">.*?</details>\s*', '', md, flags=re.S)
    # 四分律原文／白話
    md = re.sub(r'<details class="art-src">\s*<summary>([^<]*)</summary>',
                lambda m: f'\n**〔{m.group(1)}〕**\n', md)
    md = re.sub(r'<details class="art-plain">\s*<summary>([^<]*)</summary>',
                lambda m: f'\n**〔{m.group(1)}〕**\n', md)
    # 其餘 details → 普通段落
    md = re.sub(r'<details>\s*<summary>([^<]*)</summary>',
                lambda m: f'\n**〔{m.group(1)}〕**\n', md)
    md = md.replace('</details>', '\n')
    # 移除 HTML 錨點
    md = re.sub(r'<a id="[^"]*"></a>\s*', '', md)
    # 跨檔/同檔錨點連結 → 純文本（LaTeX 的 hyperref 對未定義引用會報錯）
    md = re.sub(r'\[([^\]]+)\]\(#[^)]*\)', r'\1', md)
    # 仿宋無「・」
    md = md.replace('・', '·')
    return md


def build(src_md, out_pdf, title, extra_meta=None):
    os.makedirs(TMP, exist_ok=True)
    md = prep(open(src_md, encoding='utf-8').read())
    tmp_md = os.path.join(TMP, 'doc.md')
    open(tmp_md, 'w', encoding='utf-8').write(md)

    env = dict(os.environ)
    env['PATH'] = TEXBIN + os.pathsep + env.get('PATH', '')

    hdr = os.path.join(TMP, 'header.tex')
    open(hdr, 'w', encoding='utf-8').write(r'''\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\itshape 五部律差異對照本}
\fancyhead[R]{\small\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\small\thepage}\renewcommand{\headrulewidth}{0pt}}
\usepackage{etoolbox}
\pretocmd{\tableofcontents}{\clearpage}{}{}
\apptocmd{\tableofcontents}{\clearpage}{}{}
\usepackage{titlesec}
\titlespacing*{\section}{0pt}{8pt}{4pt}
\titlespacing*{\subsection}{0pt}{6pt}{3pt}
\titlespacing*{\subsubsection}{0pt}{4pt}{2pt}
''')
    cmd = [
        'pandoc', tmp_md, '-o', out_pdf,
        '--pdf-engine=xelatex',
        '-V', 'documentclass=ctexart',
        '-V', 'CJKmainfont=FangSong',
        '-V', 'CJKsansfont=Microsoft YaHei',
        '-V', 'CJKmonofont=Consolas',
        '-V', 'geometry:margin=1.5cm',
        '-V', 'fontsize=12pt',
        '-V', 'linestretch=1.25',
        '-V', 'parskip=3pt',
        '-V', 'colorlinks=false',
        '-V', 'bookmarks=true',
        '-V', 'bookmarksopen=true',
        '--toc', '--toc-depth=3',
        '--include-in-header', hdr,
        '--metadata', f'title={title}',
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='ignore', env=env, timeout=3600)
    ok = os.path.exists(out_pdf) and os.path.getsize(out_pdf) > 1000
    if not ok:
        err = [x for x in (r.stderr or '').split('\n') if x.strip()][-6:]
        print('   ✗ 失敗：')
        for e in err:
            print('     ' + e[:140])
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    test = '--test' in sys.argv
    full = '--full' in sys.argv

    targets = JUAN
    if test:
        targets = [t for t in JUAN if '三十一' in t[0]]

    for jname, fn in targets:
        src = os.path.join(SRC, fn)
        if not os.path.exists(src):
            continue
        out = os.path.join(OUT, fn.replace('.md', '.pdf'))
        print(f'  {jname} …', end=' ', flush=True)
        if build(src, out, f'五部律差異對照本　{jname}'):
            print(f'{os.path.getsize(out)/1024/1024:.1f} MB')

    if full and not test:
        src = os.path.join(SRC, FULL)
        if os.path.exists(src):
            out = os.path.join(OUT, FULL.replace('.md', '.pdf'))
            print('  合冊 …', end=' ', flush=True)
            if build(src, out, '五部律差異對照本'):
                print(f'{os.path.getsize(out)/1024/1024:.1f} MB')

    if os.path.isdir(TMP):
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == '__main__':
    main()
