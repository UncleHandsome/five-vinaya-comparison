# -*- coding: utf-8 -*-
"""QC: verify cited quotes exist in the cited source paragraphs."""
import io, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
B = os.path.dirname(os.path.abspath(__file__))

def load(fn, bundle=False):
    d = {}
    for l in io.open(os.path.join(B, fn), encoding='utf-8'):
        if '\t' in l:
            k, t = l.rstrip('\n').split('\t', 1)
            d[k] = t
    return d

SF = {}
for fn in os.listdir(os.path.join(B, 'sifen')):
    if fn.endswith('.txt'):
        SF[fn[:3]] = load('sifen/' + fn)
WF = {}
for v in range(1, 31):
    p = 'wufen/vol%02d.txt' % v
    if os.path.exists(os.path.join(B, p)):
        WF['%02d' % v] = load(p)
W35 = load('bundles/W35.txt')
W28 = load('bundles/W28.txt')

def para(kind, num):
    if kind == 'sf':
        a, b = num.split('-')
        return SF.get(a, {}).get(b)
    else:
        if num.startswith('30-'):
            return W35.get(num)
        if num.startswith('26-'):
            return W28.get(num)
        a, b = num.split('-')
        return WF.get(a.zfill(2), {}).get(b)

txt = io.open('findings_ss/vol61a.md', encoding='utf-8').read()
bad = 0
for line in txt.splitlines():
    m = re.match(r'- (四分律|五分律)對照：(.*)', line)
    if not m:
        continue
    kind = 'sf' if m.group(1) == '四分律' else 'wf'
    body = m.group(2)
    # find citations like 067 段10, 30-55, 26-6, 18-90
    for cm in re.finditer(r'(?:(\d{3}) 段(\d+)|(\d{2}-\d+))', body):
        if cm.group(1):
            pid = cm.group(1) + '-' + cm.group(2)
        else:
            pid = cm.group(3)
        t = para(kind, pid)
        if not t:
            print('NO PARA', kind, pid)
            bad += 1
            continue
        # quotes in this citation segment (up to next citation or end)
        start = cm.end()
        nxt = re.search(r'(?:\d{3} 段\d+|\d{2}-\d+)', body[start:])
        seg = body[start:start + (nxt.start() if nxt else len(body))]
        for q in re.findall(r'「([^」]*)」', seg):
            for part in q.split('……'):
                part = part.strip('……')
                if part and part not in t:
                    print('MISS', kind, pid, repr(part), '| para:', t[:60])
                    bad += 1
print('bad =', bad)
