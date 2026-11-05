#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把附錄五／六轉成獨立、可檢索的專題網頁。

  _work/appendix5.md → 05_網頁版/比丘比丘尼戒對照表.html
  _work/appendix6.md → 05_網頁版/五部律開遮持犯表.html

複用 build_html.CSS／FOOTER，故與全站樣式、深色模式、版本戳一致。
每張表自帶搜尋框、離散值下拉篩選、點表頭排序、命中計數。
"""
import os, re, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
OUT = os.path.join(ROOT, '05_網頁版')
sys.path.insert(0, WORK)

from build_html import CSS, FOOTER, SITE_URL, _DATE, _VER  # noqa: E402

# rebuild_all 於第 5–6 步已改寫其他成品檔，第 7 步載入本模組時 git 會判為 dirty；
# 但 HEAD 仍是最初那個內容 commit，故沿用其 hash、去掉 dirty 標記，
# 使專題表與合冊版本戳一致（流程恆為「先 commit、再重建」）。
FOOTER = FOOTER.replace('-dirty', '')

PAGES = [
    {
        'src': 'appendix5.md',
        'out': '比丘比丘尼戒對照表.html',
        'title': '比丘／比丘尼戒對照表',
        'desc': '共戒對位與罪名異同，附眾學法全目。原為《五部律差異對照本》附錄五。',
        'filters': {'罪名異同': '罪名異同', '罪屬': '罪屬', '依據': '依據', '篇': '篇'},
    },
    {
        'src': 'appendix6.md',
        'out': '五部律開遮持犯表.html',
        'title': '五部律開遮持犯表',
        'desc': '差異導向之開遮持犯一覽。原為《五部律差異對照本》附錄六。',
        'filters': {'狀態': '狀態', '差異類型': '差異類型',
                    '四分': '四分', '五分': '五分', '十誦': '十誦',
                    '僧祇': '僧祇', '根有': '根有'},
    },
]

EXTRA_CSS = r"""
/* ── 專題表頁 ── */
main{max-width:1180px; margin:0 auto; padding:2rem 2.2rem 5rem}
.tbl-wrap{margin:1.4rem 0 2.4rem}
.tbl-wrap h2{margin:0 0 .2rem; font-size:20px; color:var(--fg)}
.tbl-wrap .note{font-size:13px; color:var(--fg2); margin:.2rem 0 .8rem; line-height:1.7}
.tools{display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; margin:.7rem 0 .6rem;
  padding:.55rem .7rem; background:var(--panel); border:1px solid var(--line); border-radius:4px}
