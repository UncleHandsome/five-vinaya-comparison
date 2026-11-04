#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《五部律綜合異同矩陣》網頁版生成。

特色：
  - 五律欄符號化（有✓／無✗／未比—），窄欄且醒目
  - 狀態、主稿、層級三重篩選 + 關鍵詞搜索
  - 表頭粘性、行內差異可展開
  - 側邊欄導航至各段

輸出：05_網頁版/五部律綜合異同矩陣.html
"""
import os, re, html as H

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SRC = os.path.join(ROOT, '03_成品', '五部律綜合異同矩陣.md')
OUT = os.path.join(ROOT, '05_網頁版', '五部律綜合異同矩陣.html')

SEGS = ['五分', '十誦', '僧祇', '根有']
ST_NAME = {'A': '同條增異', 'B': '同條開緣', 'C': '四分所無', 'D': '同條減略'}
LV = ['戒條', '制度', '法數', '事件']

CSS = r"""
:root{
  --fg:#1a1a1a; --fg2:#5a5a5a; --bg:#fdfdfb; --panel:#f5f4ef;
  --line:#dcd8cf; --accent:#8a5a2b; --accent2:#a8763f;
  --yes:#2e7d4f; --no:#b03a3a; --na:#b8b2a6;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--fg);
  font-family:"Noto Sans SC","NotoSansSC-VF","PingFang SC","Microsoft YaHei",sans-serif;
  font-size:14px;line-height:1.6}
.wrap{display:flex;min-height:100vh}
/* ── 側欄 ── */
nav{width:220px;flex:0 0 220px;background:var(--panel);border-right:1px solid var(--line);
  position:sticky;top:0;height:100vh;overflow-y:auto;padding:1.1rem 0 2rem;font-size:13px}
nav h1{font-size:14px;margin:0 1rem 1rem;letter-spacing:.05em}
nav h1 a{color:var(--fg);text-decoration:none}
nav .grp>b{display:block;padding:.3rem 1rem;color:var(--fg2);font-size:11.5px;letter-spacing:.08em}
nav a{display:block;padding:.24rem 1rem .24rem 1.4rem;color:var(--fg2);text-decoration:none;
  border-left:2px solid transparent;font-size:13px}
