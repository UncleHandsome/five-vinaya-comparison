# -*- coding: utf-8 -*-
"""Search keywords within 四分律 063-065 and 五分律 卷26-27 (W28)."""
import io, os, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))

def load_dir(files):
    out = []
    for fn, tag in files:
        p = os.path.join(BASE, fn)
        if not os.path.exists(p):
            continue
        for line in io.open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            if '\t' in line:
                k, v = line.split('\t', 1)
            else:
                k, v = '?', line
            out.append((tag, k, v))
    return out

CORP = load_dir([('sifen/063_雜揵度之一.txt', '四063'),
                 ('sifen/064_雜揵度之二.txt', '四064'),
                 ('sifen/065_雜揵度之三.txt', '四065'),
                 ('wufen/vol26.txt', '五26'),
                 ('wufen/vol27.txt', '五27')])

def search(kw, width=60, maxhits=8):
    print('===== %s' % kw)
    n = 0
    for tag, k, v in CORP:
        i = v.find(kw)
        if i >= 0:
            s = max(0, i - width)
            print('%-6s %-5s ...%s...' % (tag, k, v[s:i + width + 20]))
            n += 1
            if n >= maxhits:
                break
    if not n:
        print('  NOHIT')
    print()

if __name__ == '__main__':
    for kw in sys.argv[1:]:
        search(kw)
