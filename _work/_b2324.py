# -*- coding: utf-8 -*-
import io, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))

def load(p):
    d = {}
    for l in io.open(os.path.join(BASE, p), encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        seg, txt = l.split('\t', 1)
        d[seg] = txt
    return d

SRC = {
    'q23': ('sengqi/vol23.txt', '卷23'),
    'q24': ('sengqi/vol24.txt', '卷24'),
}
for f in os.listdir(os.path.join(BASE, 'sifen')):
    SRC['sf:' + f] = ('sifen/' + f, f)
for f in os.listdir(os.path.join(BASE, 'wufen')):
    SRC['wf:' + f] = ('wufen/' + f, f)
for f in os.listdir(os.path.join(BASE, 'shisong')):
    SRC['ts:' + f] = ('shisong/' + f, f)

CACHE = {}
def seg_text(src, seg):
    if src not in CACHE:
        CACHE[src] = load(SRC[src][0])
    d = CACHE[src]
    if seg not in d:
        raise SystemExit('MISSING SEG %s %s' % (src, seg))
    return d[seg]

errs = []
quoted = 0

def repl(m):
    global quoted
    body = m.group(1)
    parts = body.split('|')
    if len(parts) == 3:
        parts = parts + [parts[2]]
    if len(parts) != 4:
        errs.append('BAD PLACEHOLDER: ' + body)
        return m.group(0)
    src, seg, a, b = parts
    txt = seg_text(src, seg)
    i = txt.find(a)
    if i < 0:
        errs.append('ANCHOR-A NOT FOUND [%s 段%s]: %s' % (src, seg, a[:30]))
        return m.group(0)
    j = txt.find(b, i)
    if j < 0:
        errs.append('ANCHOR-B NOT FOUND [%s 段%s]: %s' % (src, seg, b[:30]))
        return m.group(0)
    out = txt[i:j + len(b)]
    if src.startswith('q'):
        quoted += len(out)
    return out

tpl = io.open(os.path.join(BASE, '_tpl2324.md'), encoding='utf-8').read()
out = re.sub(r'\{\{Q:([^}]*)\}\}', repl, tpl)

if errs:
    for e in errs:
        print(e)
    raise SystemExit('FAILED with %d errors' % len(errs))

io.open(os.path.join(BASE, 'findings_mk', 'vol23-24.md'), 'w', encoding='utf-8').write(out)

# stats
v23 = load('sengqi/vol23.txt'); v24 = load('sengqi/vol24.txt')
n23 = sum(len(x) for x in v23.values()); n24 = sum(len(x) for x in v24.values())
print('vol23 chars', n23, 'vol24 chars', n24, 'total', n23 + n24)
print('quoted (sengqi only) chars', quoted)
print('ratio %.2f%%' % (100.0 * quoted / (n23 + n24)))
