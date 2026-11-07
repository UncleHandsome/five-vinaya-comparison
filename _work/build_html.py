#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《五部律差異對照本》HTML 網頁版生成。

流程：
  1. 讀 Markdown（合冊或分卷）
  2. 預處理：<details> 白話塊 → 保留（HTML 版可折疊）
  3. pandoc 轉 HTML5
  4. 注入自定義 CSS 與側邊欄導航
  5. 輸出至 05_網頁版/

用法：
  python build_html.py            # 生成合冊 + 分卷 + 索引頁
  python build_html.py --single   # 只生成合冊
"""
import os, re, subprocess, sys, json, glob, shutil, html as htmlmod


def _pandoc_exe():
    """找 pandoc。WinGet 升級後 PATH 常仍指舊版空目錄，故加一層搜尋。"""
    p = shutil.which('pandoc')
    if p:
        return p
    pats = [
        os.path.expandvars(
            r'%LOCALAPPDATA%\Microsoft\WinGet\Packages'
            r'\JohnMacFarlane.Pandoc_*\pandoc-*\pandoc.exe'),
        r'C:\Program Files\Pandoc\pandoc.exe',
        r'C:\ProgramData\chocolatey\bin\pandoc.exe',
    ]
    for pat in pats:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]        # 取版號最大者
    return 'pandoc'                # 讓原 FileNotFoundError 如實浮出

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, '03_成品')
OUT = os.path.join(ROOT, '05_網頁版')

# 換帳號、換倉庫、換網域時，只改這兩行，再重跑本腳本即可
SITE_URL = 'https://unclehandsome.github.io/five-vinaya-comparison/'
REPO_URL = 'https://github.com/UncleHandsome/five-vinaya-comparison'

# 底本鳴謝與授權宣告。各卷末與合冊末均附，免單卷外流時失其出處。
FOOTER = """
<footer id="colophon">
<hr>
<p><b>底本與鳴謝</b></p>
<p>本書五部律原文，錄自大正新脩大藏經（簡稱大正藏）：四分律（T22 no. 1428，
姚秦 罽賓三藏佛陀耶舍共竺佛念譯）、五分律（T22 no. 1421，劉宋 罽賓三藏佛陀什共竺道生譯）、
摩訶僧祇律（T22 no. 1425，東晉 天竺三藏佛陀跋陀羅共法顯譯）、
十誦律（T23 no. 1435，後秦 三藏弗若多羅共鳩摩羅什譯）、
根本說一切有部毘奈耶（T23 no. 1442，唐 三藏義淨譯）。</p>
<p><b>譯出年代與歷時性</b>　前四部皆出於五世紀初二十餘年間（約 404–423），
同屬漢地早期所傳廣律；根本說一切有部律則遲至八世紀初（約 701–710）方由義淨譯出，
去前四部近三百年。二者之間非僅部派之別，亦有文獻層累之異：根有律所據，
本屬印度佛教晚期高度文學化、譬喻化之律本，長篇本生、譬喻、占相、因明諸門層見疊出；
前四部則多存古本質樸之體。故本書所見根有之「繁」，半由部派，半由時代，
讀者幸勿以同一歷史斷面之平行作品視之。</p>
<p>大正藏之電子化，為中華電子佛典協會（CBETA）多年經營之成果；本書四分律文字與校記，
並據 CBETA T22 no. 1428 電子檔覆核行文、校記與用字，謹致謝忱。CBETA 電子佛典依
Creative Commons「姓名標示—非商業性—相同方式分享」授權釋出，本書引用處依同一方式標明出處。</p>
<p>大正藏校記代號，悉依 CBETA 體例：【大】表大正藏底本，【宋】【元】【明】【宮】【聖】【乙】
等各表一藏本；凡本書引及異文，均照錄原式，不省代號。</p>
<p>本書之標點、分段、篇題、篇旨、對照欄位、異同矩陣與白話譯文，皆編者所加，非底本原有；
引據時請以 CBETA 原書覆核。若有訛失，乞方家賜正。</p>
<p><b>授權</b>　本書所增之標點、分段、篇題、篇旨、對照欄位、異同矩陣、白話譯文與檢索程式，
依 Creative Commons 姓名標示—非商業性—相同方式分享 4.0 國際版（CC BY-NC-SA 4.0）釋出；
引用、轉載、改作者請依同一條款，並標明出處。所引五部律原文之權利狀態，仍依 CBETA 原授權。</p>
<p><b>建議引用格式</b><br>
　　UncleHandsome（編）.《五部律差異對照本》. 版本 __VER__（__DATE__）. 線上資料庫.
<a href="__SITE__">__SITE__</a><br>
　　單項引用宜並舉項號與錨點，如「《五部律差異對照本》D-0450（#d-0450），版本 __VER__」。
項號於同一版本內穩定，跨版本引用請附版本戳。</p>
<p><b>BibTeX</b><br>
<code>@misc{unclehandsome_vinaya,<br>
　author = {UncleHandsome},<br>
　title = {五部律差異對照本},<br>
　year = {2026},<br>
　url = {__SITE__},<br>
　note = {版本 __VER__（__DATE__）}<br>
}</code></p>
<p><b>檔名與永久識別</b>　本檔以中文命名，Git 於 macOS（檔案系統用 NFD）與 Linux（NFC）
之間，或以正規化之差誤判為二檔；網址中的 <code>%E4%BA%94…</code> 亦不便轉寫。
故引用時請用上列網址，不用檔名；檔名之正規化形式為 NFC。
若需長期典藏與永久識別碼，宜將定稿（含 MD、CSV、HTML）打包寄存於 Zenodo 或 OSF，
取得 DOI 後於此頁補記。在此之前，版本戳即本書之引用憑據。</p>
</footer>
"""


def _jsonld(title):
    """schema.org 結構化資料，供搜尋引擎與學術索引辨識。"""
    import json as _j
    d = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "name": title,
        "author": {"@type": "Person", "name": "UncleHandsome"},
        "datePublished": _DATE,
        "inLanguage": "zh-Hant",
        "url": SITE_URL,
        "license": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "isPartOf": {"@type": "Book", "name": "五部律差異對照本"},
        "about": [
            {"@type": "Thing", "name": "Dharmaguptaka Vinaya（四分律）"},
            {"@type": "Thing", "name": "Sarvāstivāda Vinaya（十誦律）"},
            {"@type": "Thing", "name": "Mahīśāsaka Vinaya（五分律）"},
            {"@type": "Thing", "name": "Mahāsāṃghika Vinaya（摩訶僧祇律）"},
            {"@type": "Thing", "name": "Mūlasarvāstivāda Vinaya（根本說一切有部毘奈耶）"},
            {"@type": "Thing", "name": "Comparative Vinaya Studies"},
        ],
    }
    return ('<script type="application/ld+json">'
            + _j.dumps(d, ensure_ascii=False) + '</script>')


def _build_stamp():
    """版本戳：git 短雜湊（工作區有未提交改動則加 -dirty）＋ 建置日期。"""
    import datetime
    h = ''
    try:
        h = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT,
                           capture_output=True, text=True, timeout=10).stdout.strip()
        # 只監看來源目錄：rebuild 流程會先改寫成品 MD/HTML/CSV，
        # 若把它們算進 dirty，同一版本會在不同頁面出現不同戳記。
        st = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no',
                             '--', '_work', 'tools', '01_原文', '02_去重稿', '白話四分律'],
                            cwd=ROOT, capture_output=True, text=True,
                            timeout=20).stdout.strip()
        if h and st:
            h += '-dirty'
    except Exception:
        h = ''
    d = datetime.date.today().isoformat()
    return (h or 'nogit'), d


_VER, _DATE = _build_stamp()
FOOTER = (FOOTER.replace('__VER__', _VER).replace('__DATE__', _DATE)
                .replace('__SITE__', SITE_URL))

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
:root{
  --fg:#1a1a1a; --fg2:#5a5a5a; --bg:#fdfdfb; --panel:#f5f4ef;
  --line:#dcd8cf; --accent:#8a5a2b; --accent2:#a8763f;
  --quote:#f0ece2; --code:#efeadf;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth; scroll-padding-top:1.2rem}
body{
  margin:0; background:var(--bg); color:var(--fg);
  font-family:"KaiTi","STKaiti","Kaiti SC","Songti SC","SimSun",serif;
  font-size:18px; line-height:1.85;
  -webkit-font-smoothing:antialiased;
  /* 長段引文（十誦、根有多長句）在窄屏不得撐破版面 */
  /* clip 不建立捲動容器，否則 body 會搶走 sticky 的捲動祖先，側欄即不吸附 */
  overflow-x:clip; overflow-wrap:break-word; word-break:break-word;
}
/* ── 版面 ── */
.wrap{display:flex; min-height:100vh}
nav{
  width:280px; flex:0 0 280px; background:var(--panel);
  border-right:1px solid var(--line); position:sticky; top:0;
  height:100vh; overflow-y:auto; padding:1.2rem 0 3rem;
  font-family:"Microsoft YaHei","PingFang SC",sans-serif; font-size:14px;
}
nav h1{font-size:15px; margin:0 1rem 1rem; letter-spacing:.06em; font-weight:600}
nav h1 a{color:var(--fg); text-decoration:none}
nav .grp{margin:.2rem 0 .6rem}
nav .grp>b{display:block; padding:.35rem 1rem; color:var(--fg2); font-size:12.5px;
  letter-spacing:.08em; font-weight:600}
nav a{display:block; padding:.22rem 1rem .22rem 1.6rem; color:var(--fg2);
  text-decoration:none; border-left:2px solid transparent; font-size:13.5px}
nav a:hover{background:#ece8dd; color:var(--accent)}
nav a.on{border-left-color:var(--accent); color:var(--accent); background:#efeade}
nav button{display:block; width:100%; box-sizing:border-box; text-align:left;
  padding:.22rem 1rem .22rem 1.6rem; background:none; border:0;
  border-left:2px solid transparent; font-family:inherit; font-size:13.5px;
  color:var(--accent); cursor:pointer}
nav button:hover{background:#ece8dd}
nav button:focus-visible{outline:2px solid var(--accent); outline-offset:-2px}
nav details.navj{margin:0}
nav details.navj>summary{padding:.28rem 1rem; cursor:pointer; color:var(--fg2);
  font-size:13px; list-style:none; user-select:none}
nav details.navj>summary::-webkit-details-marker{display:none}
nav details.navj>summary:before{content:"▸ "; color:var(--accent2); font-size:10px}
nav details.navj[open]>summary:before{content:"▾ "}
nav details.navj>summary:hover{background:#ece8dd; color:var(--accent)}
nav a.art{padding-left:2rem; font-size:12.5px; color:#6a6258}
nav a.jie{padding-left:2.6rem; font-size:12px; color:#8a8278; line-height:1.5}
nav a.jie:hover{color:var(--accent)}
nav .jcnt{float:right; color:#b8b2a6; font-size:11px; margin-right:.2rem}
main{flex:1; min-width:0; max-width:1200px; margin:0 auto; padding:2.6rem 3rem 6rem;
  transition:max-width .18s ease}
body.wide main{max-width:none}
/* ── 標題 ── */
h1,h2,h3,h4,h5{font-family:"Microsoft YaHei","PingFang SC",sans-serif;
  line-height:1.4; color:var(--fg)}
h1{font-size:1.9rem; margin:0 0 1.6rem; letter-spacing:.04em}
h2{font-size:1.45rem; margin:3rem 0 1rem; padding-bottom:.4rem;
  border-bottom:2px solid var(--line)}
h3{font-size:1.15rem; margin:2.2rem 0 .8rem; color:var(--accent)}
h4{font-size:1.05rem; margin:1.8rem 0 .6rem; padding-left:.6rem;
  border-left:4px solid var(--accent2)}
h5{font-size:.95rem; margin:1.9rem 0 .7rem; color:var(--accent);
  padding:.35rem .8rem; background:#f3efe6; border-left:3px solid var(--accent2);
  font-family:"Microsoft YaHei",sans-serif; line-height:1.45; letter-spacing:.02em}
/* ── 段落與行內 ── */
p{margin:.7rem 0}
ul{margin:.3rem 0 .8rem; padding-left:1.15rem}
li{margin:.22rem 0; line-height:1.75}
li::marker{color:var(--accent2)}
strong{font-weight:700; color:#000}
sub{font-family:"Microsoft YaHei","PingFang SC",sans-serif; font-size:12.5px;
  color:var(--fg2); font-style:normal; display:block; margin:.5rem 0;
  letter-spacing:.02em; line-height:1.6}
code{background:var(--code); padding:.1em .35em; border-radius:3px;
  font-family:"Consolas","Courier New",monospace; font-size:.86em; color:#7a4a1a}
a{color:var(--accent); text-decoration:none}
a:hover{text-decoration:underline}
/* ── 引用塊（篇旨／節旨／說明）── */
blockquote{
  margin:1rem 0; padding:.85rem 1.1rem; background:var(--quote);
  border-left:4px solid var(--accent2); color:#3a3025;
  font-size:.96em;
}
blockquote p{margin:.3rem 0}
blockquote strong{color:var(--accent)}
/* ── 表格 ── */
table{border-collapse:collapse; width:100%; margin:1.1rem 0;
  font-family:"Microsoft YaHei","PingFang SC",sans-serif; font-size:13.5px;
  display:table; table-layout:auto}
th,td{border:1px solid var(--line); padding:.42rem .6rem; text-align:left;
  vertical-align:top}
th{background:var(--panel); font-weight:600; white-space:nowrap}
tr:nth-child(even) td{background:#faf9f5}
/* ── 折疊白話 ── */
details{margin:.7rem 0; border:1px solid var(--line); border-radius:4px;
  background:#faf8f3; padding:.3rem .8rem}
details[open]{padding-bottom:.6rem}
summary{cursor:pointer; font-family:"PingFang SC","Microsoft YaHei",sans-serif;
  font-size:13px; color:var(--fg2); padding:.3rem 0; user-select:none;
  letter-spacing:.06em}
summary:hover{color:var(--accent)}
details p{font-size:.94em; color:#4a4038; margin:.5rem 0}
/* ── 四分律原文／白話 ── */
details.art-src,details.art-plain{margin:.5rem 0 .5rem; padding:.25rem .8rem}
details.art-src{background:#fbf9f2; border-left:3px solid #c9b48a}
details.art-plain{background:#f6f8f6; border-left:3px solid #9fb59b}
details.art-src>summary,details.art-plain>summary{font-size:12.5px; letter-spacing:.04em}
details.art-src>summary{color:#8a6d3b}
details.art-plain>summary{color:#4f6b4a}
details.art-src p,details.art-plain p{font-size:.95em; line-height:1.9; margin:.45rem 0;
  text-align:justify}
details.art-src sub{display:inline; margin:0 .15em 0 0; vertical-align:baseline;
  color:#9c8a6a; font-size:11px; letter-spacing:.05em}
details.art-plain strong{color:#3f5a3a; font-size:.95em}
/* ── 本篇目錄 ── */
details.art-toc{margin:.9rem 0 1.4rem; border:1px solid var(--line); border-radius:4px;
  background:#faf8f3; padding:.4rem .9rem}
details.art-toc summary{cursor:pointer; font-family:"Microsoft YaHei",sans-serif;
  font-size:13.5px; color:var(--accent); padding:.25rem 0; letter-spacing:.03em}
details.art-toc summary:hover{color:var(--accent2)}
details.art-toc ul{list-style:none; margin:.5rem 0 .3rem; padding:0;
  columns:2; column-gap:1.6rem}
details.art-toc li{margin:.12rem 0; font-size:13px; line-height:1.65; break-inside:avoid}
details.art-toc a{color:var(--fg2); text-decoration:none}
details.art-toc a:hover{color:var(--accent); text-decoration:underline}
@media(max-width:700px){details.art-toc ul{columns:1}}
/* ── 節級差異一覽（單欄、較輕） ── */
details.art-diff{margin:.3rem 0 .85rem; padding:.18rem .7rem;
  background:#f5f6f2; border-color:var(--line)}
details.art-diff summary{font-size:12.5px; padding:.15rem 0}
details.art-diff ul{columns:1; margin:.25rem 0 .2rem}
details.art-diff li{font-size:12.5px; line-height:1.55}
details.art-diff code{font-size:11.5px}
/* ── 分隔線 ── */
hr{border:0; border-top:1px solid var(--line); margin:2.5rem 0}
/* ── 錨點高亮 ── */
:target{background:#fdf3d8; transition:background .6s}
/* ── 回到頂部 ── */
#top{position:fixed; right:1.6rem; bottom:1.6rem; width:2.6rem; height:2.6rem;
  background:var(--accent); color:#fff; border-radius:50%; display:flex;
  align-items:center; justify-content:center; text-decoration:none;
  font-size:15px; opacity:.75; z-index:99;
  font-family:sans-serif}
#top:hover{opacity:1}
/* ── 無障礙：僅供讀屏，視覺上隱藏 ── */
.sr-only{position:absolute; width:1px; height:1px; margin:-1px; padding:0;
  overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0}
/* ── 版權頁 ── */
#colophon{margin-top:3rem; font-size:13.5px; line-height:1.75; color:var(--fg2);
  font-family:"Songti SC","SimSun",serif}
#colophon p{margin:.5em 0}
#colophon b{color:var(--fg); font-size:14px; letter-spacing:.08em}
/* ── 檢索命中 ── */
.hitflash{background:#fff2b8 !important; box-shadow:0 0 0 3px #ffe680;
  transition:background .5s, box-shadow .5s; border-radius:2px}
/* ── 檢索結果清單 ── */
.findwrap{position:sticky; top:0; z-index:6; background:var(--panel);
  border-bottom:1px solid var(--line); padding-bottom:.35rem}
.findlist{position:fixed; z-index:200; width:440px; max-width:calc(100vw - 16px);
  max-height:min(58vh,480px); overflow:auto; background:var(--bg); border:1px solid var(--line);
  border-radius:4px; box-shadow:0 10px 28px rgba(0,0,0,.16); padding:.2rem}
.fl-item{display:block; width:100%; text-align:left; background:none; border:0;
  border-bottom:1px solid var(--line); padding:.42rem .5rem; cursor:pointer;
  font:inherit; font-size:12.5px; line-height:1.6; color:var(--fg)}
.fl-item:last-of-type{border-bottom:0}
.fl-item:hover,.fl-item.sel{background:var(--panel)}
.fl-item .fl-t{display:block}
.fl-item .fl-c{display:block; color:#8a8278; font-size:11px; margin-top:.12em}
.fl-item mark{background:#ffe9a8; color:inherit; padding:0 .08em; border-radius:2px}
.fl-more{padding:.4rem .5rem; font-size:11.5px; color:#8a8278; display:block}
.fl-site{color:var(--accent); text-decoration:none; border-top:1px solid var(--line)}
.fl-site:hover{text-decoration:underline}
/* ── 對讀：原文與白話左右並列 ── */
body.par details.art-src,
body.par details.art-plain{float:left; width:calc(50% - .5rem); box-sizing:border-box;
  margin:0 .9rem .7rem 0}
body.par details.art-plain{margin-right:0}
body.par details.art-src + *:not(details.art-plain),
body.par details.art-plain + *{clear:both}
body.par main:after{content:""; display:block; clear:both}
/* ── 深色模式 ── */
@media (prefers-color-scheme: dark){
  :root{
    --fg:#e6e2da; --fg2:#b3aca1; --bg:#161514; --panel:#1e1d1b;
    --line:#3a3733; --accent:#d9a05b; --accent2:#c98f4c;
    --quote:#242220; --code:#26241f;
  }
  nav{background:#1b1a18; border-right:1px solid var(--line)}
  nav a:hover,nav details.navj>summary:hover,nav button:hover{background:#2a2825}
  nav a.on{background:#2e2b26}
  nav a.art{color:#9d968b}
  nav a.jie{color:#8b857b}
  nav .jcnt{color:#6b665e}
  nav input[type=text],nav input[type=search]{background:#232120; color:var(--fg);
    border-color:var(--line)}
  #findinfo{color:#8b857b}
  .findlist{background:#1e1d1b; box-shadow:0 10px 28px rgba(0,0,0,.55)}
  .fl-item .fl-c,.fl-more{color:#8b857b}
  .fl-item mark{background:#6b5a22; color:#f3eee4}
  .fl-item:hover,.fl-item.sel{background:#2a2825}
  #colophon{color:var(--fg2)}
  details{background:#1e1d1b}
  details p{color:#c9c3b8}
  details summary{color:var(--fg2)}
  blockquote{color:#cfc8bc}
  h5{background:#26241f}
  details.art-src{background:#1c1b19; border-left-color:#8a7443}
  details.art-plain{background:#191c19; border-left-color:#5c7059}
  details.art-toc,details.art-diff{background:#1d1c1a; border-color:var(--line)}
  details.art-toc summary,details.art-diff summary{color:var(--accent)}
  details.art-src>summary{color:#c9a76a}
  details.art-plain>summary{color:#8fae8a}
  details.art-src p,details.art-plain p{color:#cfc8bc}
  details.art-toc{background:#1e1d1b}
  .hitflash{background:#4a3f1e !important; box-shadow:0 0 0 3px #6b5a22}
  #top{background:#2a2825; color:var(--fg)}
  img{opacity:.92}
}
/* ── 首頁檢索 ── */
.homefind{display:flex; gap:.5rem; flex-wrap:wrap; margin:1rem 0 .4rem}
.homefind input[type=search]{flex:1 1 320px; min-width:200px; font:inherit; font-size:15px;
  padding:.55rem .8rem; border:1px solid var(--line); border-radius:4px;
  background:#fff; color:var(--fg)}
.homefind input[type=search]:focus{outline:2px solid var(--accent2); outline-offset:1px}
.homefind button{font:inherit; font-size:14px; padding:.55rem 1.1rem; cursor:pointer;
  border:1px solid var(--accent); border-radius:4px; background:var(--accent); color:#fff}
.homefind button:hover{background:var(--accent2); border-color:var(--accent2)}
.hint{font-size:13px; color:var(--fg2); margin:.1rem 0 1.2rem; line-height:1.75}
.hint code{background:var(--code); padding:.05rem .3rem; border-radius:2px}
.homeres{margin:.2rem 0 1.4rem; max-height:62vh; overflow:auto}
.homeres .fl-item{font-size:14px; padding:.55rem .65rem; border:1px solid var(--line);
  border-radius:4px; margin-bottom:.35rem; background:var(--panel)}
.homeres .fl-item:hover{background:var(--bg); border-color:var(--accent2)}
.homeres .fl-k{display:inline-block; min-width:1.5em; margin-right:.4em; font-size:11px;
  color:var(--accent); border:1px solid var(--line); border-radius:2px; text-align:center;
  padding:0 .2em; vertical-align:.08em}
.homeres .fl-t{display:inline}
.homeres .fl-c{display:block; color:#8a8278; font-size:12px; margin-top:.18em}
.homeres .fl-more{color:#8a8278; font-size:12.5px; padding:.3rem .2rem}
@media (prefers-color-scheme: dark){
  .homefind input[type=search]{background:#232120; color:var(--fg); border-color:var(--line)}
  .homeres .fl-item{background:#1e1d1b}
  .homeres .fl-item:hover{background:#232120}
  .homeres .fl-item mark{background:#6b5a22; color:#f3eee4}
  .homeres .fl-c,.homeres .fl-more{color:#8b857b}
}
/* ── 窄屏 ── */
@media(max-width:1100px){
  nav{display:none}
  main{padding:1.4rem 1.1rem 4rem}
  body{font-size:16px}
  body.par details.art-src,
  body.par details.art-plain{float:none; width:auto; margin-right:0}
}
/* ── 打印（供 PDF 用，若直接打印本頁）── */
@media print{
  nav,#top{display:none}
  main{max-width:none; padding:0}
  details{border:0; background:none; padding:0}
  details>*{display:block !important}
  /* 長文列印：標題不落頁底孤行，表格與引文不跨頁撕裂，段落不出現單行寡婦 */
  h1,h2,h3,h4,h5,h6{break-after:avoid; page-break-after:avoid}
  table,pre,blockquote{break-inside:avoid; page-break-inside:avoid}
  tr,li{break-inside:avoid; page-break-inside:avoid}
  p,li{orphans:3; widows:3}
  a{color:inherit; text-decoration:none}
}
"""

