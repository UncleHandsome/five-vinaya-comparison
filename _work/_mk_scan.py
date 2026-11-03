import io,re,sys
sys.stdout.reconfigure(encoding='utf-8')
base='<PROJ>/_work/'
md=io.open(base+'findings_mk/vol10-11.md',encoding='utf-8').read().split('\n')
chars='们这笔这还卖当说选给来买'
chars=set('们这钱还卖当说选给来买')
for i,l in enumerate(md):
    hit=[c for c in chars if c in l]
    if hit:
        kind='QUOTE' if l.strip().startswith('>') else ('CITE' if '『' in l else 'TEXT')
        print(i+1,kind,''.join(hit),'|',l[:120])
print('=== ascii leaks ===')
for i,l in enumerate(md):
    if re.search(r'[A-Za-z]',l) and '.txt' not in l and 'RECIPE' not in l:
        print(i+1,'|',l[:140])
print('=== check 段13 char ===')
def load(f):
    d={}
    for line in io.open(base+f,encoding='utf-8'):
        p=line.rstrip('\n').split('\t',1)
        if len(p)<2:continue
        try: d[int(p[0])]=p[1]
        except: pass
    return d
V10=load('sengqi/vol10.txt')
t=V10[13]
i=t.find('知地已，使知內錢坑中')
print(repr(t[i:i+30]))