nav a:hover{background:#ece8dd;color:var(--accent)}
nav a.on{border-left-color:var(--accent);color:var(--accent);background:#efeade}
nav .n{float:right;color:#9a9286;font-size:11.5px}
/* ── 主區 ── */
main{flex:1;min-width:0;padding:1.4rem 1.6rem 3rem}
h1{font-size:1.5rem;margin:0 0 .3rem}
.lede{color:var(--fg2);font-size:13px;margin-bottom:1.2rem}
/* ── 工具列 ── */
.bar{position:sticky;top:0;z-index:20;background:rgba(253,253,251,.97);
  padding:.7rem 0 .6rem;border-bottom:1px solid var(--line);margin-bottom:.8rem;
  display:flex;flex-wrap:wrap;gap:.5rem .9rem;align-items:center}
.bar .lbl{color:var(--fg2);font-size:12px;margin-right:.2rem}
.chip{display:inline-block;padding:.18rem .55rem;border:1px solid var(--line);border-radius:3px;
  cursor:pointer;font-size:12.5px;background:#fff;user-select:none}
.chip:hover{border-color:var(--accent2);color:var(--accent)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
input[type=search]{padding:.24rem .55rem;border:1px solid var(--line);border-radius:3px;
  font-size:13px;width:180px;font-family:inherit}
input[type=search]:focus{outline:1px solid var(--accent2)}
.count{margin-left:auto;color:var(--fg2);font-size:12.5px}
/* ── 表格 ── */
.tw{border:1px solid var(--line);border-radius:4px;background:#fff}
table{border-collapse:collapse;width:100%;font-size:13px}
thead th{position:sticky;top:0;background:#efeadf;border-bottom:1px solid var(--line);
  padding:.42rem .5rem;text-align:left;font-weight:600;white-space:nowrap;font-size:12.5px;z-index:10}
tbody td{border-bottom:1px solid #ece8df;padding:.38rem .5rem;vertical-align:top}
tbody tr:hover{background:#faf7f0}
td.id{font-family:Consolas,monospace;font-size:12px;color:var(--accent);white-space:nowrap}
td.lv{white-space:nowrap;color:var(--fg2);font-size:12.5px}
td.st{text-align:center;font-weight:700;white-space:nowrap}
.st-A{color:#8a5a2b}.st-B{color:#2e6d8a}.st-C{color:#b03a3a}.st-D{color:#6a6a6a}
td.topic{min-width:190px;max-width:280px}
td.c{text-align:center;font-size:14px;width:38px}
.yes{color:var(--yes);font-weight:700}
.no{color:var(--no);font-weight:700}
.na{color:var(--na)}
td.pos{color:var(--fg2);font-size:12px;max-width:120px}
td.diff{min-width:260px;max-width:420px;color:#3a3228}
td.ev{font-family:Consolas,monospace;font-size:11.5px;color:#8a8278;white-space:nowrap}
/* ── 分段標題 ── */
.sec{margin:1.6rem 0 .5rem;padding:.35rem .7rem;background:var(--panel);
  border-left:4px solid var(--accent2);font-size:14px;font-weight:600;letter-spacing:.03em}
.sec:first-of-type{margin-top:.4rem}
/* ── 空結果 ── */
.empty{display:none;padding:2rem;text-align:center;color:var(--fg2)}
@media(max-width:1360px){
  .tw{overflow-x:auto}
  thead th{position:static}
}
@media(max-width:1000px){nav{display:none} main{padding:1rem}}
"""

JS = r"""
(function(){
  var rows = Array.prototype.slice.call(document.querySelectorAll('tbody tr'));
  var secs = Array.prototype.slice.call(document.querySelectorAll('.sec'));
  var f = {st:'', seg:'', lv:'', q:''};
  var cntEl = document.getElementById('cnt');

  function apply(){
    var n = 0;
    rows.forEach(function(tr){
      var ok = true;
      if (f.st && tr.dataset.st !== f.st) ok = false;
      if (f.seg && tr.dataset.seg !== f.seg) ok = false;
      if (f.lv && tr.dataset.lv !== f.lv) ok = false;
      if (ok && f.q){
        var s = (tr.dataset.txt || '').toLowerCase();
        if (s.indexOf(f.q) < 0) ok = false;
      }
      tr.style.display = ok ? '' : 'none';
      if (ok) n++;
    });
    // 隱藏空段（含其表格容器），並更新段內計數
    secs.forEach(function(h){
      var seg = h.dataset.seg, vis = false, shown = 0, tws = [];
      var el = h.nextElementSibling;
      while (el && !el.classList.contains('sec')){
        if (el.classList.contains('tw')){
          tws.push(el);
          Array.prototype.forEach.call(el.querySelectorAll('tbody tr'), function(t){
            if (t.style.display !== 'none') shown++;
          });
        }
        el = el.nextElementSibling;
      }
      if (shown) vis = true;
      var total = parseInt(h.dataset.total, 10);
      h.textContent = seg + '　' + total + ' 項' + (shown < total ? '（顯 ' + shown + '）' : '');
      h.style.display = vis ? '' : 'none';
      tws.forEach(function(t){ t.style.display = vis ? '' : 'none'; });
    });
    cntEl.textContent = n.toLocaleString() + ' / ' + rows.length.toLocaleString() + ' 項';
  }

  document.querySelectorAll('[data-f]').forEach(function(b){
    b.addEventListener('click', function(){
      var key = b.dataset.f, val = b.dataset.v;
      f[key] = (f[key] === val) ? '' : val;
      // 同組取消其他
      document.querySelectorAll('[data-f="'+key+'"]').forEach(function(x){ x.classList.remove('on'); });
      if (f[key]) b.classList.add('on');
      apply();
    });
  });

  var q = document.getElementById('q');
  q.addEventListener('input', function(){ f.q = q.value.trim().toLowerCase(); apply(); });

  // 目錄高亮
  var links = Array.prototype.slice.call(document.querySelectorAll('nav a[href^="#"]'));
  window.addEventListener('scroll', function(){
    var y = window.scrollY + 90, cur = null;
    links.forEach(function(a){
      var el = document.getElementById(a.getAttribute('href').slice(1));
      if (el && el.offsetTop <= y) cur = a;
    });
    links.forEach(function(a){ a.classList.remove('on'); });
    if (cur) cur.classList.add('on');
  }, {passive:true});

  apply();
})();
"""


def parse():
    t = open(SRC, encoding='utf-8').read()
    # 依「### 五分（379 項）」分段
    parts = re.split(r'^### (五分|十誦|僧祇|根有)（(\d+) 項）\s*$', t, flags=re.M)
    segs = []
    for i in range(1, len(parts), 3):
        name, claim, body = parts[i], parts[i + 1], parts[i + 2]
        rows = []
        for m in re.finditer(r'^\| (M-\d{4}) \| (.+?) \|$', body, re.M):
            cols = [m.group(1)] + [c.strip() for c in m.group(2).split(' | ')]
            if len(cols) >= 13:
                rows.append(cols[:13])
        segs.append((name, int(claim), rows))
    return segs


def cell(v):
    if v == '有':
        return '<td class="c"><span class="yes">✓</span></td>'
    if v == '無':
        return '<td class="c"><span class="no">✗</span></td>'
    return '<td class="c"><span class="na">—</span></td>'


def main():
    segs = parse()
    total = sum(len(r) for _n, _c, r in segs)

    # 側欄
    nav = ['<h1><a href="index.html">五部律差異對照本</a></h1>',
           '<div class="grp"><b>全書</b>',
           '<a href="index.html">目錄與說明</a>',
           '<a href="五部律差異對照本.html">對照本合冊</a></div>',
           '<div class="grp"><b>矩陣分段</b>']
    for name, claim, rows in segs:
        nav.append(f'<a href="#seg-{name}">{name}<span class="n">{len(rows)}</span></a>')
    nav.append('</div>')

    # 主體
    body = []
    for name, claim, rows in segs:
        body.append(f'<div class="sec" id="seg-{name}" data-seg="{name}" data-total="{len(rows)}">'
                    f'{name}　{len(rows)} 項</div>')
        body.append('<div class="tw"><table><thead><tr>'
                    '<th>編號</th><th>層級</th><th>狀態</th><th>主題</th>'
                    '<th>四分</th><th>五分</th><th>十誦</th><th>僧祇</th><th>根有</th>'
                    '<th>位置</th><th>實質差異</th><th>證據</th>'
                    '</tr></thead><tbody>')
        for c in rows:
            mid, lv, st, topic, v4, v5, v10, vmk, vgu, pos, diff, xref, ev = c
            txt = H.escape((topic + diff).lower())
            body.append(
                f'<tr data-st="{st}" data-seg="{name}" data-lv="{H.escape(lv)}" data-txt="{txt}">'
                f'<td class="id">{mid}</td>'
                f'<td class="lv">{H.escape(lv)}</td>'
                f'<td class="st st-{st}" title="{ST_NAME.get(st,"")}">{st}</td>'
                f'<td class="topic">{H.escape(topic)}</td>'
                f'{cell(v4)}{cell(v5)}{cell(v10)}{cell(vmk)}{cell(vgu)}'
                f'<td class="pos">{H.escape(pos)}</td>'
                f'<td class="diff">{H.escape(diff)}</td>'
                f'<td class="ev">{H.escape(ev)}</td>'
                '</tr>')
        body.append('</tbody></table></div>')

    # 工具列
    st_chips = ''.join(
        f'<span class="chip" data-f="st" data-v="{k}">{k} {ST_NAME[k][:2]}</span>'
        for k in 'ABCD')
    seg_chips = ''.join(
        f'<span class="chip" data-f="seg" data-v="{n}">{n}</span>'
        for n, _c, _r in segs)
    lv_chips = ''.join(
        f'<span class="chip" data-f="lv" data-v="{x}">{x}</span>' for x in LV)

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>五部律綜合異同矩陣</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<nav>{''.join(nav)}</nav>
<main>
<h1>五部律綜合異同矩陣</h1>
<div class="lede">2,124 列，每列一稿之一個保留項。五欄記該律「有／無／未比」。
<strong>「無」是文獻學斷言，「未比」只是工作進度。</strong>
原表之「補證」欄多為「—」，此處從略，全文見 CSV。</div>
<div class="bar">
  <span class="lbl">狀態</span>{st_chips}
  <span class="lbl">主稿</span>{seg_chips}
  <span class="lbl">層級</span>{lv_chips}
  <input type="search" id="q" placeholder="搜索主題或差異…">
  <span class="count" id="cnt">{total:,} 項</span>
</div>
{''.join(body)}
</main>
</div>
<script>{JS}</script>
</body></html>"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8', newline='\n').write(page)
    print(f'written {OUT}')
    print(f'  分段：' + '、'.join(f'{n} {len(r)}' for n, _c, r in segs) + f'　合 {total}')
    print(f'  大小：{os.path.getsize(OUT)/1024:.0f} KB')


if __name__ == '__main__':
    main()