CSS += r"""
/* ── 側邊欄與檢索增強（2026-11-07）────────────────────────────── */
/* 寬表橫向捲動容器（窄屏防撐破） */
.tscroll{max-width:100%; overflow-x:auto; -webkit-overflow-scrolling:touch;
  margin:.8rem 0; border-radius:3px}
.tscroll>table{margin:0}
/* 底部固定工具區：分卷前後、回目錄、展開收合、跳項號 */
nav{padding-bottom:0}
.navdock{position:sticky; bottom:0; z-index:5; margin-top:.5rem;
  background:var(--panel); border-top:1px solid var(--line);
  box-shadow:0 -6px 14px rgba(0,0,0,.05); padding:.15rem 0 .45rem}
.docklinks{display:flex; flex-wrap:wrap; gap:.22rem; padding:.3rem 1rem .05rem}
.docklinks a{flex:1 1 auto; min-width:0; text-align:center; font-size:11.5px;
  padding:.24rem .35rem; border:1px solid var(--line); border-radius:3px;
  color:var(--fg2); text-decoration:none; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis}
.docklinks a:hover{border-color:var(--accent2); color:var(--accent); background:#efeade}
.navdock .navtools{padding:.25rem 1rem 0}
.navdock .grp{padding:.3rem 1rem 0; margin:0}
#navfilter{display:block; width:calc(100% - 2rem); margin:.15rem 1rem .3rem;
  padding:.3rem .5rem; border:1px solid var(--line); border-radius:3px;
  background:#fff; color:var(--fg); font:inherit; font-size:12.5px}
#navfilter:focus{outline:2px solid var(--accent2); outline-offset:1px}
#navfinfo{font-size:11px; color:#8a8278; padding:0 1rem .3rem; min-height:1.1em}
nav a.filtered,nav details.navj.filtered{display:none}
nav a.on{font-weight:600}
#navresizer{position:fixed; top:0; left:277px; width:6px; height:100vh;
  cursor:col-resize; z-index:9; touch-action:none}
#navresizer:hover{background:var(--accent2); opacity:.45}
#navtoggle,#navburger{border:1px solid var(--line); background:var(--panel);
  color:var(--accent); cursor:pointer; font-family:"Microsoft YaHei",sans-serif; z-index:210}
#navtoggle{display:none; position:fixed; left:0; top:50%; transform:translateY(-50%);
  width:1.35rem; padding:.5rem .1rem; writing-mode:vertical-rl;
  border-left:1px solid var(--line); border-radius:0 4px 4px 0; font-size:11px}
body.navclosed #navtoggle{display:block}
#navtoggle:hover,#navburger:hover{background:#ece8dd}
body.navclosed nav{display:none}
.navtools{display:grid; grid-template-columns:1fr 1fr; gap:.25rem; padding:.4rem 1rem .2rem}
.navtools button{display:block; width:100%; padding:.28rem .2rem; text-align:center;
  border:1px solid var(--line); border-radius:3px; background:transparent;
  color:var(--fg2); font-size:11.5px}
.navtools button:hover{background:#ece8dd}
.navtools button[aria-pressed="true"]{border-color:var(--accent); color:var(--accent);
  background:#efeade}
#jump{margin-top:.1rem}
.findhead{display:flex; align-items:center; gap:.3rem}
.findhead input[type=search]{flex:1 1 auto; min-width:0; padding:.28rem .5rem;
  border:1px solid var(--line); border-radius:3px; font-size:12.5px;
  font-family:inherit; background:#fff}
.findhead input[type=search]:focus{outline:2px solid var(--accent2); outline-offset:1px}
#findhelpbtn{flex:0 0 1.55rem; height:1.55rem; border:1px solid var(--line);
  border-radius:50%; background:transparent; color:var(--accent); cursor:pointer;
  font-size:11.5px; padding:0}
#findhelpbtn:hover{background:#ece8dd}
#findhelp{font-size:11.5px; line-height:1.7; color:var(--fg2); background:var(--panel);
  border:1px solid var(--line); border-radius:3px; padding:.45rem .55rem; margin:.35rem 0 .1rem}
#findhelp[hidden]{display:none}
#findhelp code{background:var(--code); padding:0 .2em; border-radius:2px}
.findopts{display:flex; gap:.25rem; flex-wrap:wrap; margin:.35rem 0 .1rem}
.findopts button{flex:1 1 auto; font-size:11px; padding:.22rem .3rem;
  border:1px solid var(--line); border-radius:3px; background:transparent;
  color:var(--fg2); cursor:pointer; white-space:nowrap}
.findopts button[aria-pressed="true"]{border-color:var(--accent);
  background:#efeade; color:var(--accent); font-weight:600}
#findhist{display:flex; flex-wrap:wrap; align-items:center; gap:.22rem; margin:.28rem 0 0}
#findhist button{font-size:11px; padding:.12rem .4rem; border:1px solid var(--line);
  border-radius:10px; background:transparent; color:var(--fg2); cursor:pointer}
#findhist button:hover{border-color:var(--accent2); color:var(--accent)}
#findhist span{font-size:10.5px; color:#8a8278}
.fl-item .fl-p{display:block; color:var(--accent); font-size:10.5px;
  letter-spacing:.04em; margin-bottom:.1em}
.fl-item .fl-c{white-space:normal}
button.fl-load{width:100%; text-align:center; color:var(--accent); cursor:pointer;
  background:var(--panel); border:1px solid var(--line); border-radius:3px;
  font:inherit; font-size:11.5px; padding:.35rem; margin:.2rem 0}
.tryq{display:flex; flex-wrap:wrap; gap:.35rem; margin:.2rem 0 1.2rem}
.tryq span{font-size:12.5px; color:var(--fg2)}
.tryq a{font-size:12.5px; padding:.2rem .6rem; border:1px solid var(--line);
  border-radius:12px; background:var(--panel); color:var(--accent)}
.tryq a:hover{border-color:var(--accent2); background:#efeade}
@media (prefers-color-scheme: dark){
  .navdock{background:#1b1a18}
  .docklinks a{color:var(--fg2)}
  .docklinks a:hover{background:#2a2825; color:var(--accent)}
  #navfilter,.findhead input[type=search]{background:#232120; color:var(--fg); border-color:var(--line)}
  #navtoggle,#navburger{background:#1b1a18; color:var(--accent); border-color:var(--line)}
  .navtools button,.findopts button,#findhist button,#findhelpbtn{background:#1e1d1b; color:var(--fg2)}
  .navtools button[aria-pressed="true"],.findopts button[aria-pressed="true"]{background:#2e2b26; color:var(--accent)}
  .tryq a{background:#1e1d1b}
  button.fl-load{background:#1e1d1b; color:var(--accent)}
  #navfinfo,#findhist span{color:#8b857b}
}
@media(max-width:1100px){
  nav{display:block; position:fixed; left:0; top:0; height:100dvh;
    width:min(86vw,320px) !important; flex-basis:auto !important;
    transform:translateX(-102%); transition:transform .22s ease;
    z-index:310; box-shadow:6px 0 24px rgba(0,0,0,.25)}
  body.navopen nav{transform:none}
  body.navclosed nav{display:block}
  #navtoggle,#navresizer{display:none !important}
  #navburger{display:flex; position:fixed; left:.7rem; top:.7rem; z-index:300;
    width:2.2rem; height:2.2rem; align-items:center; justify-content:center;
    border-radius:4px; font-size:17px}
  #navmask{display:block; position:fixed; inset:0; z-index:305;
    background:rgba(0,0,0,.42); opacity:0; pointer-events:none; transition:opacity .2s}
  body.navopen #navmask{opacity:1; pointer-events:auto}
  main{padding-top:3.4rem}
}
@media(min-width:1101px){ #navburger,#navmask{display:none} }
@media print{
  #navtoggle,#navburger,#navmask,#navresizer{display:none !important}
  /* 列印時表格不裁切，改由瀏覽器分頁 */
  .tscroll{overflow:visible !important; max-width:none}
}

/* ── 側欄 UI 重構（2026-11-07 夜）──────────────────────────────── */
nav{scrollbar-width:thin; scrollbar-color:#d5cec2 transparent}
nav::-webkit-scrollbar{width:8px}
nav::-webkit-scrollbar-thumb{background:#d8d2c6; border-radius:4px}
nav::-webkit-scrollbar-thumb:hover{background:#c4bcae}

nav h1{font-size:15.5px; margin:.15rem 1rem .1rem; letter-spacing:.03em; font-weight:600}
nav h1 a{color:var(--fg)}
.nsub{font-size:10.5px; color:#9a9288; padding:0 1rem .55rem; letter-spacing:.08em}

/* 搜尋區 */
.findwrap{padding:.5rem 1rem .45rem; border-bottom:1px solid var(--line)}
.findhead{gap:.3rem}
.findhead input[type=search]{font-size:12px; padding:.3rem .45rem; border-radius:4px}
#findhelpbtn{width:1.45rem; height:1.45rem; font-size:11px}
.findopts{display:grid; grid-template-columns:repeat(3,1fr); gap:.2rem;
  margin:.32rem 0 .05rem}
.findopts button{font-size:10.5px; padding:.22rem .1rem; border-radius:3px;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; min-width:0}
#findinfo{font-size:10.5px; padding:.22rem 0 0; color:#9a9288}
#findhist{margin:.2rem 0 0; gap:.18rem}
#findhist button{font-size:10.5px; padding:.1rem .38rem}
#findhist span{font-size:10px}

/* 目錄頭 */
.navhead{display:flex; align-items:center; justify-content:space-between;
  padding:.55rem 1rem .1rem}
.navhead b{flex:0 0 auto; white-space:nowrap; font-size:11px; letter-spacing:.14em;
  color:#9a9288; font-weight:600}
.navhead button{flex:0 0 auto; margin-left:auto; font-size:10px; padding:.12rem .38rem; border:1px solid var(--line);
  border-radius:10px; background:transparent; color:var(--fg2); cursor:pointer;
  font-family:inherit}
.navhead button:hover{border-color:var(--accent2); color:var(--accent); background:#efeade}

/* 過濾框 */
.navfilterwrap{padding:.15rem 1rem .1rem}
#navfilter{width:100%; margin:0; font-size:11.5px; padding:.26rem .45rem; border-radius:4px}
#navfinfo{font-size:10px; padding:.15rem 0 0; color:#9a9288; min-height:1em}
#navfinfo.none{color:#a8543a}

/* 分組標題：標題＋細線 */
nav .grp{margin:.15rem 0 .25rem}
nav .grp>b{display:flex; align-items:center; gap:.4rem; padding:.5rem 1rem .18rem;
  font-size:10.5px; letter-spacing:.12em; color:#9a9288; font-weight:600}
nav .grp>b:after{content:""; flex:1; height:1px; background:var(--line)}
nav a.navhome{padding:.28rem 1rem; font-size:12px; color:var(--fg2)}

/* 卷 */
nav details.navj>summary{display:flex; align-items:center; gap:.35rem;
  padding:.32rem 1rem; font-size:12.5px; font-weight:600; color:#5f574d;
  border-left:2px solid transparent}
nav details.navj>summary:before{content:"▸"; color:#b8b2a6; font-size:9px;
  flex:0 0 .7rem}
nav details.navj[open]>summary:before{content:"▾"}
nav details.navj>summary:hover{background:#ece8dd; color:var(--accent)}
nav details.navj>summary .jcnt{margin-left:auto; float:none; font-size:9.5px;
  color:#a89f92; background:#ece8dd; border-radius:8px; padding:0 .4rem; line-height:1.6}
nav details.navj[open]>summary .jcnt{background:#e4dfd2}

/* 篇：編號 badge */
nav a.art{display:flex; align-items:baseline; gap:.45rem;
  padding:.2rem 1rem .2rem 1.55rem; font-size:12.5px; line-height:1.5;
  border-left:2px solid transparent}
nav a.art .pno{flex:0 0 2.05rem; font-size:9.5px; color:#a09889;
  font-variant-numeric:tabular-nums; letter-spacing:.02em}
nav a.art .pt{flex:1; min-width:0}
nav a.art:hover{background:#ece8dd; color:var(--accent)}
nav a.art:hover .pno{color:var(--accent2)}
nav a.art.on{border-left-color:var(--accent); background:#efeade;
  color:var(--accent); font-weight:600}
nav a.art.on .pno{color:var(--accent)}

/* 節：左側樹線 */
nav a.jie{position:relative; padding:.2rem 1rem .2rem 2.15rem; font-size:12px;
  line-height:1.5; color:#8a8278; border-left:2px solid transparent}
nav a.jie:before{content:""; position:absolute; left:1.4rem; top:0; bottom:0;
  width:1.5px; background:#dcd6c9}
nav a.jie:hover{background:#efeade; color:var(--accent)}
nav a.jie.on{border-left-color:var(--accent); background:#efeade;
  color:var(--accent); font-weight:600}

/* dock：幽靈按鈕 */
.navdock{border-top:1px solid var(--line); box-shadow:0 -8px 18px rgba(0,0,0,.05)}
.docklinks a{border-color:transparent; background:#efeade; color:#7a7268}
.docklinks a:hover{background:#e7e1d3; border-color:var(--accent2); color:var(--accent)}
.navdock .navtools button{border-color:transparent; background:transparent; color:#7a7268;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; padding:.3rem .15rem}
.navdock .navtools button:hover{background:#ece8dd; color:var(--accent)}
.navdock .navtools button[aria-pressed="true"]{background:#efeade;
  border-color:var(--accent); color:var(--accent)}

@media (prefers-color-scheme: dark){
  #navfinfo.none{color:#d98b6a}
  nav::-webkit-scrollbar-thumb{background:#3a3733}
  .nsub{color:#7d766c}
  .navhead b,nav .grp>b{color:#8b857b}
  nav .grp>b:after{background:#3a3733}
  nav details.navj>summary{color:#b3aca1}
  nav details.navj>summary .jcnt{background:#2a2825; color:#8b857b}
  nav details.navj[open]>summary .jcnt{background:#332f2a}
  nav a.art .pno{color:#6f6961}
  nav a.art:hover,nav a.jie:hover{background:#2a2825}
  nav a.art.on,nav a.jie.on{background:#2e2b26}
  nav a.jie:before{background:#3a3733}
  .docklinks a{background:#242220; color:#b3aca1}
  .docklinks a:hover{background:#2e2b26}
  .navdock{box-shadow:0 -8px 18px rgba(0,0,0,.4)}
}
@media(max-width:1100px){
  nav h1{font-size:16px}
  nav a.art{font-size:13px}
  nav a.jie{font-size:12px}
  nav details.navj>summary{font-size:13px}
}
"""

