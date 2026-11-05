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

from build_html import CSS, FOOTER, SITE_URL, _DATE, _VER, SEARCH_CORE  # noqa: E402

# rebuild_all 於第 5–6 步已改寫其他成品檔，第 7 步載入本模組時 git 會判為 dirty；
# 但 HEAD 仍是最初那個內容 commit，故沿用其 hash、去掉 dirty 標記，
# 使專題表與合冊版本戳一致（流程恆為「先 commit、再重建」）。
FOOTER = FOOTER.replace('-dirty', '')

PAGES = [
    {
        'src': 'appendix5.md',
        'out': '比丘比丘尼戒對照表.html',
        'title': '比丘／比丘尼戒對照表',
        'desc': '共戒對位與罪名異同，附眾學法已分節之目。原為《五部律差異對照本》附錄五。',
        'filters': [('罪屬', '罪屬', 0), ('尼罪屬', '罪屬', 1),
                    ('罪名異同', '罪名異同', 0), ('依據', '依據', 0),
                    ('篇', '篇', 0)],
    },
    {
        'src': 'appendix6.md',
        'out': '五部律開遮持犯表.html',
        'title': '五部律開遮持犯表',
        'desc': '差異導向之開遮持犯一覽。原為《五部律差異對照本》附錄六。',
        'filters': [('狀態', '狀態', 0), ('差異類型', '差異類型', 0),
                    ('四分', '四分', 0), ('五分', '五分', 0),
                    ('十誦', '十誦', 0), ('僧祇', '僧祇', 0),
                    ('根有', '根有', 0)],
    },
]

# 篇號的通行別名（供下拉選單顯示，免讀者只見 022）
PIAN_LABEL = {
    '022': '022 入白衣舍威儀',
    '023': '023 坐食威儀',
    '024': '024 塔寺與說法威儀',
}

EXTRA_CSS = r"""
/* ── 專題表頁（只補共用樣式不足之處，不重複宣告 main／table） ── */
main{padding:2rem 2.2rem 5rem}
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
.tbl-wrap table{font-size:13px; background:#fff; min-width:860px}
.tbl-wrap th,.tbl-wrap td{border-bottom:1px solid var(--line); padding:.42rem .6rem;
  text-align:left; vertical-align:top; line-height:1.55}
.tbl-wrap th{background:#f0ece2; color:var(--fg); font-weight:600; white-space:nowrap;
  position:sticky; top:0; cursor:pointer; user-select:none}
.tbl-wrap th:hover{background:#e8e2d4}
.tbl-wrap th.sorted::after{content:' ▲'; font-size:10px; color:var(--accent)}
.tbl-wrap th.sorted.desc::after{content:' ▼'}
.tbl-wrap tbody tr:hover{background:#faf6ec}
.tbl-wrap tbody tr[hidden]{display:none}
.tbl-wrap tfoot td{background:#f7f3e9; font-weight:600; border-top:2px solid var(--line)}
.tbl-wrap td.bad{color:#a33; font-weight:600}
.tbl-wrap td.nowrap{white-space:nowrap}
.tbl-wrap td:last-child{min-width:7.5em}
.tbl-wrap caption{caption-side:top; text-align:left; font-size:12px; color:var(--fg2);
  padding:.2rem .1rem .5rem}
.home{display:inline-block; margin:0 0 1rem; font-size:13px; color:var(--accent)}
@media print{
  .tools{display:none} th{position:static} .scroll{overflow:visible}
  /* 表格須能跨頁；只禁單列被切斷 */
  .tbl-wrap tr{break-inside:avoid; page-break-inside:avoid}
  .tbl-wrap thead{display:table-header-group}
}
@media (prefers-color-scheme: dark){
  .tools{background:#1e1d1b; border-color:var(--line)}
  .tools input[type=search],.tools select,.tools button{background:#232120; color:var(--fg);
    border-color:var(--line)}
  .tbl-wrap table{background:#1a1918}
  .tbl-wrap th{background:#26241f}
  .tbl-wrap th:hover{background:#302d27}
  .tbl-wrap tbody tr:hover{background:#242220}
  .tbl-wrap tfoot td{background:#242220}
  .tbl-wrap td,.tbl-wrap th{border-bottom-color:var(--line)}
  .tbl-wrap td.bad{color:#e08a7a}
}
"""

