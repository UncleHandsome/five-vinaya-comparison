p = '_work/assemble2.py'
t = open(p, encoding='utf-8').read()

start = t.index("vol2_paras = [l.rstrip('")
end = t.index("encoding='utf-8')]", start) + len("encoding='utf-8')]")
t = t[:start] + "vol2_paras = [l.rstrip('\\n').split('\\t', 1) for l in open(os.path.join(W, 'wufen', 'vol02.txt'), encoding='utf-8')]" + t[end:]

s = t.index("    intro = parsed[v]['intro'].strip()")
e = t.index("    for it in parsed[v]['items']:", s)
t = t[:s] + t[e:]

t = t.replace("'> %s\\n' % stats_line(v)]", "'> %s\\n' % stats_line(v), '']")
open(p, 'w', encoding='utf-8').write(t)
print('ok')
