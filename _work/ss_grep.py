# -*- coding: utf-8 -*-
import os, re, sys, glob

BASE = os.path.dirname(os.path.abspath(__file__))

def load(path, kind):
    out = []
    with open(path, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            if kind == 'sifen':
                m = re.match(r'^(\d+)\t(.*)$', line)
                if m:
                    out.append((m.group(1), m.group(2)))
                else:
                    out.append((str(i), line))
            else:
                m = re.match(r'^(\d+-\d+)\t(.*)$', line)
                if m:
                    out.append((m.group(1), m.group(2)))
                else:
                    out.append(('?', line))
    return out

def corpus(which):
    if which == 'sifen':
        files = sorted(glob.glob(os.path.join(BASE, 'sifen', '*.txt')))
        for p in files:
            yield os.path.basename(p), load(p, 'sifen')
    elif which == 'wufen':
        files = sorted(glob.glob(os.path.join(BASE, 'bundles', 'W*.txt')))
        for p in files:
            yield os.path.basename(p), load(p, 'wufen')

def search(pat, which, maxhits=6, width=90):
    rx = re.compile(pat)
    n = 0
    for name, paras in corpus(which):
        for seg, text in paras:
            for m in rx.finditer(text):
                s = max(0, m.start() - width)
                e = min(len(text), m.end() + width)
                print(f'{which}\t{name}\t{seg}\t…{text[s:e]}…')
                n += 1
                break
            if n >= maxhits:
                return
    if n == 0:
        print(f'{which}\tNOHIT\t{pat}')

if __name__ == '__main__':
    pat = sys.argv[1]
    which = sys.argv[2] if len(sys.argv) > 2 else 'both'
    mh = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    if which in ('sifen', 'both'):
        search(pat, 'sifen', mh)
    if which in ('wufen', 'both'):
        search(pat, 'wufen', mh)
