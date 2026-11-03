#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《五部律差異對照本》A4 PDF 生成。

要點：
  1. A4、內文 12pt、緊湊排版（行距 1.45、邊距 14–16mm）
  2. <details> 白話塊在 PDF 中須展開，故預處理為普通區塊
  3. 標題不孤行、表格不跨頁斷行
  4. Chrome headless --print-to-pdf

用法：
  python build_pdf.py            # 生成分卷七個 PDF
  python build_pdf.py --full     # 另生成合冊
  python build_pdf.py --test     # 只做卷三十一至三十七，驗版式
"""
import os, re, subprocess, sys, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, '03_成品')
OUT = os.path.join(ROOT, '06_PDF')
TMP = os.path.join(BASE, '_pdf_tmp')

# Chrome 路徑：可用環境變量 CHROME_PATH 覆蓋，或由 PATH 查找
CHROME = (os.environ.get('CHROME_PATH')
          or shutil.which('chrome')
          or shutil.which('google-chrome')
          or r'C:\Program Files\Google\Chrome\Application\chrome.exe')

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

CSS = r"""
@page{
  size:A4;
  margin:14mm 13mm 15mm 13mm;
}
*{box-sizing:border-box}
html,body{margin:0; padding:0}
body{
  font-family:"FangSong","STFangsong","SimSun",serif;
  font-size:12pt; line-height:1.45; color:#111;
  text-align:justify; text-justify:inter-ideograph;
  hyphens:none;
}
/* ── 標題 ── */
h1{font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:20pt;
  margin:0 0 8pt; line-height:1.3; letter-spacing:.5pt}
h2{font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:15pt;
  margin:14pt 0 6pt; padding-bottom:2pt; border-bottom:1.2pt solid #333;
  page-break-after:avoid; line-height:1.3}
h3{font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:13pt;
  margin:11pt 0 4pt; page-break-after:avoid; line-height:1.3}