.tools input[type=search],.tools select{font:inherit; font-size:13px; padding:.3rem .5rem;
  border:1px solid var(--line); border-radius:3px; background:#fff; color:var(--fg)}
.tools input[type=search]{flex:1 1 210px; min-width:150px}
.tools label{font-size:12px; color:var(--fg2)}
.tools .count{margin-left:auto; font-size:12px; color:var(--fg2); white-space:nowrap}
.tools button{font:inherit; font-size:12px; padding:.3rem .6rem; cursor:pointer;
  border:1px solid var(--line); border-radius:3px; background:#fff; color:var(--fg)}
.scroll{overflow-x:auto; -webkit-overflow-scrolling:touch;
  border:1px solid var(--line); border-radius:4px}
table{border-collapse:collapse; width:100%; font-size:13px; background:#fff}
th,td{border-bottom:1px solid var(--line); padding:.42rem .6rem; text-align:left;
  vertical-align:top; line-height:1.55}
th{background:#f0ece2; color:var(--fg); font-weight:600; white-space:nowrap;
  position:sticky; top:0; cursor:pointer; user-select:none}
th:hover{background:#e8e2d4}
th.sorted::after{content:' ▲'; font-size:10px; color:var(--accent)}
th.sorted.desc::after{content:' ▼'}
tbody tr:hover{background:#faf6ec}
tbody tr[hidden]{display:none}
td.num{text-align:right; white-space:nowrap}
td.bad{color:#a33; font-weight:600}
.home{display:inline-block; margin:0 0 1rem; font-size:13px; color:var(--accent)}
@media print{.tools{display:none} th{position:static} .scroll{overflow:visible}}
@media (prefers-color-scheme: dark){
  .tools{background:#1e1d1b; border-color:var(--line)}
  .tools input[type=search],.tools select,.tools button{background:#232120; color:var(--fg);
    border-color:var(--line)}
  table{background:#1a1918}
  th{background:#26241f}
  th:hover{background:#302d27}
  tbody tr:hover{background:#242220}
  td,th{border-bottom-color:var(--line)}
  td.bad{color:#e08a7a}
}
"""

JS = r"""
(function(){
  document.querySelectorAll('.tbl-wrap').forEach(function(wrap){
    var tid = wrap.getAttribute('data-tbl');
    var table = wrap.querySelector('table');
    var rows = Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
    var heads = Array.prototype.slice.call(table.querySelectorAll('th'));
    var box = wrap.querySelector('input[type=search]');
    var sels = Array.prototype.slice.call(wrap.querySelectorAll('select[data-col]'));
    var cnt = wrap.querySelector('.count');
    var sortCol = -1, sortDesc = false;

    function refresh(){
      var q = (box.value || '').trim().toLowerCase();
      var n = 0;
      rows.forEach(function(tr){
        var ok = !q || tr.textContent.toLowerCase().indexOf(q) >= 0;
        if (ok) {
          sels.forEach(function(sel){
            if (!sel.value) return;
            var i = parseInt(sel.getAttribute('data-col'), 10);
            var cell = tr.cells[i] ? tr.cells[i].textContent.trim() : '';
            if (cell !== sel.value) ok = false;
          });
        }
        tr.hidden = !ok;
        if (ok) n++;
      });
      cnt.textContent = '顯示 ' + n + ' / ' + rows.length + ' 列';
    }
    box.addEventListener('input', refresh);
    sels.forEach(function(s){ s.addEventListener('change', refresh); });
    wrap.querySelector('button.reset').addEventListener('click', function(){
      box.value = ''; sels.forEach(function(s){ s.value = ''; }); refresh();
    });
    heads.forEach(function(th, i){
      th.addEventListener('click', function(){
        if (sortCol === i) sortDesc = !sortDesc;
        else { sortCol = i; sortDesc = false; }
        heads.forEach(function(h){ h.classList.remove('sorted','desc'); });
        th.classList.add('sorted'); if (sortDesc) th.classList.add('desc');
        rows.sort(function(a,b){
          var x = a.cells[i] ? a.cells[i].textContent.trim() : '';
          var y = b.cells[i] ? b.cells[i].textContent.trim() : '';
          var nx = parseFloat(x.replace(/,/g,''));
          var ny = parseFloat(y.replace(/,/g,''));
          var c = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : x.localeCompare(y, 'zh-Hant');
          return sortDesc ? -c : c;
        });
        var tb = table.querySelector('tbody');
        rows.forEach(function(r){ tb.appendChild(r); });
        refresh();
      });
    });
    refresh();
  });
})();
"""


def parse_md(path):
    """回 [(標題, 說明段落, 表頭 list, 資料列 list)]。"""
    lines = open(path, encoding='utf-8').read().split('\n')
    blocks, i = [], 0
    cur_title, notes = '', []
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('### ') or ln.startswith('#### '):
            cur_title = re.sub(r'^#+\s*', '', ln).strip()
            notes = []
            i += 1
            continue
        if ln.startswith('>'):
            t = ln.lstrip('> ').strip()
            if t and t != '>':
                notes.append(t)
            i += 1
            continue
        if ln.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|$', lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip('|').split('|')]
            i += 2
            data = []
            while i < len(lines) and lines[i].startswith('|'):
                data.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            blocks.append((cur_title, '\n'.join(notes), head, data))
            continue
        i += 1
    return blocks


def esc(s):
    # 表格儲存格已含 Markdown 粗體，轉成 <strong>
    s = H.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return s


def build_page(cfg):
    blocks = parse_md(os.path.join(WORK, cfg['src']))
    out = []
    out.append('<!DOCTYPE html>\n<html lang="zh-Hant">\n<head><meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    out.append('<meta name="color-scheme" content="light">')
    out.append(f'<title>{H.escape(cfg["title"])}　｜　五部律差異對照本</title>')
    out.append(f'<meta name="description" content="{H.escape(cfg["desc"])}">')
    out.append(f'<meta name="citation_title" content="{H.escape(cfg["title"])}">')
    out.append('<meta name="citation_author" content="UncleHandsome">')
    out.append(f'<meta name="citation_publication_date" content="{_DATE}">')
    out.append('<meta name="DC.rights" content="CC BY-NC-SA 4.0">')
    out.append(f'<style>{CSS}\n{EXTRA_CSS}</style>\n</head>\n<body><div class="wrap">')
    out.append('<nav><h1><a href="index.html">五部律差異對照本</a></h1>'
               '<div class="grp"><b>專題表</b>'
               '<a href="index.html">← 回目錄</a>'
               '<a href="五部律差異對照本.html">對照本合冊</a>'
               '<a href="比丘比丘尼戒對照表.html">戒對照表</a>'
               '<a href="五部律開遮持犯表.html">開遮持犯表</a>'
               '<a href="五部律綜合異同矩陣.html">異同矩陣</a></div></nav>')
    out.append('<main>')
    out.append(f'<a class="home" href="index.html">← 回目錄</a>')
    out.append(f'<h1>{H.escape(cfg["title"])}</h1>')
    out.append(f'<blockquote><p>{H.escape(cfg["desc"])}</p></blockquote>')

    for n, (title, notes, head, data) in enumerate(blocks, 1):
        out.append(f'<section class="tbl-wrap" data-tbl="{n}">')
        if title:
            out.append(f'<h2>{H.escape(title)}</h2>')
        if notes:
            out.append('<p class="note">' +
                       '<br>'.join(esc(x) for x in notes.split('\n') if x.strip()) +
                       '</p>')
        out.append('<div class="tools">')
        out.append('<label>搜尋</label><input type="search" placeholder="輸入關鍵詞即時過濾" aria-label="搜尋表格">')
        # 離散值欄下拉
        for label, colname in cfg['filters'].items():
            if colname not in head:
                continue
            ci = head.index(colname)
            vals = sorted(set(r[ci] for r in data if ci < len(r) and len(r[ci]) <= 12))
            if not (1 < len(vals) <= 12):
                continue
            opts = ''.join(f'<option value="{H.escape(v)}">{H.escape(v)}</option>' for v in vals)
            out.append(f'<label>{H.escape(label)}</label>'
                       f'<select data-col="{ci}" aria-label="篩選{H.escape(label)}">'
                       f'<option value="">全部</option>{opts}</select>')
        out.append('<button type="button" class="reset">清除</button>')
        out.append('<span class="count"></span></div>')
        out.append('<div class="scroll"><table><thead><tr>')
        out.extend(f'<th scope="col">{esc(c)}</th>' for c in head)
        out.append('</tr></thead><tbody>')
        for row in data:
            out.append('<tr>')
            for j, c in enumerate(head):
                v = row[j] if j < len(row) else ''
                cls = ''
                if c == '罪名異同' and '異' in v:
                    cls = ' class="bad"'
                out.append(f'<td{cls}>{esc(v)}</td>')
            out.append('</tr>')
        out.append('</tbody></table></div></section>')

    out.append(FOOTER)
    out.append('</main></div>')
    out.append(f'<script>{JS}</script>')
    out.append('</body></html>')
    p = os.path.join(OUT, cfg['out'])
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
    rows = sum(len(b[3]) for b in blocks)
    print(f'  {cfg["out"]}：{len(blocks)} 表／{rows} 列　{os.path.getsize(p)/1024:.0f} KB')


def main():
    os.makedirs(OUT, exist_ok=True)
    for cfg in PAGES:
        build_page(cfg)


if __name__ == '__main__':
    main()