# ── 檢索核心（合冊／分卷／首頁共用）──────────────────────────────
# 正規化：全半角與標點去除、繁簡異體折疊、梵巴轉寫去變音符。
# 同義詞：律學名相別名（單提↔波逸提、捨墮↔尼薩耆波逸提……），
#         查「波逸提」亦得「單提」，惟排序在精確命中之後。
SEARCH_CORE = r"""
window.VS = (function(){
  var PUNC = /[\s\u3000，。、；：？！「」『』（）()\[\]【】〈〉《》·．,.;:?!'"“”‘’—－\-…／\/]/g;
  // 異體字折疊（鍵為罕見體，值為通行體）
  var FOLD = {'麁':'麤','鉢':'缽','著':'着','牀':'床','汙':'污',
    '脚':'腳','㥲':'瞋','柰':'奈','㝹':'兔','説':'說','摺':'襵',
    '衆':'眾','敎':'教','卽':'即','爲':'為','凈':'淨','倂':'併','峯':'峰','羣':'群',
    '眞':'真','覩':'睹','穉':'稚','疎':'疏','隣':'鄰','牕':'窗','窻':'窗','牎':'窗',
    '鷄':'雞','兎':'兔','豬':'猪','貓':'猫','蟁':'蚊','螘':'蟻','鼈':'鱉',
    '麪':'麵','麫':'麵','煑':'煮','甞':'嘗','嚐':'嘗','塚':'冢','冡':'冢','冐':'冒',
    '凖':'準','况':'況','凄':'淒','敍':'敘','牠':'他','麽':'麼',
    '尠':'鮮','尟':'鮮','尢':'尤','尲':'尷','尶':'尷','屛':'屏','峩':'峨','巗':'巖',
    '幷':'並','幇':'幫','廼':'乃','迺':'乃','衹':'只','喫':'吃','箒':'帚','篛':'箬',
    '粧':'妝','糉':'粽','糰':'團','絃':'弦','綫':'線','罇':'樽','羗':'羌','翫':'玩',
    '耑':'專','肻':'肯','脣':'唇','腅':'臉','舘':'館','菓':'果','萞':'蓖','蔴':'麻',
    '薫':'薰','藴':'蘊','蘂':'蕊','虵':'蛇','蝨':'蝨','衂':'衄','袵':'衽','裠':'裙',
    '襍':'雜','覈':'核','謌':'歌','貍':'狸','賸':'剩','跥':'跺','蹟':'跡','躭':'耽',
    '軃':'嚲','輭':'軟','迻':'移','遶':'繞','邨':'村','醎':'鹹','鈎':'鉤','鉋':'刨',
    '銲':'焊','鍊':'煉','鎗':'槍','鑪':'爐','閒':'閑','閙':'鬧','陞':'升','隖':'塢',
    '靑':'青','鞵':'鞋','韈':'襪','頫':'俯','顚':'顛','餧':'餵','饑':'飢','驘':'騾',
    '髩':'鬢','鬭':'鬥','魲':'鱸','鮎':'鯰','鵶':'鴉','鷰':'燕','麕':'麇','黴':'霉',
    '齩':'咬','龞':'鱉'};
  // 律學名相別名（鍵值皆為已正規化之形）
  var SYN = {
    '波逸提':['單提'], '單提':['波逸提'],
    '尼薩耆波逸提':['捨墮','尼薩耆'], '捨墮':['尼薩耆波逸提','尼薩耆'], '尼薩耆':['捨墮'],
    '僧殘':['僧伽婆尸沙'], '僧伽婆尸沙':['僧殘'],
    '眾學':['式叉迦羅尼','學法'], '式叉迦羅尼':['眾學'],
    '突吉羅':['惡作'], '惡作':['突吉羅'],
    '偷蘭遮':['偷羅遮','土羅遮'], '偷羅遮':['偷蘭遮'],
    '提舍尼':['波羅提提舍尼'], '波羅提提舍尼':['提舍尼'],
    '僧祇':['摩訶僧祇'], '摩訶僧祇':['僧祇'],
    '根有':['根本說一切有部'], '根本說一切有部':['根有'],
    '五分':['彌沙塞'], '彌沙塞':['五分'],
    '四分':['法藏部','曇無德'], '法藏部':['四分'],
    '十誦':['薩婆多'], '薩婆多':['十誦'],
    '揵度':['犍度'], '犍度':['揵度'],
    '毘尼':['毗尼'], '毗尼':['毘尼'],
    '婬':['淫'], '淫':['婬'],
    '滅諍':['滅諍法','七滅諍'],
    // 根有（義淨新譯）與僧祇（大眾部）之別譯
    '波羅夷':['波羅市迦'], '波羅市迦':['波羅夷'],
    '偷蘭遮':['偷羅遮','土羅遮','窣吐羅底也','窣吐羅'],
    '窣吐羅底也':['偷蘭遮'], '窣吐羅':['偷蘭遮'],
    '突吉羅':['惡作','越法罪','越毘尼'], '越法罪':['突吉羅'], '越毘尼':['突吉羅'],
    '比丘':['苾芻'], '苾芻':['比丘'],
    '比丘尼':['苾芻尼'], '苾芻尼':['比丘尼'],
    '僧祇':['摩訶僧祇','大眾部'], '大眾部':['僧祇'],
    '根有':['根本說一切有部','有部'], '有部':['根有'],
    // 度量衡異譯（vitasti）
    '搩手':['磔手','張手'], '磔手':['搩手','張手'], '張手':['搩手','磔手'],
    '肘':['肘量']
  };
  var strip = function(s){
    s = String(s);
    if (s.normalize){
      try { s = s.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); } catch(e){}
    }
    return s;
  };
  var norm = function(s){
    s = strip(s).replace(PUNC, '').toLowerCase();
    var o = '';
    for (var i = 0; i < s.length; i++){
      var c = s.charAt(i);
      o += (FOLD[c] || c);
    }
    return o;
  };
  // 子序列模糊：可容漏字、跳字，但首末跨度不得過散
  var fuzzy = function(hay, needle){
    if (needle.length < 2) return false;
    var i = 0, j = 0, first = -1, last = -1;
    while (i < hay.length && j < needle.length){
      if (hay.charAt(i) === needle.charAt(j)){
        if (first < 0) first = i;
        last = i; j++;
      }
      i++;
    }
    if (j < needle.length) return false;
    return (last - first + 1) <= needle.length * 2;
  };
  var parseQuery = function(q){
    var inc = [], exc = [], phr = [], raw = [], m;
    var re = /"([^"]+)"|(\S+)/g;
    while ((m = re.exec(q))){
      if (m[1]){
        var p = norm(m[1]);
        if (p){ phr.push(p); raw.push(m[1]); }
      } else {
        var t = m[2];
        if (t.charAt(0) === '-' && t.length > 1){
          var e = norm(t.slice(1));
          if (e) exc.push(e);
        } else {
          var v = norm(t);
          if (v){ inc.push(v); raw.push(t); }
        }
      }
    }
    var groups = [];
    for (var i = 0; i < inc.length; i++){
      var t2 = inc[i], g = [t2], alt = SYN[t2];
      if (alt){
        for (var j = 0; j < alt.length; j++){
          if (alt[j] !== t2) g.push(alt[j]);
        }
      }
      groups.push(g);
    }
    return {inc: groups, exc: exc, phr: phr, raw: raw, n: groups.length + phr.length};
  };
  // 回傳 0 未中、1 精確、2 同義詞、3 模糊
  var matchGroup = function(hay, g){
    if (hay.indexOf(g[0]) >= 0) return 1;
    for (var i = 1; i < g.length; i++){
      if (hay.indexOf(g[i]) >= 0) return 2;
    }
    for (var k = 0; k < g.length; k++){
      if (fuzzy(hay, g[k])) return 3;
    }
    return 0;
  };
  return {norm: norm, strip: strip, fuzzy: fuzzy, parseQuery: parseQuery, matchGroup: matchGroup};
})();
"""