h4{font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:12pt;
  margin:9pt 0 3pt; page-break-after:avoid;
  border-left:3pt solid #8a5a2b; padding-left:5pt; line-height:1.35}
h5{font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:10.5pt;
  margin:10pt 0 3pt; page-break-after:avoid; color:#8a5a2b;
  background:#f5f1e8; border-left:2.5pt solid #a8763f; padding:2pt 6pt; line-height:1.4}
/* ── 段落 ── */
p{margin:2.5pt 0; orphans:2; widows:2}
strong{font-weight:700}
sub{font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:8.5pt;
  color:#555; font-style:normal; display:block; margin:1.5pt 0 3pt;
  line-height:1.4; letter-spacing:.2pt}
code{font-family:"Consolas",monospace; font-size:9.5pt; color:#7a4a1a}
a{color:#111; text-decoration:none}
/* ── 引用塊 ── */
blockquote{
  margin:4pt 0; padding:3pt 7pt; background:#f4f1e8;
  border-left:2.5pt solid #a8763f; font-size:10.5pt; line-height:1.45;
  page-break-inside:avoid;
}
blockquote p{margin:1pt 0}
/* ── 表格 ── */
table{border-collapse:collapse; width:100%; margin:5pt 0;
  font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:9pt;
  page-break-inside:avoid}
th,td{border:.5pt solid #999; padding:2pt 4pt; text-align:left; vertical-align:top}
th{background:#eee; font-weight:600}
/* ── 白話塊（由 details 預處理而來）── */
.bh{margin:3pt 0 5pt; padding:3pt 7pt; background:#faf8f2;
  border-left:2pt solid #ccc; font-size:10pt; line-height:1.42;
  page-break-inside:avoid}
.bh-l{font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:8pt;
  color:#777; letter-spacing:1pt; margin-bottom:1pt}
.bh p{margin:1pt 0}
/* ── 四分律原文／白話 ── */
.src{margin:4pt 0 4pt; padding:3pt 8pt; background:#fbf9f2;
  border-left:2.5pt solid #c9b48a; font-size:10.5pt; line-height:1.5}
.src p{margin:1.5pt 0; text-align:justify}
.src sub{display:inline; vertical-align:baseline; font-size:7.5pt;
  color:#9c8a6a; margin-right:1.5pt}
.plain{margin:3pt 0 5pt; padding:3pt 8pt; background:#f6f8f6;
  border-left:2.5pt solid #9fb59b; font-size:9.5pt; line-height:1.45; color:#3f4a3c}
.plain p{margin:1.5pt 0; text-align:justify}
.plain strong{font-size:9.5pt; color:#33502e}
.bl{font-family:"Microsoft YaHei","SimHei",sans-serif; font-size:8pt;
  color:#8a7a5a; letter-spacing:1pt; margin-bottom:1.5pt}
.src .bl{color:#8a6d3b}
.plain .bl{color:#5f7a58}
/* ── 列表 ── */
ul,ol{margin:3pt 0 3pt 1.2em; padding:0}
li{margin:1.5pt 0}
/* ── 分隔線 ── */
hr{border:0; border-top:.5pt solid #bbb; margin:8pt 0}
/* ── 封面 ── */
.cover{height:257mm; display:flex; flex-direction:column; justify-content:center;
  page-break-after:always; text-align:center}
.cover .t{font-family:"Microsoft YaHei","SimHei",sans-serif;
  font-size:34pt; letter-spacing:6pt; margin-bottom:10mm; line-height:1.3}
.cover .sub{font-size:14pt; color:#444; letter-spacing:2pt; margin-bottom:22mm}
.cover .rule{width:60mm; height:1pt; background:#8a5a2b; margin:0 auto 18mm}
.cover .meta{font-size:11pt; color:#555; line-height:2.1}
.cover .foot{position:absolute; bottom:0; left:0; right:0; font-size:9.5pt; color:#777}
/* ── 目錄 ── */
.toc{page-break-after:always; padding-top:4mm}
.toc h2{font-family:"Microsoft YaHei","SimHei",sans-serif;
  font-size:18pt; border:0; margin:0 0 8mm; letter-spacing:2pt}
.toc .lv1{font-family:"Microsoft YaHei","SimHei",sans-serif;
  font-size:12pt; margin:6mm 0 2mm; font-weight:700}
.toc .lv2{font-size:10.5pt; margin:1.6mm 0 1.6mm 8mm; color:#333;
  display:flex; justify-content:space-between}
.toc .lv2 .n{color:#777; font-family:"Microsoft YaHei",sans-serif; font-size:9.5pt}
/* ── 項目標題不與正文分離 ── */
p:has(> strong:first-child){page-break-after:avoid}
"""


def prep_md(md):
    """預處理：details → 普通區塊（PDF 不折疊）；移除錨點標籤"""
    # 本篇目錄在 PDF 中無用（已有書籤與目錄頁），整段移除
    md = re.sub(r'<details class="art-toc">.*?</details>\s*', '', md, flags=re.S)
    # 四分律原文／白話：改為帶標籤的普通區塊
    md = re.sub(r'<details class="art-src">\s*<summary>([^<]*)</summary>',
                lambda m: f'<div class="src"><div class="bl">〔{m.group(1)}〕</div>\n', md)
    md = re.sub(r'<details class="art-plain">\s*<summary>([^<]*)</summary>',
                lambda m: f'<div class="plain"><div class="bl">〔{m.group(1)}〕</div>\n', md)
    # 其餘 <details><summary>白話</summary> ... </details>
    md = re.sub(
        r'<details>\s*<summary>([^<]*)</summary>',
        lambda m: f'<div class="bh"><div class="bh-l">〔{m.group(1)}〕</div>\n',
        md)
    md = md.replace('</details>', '</div>')
    # 移除空錨點（PDF 無需跳轉）
    md = re.sub(r'<a id="[^"]*"></a>\s*', '', md)
    return md


def make_cover(title, subtitle, meta_lines):
    m = ''.join(f'<div>{x}</div>' for x in meta_lines)
    return f'''<div class="cover">
<div class="t">{title}</div>
<div class="sub">{subtitle}</div>
<div class="rule"></div>
<div class="meta">{m}</div>
</div>'''


def make_toc(md):
    """從 md 抽取章節，生成目錄（無頁碼）。合冊用 ##/###，分卷用 #### 篇名。"""
    out = ['<div class="toc"><h2>目　錄</h2>']
    if re.search(r'^## ', md, re.M):
        # 合冊：## 為部，### 為卷
        for m in re.finditer(r'^## ([^\n]+)$', md, re.M):
            if m.group(1).strip() == '目錄':
                continue   # 目錄條目不入 PDF 目錄
            out.append(f'<div class="lv1">{m.group(1)}</div>')
            start = m.end()
            nxt = re.search(r'^## ', md[start:], re.M)
            seg = md[start: start + (nxt.start() if nxt else len(md))]
            for m2 in re.finditer(r'^### ([^\n]+)$', seg, re.M):
                out.append(f'<div class="lv2"><span>{m2.group(1)}</span></div>')
    else:
        # 分卷：有篇則列篇目，否則列節
        arts = list(re.finditer(r'^#### (\d{3})　([^\n]+)$', md, re.M))
        if arts:
            out.append('<div class="lv1">本卷篇目</div>')
        else:
            out.append('<div class="lv1">本冊內容</div>')
            for m in re.finditer(r'^#### ([^\n]+)$', md, re.M):
                t = re.sub(r'<[^>]+>', '', m.group(1))
                out.append(f'<div class="lv2"><span>{t}</span></div>')
            out.append('</div>')
            return ''.join(out)
        for m in arts:
            t = re.sub(r'<[^>]+>', '', m.group(2))
            out.append(f'<div class="lv2"><span>{m.group(1)}　{t}</span></div>')
    out.append('</div>')
    return ''.join(out)


def md_to_pdf(md_path, pdf_path, title, md_text=None):
    md = md_text if md_text is not None else open(md_path, encoding='utf-8').read()
    md = prep_md(md)

    p = subprocess.run(['pandoc', '-f', 'gfm', '-t', 'html5', '--no-highlight'],
                       input=md.encode('utf-8'), capture_output=True)
    if p.returncode != 0:
        print('  pandoc 失敗：', p.stderr.decode('utf-8')[:300])
        return False
    body = p.stdout.decode('utf-8')

    _sub = title.replace('五部律差異對照本', '').strip() or '全一冊'
    cover = make_cover('五部律差異對照本', '以《四分律》為軸　五部對校',
                       [f'— {_sub} —', '2,124 項差異　·　七十五篇　·　576 節　·　九組歸併',
                        'A4 · 內文 12pt · 緊湊排版'])
    toc = make_toc(md)
    page = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<title>{title}</title>
<style>{CSS}</style></head>
<body>
{cover}
{toc}
{body}
</body></html>"""

    os.makedirs(TMP, exist_ok=True)
    tmp_html = os.path.join(TMP, os.path.basename(pdf_path).replace('.pdf', '.html'))
    open(tmp_html, 'w', encoding='utf-8').write(page)

    cmd = [
        CHROME, '--headless', '--disable-gpu', '--no-sandbox',
        '--print-to-pdf-no-header',
        f'--print-to-pdf={pdf_path}',
        '--no-pdf-header-footer',
        'file:///' + tmp_html.replace('\\', '/'),
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=1800)
    ok = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000
    if not ok:
        print('  Chrome 失敗：', r.stderr.decode('utf-8', 'ignore')[:300])
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
            print(f'  跳過：{fn}')
            continue
        out = os.path.join(OUT, fn.replace('.md', '.pdf'))
        print(f'  {jname} …', end=' ', flush=True)
        if md_to_pdf(src, out, f'五部律差異對照本　{jname}'):
            print(f'{os.path.getsize(out)/1024/1024:.1f} MB')

    if full and not test:
        src = os.path.join(SRC, FULL)
        if os.path.exists(src):
            out = os.path.join(OUT, FULL.replace('.md', '.pdf'))
            print('  合冊 …', end=' ', flush=True)
            if md_to_pdf(src, out, '五部律差異對照本'):
                print(f'{os.path.getsize(out)/1024/1024:.1f} MB')


if __name__ == '__main__':
    try:
        main()
    finally:
        # 清理中間 HTML，避免累積
        import shutil
        if os.path.isdir(TMP):
            shutil.rmtree(TMP, ignore_errors=True)
