# -*- coding: utf-8 -*-
import re, io
md=open('_work/findings_ss/vol42-43.md',encoding='utf-8').read()
lines=md.splitlines()
# collect quoted originals
quotes=[]
for ln in lines:
    if ln.startswith('  > ') and '（節錄）' not in ln:
        quotes.append(ln[4:].strip())
print('quotes',len(quotes),'chars',sum(len(q) for q in quotes))
# source texts
def vol(v):
    return ''.join(ln.split('\t',1)[1] for ln in open('_work/shisong/vol%s.txt'%v,encoding='utf-8').read().splitlines() if '\t' in ln)
src=vol('42')+vol('43')
bad=[q for q in quotes if q not in src]
print('quotes not found:',len(bad))
for q in bad: print(repr(q[:60]))
# 對照 quotes
sifen=''
for f in ['026_八波羅夷法.txt','027_十七僧殘法之初.txt','028_十七僧殘法之餘.txt']:
    sifen+=''.join(ln.split('\t',1)[1] for ln in open('_work/sifen/'+f,encoding='utf-8').read().splitlines() if '\t' in ln)
wufen=''
for f in ['W09.txt','W10.txt']:
    for ln in open('_work/bundles/'+f,encoding='utf-8'):
        p=ln.rstrip('\n').split('\t')
        if len(p)>=2 and re.match(r'^\d+-\d+$',p[0]): wufen+=p[1]
cites=[]
for ln in lines:
    if ln.startswith('- 四分律對照：') or ln.startswith('- 五分律對照：'):
        cites+=re.findall(r'「([^」]+)」',ln)
print('cites',len(cites))
badc=[]
for c in cites:
    if c not in sifen and c not in wufen: badc.append(c)
print('cites not found:',len(badc))
for c in badc: print(repr(c[:80]))