# ── 首頁全站索引檢索（延遲載入 search_index.js，不載合冊）──────────
HOME_SEARCH = r"""
(function(){
  var form = document.getElementById('homeform');
  var q = document.getElementById('homeq');
  var box = document.getElementById('homeres');
  if (!form || !q || !box || !window.VS) return;
  var loading = false, wait = null, recs = null, timer = null, lastQ = '';

  var load = function(fn){
    if (window.SIDX){ recs = window.SIDX; return fn(); }
    wait = fn;
    if (loading) return;
    loading = true;
    var s = document.createElement('script');
    s.src = 'search_index.js';
    s.onload = function(){
      recs = window.SIDX || []; loading = false;
      var f = wait; wait = null; if (f) f();
    };
    s.onerror = function(){
      loading = false;
      box.innerHTML = '<p class="fl-more">索引載入失敗，請改用' +
        '<a href="五部律差異對照本.html">合冊</a>側欄檢索。</p>';
    };
    document.head.appendChild(s);
  };

  var esc = function(s){
    return String(s).replace(/[&<>"]/g, function(c){
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c];
    });
  };
  var tokens = function(qq){
    var out = [], m, re = /"([^"]+)"|(\S+)/g;
    while ((m = re.exec(qq))){
      var t = m[1] || m[2];
      if (!t || t.charAt(0) === '-') continue;
      out.push(t);
    }
    return out;
  };
  var hl = function(text, qq){
    var ts = tokens(qq), low = String(text).toLowerCase();
    for (var i = 0; i < ts.length; i++){
      var k = low.indexOf(ts[i].toLowerCase());
      if (k >= 0){
        return esc(text.slice(0, k)) + '<mark>' + esc(text.slice(k, k + ts[i].length)) +
               '</mark>' + esc(text.slice(k + ts[i].length));
      }
    }
    return esc(text);
  };

  var KIND = {p: '篇', u: '節', d: '項', s: '項', g: '組', x: '頁'};

  var search = function(qq){
    var pq = VS.parseQuery(qq);
    if (!pq.n || !recs) return [];
    var out = [];
    for (var i = 0; i < recs.length; i++){
      var r = recs[i];
      var nt = String(r[2] || '').toLowerCase();
      var nb = String(r[3] || '').toLowerCase();
      var nc = String(r[5] || '').toLowerCase();
      var ex = false;
      for (var e = 0; e < pq.exc.length; e++){
        if (nt.indexOf(pq.exc[e]) >= 0 || nb.indexOf(pq.exc[e]) >= 0){ ex = true; break; }
      }
      if (ex) continue;
      var score = 0, miss = false;
      for (var j = 0; j < pq.inc.length; j++){
        var g = pq.inc[j];
        var s1 = VS.matchGroup(nt, g);
        var s2 = s1 ? 0 : VS.matchGroup(nb, g);
        var s3 = (s1 || s2) ? 0 : VS.matchGroup(nc, g);
        if (!s1 && !s2 && !s3){ miss = true; break; }
        score += s1 ? 0 : (s2 ? 1 : 2);
      }
      if (miss) continue;
      var pok = true;
      for (var k = 0; k < pq.phr.length; k++){
        if (nt.indexOf(pq.phr[k]) < 0 && nb.indexOf(pq.phr[k]) < 0){ pok = false; break; }
      }
      if (!pok) continue;
      out.push({r: r, s: score, i: i});
    }
    out.sort(function(a, b){ return a.s - b.s || a.i - b.i; });
    return out;
  };

  var render = function(qq){
    var res = search(qq);
    box.innerHTML = '';
    var full = '五部律差異對照本.html?q=' + encodeURIComponent(qq);
    if (!res.length){
      box.innerHTML = '<p class="fl-more">索引中無「' + esc(qq) + '」。</p>' +
        '<a class="fl-more" href="' + full + '">在合冊中全文檢索（含原文與白話）→</a>';
      return;
    }
    var n = Math.min(res.length, 60);
    for (var i = 0; i < n; i++){
      var r = res[i].r;
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'fl-item';
      b.innerHTML = '<span class="fl-k">' + (KIND[r[0]] || '') + '</span>' +
        '<span class="fl-t">' + hl(r[2], qq) + '</span>' +
        '<span class="fl-c">' + esc(r[5] || '') +
        (r[3] ? '　·　' + hl(r[3], qq) : '') + '</span>';
      b.addEventListener('click', (function(h){
        return function(){ location.href = h; };
      })(r[4]));
      box.appendChild(b);
    }
    var foot = document.createElement('div');
    foot.className = 'fl-more';
    foot.innerHTML = '共 ' + res.length + ' 項' +
      (res.length > n ? '，僅列前 ' + n + ' 項' : '') +
      '　·　<a href="' + full + '">在合冊中全文檢索 →</a>';
    box.appendChild(foot);
  };

  var go = function(){
    var qq = q.value.trim();
    if (!qq){ box.innerHTML = ''; lastQ = ''; return; }
    if (qq === lastQ) return;
    lastQ = qq;
    load(function(){ render(qq); });
  };
  q.addEventListener('input', function(){
    clearTimeout(timer);
    timer = setTimeout(go, 180);
  });
  form.addEventListener('submit', function(e){ e.preventDefault(); lastQ = ''; go(); });

  (function(){
    var m = (location.search || '').match(/[?&]q=([^&]*)/);
    if (!m) return;
    var q0 = '';
    try { q0 = decodeURIComponent(m[1].replace(/\+/g, ' ')); } catch (err){ return; }
    if (!q0) return;
    q.value = q0;
    setTimeout(go, 120);
  })();
})();
"""

SEARCH_BOX = r"""
<div class="grp findwrap" style="padding:.2rem 1rem .55rem">
<label for="find" class="sr-only">全文檢索</label>
<div class="findhead">
<input type="search" id="find"
  placeholder="檢索全文…（Ctrl+F）"
  aria-label="多關鍵字模糊檢索，含折疊內容。空白分隔多詞，減號排除，引號片語"
  autocomplete="off">
<button type="button" id="findhelpbtn" aria-expanded="false" aria-controls="findhelp"
  aria-label="檢索語法說明" title="檢索語法說明">?</button>
</div>
<div id="findhelp" hidden>
<b>多詞</b>　空白分隔，須全部命中（<code>迦絺那 自恣</code>）<br>
<b>排除</b>　<code>-四分</code>　　<b>片語</b>　<code>"非親里"</code><br>
<b>別名</b>　波逸提＝單提、捨墮＝尼薩耆、比丘＝苾芻… 自動並查<br>
<b>模糊</b>　容漏字（<code>摩埵</code> 可中「摩那埵」）<br>
<b>快捷</b>　<code>Ctrl+K</code> 或 <code>/</code> 聚焦（<code>Ctrl+F</code> 為瀏覽器原生查找）；
<code>Enter</code> 逐處跳；<code>F3</code>／<code>Shift+F3</code> 前後巡覽；<code>↑↓</code> 選結果
</div>
<div class="findopts" role="group" aria-label="檢索範圍">
<button type="button" data-scope="all" aria-pressed="true" title="全文（含白話與四分原文）">全部</button>
<button type="button" data-scope="title" aria-pressed="false" title="只搜標題與項名">標題</button>
<button type="button" data-scope="core" aria-pressed="false" title="排除白話與四分律原文">略原文</button>
</div>
<div id="findinfo" role="status" aria-live="polite"
  style="font-size:11.5px;color:#8a8278;padding:.25rem .1rem 0;min-height:1.2em"></div>
<div id="findhist" aria-label="近期檢索"></div>
<div id="findlist" class="findlist" role="listbox" aria-label="檢索結果" hidden></div>
</div>
"""

