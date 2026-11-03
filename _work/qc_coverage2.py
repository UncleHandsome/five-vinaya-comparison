import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

def vol_n(v):
    return len([l for l in open(os.path.join(W, 'wufen', 'vol%02d.txt' % v), encoding='utf-8') if l.strip()])

def ids_from(text, v):
    got = set()
    # V-A～V-B
    for m in re.finditer(r'(\d+)\s*[-–]\s*(\d+)\s*[～~]\s*(\d+)\s*[-–]\s*(\d+)', text):
        if int(m.group(1)) == v and int(m.group(3)) == v:
            got.update(range(int(m.group(2)), int(m.group(4)) + 1))
    # V-A～B (same volume)
    for m in re.finditer(r'(\d+)\s*[-–]\s*(\d+)\s*[～~]\s*(\d+)(?!\s*[-–])', text):
        if int(m.group(1)) == v:
            a, b = int(m.group(2)), int(m.group(3))
            if a <= b and b - a < 300:
                got.update(range(a, b + 1))
    # 段A～B / 段A-B
    for m in re.finditer(r'段\s*(\d+)\s*[～~\-–]\s*(\d+)', text):
        a, b = int(m.group(1)), int(m.group(2))
        if a <= b and b - a < 300:
            got.update(range(a, b + 1))
    # single 段N or 第N段
    for m in re.finditer(r'(?:段|第)\s*(\d+)\s*段?', text):
        got.add(int(m.group(1)))
    # V-A single (avoid range already)
    for m in re.finditer(r'(\d+)\s*[-–]\s*(\d+)', text):
        if int(m.group(1)) == v:
            got.add(int(m.group(2)))
    # lists after 段: 段3、5、7
    for m in re.finditer(r'段\s*([\d、，,\s]+)', text):
        for x in re.findall(r'\d+', m.group(1)):
            got.add(int(x))
    return got

print('vol total mentioned missing sample')
for v in range(1, 31):
    f = os.path.join(W, 'findings', 'vol%02d.md' % v)
    t = open(f, encoding='utf-8').read()
    cut = t.find('## 統計')
    body = t if cut < 0 else t[:cut]
    ids = ids_from(body, v)
    n = vol_n(v)
    missing = [x for x in range(1, n + 1) if x not in ids]
    print(v, n, len(ids), len(missing), missing[:15])
