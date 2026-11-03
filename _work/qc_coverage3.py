import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

def vol_n(v):
    return len([l for l in open(os.path.join(W, 'wufen', 'vol%02d.txt' % v), encoding='utf-8') if l.strip()])

def ids_from(text, v, n):
    got = set()
    # V-A～V-B
    for m in re.finditer(r'(\d+)\s*[-–]\s*(\d+)\s*[～~]\s*(\d+)\s*[-–]\s*(\d+)', text):
        if int(m.group(1)) == v and int(m.group(3)) == v:
            got.update(range(int(m.group(2)), int(m.group(4)) + 1))
    # V-A～B
    for m in re.finditer(r'(\d+)\s*[-–]\s*(\d+)\s*[～~]\s*(\d+)(?!\s*[-–])', text):
        if int(m.group(1)) == v:
            a, b = int(m.group(2)), int(m.group(3))
            if a <= b and b - a < 300:
                got.update(range(a, b + 1))
    # 段A～B
    for m in re.finditer(r'段\s*(\d+)\s*[～~\-–]\s*(\d+)', text):
        a, b = int(m.group(1)), int(m.group(2))
        if a <= b and b - a < 300:
            got.update(range(a, b + 1))
    # 段N
    for m in re.finditer(r'(?:段|第)\s*(\d+)\s*段?', text):
        got.add(int(m.group(1)))
    # A-B heuristic
    for m in re.finditer(r'(\d+)\s*[-–]\s*(\d+)', text):
        a, b = int(m.group(1)), int(m.group(2))
        if a == v:
            got.add(b)
        elif v != 1 and a <= 30 and a < b <= n:
            got.update(range(a, b + 1))
        elif v == 1 and a != 1 and a < b <= n:
            got.update(range(a, b + 1))
    # lists
    for m in re.finditer(r'段\s*([\d、，,\s]+)', text):
        for x in re.findall(r'\d+', m.group(1)):
            got.add(int(x))
    return got

print('vol total mentioned missing')
for v in range(1, 31):
    f = os.path.join(W, 'findings', 'vol%02d.md' % v)
    t = open(f, encoding='utf-8').read()
    cut = t.find('## 統計')
    body = t if cut < 0 else t[:cut]
    n = vol_n(v)
    ids = ids_from(body, v, n)
    missing = [x for x in range(1, n + 1) if x not in ids]
    print(v, n, len(ids), len(missing), missing[:20])
