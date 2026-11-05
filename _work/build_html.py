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
        st = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT,
                            capture_output=True, text=True, timeout=20).stdout.strip()
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
  overflow-x:hidden; overflow-wrap:break-word; word-break:break-word;
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

JS = r"""
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
      wbtn.textContent = document.body.classList.contains('wide') ? '切換舒適寬度' : '切換寬屏';
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
      bar.textContent = anyClosed ? '全部收起' : '全部展開';
    });
  }
  // 對讀：原文與白話左右並列
  var pbtn = document.getElementById('par');
  if (pbtn){
    if (localStorage.getItem('wb_par') === '1') document.body.classList.add('par');
    var syncP = function(){
      var on = document.body.classList.contains('par');
      pbtn.textContent = on ? '對讀：開' : '對讀：原文並白話';
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
  // 全文檢索：含折疊（未展開）內容，命中則自動展開並跳至該處
  var fbox = document.getElementById('find');
  var finfo = document.getElementById('findinfo');
  if (fbox){
    var hits = [], cur = -1, timer = null, LIMIT = 3000;

    var collect = function(q){
      var root = document.getElementById('main') || document.body;
      var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
      var out = [], n, lq = q.toLowerCase();
      while ((n = w.nextNode())){
        var pe = n.parentElement;
        if (!pe) continue;
        var t = pe.tagName;
        if (t === 'SCRIPT' || t === 'STYLE' || t === 'NOSCRIPT') continue;
        if (n.data && n.data.toLowerCase().indexOf(lq) >= 0){
          out.push(n);
          if (out.length >= LIMIT) break;
        }
      }
      return out;
    };

    var reveal = function(node){
      var el = node.parentElement;
      while (el){
        if (el.tagName === 'DETAILS') el.open = true;
        el = el.parentElement;
      }
    };

    var go = function(i){
      if (!hits.length) return;
      cur = ((i % hits.length) + hits.length) % hits.length;
      var node = hits[cur];
      reveal(node);
      var pe = node.parentElement;
      pe.classList.add('hitflash');
      // 展開 details 會使上方版面變高，瀏覽器的 scroll anchoring 隨之補償，
      // 把剛跳到的位置又推走；此處暫停 anchoring，並於兩帧後再校正一次。
      // 展開 details 之後，上方內容的高度往往要到數百毫秒後才定；scrollIntoView
      // 於此時會落在舊座標。改以絕對座標直接捲動，並在版面穩定前後各校正一次。
      var de = document.documentElement;
      var oldAnchor = de.style.overflowAnchor;
      de.style.overflowAnchor = 'none';
      var jump = function(){
        var y = pe.getBoundingClientRect().top + window.pageYOffset
                - Math.max(80, (window.innerHeight - pe.offsetHeight) / 2);
        window.scrollTo(0, Math.max(0, y));
      };
      jump();
      [120, 350, 700, 1200, 2000].forEach(function(t){ setTimeout(jump, t); });
      setTimeout(function(){
        pe.classList.remove('hitflash');
        de.style.overflowAnchor = oldAnchor;
      }, 2600);
      finfo.textContent = '第 ' + (cur + 1) + ' / ' + hits.length + ' 處' +
        (hits.length >= LIMIT ? '（已達上限，請加長關鍵詞）' : '');
    };

    var run = function(jump){
      var q = fbox.value.trim();
      if (q.length < 1){ hits = []; cur = -1; finfo.textContent = ''; return; }
      if (q !== run.last){
        hits = collect(q); cur = -1; run.last = q;
      }
      if (!hits.length){ finfo.textContent = '「' + q + '」：0 處'; return; }
      go(jump ? cur + 1 : 0);
    };

    fbox.addEventListener('input', function(){
      clearTimeout(timer);
      timer = setTimeout(function(){ run(false); }, 320);
    });
    fbox.addEventListener('keydown', function(e){
      if (e.key === 'Enter'){ e.preventDefault(); run(true); }
      if (e.key === 'Escape'){ fbox.value = ''; hits = []; finfo.textContent = ''; }
    });
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
    """從 Markdown 提取目錄結構，生成側邊欄"""
    parts = []
    parts.append('<h1><a href="index.html">五部律差異對照本</a></h1>')
    parts.append('<div class="grp"><b>全書</b>')
    parts.append('<a href="index.html">目錄與說明</a>')
    parts.append('</div>')

    # 分卷檔加前後卷導覽：單篇成檔時，讀者從搜尋引擎進來會成孤島
    _names = [j for j, _f in JUAN]
    if cur in _names:
        _i = _names.index(cur)
        _prev = _names[_i - 1] if _i > 0 else None
        _next = _names[_i + 1] if _i + 1 < len(_names) else None
        if _prev or _next:
            parts.append('<div class="grp"><b>分卷</b>')
            if _prev:
                parts.append(f'<a href="五部律差異對照本_{htmlmod.escape(_prev)}.html">'
                             f'← {htmlmod.escape(_prev)}</a>')
            if _next:
                parts.append(f'<a href="五部律差異對照本_{htmlmod.escape(_next)}.html">'
                             f'→ {htmlmod.escape(_next)}</a>')
            parts.append('</div>')

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
            parts.append(f'<details class="navj"><summary>{htmlmod.escape(head)}</summary>')
            for n, title in arts:
                t = htmlmod.escape(re.sub(r'<[^>]+>', '', title))
                parts.append(f'<a href="#p{n}" class="art">{n}　{t}</a>')
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
                parts.append(f'<a href="#p{n}">{n}　{t}</a>')
        parts.append('</div>')
        parts.append('<div class="grp"><b>其他</b>')
        parts.append('<a href="index.html">← 回目錄</a>')
        parts.append('</div>')

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

    _cur = None
    if not is_full:
        _b = os.path.basename(out_path)
        if _b.startswith('五部律差異對照本_') and _b.endswith('.html'):
            _c = _b[len('五部律差異對照本_'):-5]
            if any(_c == _j for _j, _f in JUAN):
                _cur = _c
    nav = build_nav(md_text, is_full, _cur)

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
<div class="grp" style="margin-top:1.2rem">
<button type="button" id="toggle" aria-controls="main">全部展開／收起</button>
<button type="button" id="width">切換寬屏</button>
<button type="button" id="par" aria-pressed="false">對讀：原文並白話</button>
</div>
<div class="grp" style="padding:.4rem 1rem 0">
<label for="jump" class="sr-only">跳至指定編號</label>
<input type="text" id="jump" placeholder="跳至 D-0450" aria-label="跳至指定編號，如 D-0450"
  style="width:100%;padding:.28rem .5rem;border:1px solid var(--line);border-radius:3px;
  font-size:12.5px;font-family:inherit;background:#fff">
</div>
<div class="grp" style="padding:.4rem 1rem 0">
<label for="find" class="sr-only">全文檢索</label>
<input type="search" id="find" placeholder="全文檢索（Enter 逐處）" aria-label="全文檢索，含折疊內容"
  style="width:100%;padding:.28rem .5rem;border:1px solid var(--line);border-radius:3px;
  font-size:12.5px;font-family:inherit;background:#fff">
<div id="findinfo" role="status" aria-live="polite"
  style="font-size:11.5px;color:#8a8278;padding:.25rem .1rem 0;min-height:1.2em"></div>
</div>
</nav>
<main id="main">
{_banner}
{body}
{FOOTER}
</main>
</div>
<a href="#top-anchor" id="top" aria-label="回到頂部">↑</a>
<script>{JS}</script>
</body>
</html>"""
    open(out_path, 'w', encoding='utf-8', newline='\n').write(page)
    return True


def build_index():
    """索引頁"""
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

<h2>怎麼用</h2>
<ol>
<li><strong>讀律時查</strong>：讀四分律至某篇，翻至本書同篇。每篇先有「篇旨」述其內容，次依四分段號列差異。</li>
<li><strong>查某部獨有何制</strong>：看「四分所無與歸併組」，按主稿分節。</li>
<li><strong>同一制度兩稿並列</strong>：看第三部歸併組（甲表 G1–G7 同條歸併、乙表 T1–T3 同題異制）。</li>
</ol>

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
           '<div class="grp"><b>全書</b>'
           '<a href="index.html">目錄與說明</a>'
           '<a href="五部律差異對照本.html">對照本合冊</a>'
           '<a href="五部律綜合異同矩陣.html">異同矩陣</a></div>'
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
</div></body></html>"""
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(page)


def main():
    os.makedirs(OUT, exist_ok=True)
    single = '--single' in sys.argv

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
