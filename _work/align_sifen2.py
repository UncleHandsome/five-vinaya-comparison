#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""白話四分律 → 四分律段 對齊

思路：白話是原文的逐句翻譯，次序一致，故做「單調」對齊即可。
以 IDF 加權的字元 bigram cosine 為相似度，帶寬依累積字數比例。

DP 狀態 dp[i][j]：前 i 段原文、前 j 段白話的最大得分
  - 略過原文段 i      ：dp[i-1][j] - gap
  - 把白話 j 歸給段 i ：dp[i][j-1] + 100*cos(段i, 白j) - base
第二式允許「一段原文對多段白話」（譯者把長段拆成數段），
正是舊版 1:1 配對做不到、以致大量白話被略過的原因。

用法：
    python align_sifen2.py --test 01-10
    python align_sifen2.py --build        # 產出 _work/sifen_plain.json
"""
import re, json, os, sys, glob, math, collections

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
PLAIN_DIR = os.path.join(ROOT, '白話四分律')
SIFEN_DIR = os.path.join(BASE, 'sifen')

RANGES = ['01-10', '11-21', '22-30', '31-37', '38-49', '50-60']
RANGE_SEGS = {
    '01-10': list(range(0, 13)),
    '11-21': list(range(13, 26)),
    '22-30': list(range(26, 38)),
    '31-37': [38],
    '38-49': list(range(39, 61)),
    '50-60': list(range(61, 75)),
}
RE_MARK = re.compile(r'^【\s*(白話直譯|義理通解|如何用心)')


def cjk(s):
    return re.sub(r'[^\u4e00-\u9fff]', '', s)


def toks(s):
    s = cjk(s)
    return [s[i:i + 2] for i in range(len(s) - 1)]


def load_segs():
    out = []
    for f in sorted(glob.glob(os.path.join(SIFEN_DIR, '*.txt'))):
        no = int(os.path.basename(f)[:3])
        for l in open(f, encoding='utf-8', errors='ignore'):
            l = l.rstrip('\n')
            if not l.strip():
                continue
            m = re.match(r'^(\d+)\t(.*)$', l)
            if m:
                out.append((no, int(m.group(1)), m.group(2)))
    return out


def load_plain(rng):
    """回傳 (段落清單, 每段所屬 block 序)"""
    p = os.path.join(PLAIN_DIR, rng + '.txt')
    lines = open(p, encoding='utf-8').read().split('\n')
    paras, blocks = [], []
    on, bidx = False, -1
    for l in lines:
        s = l.strip()
        if not s:
            continue
        m = RE_MARK.match(s)
        if m:
            on = (m.group(1) == '白話直譯')
            if on:
                bidx += 1
            continue
        if on:
            blocks.append(bidx)
            paras.append(s)
    return paras, blocks


class Sim:
    def __init__(self, corpus):
        df = collections.Counter()
        for t in corpus:
            df.update(set(t))
        N = len(corpus)
        self.idf = {k: math.log((N + 1) / (v + 1)) + 1.0 for k, v in df.items()}
        self.default = math.log(N + 1) + 1.0
        self.cache = {}

    def vec(self, s):
        v = self.cache.get(s)
        if v is None:
            c = collections.Counter(toks(s))
            v = {k: n * self.idf.get(k, self.default) for k, n in c.items()}
            nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
            v = {k: x / nrm for k, x in v.items()}
            self.cache[s] = v
        return v

    def cos(self, a, b):
        va, vb = self.vec(a), self.vec(b)
        if len(va) > len(vb):
            va, vb = vb, va
        return sum(x * vb.get(k, 0.0) for k, x in va.items())


def align(A, B, sim, band=0.22, gap=0.6, base=2.0):
    """回傳 assign[j] = 原文段索引（或 -1）"""
    n, m = len(A), len(B)
    la = [len(cjk(x)) for x in A]
    lb = [len(cjk(x)) for x in B]
    sa, sb = sum(la) or 1, sum(lb) or 1
    pa = [0.0] * (n + 1)
    for i in range(1, n + 1):
        pa[i] = pa[i - 1] + la[i - 1] / sa
    pb = [0.0] * (m + 1)
    for j in range(1, m + 1):
        pb[j] = pb[j - 1] + lb[j - 1] / sb

    NEG = -1e18
    prev = [NEG] * (m + 1)
    prev[0] = 0.0
    ptr = [[0] * (m + 1) for _ in range(n + 1)]
    for j in range(1, m + 1):
        prev[j] = prev[j - 1] - base          # 段 0 不存在，白話無處可歸
        ptr[0][j] = 2
    for i in range(1, n + 1):
        cur = [NEG] * (m + 1)
        cur[0] = prev[0] - gap
        ptr[i][0] = 1
        for j in range(1, m + 1):
            if abs(pa[i] - pb[j]) > band:
                continue
            best, op = prev[j] - gap, 1        # 略過段 i
            v = cur[j - 1] + 100.0 * sim.cos(A[i - 1], B[j - 1]) - base
            if v > best:
                best, op = v, 3
            cur[j] = best
            ptr[i][j] = op
        prev = cur
    # 回溯
    i, j = n, m
    assign = [-1] * m
    while j > 0:
        op = ptr[i][j] if i > 0 else 2
        if op == 3:
            assign[j - 1] = i - 1
            j -= 1
        elif op == 1:
            i -= 1
        else:
            j -= 1
    return assign


def to_plain(segs, paras, assign):
    """assign → {篇-段: 白話文字}"""
    out = collections.defaultdict(list)
    for j, i in enumerate(assign):
        if i >= 0:
            out[i].append(paras[j])
    return {'%03d-%d' % (segs[i][0], segs[i][1]): '\n'.join(ps) for i, ps in out.items()}


def build(out_path=None, verbose=True):
    allsegs = load_segs()
    plain, report = {}, []
    for rng in RANGES:
        keep = set(RANGE_SEGS[rng])
        segs = [x for x in allsegs if x[0] in keep]
        paras, _b = load_plain(rng)
        sim = Sim([t for no, sg, t in allsegs] + paras)
        assign = align([t for no, sg, t in segs], paras, sim)
        part = to_plain(segs, paras, assign)
        plain.update(part)
        miss = sum(1 for j in assign if j < 0)
        report.append((rng, len(segs), len(paras), miss, len(part)))
        if verbose:
            print('%s：段 %d／白話段 %d／未歸 %d／落段 %d' % (rng, len(segs), len(paras), miss, len(part)))
    if out_path:
        json.dump(plain, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        if verbose:
            print('寫出 %s（%d 段有白話，佔 %.1f%%）' % (
                out_path, len(plain), 100.0 * len(plain) / len(allsegs)))
    return plain, report


if __name__ == '__main__':
    if '--build' in sys.argv:
        build(os.path.join(BASE, 'sifen_plain.json'))
    elif '--test' in sys.argv:
        rng = sys.argv[sys.argv.index('--test') + 1]
        allsegs = load_segs()
        keep = set(RANGE_SEGS[rng])
        segs = [x for x in allsegs if x[0] in keep]
        paras, _b = load_plain(rng)
        sim = Sim([t for no, sg, t in allsegs] + paras)
        assign = align([t for no, sg, t in segs], paras, sim)
        miss = sum(1 for j in assign if j < 0)
        print('%s：段 %d／白話段 %d／未歸 %d' % (rng, len(segs), len(paras), miss))
        import random
        random.seed(3)
        idx = random.sample(range(len(paras)), 8)
        for j in sorted(idx):
            i = assign[j]
            print('=' * 74)
            if i >= 0:
                print('段[%03d-%d] %s' % (segs[i][0], segs[i][1], segs[i][2][:100]))
            print('白      %s' % paras[j][:100])
            if i >= 0:
                print('  cos=%.3f' % sim.cos(segs[i][2], paras[j]))
