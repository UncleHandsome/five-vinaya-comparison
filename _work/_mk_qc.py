import io,re,sys,os
sys.stdout.reconfigure(encoding='utf-8')
base='<PROJ>/_work/'
def load(f):
    d={}
    for line in io.open(base+f,encoding='utf-8'):
        p=line.rstrip('\n').split('\t',1)
        if len(p)<2:continue
        try: d[int(p[0])]=p[1]
        except: pass
    return d
V={'10':load('sengqi/vol10.txt'),'11':load('sengqi/vol11.txt')}
REF={}
def ref(f):
    if f not in REF:
        REF[f]=load(f)
    return REF[f]
md=io.open(base+'findings_mk/vol10-11.md',encoding='utf-8').read()
errs=[]
# 1) 原文 quotes
pat=re.compile(r'>\s*〔卷(\d+)·段(\d+)〕(.*)')
for m in pat.finditer(md):
    v,n,q=m.group(1),int(m.group(2)),m.group(3).strip()
    parts=[p for p in re.split(r'…|……|\.\.\.',q) if p.strip()]
    for p in parts:
        p=p.strip()
        if p.startswith('（') or p.startswith('('):
            continue
        if p not in V[v].get(n,''):
            errs.append(('原文', '卷%s段%d'%(v,n), p[:40]))
# 2) 對照 citations: file 段N：『...』
pat2=re.compile(r'([\w\u4e00-\u9fff\.\-_0-9]+\.txt)\s*段(\d+)：『(.+?)』',re.S)
for m in pat2.finditer(md):
    f,n,q=m.group(1),int(m.group(2)),m.group(3)
    cand=[d for d in ['sifen','wufen','shisong'] if os.path.exists(base+d+'/'+f)]
    if not cand:
        errs.append(('對照檔不存在',f,'段%d'%n)); continue
    t=ref(cand[0]+'/'+f).get(n,'')
    if q.replace(' ','') not in t.replace(' ',''):
        errs.append(('對照',cand[0]+'/'+f,'段%d'%n,q[:40]))
# 3) simplified chars check
simp='们无个来说对过还给让这那时间财务买卖让钱记设认选后听属谁为么东西当尽种类记数据点点关阀队虽双辞'
found={}
for ch in set(simp):
    if ch in md: found[ch]=md.count(ch)
# 4) coverage
def segs(v): return set(range(1,max(V[v])+1))
retained=set()
for m in re.finditer(r'卷(\d+)·段(\d+)',md):
    retained.add((m.group(1),int(m.group(2))))
# parse 刪除表 ranges
deleted=set()
for line in md.split('\n'):
    if line.startswith('| 卷'):
        cell=line.split('|')[1].strip()
        for mm in re.finditer(r'卷(\d+)·段(\d+)(?:～段?(\d+))?',cell):
            v=mm.group(1); a=int(mm.group(2)); b=int(mm.group(3)) if mm.group(3) else a
            for k in range(a,b+1): deleted.add((v,k))
for v,n in retained: deleted.discard((v,n))
missing=[]
for v in ['10','11']:
    for k in segs(v):
        if (v,k) not in retained and (v,k) not in deleted: missing.append('卷%s段%d'%(v,k))
double=sorted(x for x in retained if x in deleted)
print('QUOTE/CITE ERRORS:',len(errs))
for e in errs: print('  ',e)
print('SIMPLIFIED:',found)
print('MISSING SEGMENTS:',missing)
print('DOUBLE:',double)
