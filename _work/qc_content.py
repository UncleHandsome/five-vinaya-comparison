import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, '五分律_去重白話', '五分律_去重白話_合冊.md')
t = open(p, encoding='utf-8').read()

def norm(s):
    s = re.sub(r'[\s\u3000]', '', s)
    return re.sub(r'[^\u4e00-\u9fff]', '', s)

items = re.split(r'^### ', t, flags=re.M)[1:]
print('items', len(items))
missing = []
short = []
long = []
titles = {}
for it in items:
    title = it.split('\n')[0].strip()
    body = it
    # stop at next volume heading if any
    for key in ('- 位置', '- 四分律對照', '- 差異說明', '- 原文', '- 白話'):
        if key not in body:
            missing.append((title, key))
    q = ''.join(re.sub(r'^\s*>\s?', '', l) for l in body.split('\n') if l.strip().startswith('>'))
    b = ''
    m = re.search(r'^-\s*白話[^\n]*\n(.*)$', body, re.M | re.S)
    if m:
        b = m.group(1)
        b = b.split('\n### ')[0]
    qn, bn = len(norm(q)), len(norm(b))
    if qn >= 50:
        if bn < qn * 0.45:
            short.append((title, qn, bn))
        elif bn > qn * 3.2:
            long.append((title, qn, bn))
    titles[title] = titles.get(title, 0) + 1

print('missing fields', len(missing))
for x in missing[:10]:
    print('  MISSING', x)
print('short translations', len(short))
for x in short[:12]:
    print('  SHORT', x)
print('long translations', len(long))
for x in long[:12]:
    print('  LONG', x)
dups = [(k, v) for k, v in titles.items() if v > 1]
print('duplicate titles', len(dups))
for d in dups[:10]:
    print('  DUP', d)

hi = '这们时说过还进来对开关门问间长东车马鸟鱼龙风飞书写学觉见观听声义议论証识语话读谁请谢变边达运远连选阳阴队阶际随隐难页顶项顺须顾顿预领颇颈颊频颗题颜额饭饮饱饿馆驾骑骗鲜鸡鸣鸭鹅鹰麦黄齐齿龄龟个么儿几头尽层属岁'
print('simplified hits', ''.join(sorted(set(c for c in t if c in set(hi)))) or 'none')
print('chars', len(t), 'CJK', len(norm(t)))
