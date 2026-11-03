import os, re, glob, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
OUT = os.path.join(ROOT, '五分律_去重白話')
os.makedirs(OUT, exist_ok=True)

META = {
1: '第一分初波羅夷法（上）',
2: '初波羅夷法（下）・僧殘法（一至六）',
3: '僧殘法（七至十三）',
4: '不定法・捨墮法（一至十三）',
5: '捨墮法（十四至三十）',
6: '單提法（一至二十一）',
7: '單提法（二十二至三十七）',
8: '單提法（三十八至六十三）',
9: '單提法（六十四至九十一）',
10: '悔過法・眾學法・七滅諍法',
11: '尼律波羅夷・尼律僧殘',
12: '尼律捨墮・尼律墮（上）',
13: '尼律墮（中）',
14: '尼律墮（下）・尼律悔過・尼律眾學',
15: '受戒法（上）',
16: '受戒法（中）',
17: '受戒法（下）',
18: '布薩法',
19: '安居法・自恣法',
20: '衣法（上）',
21: '衣法（下）・皮革法',
22: '藥法・食法・迦絺那衣法',
23: '滅諍法・羯磨法（上）',
24: '羯磨法（下）',
25: '破僧法・臥具法',
26: '雜法',
27: '威儀法',
28: '遮布薩法・別住法・調伏法',
29: '比丘尼法',
30: '五百集法・七百集法',
}

def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    s = re.sub(r'[^\u4e00-\u9fff]', '', s)
    return s