JS = r"""
__SEARCH_CORE__
(function(){
  // 目錄高亮：滾動時標記當前章節
  var links = Array.prototype.slice.call(document.querySelectorAll('nav a[href^="#"]'));
  var map = {};
  links.forEach(function(a){
    var id = a.getAttribute('href').slice(1);
    var el = document.getElementById(id);
    if (el) map[id] = {a:a, el:el};
  });
  function onScroll(){
    var y = window.scrollY + 120, cur = null;
    for (var id in map){
      if (map[id].el.offsetTop <= y) cur = id;
    }
    links.forEach(function(a){ a.classList.remove('on'); });
    if (cur && map[cur]) map[cur].a.classList.add('on');
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();
  // 跳至項號
  var jp = document.getElementById('jump');
  if (jp){
    jp.addEventListener('keydown', function(e){
      if (e.key !== 'Enter') return;
      var v = jp.value.trim().toUpperCase().replace(/^([DS])-?(\d{1,4})$/, '$1-$2');
      var m = v.match(/^([DS])-(\d{1,4})$/);
      if (!m) return;
      var id = (m[1] + '-' + m[2].padStart(4, '0')).toLowerCase();
      var el = document.getElementById(id);
      if (el){
        el.scrollIntoView({behavior:'smooth', block:'start'});
        el.style.transition = 'background .8s';
        el.style.background = '#fdf3d8';
        setTimeout(function(){ el.style.background = ''; }, 1600);
      } else {
        jp.value = '無此項或不在本卷';
        setTimeout(function(){ jp.value = ''; }, 1200);
      }
    });
  }
  // 寬度切換
  var wbtn = document.getElementById('width');
  if (wbtn){
    if (localStorage.getItem('wb_wide') === '1') document.body.classList.add('wide');
    var syncW = function(){
      wbtn.textContent = document.body.classList.contains('wide') ? '舒適寬' : '寬屏';
    };
    syncW();
    wbtn.addEventListener('click', function(e){
      e.preventDefault();
      document.body.classList.toggle('wide');
      localStorage.setItem('wb_wide', document.body.classList.contains('wide') ? '1' : '0');
      syncW();
    });
  }
  // 全部展開／折疊
  var bar = document.getElementById('toggle');
  if (bar){
    bar.addEventListener('click', function(){
      var ds = document.querySelectorAll('details');
      var anyClosed = Array.prototype.some.call(ds, function(d){ return !d.open; });
      Array.prototype.forEach.call(ds, function(d){ d.open = anyClosed; });
      bar.textContent = anyClosed ? '收起' : '展開';
    });
  }
  // 對讀：原文與白話左右並列
  var pbtn = document.getElementById('par');
  if (pbtn){
    if (localStorage.getItem('wb_par') === '1') document.body.classList.add('par');
    var syncP = function(){
      var on = document.body.classList.contains('par');
      pbtn.textContent = on ? '對讀：開' : '對讀';
      pbtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    };
    syncP();
    pbtn.addEventListener('click', function(){
      document.body.classList.toggle('par');
      var on = document.body.classList.contains('par');
      localStorage.setItem('wb_par', on ? '1' : '0');
      if (on){
        // 對讀時把原文與白話兩塊一併打開，否則並列亦無可讀
        Array.prototype.forEach.call(
          document.querySelectorAll('details.art-src, details.art-plain'),
          function(d){ d.open = true; });
      }
      syncP();
    });
  }
  // ── 全文檢索：合冊／分卷 ──────────────────────────────────────
  // 語法：空白分隔多詞（須全部命中）；-詞 排除；"片語" 要求連續。
  // 排序：標題命中 → 精確 → 同義詞 → 模糊；同分依文序。
  // 呈現：側欄結果清單可點擊；Enter 逐處跳，↑↓ 選擇。
  var fbox = document.getElementById('find');
  var finfo = document.getElementById('findinfo');
  var flist = document.getElementById('findlist');
  if (fbox && window.VS){
    var hits = [], cur = -1, sel = -1, timer = null, LIMIT = 3000, SHOW = 200;
    var pqCache = null;

    // 目錄、頁腳等重複區不入檢索，免同一標題命中兩次
    var skipZone = function(el){
      var up = el, d = 0;
      while (up && d < 5){
        if (up.tagName === 'DETAILS' &&
            String(up.className || '').indexOf('art-toc') >= 0) return true;
        if (up.tagName === 'FOOTER' || up.tagName === 'NAV') return true;
        up = up.parentElement; d++;
      }
      return false;
    };
    // 「略白話・原文」範圍：排除每節所附四分律原文與白話摺疊塊
    var inFold = function(el){
      var up = el, d = 0;
      while (up && d < 6){
        if (up.tagName === 'DETAILS'){
          var c = String(up.className || '');
          if (c.indexOf('art-src') >= 0 || c.indexOf('art-plain') >= 0) return true;
        }
        up = up.parentElement; d++;
      }
      return false;
    };

    // 項目標題（<p><strong>D-0002</strong>　…）權重同標題
    var isTitle = function(pe){
      var f = pe.firstElementChild;
      return !!(f && f.tagName === 'STRONG' &&
                /^[DST]-\d{4}$/.test(f.textContent.trim()));
    };

    var collect = function(q){
      var pq = VS.parseQuery(q);
      pqCache = pq;
      if (!pq.n) return [];
      var root = document.getElementById('main') || document.body;
      var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
      var nodes = [], masks = [], exf = [], rank = [], head = [], n;
      while ((n = w.nextNode())){
        var pe = n.parentElement;
        if (!pe) continue;
        var tag = pe.tagName;
        if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') continue;
        var scope = window.VS_SCOPE || 'all';
        var isHead = (/^H[2-5]$/.test(tag) || isTitle(pe));
        if ((scope === 'core' && inFold(pe)) || (scope === 'title' && !isHead)){
          nodes.push(n); masks.push(0); exf.push(0); rank.push(0); head.push(0); continue;
        }
        if (skipZone(pe)){
          nodes.push(n); masks.push(0); exf.push(1); rank.push(0); head.push(0); continue;
        }
        // 正規化結果快取於文字節點，第二次查詢起不必重算
        var hay = n._n;
        if (hay === undefined){ hay = n._n = VS.norm(n.data || ''); }
        nodes.push(n);
        if (!hay){ masks.push(0); exf.push(0); rank.push(0); head.push(0); continue; }
        var ex = 0;
        for (var i = 0; i < pq.exc.length; i++){
          if (hay.indexOf(pq.exc[i]) >= 0){ ex = 1; break; }
        }
        var m = 0, r = 0;
        if (!ex){
          for (var j = 0; j < pq.inc.length; j++){
            var rr = VS.matchGroup(hay, pq.inc[j]);
            if (rr){ m |= (1 << j); if (rr > r) r = rr; }
          }
          for (var k = 0; k < pq.phr.length; k++){
            if (hay.indexOf(pq.phr[k]) >= 0){
              m |= (1 << (pq.inc.length + k)); if (r < 1) r = 1;
            }
          }
        }
        masks.push(m); exf.push(ex); rank.push(r);
        head.push(isHead ? 1 : 0);
      }
      var full = (1 << pq.n) - 1;
      var out = [];
      if (pq.n === 1){
        for (var y = 0; y < nodes.length; y++){
          if (!masks[y] || exf[y]) continue;
          out.push({n: nodes[y], s: head[y] ? 0 : rank[y], i: y});
        }
      } else {
        // 多詞：以「鄰近段落群」為一處（同一卡片／同一節內全部命中）
        var W = 40;
        for (var h = 0; h < nodes.length; h++){
          if (!masks[h] || exf[h]) continue;
          var acc = 0, last = h, ok = false, best = 0;
          var end = Math.min(nodes.length, h + W);
          for (var t = h; t < end; t++){
            acc |= masks[t];
            if (rank[t] > best) best = rank[t];
            if ((acc & full) === full){ last = t; ok = true; break; }
          }
          if (ok){
            out.push({n: nodes[h], s: head[h] ? 0 : best, i: h});
            h = last;
          }
          if (out.length >= LIMIT) break;
        }
      }
      out.sort(function(a, b){ return a.s - b.s || a.i - b.i; });
      return out.slice(0, LIMIT);
    };

    var reveal = function(node){
      var el = node.parentElement;
      while (el){
        if (el.tagName === 'DETAILS') el.open = true;
        el = el.parentElement;
      }
    };

    // 往上找最近的前置標題，作為結果的脈絡（篇／節）
    var nearest = function(node, s){
      var el = node.parentElement;
      while (el && el.id !== 'main'){
        var p = el.previousElementSibling;
        while (p){
          if (p.matches && p.matches(s)) return p;
          p = p.previousElementSibling;
        }
        el = el.parentElement;
      }
      return null;
    };

    var go = function(i){
      if (!hits.length) return;
      cur = ((i % hits.length) + hits.length) % hits.length;
      var node = hits[cur].n;
      reveal(node);
      var pe = node.parentElement;
      // 前一次的高亮須先清除，否則逐處巡覽會累積多個 .hitflash
      Array.prototype.forEach.call(document.querySelectorAll('.hitflash'),
        function(x){ x.classList.remove('hitflash'); });
      pe.classList.add('hitflash');
      // 展開 details 會使上方版面變高，瀏覽器的 scroll anchoring 隨之補償，
      // 把剛跳到的位置又推走；此處暫停 anchoring，並於兩帧後再校正一次。
      var de = document.documentElement;
      var oldAnchor = de.style.overflowAnchor;
      var oldBehav = de.style.scrollBehavior;
      de.style.overflowAnchor = 'none';
      // 全站 CSS 有 scroll-behavior:smooth，多次校正會被平滑動畫互相打斷
      de.style.scrollBehavior = 'auto';
      var targetTop = Math.max(80, (window.innerHeight - pe.offsetHeight) / 2);
      var jump = function(){
        var y = pe.getBoundingClientRect().top + window.pageYOffset - targetTop;
        window.scrollTo({top: Math.max(0, y), behavior: 'instant'});
      };
      jump();
      var stable = 0, t0 = Date.now(), lastTry = 0;
      var tick = function(){
        var now = Date.now();
        var d = Math.abs(pe.getBoundingClientRect().top - targetTop);
        if (d <= 8){
          stable++;
        } else {
          stable = 0;
          if (now - lastTry > 120){ lastTry = now; jump(); }
        }
        if (stable < 4 && now - t0 < 6000){ requestAnimationFrame(tick); }
      };
      requestAnimationFrame(tick);
      if (document.fonts && document.fonts.ready){
        document.fonts.ready.then(function(){ setTimeout(jump, 60); });
      }
      setTimeout(function(){ pe.classList.remove('hitflash'); }, 3000);
      setTimeout(function(){
        de.style.overflowAnchor = oldAnchor;
        de.style.scrollBehavior = oldBehav;
      }, 6400);
      sel = -1;
      markSel();
      place();
      finfo.textContent = '第 ' + (cur + 1) + ' / ' + hits.length + ' 處' +
        (hits.length >= LIMIT ? '（已達上限；可切「僅標題・項名」或加長關鍵詞）' : '');
    };

    var esc = function(s){
      return String(s).replace(/[&<>"]/g, function(c){
        return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c];
      });
    };

    var snipOf = function(node){
      var t = String(node.data || '').replace(/\s+/g, ' ').trim();
      if (!t) return '';
      var low = t.toLowerCase(), pos = -1, len = 0;
      var raws = (pqCache && pqCache.raw) || [];
      for (var i = 0; i < raws.length && pos < 0; i++){
        var k = low.indexOf(String(raws[i]).toLowerCase());
        if (k >= 0){ pos = k; len = String(raws[i]).length; }
      }
      if (pos < 0){ pos = 0; len = 0; }
      var a = Math.max(0, pos - 26), b = Math.min(t.length, pos + len + 54);
      return (a > 0 ? '…' : '') + t.slice(a, b) + (b < t.length ? '…' : '');
    };

    var hl = function(text){
      var raws = (pqCache && pqCache.raw) || [];
      var t = String(text), low = t.toLowerCase(), ranges = [];
      for (var i = 0; i < raws.length; i++){
        var r = String(raws[i]); if (!r) continue;
        var k = 0;
        while ((k = low.indexOf(r.toLowerCase(), k)) >= 0){
          ranges.push([k, k + r.length]); k += r.length;
        }
      }
      if (!ranges.length) return esc(t);
      ranges.sort(function(a, b){ return a[0] - b[0]; });
      var merged = [], last = null;
      for (var j = 0; j < ranges.length; j++){
        if (last && ranges[j][0] <= last[1]) last[1] = Math.max(last[1], ranges[j][1]);
        else { last = ranges[j].slice(); merged.push(last); }
      }
      var out = '', p = 0;
      for (var m = 0; m < merged.length; m++){
        out += esc(t.slice(p, merged[m][0])) + '<mark>' +
               esc(t.slice(merged[m][0], merged[m][1])) + '</mark>';
        p = merged[m][1];
      }
      return out + esc(t.slice(p));
    };

    var render = function(){
      if (!flist) return;
      flist.innerHTML = '';
      if (!hits.length){ flist.hidden = true; return; }
      var n = Math.min(hits.length, SHOW);
      var frag = document.createDocumentFragment();
      for (var i = 0; i < n; i++){
        var node = hits[i].n;
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'fl-item'; b.setAttribute('data-i', i);
        var h5 = nearest(node, 'h5'), h4 = nearest(node, 'h4'), h3 = nearest(node, 'h3');
        var ctx = [h3 ? h3.textContent.trim() : '', h4 ? h4.textContent.trim() : '',
                   h5 ? h5.textContent.trim() : ''].filter(Boolean).join('　›　');
        var aid = nearest(node, 'a[id^="d-"],a[id^="s-"]');
        var idTxt = aid ? aid.id.toUpperCase() : '';
        b.innerHTML = (idTxt ? '<span class="fl-p">' + esc(idTxt) + '</span>' : '') +
                      '<span class="fl-t">' + hl(snipOf(node) || node.data || '') + '</span>' +
                      (ctx ? '<span class="fl-c">' + esc(ctx) + '</span>' : '');
        b.addEventListener('click', (function(idx){
          return function(){ go(idx); };
        })(i));
        frag.appendChild(b);
      }
      flist.appendChild(frag);
      if (hits.length > SHOW){
        var more = document.createElement('button');
        more.type = 'button'; more.className = 'fl-load';
        more.textContent = '載入更多（已列 ' + SHOW + ' / ' + hits.length + ' 處）';
        more.addEventListener('click', function(){ SHOW += 200; render(); });
        flist.appendChild(more);
      }
      var site = document.createElement('a');
      site.className = 'fl-more fl-site';
      var isFull = /五部律差異對照本\.html$/.test(location.pathname);
      site.href = (isFull ? 'index.html?q=' : '五部律差異對照本.html?q=') +
                  encodeURIComponent(fbox.value.trim());
      site.textContent = isFull ? '回到首頁重新檢索 →' : '在全書中全文檢索此詞 →';
      flist.appendChild(site);
      place();
      flist.hidden = false;
    };

    // 面板浮動於側欄之上，避免被 nav 的 overflow 裁切
    var place = function(n){
      n = n || 0;
      var r = fbox.getBoundingClientRect();
      // 版面未定（字體或長頁重排）時 rect 可能為 0，稍候再試
      if (r.bottom < 10 && n < 40){
        requestAnimationFrame(function(){ place(n + 1); });
        return;
      }
      flist.style.left = Math.max(8, r.left) + 'px';
      flist.style.top = (r.bottom + 4) + 'px';
      flist.style.width = Math.min(440, window.innerWidth - 16) + 'px';
      var below = window.innerHeight - r.bottom - 12;
      flist.style.maxHeight = Math.max(160, Math.min(480, below)) + 'px';
    };

    var markSel = function(){
      if (!flist || flist.hidden) return;
      var items = flist.querySelectorAll('.fl-item');
      for (var i = 0; i < items.length; i++){
        if (i === sel){
          items[i].classList.add('sel');
          items[i].scrollIntoView({block: 'nearest'});
        } else {
          items[i].classList.remove('sel');
        }
      }
    };

    var run = function(jump){
      var q = fbox.value.trim();
      sel = -1;
      if (q.length < 1){
        hits = []; cur = -1; finfo.textContent = '';
        if (flist) flist.hidden = true;
        return;
      }
      var key = q + '|' + (window.VS_SCOPE || 'all');
      if (key !== run.last){ hits = collect(q); cur = -1; run.last = key; }
      if (!hits.length){
        if (flist) flist.hidden = true;
        var tip = (q.indexOf('-') >= 0 || q.indexOf('"') >= 0)
          ? '（請檢查 -排除 與 "片語" 之語法）'
          : (q.split(/\s+/).length > 1 ? '（多詞須全部命中，可減少詞數）' : '');
        finfo.textContent = '「' + q + '」：0 處' + tip;
        return;
      }
      render();
      if (jump){ go(cur + 1); }
      else { finfo.textContent = '「' + q + '」：' + hits.length + ' 處（Enter 跳至首處）'; }
    };

    fbox.addEventListener('input', function(){
      clearTimeout(timer);
      timer = setTimeout(function(){ run(false); }, 300);
    });
    fbox.addEventListener('keydown', function(e){
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp'){
        if (!hits.length) return;
        e.preventDefault();
        var n = Math.min(hits.length, SHOW);
        sel = e.key === 'ArrowDown' ? (sel + 1) % n : (sel <= 0 ? n - 1 : sel - 1);
        markSel();
        return;
      }
      if (e.key === 'Enter'){ e.preventDefault(); if (sel >= 0) go(sel); else run(true); }
      if (e.key === 'Escape'){
        fbox.value = ''; hits = []; cur = -1; sel = -1; finfo.textContent = '';
        if (flist) flist.hidden = true;
      }
    });
    fbox.addEventListener('focus', function(){
      if (hits.length && flist){ place(); flist.hidden = false; }
    });
    window.addEventListener('resize', function(){ if (flist && !flist.hidden) place(); });
    window.addEventListener('scroll', function(){ if (flist && !flist.hidden) place(); }, true);
    document.addEventListener('click', function(e){
      if (flist && !flist.hidden && !flist.contains(e.target) && e.target !== fbox){
        flist.hidden = true;
      }
    });
    // 由首頁或外部連結 ?q= 帶入，自動執行一次
    (function(){
      var m = (location.search || '').match(/[?&]q=([^&]*)/);
      if (!m) return;
      var q0 = '';
      try { q0 = decodeURIComponent(m[1].replace(/\+/g, ' ')); } catch (err){ return; }
      if (!q0) return;
      fbox.value = q0;
      setTimeout(function(){ run(true); }, 260);
    })();
    // 供 COMMON_JS 之 F3／Shift+F3 逐處巡覽
    window.VS_API = {
      next: function(d){ if (hits.length) go((cur + d + hits.length) % hits.length); },
      count: function(){ return hits.length; }
    };
  }
  // 列印前自動展開全部折疊（CSS 對 closed details 的內容未必生效），列印後復原
  (function(){
    var saved = null;
    var openAll = function(){
      var ds = document.querySelectorAll('details');
      saved = Array.prototype.map.call(ds, function(d){ return d.open; });
      Array.prototype.forEach.call(ds, function(d){ d.open = true; });
    };
    var restore = function(){
      if (!saved) return;
      var ds = document.querySelectorAll('details');
      Array.prototype.forEach.call(ds, function(d, i){
        if (i < saved.length) d.open = saved[i];
      });
      saved = null;
    };
    window.addEventListener('beforeprint', openAll);
    window.addEventListener('afterprint', restore);
  })();
})();
"""