JS = r"""
(function(){
  // 檢索核心與對照本共用（正規化、同義詞、模糊）
  var norm = function(x){ return VS.norm(x); };

  // 中文數字（供「020-八十一」這種編號排序）
  var CN = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9};
  function cn2i(s){
    if (!s) return 0;
    if (s.indexOf('百') >= 0){
      var p = s.split('百'), n = (CN[p[0]] || 1) * 100, r = p[1] || '';
      if (r.charAt(0) === '零') r = r.slice(1);
      if (!r) return n;
      if (r.indexOf('十') >= 0){
        var q = r.split('十');
        return n + (CN[q[0]] || 1) * 10 + (CN[q[1]] || 0);
      }
      return n + (CN[r] || 0);
    }
    if (s.indexOf('十') >= 0){
      var t = s.split('十');
      return (CN[t[0]] || 1) * 10 + (CN[t[1]] || 0);
    }
    return CN[s] || 0;
  }
  // 排序鍵：篇-節（如 020-八十一）＞ 純數字 ＞ 文字
  function sortKey(s){
    var m = s.match(/^(\d{1,3})-(\S+)$/);
    if (m) return [0, parseInt(m[1], 10), cn2i(m[2]), s];
    if (/^[\d.,]+$/.test(s)) return [1, parseFloat(s.replace(/,/g, '')), 0, s];
    return [2, 0, 0, s];
  }
  function cmp(x, y){
    var a = sortKey(x), b = sortKey(y);
    for (var i = 0; i < 4; i++){
      if (a[i] < b[i]) return -1;
      if (a[i] > b[i]) return 1;
    }
    return 0;
  }

  document.querySelectorAll('.tbl-wrap').forEach(function(wrap){
    var table = wrap.querySelector('table');
    var tb = table.querySelector('tbody');
    var rows = Array.prototype.slice.call(tb.querySelectorAll('tr'));
    var orig = rows.slice();
    var heads = Array.prototype.slice.call(table.querySelectorAll('thead th'));
    var box = wrap.querySelector('input[type=search]');
    var sels = Array.prototype.slice.call(wrap.querySelectorAll('select[data-col]'));
    var cnt = wrap.querySelector('.count');
    var sortCol = -1, sortDesc = false;

    function refresh(){
      var pq = VS.parseQuery(box.value || '');
      var n = 0, anySel = false;
      sels.forEach(function(s){ if (s.value) anySel = true; });
      rows.forEach(function(tr){
        var ok = true;
        if (pq.n || pq.exc.length){
          if (tr._norm === undefined) tr._norm = norm(tr.textContent);
          var hay = tr._norm;
          for (var a = 0; a < pq.exc.length; a++){
            if (hay.indexOf(pq.exc[a]) >= 0){ ok = false; break; }
          }
          if (ok) for (var b = 0; b < pq.phr.length; b++){
            if (hay.indexOf(pq.phr[b]) < 0){ ok = false; break; }
          }
          if (ok) for (var c = 0; c < pq.inc.length; c++){
            if (!VS.matchGroup(hay, pq.inc[c])){ ok = false; break; }
          }
        }
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
      var hint = '';
      if (n === 0 && !anySel && pq.n > 1){
        hint = '（多詞須同一列全部命中，可減少詞數）';
      }
      cnt.textContent = '顯示 ' + n + ' / ' + rows.length + ' 列' + hint;
    }
    box.addEventListener('input', refresh);
    box.addEventListener('keydown', function(e){
      if (e.key === 'Enter') e.preventDefault();   // 免行動鍵盤觸發頁面重載
    });
    sels.forEach(function(s){ s.addEventListener('change', refresh); });
    wrap.querySelector('button.reset').addEventListener('click', function(){
      box.value = ''; sels.forEach(function(s){ s.value = ''; });
      sortCol = -1; sortDesc = false;
      heads.forEach(function(h){ h.classList.remove('sorted', 'desc'); });
      orig.forEach(function(r){ tb.appendChild(r); });
      rows = orig.slice();
      refresh();
    });
    heads.forEach(function(th, i){
      th.addEventListener('click', function(){
        // 三態：升冪 → 降冪 → 還原原文序
        if (sortCol !== i){ sortCol = i; sortDesc = false; }
        else if (!sortDesc){ sortDesc = true; }
        else {
          sortCol = -1; sortDesc = false;
          heads.forEach(function(h){ h.classList.remove('sorted', 'desc'); });
          orig.forEach(function(r){ tb.appendChild(r); });
          rows = orig.slice();
          refresh();
          return;
        }
        heads.forEach(function(h){ h.classList.remove('sorted', 'desc'); });
        th.classList.add('sorted'); if (sortDesc) th.classList.add('desc');
        rows.sort(function(a, b){
          var x = a.cells[i] ? a.cells[i].textContent.trim() : '';
          var y = b.cells[i] ? b.cells[i].textContent.trim() : '';
          var c = cmp(x, y);
          return sortDesc ? -c : c;
        });
        rows.forEach(function(r){ tb.appendChild(r); });
        refresh();
      });
    });
    refresh();
  });
})();
"""


def plain(s):
    """去掉 Markdown 標記，取純文字（供篩選值比對）。"""
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'`(.+?)`', r'\1', s)
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
    return s.strip()


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


def uniq_heads(head):
    """重複表頭一律加限定語（兩個「已對位」→ 比丘·已對位／比丘尼·已對位）。"""
    import collections as _c
    cnt = _c.Counter(head)
    out, group = [], ''
    for h in head:
        if h in ('比丘', '比丘尼'):
            group = h
        if cnt[h] > 1 and group and h != group:
            out.append(group + '·' + h)
        elif cnt[h] > 1:
            out.append(h + '（' + group + '）' if group else h)
        else:
            out.append(h)
    return out