def vol_text(v):
    p = os.path.join(W, 'wufen', 'vol%02d.txt' % v)
    return ''.join(t for _, t in (l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8')))

def clean_quote_line(s):
    s = s.strip()
    if not s.startswith('>'):
        return s
    body = s.lstrip('>').strip()
    if body.startswith('底本：') or body.startswith('對校本：') or body.startswith('凡例'):
        return None
    m = re.match(r'^段\s*(\d+)\s*[（(](節錄|節引)[）)]\s*[：:]\s*(.*)$', body)
    if m:
        return '> **段%s（%s）**　%s' % (m.group(1), m.group(2), m.group(3))
    m = re.match(r'^段\s*(\d+)\s*[：:]\s*(.*)$', body)
    if m:
        return '> **段%s**　%s' % (m.group(1), m.group(2))
    m = re.match(r'^〔段([^〕]{1,12})〕\s*(.*)$', body)
    if m:
        return '> **段%s**　%s' % (m.group(1), m.group(2))
    m = re.match(r'^（段([^）]{1,12})）\s*(.*)$', body)
    if m:
        return '> **段%s**　%s' % (m.group(1), m.group(2))
    return '> ' + body if body else '>'

def clean_item(title, body):
    out = [title]
    for raw in body.split('\n'):
        s = raw.strip()
        if s.startswith('>'):
            c = clean_quote_line(s)
            if c is None:
                continue
            c = re.sub(r'(段\s*\d+\s*[–\-]\s*\d+\s*[：:])', '\\n>\\n> **\\1**　', c)
            c = re.sub(r'(段\s*\d+\s*[：:])', '\\n>\\n> **\\1**　', c)
            out.extend(c.split('\n'))
        else:
            out.append(raw.rstrip())
    t = '\n'.join(out)
    t = re.sub(r'^\s*-\s*', '- ', t, flags=re.M)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

parsed = {}
for v in range(1, 31):
    f = os.path.join(W, 'findings', 'vol%02d.md' % v)
    text = open(f, encoding='utf-8').read()
    title = re.search(r'^# (.*)$', text, re.M).group(1)
    # split sections by ## headings
    pos = [(m.start(), m.group(1)) for m in re.finditer(r'^## (.*)$', text, re.M)]
    intro = text[:pos[0][0]] if pos else text
    intro = re.sub(r'^# .*$', '', intro, flags=re.M).strip()
    sections = {}
    for i, (p, name) in enumerate(pos):
        end = pos[i+1][0] if i+1 < len(pos) else len(text)
        sections[name.strip()] = text[p:end]
    keep = sections.get('保留項', '')
    items_raw = re.split(r'^### ', keep, flags=re.M)[1:]
    items = []
    for it in items_raw:
        lines = it.split('\n')
        t = lines[0].strip()
        if not t or t.startswith('已知線索') or t.startswith('定稿補記'):
            continue
        items.append(clean_item('### ' + t, '\n'.join(lines[1:])))
    deletion = sections.get('刪除項（彙總）') or sections.get('刪除項') or ''
    doubts = sections.get('存疑', '')
    parsed[v] = {'title': title, 'intro': intro, 'items': items,
                 'deletion': deletion, 'doubts': doubts}

# recompute kept chars
stats = []
for v in range(1, 31):
    src = vol_text(v)
    total = len(src)
    kept = 0
    for it in parsed[v]['items']:
        for ln in it.split('\n'):
            if ln.strip().startswith('>'):
                q = re.sub(r'^\>\s*', '', ln.strip())
                q = re.sub(r'^\*\*[^*]+\*\*\s*', '', q)
                if q.startswith('（中略') or not q:
                    continue
                kept += len(norm(q))
    stats.append({'v': v, 'total': total, 'kept': kept, 'items': len(parsed[v]['items']),
                  'ratio': kept / total if total else 0})

with open(os.path.join(W, 'assembly_stats.json'), 'w', encoding='utf-8') as fh:
    json.dump(stats, fh, ensure_ascii=False, indent=1)

# build main document
def stats_line(v):
    s = stats[v-1]
    return '全卷 %s 字，本稿保留 %s 字（%.1f%%），保留 %d 項；其餘與四分律文意重複者刪略，詳見附錄一。' % (
        format(s['total'], ','), format(s['kept'], ','), s['ratio']*100, s['items'])

FANLI = '''# 五分律去重白話

以《五分律》（彌沙塞部）為底本，以《四分律》（曇無德部）為對校本；凡兩律文意重複者刪除，僅保留五分律獨有或具實質差異之內容，並譯為現代繁體中文。

## 凡例

一、底本：《五分律》三十卷，據本資料夾 `五分律/01-10原文.txt`、`11-20原文.txt`、`21-30原文.txt`。對校本：《四分律》六十卷，據 `四分律/` 各檔；《十誦律》六十一卷，據 `十誦律/` 各檔。三律分屬不同部派（五分律屬分別說系，四分律屬法藏部，十誦律屬說一切有部），譯語、詳略、次第本有差異，故不以字句異同為去取，而以「戒條／制度／事件」為單位。

二、判重口徑：
1. 四分律有同一戒、同一制度、同一事件，且內容實質相同者，視為重複，刪除。
2. 同一戒或同一事件中，五分律有實質增異者（戒條有無、判罪輕重、程序羯磨、法數清單、關鍵人物或結局不同，或四分律全無之獨立故事），保留其增異部分。
3. 僅屬譯語、詳略、修辭、次序不同，或名相體系相同而用字不同者，不保留。
4. 五分律僅將四分律一句話擴寫為同一情節之細節者，不保留；四分律全無、五分律自有完整情節者，保留。

三、保留比例：全書三十四萬一千餘字，本稿保留約四萬字，約百分之十二。各卷比例見「全書統計」。未保留部分並非全無價值，而是與四分律大體相應；其刪略理由逐卷列於附錄一，存疑未決者列於附錄二。

四、編次：仍依五分律卷次。每卷先標篇名、範圍與刪略統計，再列保留項。每項含「位置」（底本段號）、「四分律對照」、「差異說明」、「原文」、「白話」五目；凡判為「四分所無」之項，另增「十誦律對照」一目，附於「四分律對照」之後。原文皆逐字迻錄，段號以便覆核；白話力求逐句對應，術語首次出現時以括號簡註。

四之一、十誦律對照之體例：此目專為「四分所無」諸項而設。四分律既無，尚須確認是否為五分律所獨有；若十誦律亦有同條，則此項非孤本，僅屬部派間之詳略增異。故逐項以《十誦律》全庫檢索，凡得同條者標明卷、段並迻錄其文，於說明中判其為「同條」、「同條增異」、「同條減略」或「同題異制」；遍查不得者，記其查詞，以便覆核。查詞至少三組，蓋兩律譯語懸殊（如五分律「忍辱第一道」十誦律作「忍是勤中上」），單詞檢索易致失實。

五、引文符號：`（中略：段X–Y）` 表示前後引文之間有省略，其後或附一句說明所略何事，作 `（中略：段X–Y，述……）`；`（節引）`、`（節錄）` 表示只取該段一部分。方括號內之補字、異體字均照底本，不加改動。

六、資料限制：
1. 本資料夾《四分律》尼律單提法第一至八十六戒僅存戒條列表，緣起從缺；此部分之比對以戒條有無與內容異同為準，不以緣起有無判為五分律獨有。
2. 《四分律》自恣揵度之一未收入本資料夾，卷十九自恣法之比對以其餘可得部分及全庫檢索為據。
3. 部分篇章（如五分律「威儀法」「羯磨法」）在四分律無獨立對應篇章，僅能就內容相近之揵度比對，詳見各卷說明。
4. 上傳之差異分析（附件）已逐條核實；其誤記、過度推斷或版本不合者，於附錄三標明，不據以入稿。
5. 「十誦律對照」一目僅施於判為「四分所無」之一百一十項，非逐項皆備；其餘諸項與四分律既有對應，已無孤本之疑，不另作十誦律之比對。此目旨在消除「四分所無即五分獨有」之假性判定，不代全律之交叉校勘。

## 全書統計

| 卷 | 篇目 | 全卷字數 | 保留字數 | 比例 | 保留項數 |
|---:|---|---:|---:|---:|---:|
'''

lines = [FANLI]
for s in stats:
    lines.append('| %d | %s | %s | %s | %.1f%% | %d |' % (
        s['v'], META[s['v']], format(s['total'], ','), format(s['kept'], ','), s['ratio']*100, s['items']))
tt = sum(s['total'] for s in stats); tk = sum(s['kept'] for s in stats); ti = sum(s['items'] for s in stats)
lines.append('| **合計** | 三十卷 | **%s** | **%s** | **%.1f%%** | **%d** |' % (
    format(tt, ','), format(tk, ','), tk/tt*100, ti))
lines.append('\n> 字數以中文字計，不含標點、段號與空白。保留字數指本稿引文之字數；同一段若分段引用，僅計一次。\n')

# TOC
lines.append('## 目錄\n')
for s in stats:
    lines.append('- [卷%d　%s](#卷%d)（%d 項）' % (s['v'], META[s['v']], s['v'], s['items']))
lines.append('- [附錄一：刪略總表](#附錄一刪略總表)')
lines.append('- [附錄二：存疑總表](#附錄二存疑總表)')
lines.append('- [附錄三：上傳差異分析核實報告](#附錄三上傳差異分析核實報告)')
lines.append('- [附錄四：工作方法與資料限制](#附錄四工作方法與資料限制)\n')

# volumes
for v in range(1, 31):
    lines.append('\n---\n')
    lines.append('## 卷%d　%s\n' % (v, META[v]))
    lines.append('> %s\n' % stats_line(v))
    intro = parsed[v]['intro'].strip()
    if intro:
        # keep only first paragraph, drop metadata-ish lines
        para = [p.strip() for p in re.split(r'\n\s*\n', intro) if p.strip()]
        if para:
            p0 = para[0]
            p0 = re.sub(r'^> ', '', p0)
            if len(p0) > 320:
                p0 = p0[:320] + '……'
            lines.append('> %s\n' % p0.replace('\n', ' '))
    for it in parsed[v]['items']:
        lines.append(it.strip() + '\n')

main = '\n'.join(lines)

# appendices
app = ['\n---\n', '# 附錄一：刪略總表\n',
       '下表逐卷列出未保留之段落及其四分律對應。段號為底本段號；「遍查未見」表示已檢索四分律全庫未得對應。此表為刪略之審計紀錄，非閱讀正文。\n']
for v in range(1, 31):
    app.append('\n## 卷%d　%s\n' % (v, META[v]))
    d = parsed[v]['deletion'].strip()
    d = re.sub(r'^## .*$', '', d, flags=re.M).strip()
    app.append(d + '\n')

app += ['\n---\n', '# 附錄二：存疑總表\n',
        '以下各條界限難定，暫未入正文，另記待裁。\n']
for v in range(1, 31):
    d = parsed[v]['doubts'].strip()
    d = re.sub(r'^## .*$', '', d, flags=re.M).strip()
    if d:
        app.append('\n## 卷%d　%s\n' % (v, META[v]))
        app.append(d + '\n')

appendix1 = '\n'.join(app)

open(os.path.join(OUT, '五分律_去重白話_合冊.md'), 'w', encoding='utf-8').write(main + '\n' + appendix1)
# split by source file groups
for name, a, b in (('卷一至卷十', 1, 10), ('卷十一至卷二十', 11, 20), ('卷二十一至卷三十', 21, 30)):
    chunk = main.split('\n## 卷')[0]  # header
    # rebuild subset
    sub = []
    for v in range(a, b+1):
        sub.append('\n---\n## 卷%d　%s\n' % (v, META[v]))
        sub.append('> %s\n' % stats_line(v))
        intro = parsed[v]['intro'].strip()
        if intro:
            para = [p.strip() for p in re.split(r'\n\s*\n', intro) if p.strip()]
            if para:
                p0 = re.sub(r'^> ', '', para[0])
                if len(p0) > 320:
                    p0 = p0[:320] + '……'
                sub.append('> %s\n' % p0.replace('\n', ' '))
        for it in parsed[v]['items']:
            sub.append(it.strip() + '\n')
    body = '\n'.join(sub)
    head = main.split('\n## 卷')[0]
    open(os.path.join(OUT, '五分律_去重白話_%s.md' % name), 'w', encoding='utf-8').write(head + body)

print('items total', ti, 'kept', tk, 'total', tt, 'ratio', round(tk/tt*100, 1))
print('written to', OUT)