JS = JS.replace('__SEARCH_CORE__', SEARCH_CORE)


# ── 全站共用：快捷鍵 + 側邊欄增強（合冊／分卷／首頁／矩陣／專題表）──────
SHORTCUT_JS = r"""
(function(){
  var focusSearch = function(){
    var el = document.getElementById('find') || document.getElementById('homeq') ||
             document.getElementById('q') ||
             document.querySelector('main input[type=search]') ||
             document.querySelector('input[type=search]');
    if (!el) return;
    // 窄屏時搜尋框在抽屜內，先開抽屜再聚焦
    if (window.innerWidth <= 1100 && el.closest && el.closest('nav')){
      document.body.classList.add('navopen');
    }
    el.focus(); if (el.select) el.select();
  };
  var rf = document.getElementById('refresh');
  if (rf) rf.addEventListener('click', function(e){
    e.preventDefault();
    location.replace(location.pathname + '?_=' + Date.now() + (location.hash || ''));
  });
  document.addEventListener('keydown', function(e){
    var ae = document.activeElement || {};
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName || '');
    if (!typing && e.key === '/'){ e.preventDefault(); focusSearch(); return; }
    if ((e.ctrlKey || e.metaKey) && String(e.key).toLowerCase() === 'k'){
      e.preventDefault(); focusSearch(); return;
    }
    if (e.key === 'F3'){
      e.preventDefault();
      if (window.VS_API && window.VS_API.count()) window.VS_API.next(e.shiftKey ? -1 : 1);
      else focusSearch();
      return;
    }
    if (e.altKey && String(e.key).toLowerCase() === 'n'){
      e.preventDefault();
      if (window.innerWidth <= 1100){
        document.body.classList.toggle('navopen');
      } else {
        var el = document.getElementById('navtoggle');
        var c = !document.body.classList.contains('navclosed');
        document.body.classList.toggle('navclosed', c);
        if (el) el.style.left = '0px';
        try { localStorage.setItem('wb_nav_closed', c ? '1' : '0'); } catch(err){}
      }
      return;
    }
    if (e.key === 'Escape' && document.body.classList.contains('navopen')){
      document.body.classList.remove('navopen');
    }
  });
})();
"""

SIDEBAR_JS = r"""
(function(){
  var nav = document.querySelector('nav');
  if (!nav) return;
  var KEY = 'wb_nav_' + location.pathname.split('/').pop();
  var dts = Array.prototype.slice.call(nav.querySelectorAll('details.navj'));
  var links = Array.prototype.slice.call(nav.querySelectorAll('a'))
    .filter(function(a){ return !(a.parentElement && a.parentElement.tagName === 'H1'); });

  // 一、目錄摺疊狀態記憶（按頁分別存）
  var saved = null;
  try { saved = JSON.parse(localStorage.getItem(KEY + '_open') || 'null'); } catch(e){}
  if (saved) dts.forEach(function(d, i){ if (i < saved.length) d.open = !!saved[i]; });
  var saveOpen = function(){
    try { localStorage.setItem(KEY + '_open',
      JSON.stringify(dts.map(function(d){ return d.open; }))); } catch(e){}
  };
  nav.addEventListener('click', function(e){
    var t = e.target;
    if (t && (t.tagName === 'SUMMARY' ||
        (t.parentElement && t.parentElement.tagName === 'SUMMARY'))){
      setTimeout(saveOpen, 0);
    }
  });

  // 二、目錄過濾：輸入即篩篇名／節名，命中之所屬卷自動展開
  var f = document.getElementById('navfilter');
  var info = document.getElementById('navfinfo');
  if (f && window.VS){
    var apply = function(){
      var q = f.value.trim(), nq = q ? VS.norm(q) : '', shown = 0;
      dts.forEach(function(d){ d.classList.remove('filtered'); });
      links.forEach(function(a){
        var ok = !nq || VS.norm(a.textContent).indexOf(nq) >= 0;
        a.classList.toggle('filtered', !ok);
        if (ok) shown++;
      });
      if (nq){
        dts.forEach(function(d){
          var kids = d.querySelectorAll('a'), any = false;
          for (var i = 0; i < kids.length; i++){
            if (!kids[i].classList.contains('filtered')){ any = true; break; }
          }
          var sum = d.querySelector('summary');
          var self = sum && VS.norm(sum.textContent).indexOf(nq) >= 0;
          if (self){
            // 篇名／卷名在 <summary> 而非 <a>；命中時展開其下所有節，並計入可見數
            Array.prototype.forEach.call(kids, function(a){
              if (a.classList.contains('filtered')) shown++;
              a.classList.remove('filtered');
            });
            any = true;
          }
          d.classList.toggle('filtered', !any && !self);
          if (!d.classList.contains('filtered')) d.open = true;
        });
      }
      if (info){
        info.textContent = !nq ? '' :
          (shown ? ('符合 ' + shown + ' 項（Esc 清除）') : '無符合項（Esc 清除）');
        info.classList.toggle('none', !!nq && !shown);
      }
    };
    // 中文輸入法：拼音階段會連發 input，等 compositionend 再篩，免目錄逐鍵閃動
    var composing = false, ftimer = null;
    f.addEventListener('compositionstart', function(){ composing = true; });
    f.addEventListener('compositionend', function(){ composing = false; apply(); });
    f.addEventListener('input', function(){
      if (composing) return;
      clearTimeout(ftimer);
      ftimer = setTimeout(apply, 120);
    });
    f.addEventListener('keydown', function(e){
      if (e.key === 'Escape'){ f.value = ''; apply(); f.blur(); }
    });
  }

  // 二之一、捲動位置記憶（按頁）
  try {
    var _st = parseInt(localStorage.getItem(KEY + '_scroll') || '0', 10);
    if (_st > 0) nav.scrollTop = _st;
  } catch(e){}
  var _stTimer = null;
  nav.addEventListener('scroll', function(){
    clearTimeout(_stTimer);
    _stTimer = setTimeout(function(){
      try { localStorage.setItem(KEY + '_scroll', String(Math.round(nav.scrollTop))); } catch(e){}
    }, 250);
  }, {passive:true});

  // 二之二、目錄層級的「全部展開／收起」
  var na = document.getElementById('navall');
  if (na) na.addEventListener('click', function(){
    var ds = nav.querySelectorAll('details.navj'), anyClosed = false;
    for (var i = 0; i < ds.length; i++){ if (!ds[i].open){ anyClosed = true; break; } }
    for (var j = 0; j < ds.length; j++) ds[j].open = anyClosed;
    na.textContent = anyClosed ? '全部收起' : '全部展開';
    na.setAttribute('aria-pressed', String(anyClosed));
  });

  // 三、捲動時自動展開當前位置所屬卷，並把該項捲入側欄可視區。
  // 使用者正在側欄內捲動／滑鼠停留時不打斷，避免目錄自己亂跳。
  var tick = null, navBusyUntil = 0, autoScrolling = false;
  nav.addEventListener('wheel', function(){ navBusyUntil = Date.now() + 5000; }, {passive:true});
  nav.addEventListener('scroll', function(){
    if (!autoScrolling) navBusyUntil = Date.now() + 5000;
  }, {passive:true});
  window.addEventListener('scroll', function(){
    if (tick) return;
    tick = setTimeout(function(){
      tick = null;
      if (Date.now() < navBusyUntil || nav.matches(':hover')) return;
      var on = nav.querySelector('a.on');
      if (!on) return;
      var d = on.parentElement;
      while (d && d !== nav){ if (d.tagName === 'DETAILS') d.open = true; d = d.parentElement; }
      var r = on.getBoundingClientRect(), nr = nav.getBoundingClientRect();
      if (r.top < nr.top + 40 || r.bottom > nr.bottom - 40){
        autoScrolling = true;
        nav.scrollTop += (r.top - nr.top) - nav.clientHeight / 3;
        setTimeout(function(){ autoScrolling = false; }, 80);
      }
    }, 180);
  }, {passive:true});

  // 四、拖曳調寬（220–520px），寬度記憶
  var rz = document.createElement('div');
  rz.id = 'navresizer'; rz.title = '拖曳調整側欄寬度';
  nav.appendChild(rz);
  var W = 280;
  try { W = parseInt(localStorage.getItem('wb_nav_w') || '280', 10) || 280; } catch(e){}
  var setW = function(w){
    w = Math.max(220, Math.min(520, w));
    nav.style.width = w + 'px'; nav.style.flexBasis = w + 'px';
    rz.style.left = (w - 3) + 'px';
    var t = document.getElementById('navtoggle');
    if (t && !document.body.classList.contains('navclosed')) t.style.left = w + 'px';
  };
  if (window.innerWidth > 1100) setW(W);
  var dragging = false;
  rz.addEventListener('pointerdown', function(e){
    dragging = true; rz.setPointerCapture(e.pointerId); e.preventDefault();
  });
  rz.addEventListener('pointermove', function(e){ if (dragging) setW(e.clientX); });
  rz.addEventListener('pointerup', function(){
    if (!dragging) return; dragging = false;
    try { localStorage.setItem('wb_nav_w', String(parseInt(nav.style.width, 10) || 280)); } catch(e){}
  });

  // 五、桌面收起／展開；窄屏抽屜（漢堡 + 遮罩）
  var tg = document.createElement('button');
  tg.id = 'navtoggle'; tg.type = 'button'; tg.textContent = '側欄';
  tg.setAttribute('aria-label', '收起或展開側邊欄（Alt+N）');
  document.body.appendChild(tg);
  var setClosed = function(c){
    document.body.classList.toggle('navclosed', c);
    tg.style.left = '0px';
    try { localStorage.setItem('wb_nav_closed', c ? '1' : '0'); } catch(e){}
  };
  try { if (localStorage.getItem('wb_nav_closed') === '1') document.body.classList.add('navclosed'); } catch(e){}
  var nh = document.getElementById('navhide');
  if (!nh){
    nh = document.createElement('button');
    nh.id = 'navhide'; nh.type = 'button'; nh.textContent = '收起側欄';
    nh.title = '收起側邊欄（Alt+N）';
    nh.style.marginTop = '.4rem';
    nav.appendChild(nh);
  }
  nh.addEventListener('click', function(){ if (window.innerWidth > 1100) setClosed(true); });
  tg.addEventListener('click', function(){
    if (window.innerWidth <= 1100){ document.body.classList.remove('navopen'); return; }
    setClosed(!document.body.classList.contains('navclosed'));
  });
  var burger = document.createElement('button');
  burger.id = 'navburger'; burger.type = 'button'; burger.innerHTML = '☰';
  burger.setAttribute('aria-label', '開啟側邊欄（Alt+N）');
  document.body.appendChild(burger);
  var mask = document.createElement('div');
  mask.id = 'navmask'; document.body.appendChild(mask);
  burger.addEventListener('click', function(){ document.body.classList.toggle('navopen'); });
  mask.addEventListener('click', function(){ document.body.classList.remove('navopen'); });
  nav.addEventListener('click', function(e){
    if (window.innerWidth <= 1100 && e.target.tagName === 'A' &&
        e.target.getAttribute('href')){
      setTimeout(function(){ document.body.classList.remove('navopen'); }, 120);
    }
  });
})();
"""

COMMON_JS = SHORTCUT_JS + SIDEBAR_JS

NAV_FILTER_HTML = (
    '<div class="navfilterwrap">'
    '<label for="navfilter" class="sr-only">過濾目錄</label>'
    '<input type="search" id="navfilter" placeholder="篩選　篇名／戒名" '
    'autocomplete="off" aria-label="過濾側邊欄目錄">'
    '<div id="navfinfo" role="status" aria-live="polite"></div></div>'
)

# ── 合冊／分卷專用：範圍、說明、歷史、同義詞提示 ─────────────────────
FIND_EXTRA = r"""
(function(){
  var fbox = document.getElementById('find');
  if (!fbox || !window.VS) return;

  // 檢索範圍
  var opts = document.querySelectorAll('.findopts button');
  Array.prototype.forEach.call(opts, function(b){
    b.addEventListener('click', function(){
      Array.prototype.forEach.call(opts, function(x){ x.setAttribute('aria-pressed', 'false'); });
      b.setAttribute('aria-pressed', 'true');
      window.VS_SCOPE = b.getAttribute('data-scope');
      fbox.dispatchEvent(new Event('input', {bubbles: true}));
      fbox.focus();
    });
  });

  // 語法說明
  var hb = document.getElementById('findhelpbtn'), hp = document.getElementById('findhelp');
  if (hb && hp){
    hb.addEventListener('click', function(){
      hp.hidden = !hp.hidden;
      hb.setAttribute('aria-expanded', String(!hp.hidden));
    });
  }

  // 近期檢索（localStorage，最多 8 筆）
  var hist = document.getElementById('findhist'), HKEY = 'wb_find_hist';
  var getH = function(){ try { return JSON.parse(localStorage.getItem(HKEY) || '[]'); } catch(e){ return []; } };
  var setH = function(a){ try { localStorage.setItem(HKEY, JSON.stringify(a.slice(0, 8))); } catch(e){} };
  var drawH = function(){
    if (!hist) return;
    var a = getH(); hist.innerHTML = '';
    if (!a.length) return;
    var lab = document.createElement('span'); lab.textContent = '近期：'; hist.appendChild(lab);
    a.forEach(function(q){
      var b = document.createElement('button'); b.type = 'button'; b.textContent = q;
      b.title = '套用此檢索詞';
      b.addEventListener('click', function(){
        fbox.value = q; fbox.dispatchEvent(new Event('input', {bubbles: true})); fbox.focus();
      });
      hist.appendChild(b);
    });
    var c = document.createElement('button'); c.type = 'button'; c.textContent = '清除';
    c.addEventListener('click', function(){ setH([]); drawH(); });
    hist.appendChild(c);
  };
  drawH();
  fbox.addEventListener('keydown', function(e){
    if (e.key !== 'Enter') return;
    var q = fbox.value.trim(); if (q.length < 2) return;
    var a = getH().filter(function(x){ return x !== q; }); a.unshift(q); setH(a); drawH();
  });

  // 同義詞提示：查「波逸提」時提示「單提」等別名
  var info = document.getElementById('findinfo');
  fbox.addEventListener('input', function(){
    setTimeout(function(){
      var q = fbox.value.trim();
      if (!q || !info || info.textContent.indexOf('同義詞') >= 0) return;
      var pq = VS.parseQuery(q), alts = [];
      for (var i = 0; i < pq.inc.length; i++){
        var g = pq.inc[i];
        for (var j = 1; j < g.length; j++){
          if (alts.indexOf(g[j]) < 0) alts.push(g[j]);
        }
      }
      if (alts.length) info.textContent += '　·　同義詞：' + alts.join('、');
    }, 360);
  });
})();
"""



