import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')
OUT = os.path.join(W, 'sifen_chunks')
os.makedirs(OUT, exist_ok=True)

def load(name):
    p = os.path.join(W, 'sifen', name)
    return [l.rstrip('\n').split('\t', 1) for l in open(p, encoding='utf-8')]

def dump(rows, name, title):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as fh:
        fh.write('# %s\n' % title)
        for n, t in rows:
            fh.write('%s\t%s\n' % (n, t))

src = load('038__開頭_.txt')
dump([r for r in src if 1 <= int(r[0]) <= 70], 'shoujie_1.txt', '四分律受戒揵度 段1-70')
dump([r for r in src if 71 <= int(r[0]) <= 130], 'shoujie_2.txt', '四分律受戒揵度 段71-130')
dump([r for r in src if 131 <= int(r[0]) <= 185], 'shoujie_3.txt', '四分律受戒揵度 段131-185')
dump([r for r in src if 186 <= int(r[0]) <= 262], 'shuojie.txt', '四分律說戒揵度 段186-262')
dump([r for r in src if 263 <= int(r[0]) <= 330], 'anju.txt', '四分律安居揵度 段263-330')
dump(load('039_自恣揵度之二.txt'), 'zizi.txt', '四分律自恣揵度之二')
print('ok')
