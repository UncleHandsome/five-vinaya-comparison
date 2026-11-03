import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

def vol_n(v):
    return len([l for l in open(os.path.join(W, 'wufen', 'vol%02d.txt' % v), encoding='utf-8') if l.strip()])

def ids_from(text, v):
    got = set()
    # vol-para ranges: 2-73～2-76 or 1-3
    for m in re.finditer(r'(\d+)\s*[-–]\s*(\d+)', text):
        a, b = int(m.group(1)), int(m.group(2))
        if a == v:
            for x in range(b, min(b, 999) + 1):
                got.add(x); break
    # para ranges after 段
    for m in re.finditer(r'段\s*(\d+)\s*[～~\-–]\s*(\d+)', text):
        a, b = int(m.group(1)), int(m.group(2))
        if a <= b and b - a < 300:
            got.update(range(a, b + 1))
    # single 段N or 第N段
    for m in re.finditer(r'(?:段|第)\s*(\d+)\s*段?', text):
        got.add(int(m.group(1)))
    # bare 1-3 style already handled; add trailing numbers after 段 lists
    for m in re.finditer(r'段\s*(\d+)(?:\s*[、，,]\s*(\d+))+', text):
        for x in re.findall(r'\d+', m.group(0)):
            got.add(int(x))
    return got

print('vol total mentioned missing sample')
for v in range(1, 31):
    f = os.path.join(W, 'findings', 'vol%02d.md' % v)
    t = open(f, encoding='utf-8').read()
    # take 保留項 + 刪除項 + 存疑 (exclude 統計)
    cut = t.find('## 統計')
    body = t if cut < 0 else t[:cut]
    ids = ids_from(body, v)
    n = vol_n(v)
    missing = [x for x in range(1, n + 1) if x not in ids]
    print(v, n, len(ids), len(missing), missing[:12])