_CN_D = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
         '六': 6, '七': 7, '八': 8, '九': 9}


def cn2num(s):
    """中文數字轉阿拉伯數字，支援「二十四」「一百七十八」等複合式。"""
    s = (s or '').strip()
    if not s:
        return 0
    if s == '十':
        return 10
    if '百' in s:
        a, _, b = s.partition('百')
        n = (_CN_D.get(a, 1) if a else 1) * 100
        if not b:
            return n
        if b == '十':
            return n + 10
        if '十' in b:
            c, _, d = b.partition('十')
            return n + (_CN_D.get(c, 1) if c else 1) * 10 + _CN_D.get(d, 0)
        return n + _CN_D.get(b, 0)
    if '十' in s:
        a, _, b = s.partition('十')
        return (_CN_D.get(a, 1) if a else 1) * 10 + _CN_D.get(b, 0)
    return _CN_D.get(s, 0)


def build_nav(md_text, is_full, cur=None):
    """從 Markdown 提取目錄結構，生成側邊欄。

    末尾輸出 <div class="navdock"> 的開始標籤但不閉合：常用控件（分卷前後、
    回目錄、展開收合、跳項號）由 md_to_html 的模板接著放進去，成為
    position:sticky;bottom:0 的固定工具區，捲目錄時不會跟著跑掉。
    """
    parts = []
    dock = []
    parts.append('<h1><a href="index.html">五部律差異對照本</a></h1>')
    parts.append('<div class="nsub">以四分律為軸　五部對校</div>')
    parts.append('<!--SEARCH-->')
    parts.append('<div class="navhead"><b>目錄</b>'
                 '<button type="button" id="navall" aria-pressed="false" '
                 'title="展開或收起全部卷次">全部展開</button></div>')
    parts.append(NAV_FILTER_HTML)
    parts.append('<div class="grp"><a href="index.html" class="navhome">'
                 '←　目錄與說明</a></div>')

    # 分卷檔加前後卷導覽：單篇成檔時，讀者從搜尋引擎進來會成孤島
    _names = [j for j, _f in JUAN]
    if cur in _names:
        _i = _names.index(cur)
        _prev = _names[_i - 1] if _i > 0 else None
        _next = _names[_i + 1] if _i + 1 < len(_names) else None
        if _prev or _next or True:
            dock.append('<div class="docklinks">')
            if _prev:
                dock.append(f'<a href="五部律差異對照本_{htmlmod.escape(_prev)}.html" '
                            f'title="上一卷：{htmlmod.escape(_prev)}">← 前卷</a>')
            if _next:
                dock.append(f'<a href="五部律差異對照本_{htmlmod.escape(_next)}.html" '
                            f'title="下一卷：{htmlmod.escape(_next)}">後卷 →</a>')
            dock.append('<a href="index.html" title="回目錄與說明">目錄</a>')
            dock.append('<a href="#" id="refresh" title="強制重新抓取本頁（破快取）">↻ 更新</a>')
            dock.append('</div>')

    if is_full:
        # 合冊：卷次下嵌該卷篇目（可折疊）
        parts.append('<div class="grp"><b>第一部　按四分篇次</b>')
        # 依「### 卷次」切段，取每段內的 #### 篇
        secs = re.split(r'^### ', md_text, flags=re.M)
        for sec in secs[1:]:
            head = sec.split('\n', 1)[0].strip()
            if not head.startswith('卷'):
                continue
            arts = re.findall(r'^#### (\d{3})　([^\n]+)$', sec, re.M)
            if not arts:
                continue
            parts.append(f'<details class="navj"><summary>{htmlmod.escape(head)}'
                         f'<span class="jcnt">{len(arts)}</span></summary>')
            for n, title in arts:
                t = htmlmod.escape(re.sub(r'<[^>]+>', '', title))
                parts.append(f'<a href="#p{n}" class="art">'
                             f'<span class="pno">{n}</span><span class="pt">{t}</span></a>')
            parts.append('</details>')
        parts.append('</div>')
        parts.append('<div class="grp"><b>第二部　四分所無</b>')
        for c in ['五分', '十誦', '僧祇', '根有']:
            parts.append(f'<a href="#add{c}">{c}所增</a>')
        parts.append('</div>')
        parts.append('<div class="grp"><b>第三部　歸併組</b>')
        parts.append('<a href="#gt-g">甲、同條歸併七組</a>')
        parts.append('<a href="#gt-t">乙、同題異制三組</a>')
        parts.append('</div>')
        parts.append('<div class="grp"><b>附錄</b>')
        parts.append('<a href="#ap1">一、歸位方法</a>')
        parts.append('<a href="#ap2">二、分部統計</a>')
        parts.append('<a href="#ap3">三、篇目卷次</a>')
        parts.append('</div>')
    else:
        # 分卷：列該卷各篇；有戒條者折疊展開，便於直達
        parts.append('<div class="grp"><b>本卷篇目</b>')
        secs = re.split(r'(?=^#### \d{3}　)', md_text, flags=re.M)
        for sec in secs:
            m = re.match(r'^#### (\d{3})　([^\n]+)', sec)
            if not m:
                continue
            n, title = m.group(1), m.group(2)
            t = htmlmod.escape(re.sub(r'<[^>]+>', '', title))
            units = re.findall(r'<a id="u(\d{3})-(\d+)"></a>\s*\n+\s*##### ([^\n]+)', sec)
            if units:
                parts.append(f'<details class="navj"><summary>{n}　{t}'
                             f'<span class="jcnt">{len(units)}</span></summary>')
                for pn, a, lbl in units:
                    lbl = htmlmod.escape(re.sub(r'<[^>]+>', '', lbl).strip()) or f'段{a}'
                    parts.append(f'<a href="#u{pn}-{a}" class="jie">{lbl}</a>')
                parts.append('</details>')
            else:
                parts.append(f'<a href="#p{n}" class="art">'
                             f'<span class="pno">{n}</span><span class="pt">{t}</span></a>')
        parts.append('</div>')

    if is_full:
        dock.append('<div class="docklinks">'
                    '<a href="index.html" title="回目錄與說明">目錄</a>'
                    '<a href="#" id="refresh" title="強制重新抓取本頁（破快取）">↻ 更新</a>'
                    '</div>')

    parts.append('<div class="navdock">')
    parts.extend(dock)
    return '\n'.join(parts)


def juan_id(name):
    return 'juan-' + str(abs(hash(name)) % 100000)


def md_to_html(md_path, out_path, title, is_full, md_text=None):
    if md_text is None:
        md_text = open(md_path, encoding='utf-8').read()

    # pandoc：gfm → html5 片段（不帶 standalone，我們自己包）
    p = subprocess.run(
        [_pandoc_exe(), '-f', 'gfm', '-t', 'html5', '--no-highlight'],
        input=md_text.encode('utf-8'), capture_output=True
    )
    if p.returncode != 0:
        print('pandoc 失敗：', p.stderr.decode('utf-8')[:400])
        return False
    # pandoc 在 Windows 上輸出 CRLF；此處先歸 LF，寫檔時亦不再轉換，
    # 否則 text mode 會把 \n 再轉成 \r\n，成 \r\r\n（雙重回車）。
    body = p.stdout.decode('utf-8').replace('\r\n', '\n')
    # 寬表（附錄統計等）在窄屏會撐破版面：外包一層可橫向捲動的容器
    body = re.sub(r'<table>.*?</table>',
                  lambda m: '<div class="tscroll">' + m.group(0) + '</div>',
                  body, flags=re.S)

    _cur = None
    if not is_full:
        _b = os.path.basename(out_path)
        if _b.startswith('五部律差異對照本_') and _b.endswith('.html'):
            _c = _b[len('五部律差異對照本_'):-5]
            if any(_c == _j for _j, _f in JUAN):
                _cur = _c
    nav = build_nav(md_text, is_full, _cur)
    # 檢索框置於站名之後、目錄之前，並隨側欄吸附
    nav = nav.replace('<!--SEARCH-->', SEARCH_BOX, 1)

    # 分卷頁不含卷首凡例，故於正文前附一則小凡例，免〔十誦 A〕一類標記無所解
    _banner = '' if is_full else """
<details class="art-toc" style="margin:.4rem 0 1.4rem">
<summary>本卷凡例（狀態代號、項號與錨點）</summary>
<p><b>狀態</b>　<b>A</b> 同條增異——同條而內容有實質差異（判罪輕重、程序先後、法數多寡、人物結局）；
<b>B</b> 同條開緣——同條而另立開許或新增限制；<b>C</b> 四分所無——四分律無此戒此制而他部有之；
<b>D</b> 同條減略。四目沿用各稿原判，A 與 D 之界不嚴，讀者當以「差異說明」為準。</p>
<p><b>〔某律 X〕</b>　方括號內為該項所屬之律與狀態，如「〔十誦 A〕」謂此項出十誦、狀態為 A。</p>
<p><b>項號</b>　<code>D-</code> 屬第一部（按四分篇次），<code>S-</code> 屬第二部（按所屬律），
<code>M-</code> 為矩陣編號。項號全書連續，可跨卷徑引。</p>
<p><b>錨點</b>　<code>#p008</code> 為篇、<code>#u008-24</code> 為節、<code>#d-0201</code> 為項，可作外部深鏈。</p>
<p><b>全書凡例</b>　見<a href="五部律差異對照本.html">合冊</a>卷首（名義、引文、狀態、錨點、文本處理凡十四條）。</p>
</details>
"""
    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>{htmlmod.escape(title)}</title>
<meta name="author" content="UncleHandsome">
<meta name="description" content="以《四分律》為軸，對校《五分律》《十誦律》《摩訶僧祇律》《根本說一切有部毘奈耶》五部廣律之逐項差異對照本。">
<meta name="keywords" content="四分律,五分律,十誦律,摩訶僧祇律,根本說一切有部毘奈耶,律藏,戒律,對照本,vinaya">
<link rel="canonical" href="{SITE_URL}">
<meta name="citation_title" content="{htmlmod.escape(title)}">
<meta name="citation_author" content="UncleHandsome">
<meta name="citation_publication_date" content="{_DATE}">
<meta name="citation_language" content="zh-Hant">
<meta name="citation_fulltext_html_url" content="{SITE_URL}">
<meta name="DC.title" content="{htmlmod.escape(title)}">
<meta name="DC.creator" content="UncleHandsome">
<meta name="DC.date" content="{_DATE}">
<meta name="DC.language" content="zh-Hant">
<meta name="DC.rights" content="CC BY-NC-SA 4.0">
<meta property="og:type" content="article">
<meta property="og:site_name" content="五部律差異對照本">
<meta property="og:title" content="{htmlmod.escape(title)}">
<meta property="og:description" content="以四分律為底本，橫向比對五分律、十誦律、摩訶僧祇律、根本說一切有部毘奈耶之戒條與制度差異。">
<meta property="og:locale" content="zh_TW">
<meta property="og:url" content="{SITE_URL}">
<meta name="twitter:card" content="summary">
{_jsonld(title)}
<style>{CSS}</style>
</head>
<body>
<a id="top-anchor"></a>
<div class="wrap">
<nav>
{nav}
<div class="navtools">
<button type="button" id="toggle" aria-controls="main" title="展開或收起正文全部摺疊塊">展開／收起</button>
<button type="button" id="width" title="切換寬屏／舒適寬度">寬屏</button>
<button type="button" id="par" aria-pressed="false" title="四分原文與白話左右並列">對讀</button>
<button type="button" id="navhide" title="收起側邊欄（Alt+N）">收起</button>
</div>
<div class="grp" style="padding:.4rem 1rem 0">
<label for="jump" class="sr-only">跳至指定編號</label>
<input type="text" id="jump" placeholder="跳至 D-0450" aria-label="跳至指定編號，如 D-0450"
  style="width:100%;padding:.28rem .5rem;border:1px solid var(--line);border-radius:3px;
  font-size:12.5px;font-family:inherit;background:#fff">
