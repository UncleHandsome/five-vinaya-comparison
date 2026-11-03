# -*- coding: utf-8 -*-
import io, json, os

BASE = r"<PROJ>\_work"
SRC = {"29": os.path.join(BASE, "sengqi", "vol29.txt"),
       "30": os.path.join(BASE, "sengqi", "vol30.txt")}

SEG = {}
for v, p in SRC.items():
    t = io.open(p, encoding="utf-8").read()
    d = {}
    for L in t.split("\n"):
        if "\t" in L:
            n, s = L.split("\t", 1)
            d[int(n)] = s
    SEG[v] = d

def q(v, seg, start=None, end=None):
    s = SEG[v][seg]
    if start is None:
        return s
    i = s.find(start)
    assert i >= 0, "START NOT FOUND vol%s seg%d: %r" % (v, seg, start)
    j = s.find(end, i)
    assert j >= 0, "END NOT FOUND vol%s seg%d: %r" % (v, seg, end)
    return s[i:j+len(end)]

QUOTES = []
def Q(v, seg, start, end):
    txt = q(v, seg, start, end)
    QUOTES.append((v, seg, txt))
    return "> 〔卷%s·段%d〕%s" % (v, seg, txt)