def build_page(cfg):
    blocks = parse_md(os.path.join(WORK, cfg['src']))
    out = []
    out.append('<!DOCTYPE html>\n<html lang="zh-Hant">\n<head><meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    out.append('<meta name="color-scheme" content="light dark">')
    out.append(f'<title>{H.escape(cfg["title"])}　｜　五部律差異對照本</title>')
    out.append(f'<meta name="description" content="{H.escape(cfg["desc"])}">')
    out.append(f'<meta name="citation_title" content="{H.escape(cfg["title"])}">')
    out.append('<meta name="citation_author" content="UncleHandsome">')
    out.append(f'<meta name="citation_publication_date" content="{_DATE}">')
    out.append('<meta name="DC.rights" content="CC BY-NC-SA 4.0">')
    out.append(f'<style>{CSS}\n{EXTRA_CSS}</style>\n</head>\n<body><div class="wrap">')
    nav = ('<nav><h1><a href="index.html">五部律差異對照本</a></h1>'
           '<div class="grp"><b>專題表</b>'
           '<a href="index.html">← 回目錄</a>'
           '<a href="五部律差異對照本.html">對照本合冊</a>'
           f'<a href="比丘比丘尼戒對照表.html"{" class=\"on\"" if cfg["out"] == "比丘比丘尼戒對照表.html" else ""}>戒對照表</a>'
           f'<a href="五部律開遮持犯表.html"{" class=\"on\"" if cfg["out"] == "五部律開遮持犯表.html" else ""}>開遮持犯表</a>'
           '<a href="五部律綜合異同矩陣.html">異同矩陣</a></div></nav>')
    out.append(nav)
    out.append('<main>')
    out.append(f'<a class="home" href="index.html">← 回目錄</a>')
    out.append(f'<h1>{H.escape(cfg["title"])}</h1>')
    out.append(f'<blockquote><p>{H.escape(cfg["desc"])}</p></blockquote>')

    for n, (title, notes, head, data) in enumerate(blocks, 1):
        heads = uniq_heads(head)
        # 合計列移入 tfoot，免被排序
        body, foot = [], []
        for row in data:
            first = plain(row[0]) if row else ''
            if first.startswith('合計') or first.startswith('五篇合計'):
                foot.append(row)
            else:
                body.append(row)
        out.append(f'<section class="tbl-wrap" data-tbl="{n}">')
        if title:
            out.append(f'<h2>{H.escape(title)}</h2>')
        if notes:
            out.append('<p class="note">' +
                       '<br>'.join(esc(x) for x in notes.split('\n') if x.strip()) +
                       '</p>')
        out.append('<div class="tools">')
        out.append('<label>搜尋</label><input type="search" '
                   'placeholder="多關鍵字：空白分隔；-詞排除；&quot;片語&quot;" '
                   'aria-label="多關鍵字模糊搜尋：空白分隔多詞，減號排除，引號片語">')
        for label, colname, occ in cfg['filters']:
            idxs = [k for k, c in enumerate(head) if c == colname]
            if len(idxs) <= occ:
                continue
            ci = idxs[occ]
            vals = sorted(set(plain(r[ci]) for r in body
                               if ci < len(r) and len(plain(r[ci])) <= 14))
            vals = [v for v in vals if v]
            if not (1 < len(vals) <= 12):
                continue
            opts = ''.join(
                f'<option value="{H.escape(v)}">'
                f'{H.escape(PIAN_LABEL.get(v, v))}</option>' for v in vals)
            out.append(f'<label>{H.escape(label)}</label>'
                       f'<select data-col="{ci}" aria-label="篩選{H.escape(label)}">'
                       f'<option value="">全部</option>{opts}</select>')
        out.append('<button type="button" class="reset">清除</button>')
        out.append('<span class="count" role="status" aria-live="polite"></span></div>')
        out.append('<div class="scroll"><table>')
        out.append(f'<caption>{H.escape(title or cfg["title"])}'
                   f'（{len(body)} 列）</caption>')
        out.append('<thead><tr>')
        out.extend(f'<th scope="col">{esc(c)}</th>' for c in heads)
        out.append('</tr></thead><tbody>')
        for row in body:
            out.append('<tr>')
            for j, c in enumerate(head):
                v = row[j] if j < len(row) else ''
                cls = []
                if c == '罪名異同' and '異' in v:
                    cls.append('bad')
                if re.match(r'^\d{3}-', plain(v)):
                    cls.append('nowrap')
                out.append(f'<td{" class=\"" + " ".join(cls) + "\"" if cls else ""}>{esc(v)}</td>')
            out.append('</tr>')
        out.append('</tbody>')
        if foot:
            out.append('<tfoot>')
            for row in foot:
                out.append('<tr>')
                for j in range(len(head)):
                    v = row[j] if j < len(row) else ''
                    out.append(f'<td>{esc(v)}</td>')
                out.append('</tr>')
            out.append('</tfoot>')
        out.append('</table></div></section>')

    out.append(FOOTER)
    out.append('</main></div>')
    out.append(f'<script>{SEARCH_CORE}</script>\n<script>{JS}</script>')
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