</div>
</div><!-- /.navdock -->
</nav>
<main id="main">
{_banner}
{body}
{FOOTER}
</main>
</div>
<a href="#top-anchor" id="top" aria-label="回到頂部">↑</a>
<script>{JS}</script>
<script>{COMMON_JS}</script>
<script>{FIND_EXTRA}</script>
</body>
</html>"""
    open(out_path, 'w', encoding='utf-8', newline='\n').write(page)
    return True


def _a5_pairs():
    """附錄五共戒對位組數（讀生成物，免寫死）。"""
    p = os.path.join(BASE, 'appendix5.md')
    if not os.path.exists(p):
        return 0
    t = open(p, encoding='utf-8').read().split('#### 附錄五之二')[0]
    return max(0, sum(1 for l in t.splitlines()
                      if l.startswith('| ') and '---' not in l) - 1)


def _plain(s):
    """去 Markdown 標記，留純文字（供索引摘要）。"""
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('**', '').replace('`', '').replace('\\', '')
    return re.sub(r'\s+', ' ', s).strip()


def build_search_index():
    """全站索引：篇／節／項三級，供首頁即時檢索（不載合冊）。

    每筆 [類, 編號, 標題, 摘要, 連結, 脈絡]。
    類：p 篇、u 節、d/s 項、g 歸併組、x 專題頁。
    """
    recs = []
    for jname, fn in JUAN:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            continue
        page = fn.replace('.md', '.html')
        lines = open(p, encoding='utf-8').read().split('\n')
        pian_no = pian = ''
        jie = ''
        pend = ''
        pian_idx = None
        for i, ln in enumerate(lines):
            m = re.match(r'^<a id="(u\d{3}-\d+)"></a>$', ln)
            if m:
                pend = m.group(1)
                continue
            m = re.match(r'^#### (\d{3})\u3000(.+)$', ln)
            if m:
                pian_no, pian = m.group(1), _plain(m.group(2))
                snip = ''
                for k in range(i + 1, min(i + 10, len(lines))):
                    if lines[k].startswith('> **篇旨**'):
                        snip = _plain(lines[k].split('：', 1)[-1])[:78]
                        break
                recs.append(['p', pian_no, f'{pian_no}　{pian}', snip, page + '#', ''])
                pian_idx = len(recs) - 1
                jie = ''
                continue
            m = re.match(r'^#### `([GT]\d+)`\u3000(.+)$', ln)
            if m:
                gid, gtitle = m.group(1), _plain(m.group(2))
                recs.append(['g', gid, gtitle, '', f'{page}#gt-{gid}', '第三部　歸併組'])
                continue
            m = re.match(r'^##### (.+)$', ln)
            if m:
                jie = _plain(m.group(1))
                anchor = pend or ''
                if pian_idx is not None and recs[pian_idx][4].endswith('#'):
                    recs[pian_idx][4] += anchor
                recs.append(['u', anchor or f'u{pian_no}', jie, '',
                             page + ('#' + anchor if anchor else ''),
                             f'{pian_no}　{pian}'])
                pend = ''
                continue
            m = re.match(r'^\*\*([DST]-\d{4})\*\*\u3000(.+)$', ln)
            if m:
                rid, title = m.group(1), _plain(m.group(2))
                snip = ''
                for k in range(i + 1, min(i + 26, len(lines))):
                    nxt = lines[k]
                    if nxt.startswith('- '):
                        snip = _plain(nxt[2:])[:86]
                        break
                    if (re.match(r'^\*\*[DST]-\d{4}\*\*', nxt) or
                            nxt.startswith('#### ') or nxt.startswith('##### ')):
                        break
                recs.append([rid[0].lower(), rid, title, snip,
                             f'{page}#{rid.lower()}',
                             f'{pian_no}　{pian}' + (f'／{jie}' if jie else '')])
                continue

    # 節摘要：取該節各項標題，供整節層級檢索（單項摘要未含之詞亦可由節命中）
    for i, r in enumerate(recs):
        if r[0] != 'u':
            continue
        ts = []
        for j in range(i + 1, len(recs)):
            if recs[j][0] in ('u', 'p', 'g'):
                break
            if recs[j][0] in ('d', 's'):
                ts.append(recs[j][2])
            if len(ts) >= 10:
                break
        if ts:
            r[3] = '；'.join(ts)[:150]

    recs += [
        ['x', '矩陣', '五部律綜合異同矩陣', '2,124 列，五欄記各律有無，可篩選排序',
         '五部律綜合異同矩陣.html', '專題'],
        ['x', '對照', '比丘／比丘尼戒對照表', '共戒對位 %d 組，附眾學法 58 目' % _a5_pairs(),
         '比丘比丘尼戒對照表.html', '專題表'],
        ['x', '開遮', '五部律開遮持犯表', '657 列，差異導向，五欄記各律有無',
         '五部律開遮持犯表.html', '專題表'],
    ]

    out = os.path.join(OUT, 'search_index.js')
    js = 'window.SIDX=' + json.dumps(recs, ensure_ascii=False,
                                    separators=(',', ':')) + ';\n'
    open(out, 'w', encoding='utf-8', newline='\n').write(js)
    kinds = {}
    for r in recs:
        kinds[r[0]] = kinds.get(r[0], 0) + 1
    print('  索引：%d 筆（%s）%.0f KB' % (
        len(recs), '／'.join(f'{k} {v}' for k, v in sorted(kinds.items())),
        os.path.getsize(out) / 1024))


def build_index():
    """索引頁"""
    _a5 = _a5_pairs()
    rows = []
    for jname, fn in JUAN:
        p = os.path.join(SRC, fn)
        if os.path.exists(p):
            t = open(p, encoding='utf-8').read()
            n = len(re.findall(r'^\*\*D-\d{4}\*\*', t, re.M)) + len(re.findall(r'^\*\*S-\d{4}\*\*', t, re.M))
            rows.append((jname, fn.replace('.md', '.html'), n))

    total = sum(n for _, _, n in rows)
    li = '\n'.join(
        f'<tr><td><a href="{h}">{j}</a></td><td style="text-align:right">{n:,}</td></tr>'
        for j, h, n in rows)

    body = f"""
<h1>五部律差異對照本</h1>
<blockquote><p><strong>以《四分律》為閱讀主線，一冊在手，遍知五部之異同。</strong></p>
<p>讀四分律至某篇某戒，翻至本書同篇，即見其餘四部於此處有何增、減、開、異。</p></blockquote>

<h2>全書檢索</h2>
<form class="homefind" action="五部律差異對照本.html" method="get" role="search">
  <input type="search" name="q" id="homeq" required autocomplete="off"
    placeholder="例：摩那埵 波逸提　或　迦絺那 -四分"
    aria-label="全書檢索：空白分隔多詞，減號排除，引號片語">
  <button type="submit">搜尋</button>
</form>
<p class="hint">支援<strong>多關鍵字</strong>（空白分隔，須全部命中）、
<strong>排除</strong>（<code>-四分</code>）、<strong>片語</strong>（<code>"非親里"</code>），
並容<strong>漏字模糊</strong>（<code>摩埵</code> 可中「摩那埵」）與<strong>名相別名</strong>
（查<code>波逸提</code>亦得「單提」、查<code>捨墮</code>亦得「尼薩耆」）。
送出後於合冊全文檢索並跳至首處；合冊較大，首次載入需數秒。</p>
<div class="tryq"><span>快速試：</span>
<a href="五部律差異對照本.html?q=摩那埵">摩那埵</a>
<a href="五部律差異對照本.html?q=迦絺那%20自恣">迦絺那 自恣</a>
<a href="五部律差異對照本.html?q=%22非親里%22">"非親里"</a>
<a href="五部律差異對照本.html?q=波逸提%20-四分">波逸提 -四分</a>
<a href="五部律差異對照本.html?q=苾芻">苾芻（＝比丘）</a></div>

<h2>五部律</h2>
<table>
<tr><th>律</th><th>部派</th><th>譯者</th><th>大正藏</th><th style="text-align:right">卷數</th></tr>
<tr><td><strong>四分律</strong></td><td>法藏部</td><td>姚秦 佛陀耶舍、竺佛念</td><td>T22, no. 1428</td><td style="text-align:right">60</td></tr>
<tr><td>五分律</td><td>彌沙塞部</td><td>劉宋 佛陀什、竺道生</td><td>T22, no. 1421</td><td style="text-align:right">30</td></tr>
<tr><td>十誦律</td><td>說一切有部</td><td>後秦 弗若多羅、鳩摩羅什</td><td>T23, no. 1435</td><td style="text-align:right">61</td></tr>
<tr><td>摩訶僧祇律</td><td>大眾部</td><td>東晉 佛陀跋陀羅、法顯</td><td>T22, no. 1425</td><td style="text-align:right">40</td></tr>
<tr><td>根本說一切有部毘奈耶</td><td>根本說一切有部</td><td>唐 義淨</td><td>T23, no. 1442</td><td style="text-align:right">50</td></tr>
</table>

<h2>全書</h2>
<table>
<tr><th>卷次</th><th style="text-align:right">項數</th></tr>
<tr><td><a href="五部律差異對照本.html"><strong>合冊（全）</strong></a>
<br><span style="font-size:12px;color:#8a8278">檔案較大，建議用電腦瀏覽</span></td>
<td style="text-align:right">{total:,}</td></tr>
{li}
</table>

<h2>兩本書</h2>
<table>
<tr><th>書</th><th>用途</th></tr>
<tr><td><a href="五部律差異對照本.html"><strong>五部律差異對照本</strong></a></td>
<td>按四分律七十五篇次第讀。每篇有篇旨，每項有差異、原文、他部對照。適合<strong>讀律時查</strong>。</td></tr>
<tr><td><a href="五部律綜合異同矩陣.html"><strong>五部律綜合異同矩陣</strong></a></td>
<td>每列一項，五欄記各律有無。可按狀態、所屬律、層級篩選，適合<strong>查證與統計</strong>。</td></tr>
</table>

<h2>專題表（可搜尋、篩選、排序）</h2>
<table>
<tr><th>表</th><th>內容</th></tr>
<tr><td><a href="比丘比丘尼戒對照表.html"><strong>比丘／比丘尼戒對照表</strong></a></td>
<td>只列<strong>共戒</strong>：對位 {_a5} 組，逐組標罪名異同（如摩觸戒比丘結僧殘、比丘尼結波羅夷），
並附眾學法全 58 目。可依罪屬、罪名異同篩選。原為附錄五。</td></tr>
<tr><td><a href="五部律開遮持犯表.html"><strong>五部律開遮持犯表</strong></a></td>
<td>差異導向，657 列，五欄記各律有無；可依狀態、差異類型、各部欄篩選，點表頭排序。
空白一律為「未比」（未經比勘），<strong>非謂該部無此開緣</strong>。原為附錄六。</td></tr>
</table>

<h2>怎麼用</h2>
<ol>
<li><strong>讀律時查</strong>：讀四分律至某篇，翻至本書同篇。每篇先有「篇旨」述其內容，次依四分段號列差異。</li>
<li><strong>查某部獨有何制</strong>：看「四分所無與歸併組」，按主稿分節。</li>
<li><strong>同一制度兩稿並列</strong>：看第三部歸併組（甲表 G1–G7 同條歸併、乙表 T1–T3 同題異制）。</li>
</ol>

<h2>側邊欄與檢索</h2>
<ul>
<li><strong>快捷鍵</strong>　<code>Ctrl+K</code> 或 <code>/</code> 聚焦站內檢索（<code>Ctrl+F</code> 留給瀏覽器原生查找）；
<code>F3</code>／<code>Shift+F3</code> 前後巡覽命中處；<code>Alt+N</code> 收起或喚出側欄。</li>
<li><strong>目錄過濾</strong>　側欄上方輸入篇名／戒名即時篩出所在卷節，<code>Esc</code> 清除；
卷次摺疊狀態、側欄寬度與收起狀態都會記住。</li>
<li><strong>檢索範圍</strong>　可切「全部／僅標題・項名／略白話・原文」；
結果附「卷 › 篇 › 節」脈絡與項號，可「載入更多」，並保留近期檢索。</li>
<li><strong>窄屏</strong>　點左上 <strong>☰</strong> 喚出側欄抽屜；側欄右緣可拖曳調整寬度。</li>
</ul>

<h2>凡例摘要</h2>
<ul>
<li>每項八目：序號、標題、狀態與出處、差異、本稿原文、白話、他部對照、補證。</li>
<li>狀態：<strong>A</strong> 同條增異、<strong>B</strong> 同條開緣、<strong>C</strong> 四分所無、<strong>D</strong> 同條減略。</li>
<li>項號前綴：<code>D</code> 第一部（按四分篇次）、<code>S</code> 第二部（按主稿）、
<code>G</code>／<code>T</code> 第三部歸併組（G 為同條歸併，T 為同題異制）。</li>
<li>「遍查未見」為文獻學斷言，謂四分律無此制，非工作進度之闕漏；
若散見雜篇或名相異稱者，歡迎指正。</li>
</ul>

<hr>
<p style="font-size:13px;color:#8a8278">
原始碼、勘誤與 Issue：
<a href="{REPO_URL}">GitHub</a>
　·　
<a href="{SITE_URL}">線上版</a>
</p>
"""
    nav = ('<h1><a href="index.html">五部律差異對照本</a></h1>'
           '<div class="nsub">以四分律為軸　五部對校</div>'
           + NAV_FILTER_HTML +
           '<div class="grp"><b>全書</b>'
           '<a href="index.html">目錄與說明</a>'
           '<a href="五部律差異對照本.html">對照本合冊</a>'
           '<a href="五部律綜合異同矩陣.html">異同矩陣</a></div>'
           '<div class="grp"><b>專題表</b>'
           '<a href="比丘比丘尼戒對照表.html">比丘／比丘尼戒對照</a>'
           '<a href="五部律開遮持犯表.html">開遮持犯表</a></div>'
           '<div class="grp"><b>分卷</b>'
           + ''.join(f'<a href="{h}">{j}</a>' for j, h, _ in rows)
           + '</div>')

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="author" content="UncleHandsome">
<meta name="description" content="《五部律差異對照本》線上版：以四分律為軸，對校五部廣律。">
<meta name="citation_title" content="五部律差異對照本">
<meta name="citation_author" content="UncleHandsome">
<meta name="citation_publication_date" content="{_DATE}">
<meta name="citation_language" content="zh-Hant">
<meta name="DC.rights" content="CC BY-NC-SA 4.0">
<link rel="canonical" href="{SITE_URL}">
<title>五部律差異對照本</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<nav>{nav}</nav>
<main>{body}
{FOOTER}
</main>
</div>
<script>{SEARCH_CORE}</script>
<script>{COMMON_JS}</script>
</body></html>"""
    page = page.replace('__CORE__', SEARCH_CORE).replace('__HOMEJS__', HOME_SEARCH)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(page)


def main():
    os.makedirs(OUT, exist_ok=True)
    single = '--single' in sys.argv

    # 首頁索引暫停（2026-11-05）：首頁改回合冊全文檢索。
    # 要開回：加 --with-index，並將 build_index 的表單 action 改回 index.html。
    if '--with-index' in sys.argv:
        build_search_index()
    if not single:
        build_index()
        print('索引頁：index.html')

    # 分卷
    for jname, fn in JUAN:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            print(f'  跳過（無檔）：{fn}')
            continue
        out = os.path.join(OUT, fn.replace('.md', '.html'))
        ok = md_to_html(p, out, f'五部律差異對照本　{jname}', False)
        if ok:
            sz = os.path.getsize(out)
            print(f'  {jname}: {sz/1024:.0f} KB')

    # 合冊
    full_p = os.path.join(SRC, FULL)
    if os.path.exists(full_p):
        out = os.path.join(OUT, FULL.replace('.md', '.html'))
        ok = md_to_html(full_p, out, '五部律差異對照本', True)
        if ok:
            print(f'  合冊: {os.path.getsize(out)/1024/1024:.1f} MB')


if __name__ == '__main__':
    main()
