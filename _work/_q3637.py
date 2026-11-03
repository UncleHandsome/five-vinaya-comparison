# -*- coding: utf-8 -*-
import re, json
def load(f):
    d={}
    for l in open(f,encoding='utf-8').read().split('\n'):
        if not l.strip(): continue
        m=re.match(r'^(\d+)\t(.*)$', l)
        if m: d[int(m.group(1))]=m.group(2)
    return d
V36=load('sengqi/vol36.txt'); V37=load('sengqi/vol37.txt')
def seg(v,n): return (V36 if v==36 else V37)[n]
def sub(v,n,a=None,b=None):
    t=seg(v,n)
    i=0
    if a:
        i=t.index(a)
    j=len(t)
    if b:
        j=t.index(b,i)+len(b)
    return t[i:j]
qs={
 'q1':sub(36,3,'佛言：「得。瞿曇彌！','是名篤信善女人受持此比尼五事利益。」'),
 'q2':seg(36,9),
 'q3':seg(36,10),
 'q4':seg(36,13),
 'q5':seg(36,21)+'\n'+seg(36,22),
 'q6':seg(36,29)+'\n'+seg(36,41),
 'q7':seg(36,30),
 'q8':seg(36,52),
 'q9':sub(36,53,'若比丘尼見他犯重罪','得偷蘭遮。'),
 'q10':sub(36,58,'如法比尼者','邊見。'),
 'q11':seg(36,63),
 'q12':sub(36,70,'若比丘尼諍訟相言','僧伽婆尸沙。」')+'\n'+seg(36,74),
 'q13':seg(36,79),
 'q14':sub(36,81,'復次諸比丘尼道路行','佛言：「不欲，無罪。」'),
 'q15':seg(36,86),
 'q16':seg(36,106),
 'q17':seg(36,109),
 'q18':seg(36,111)+'\n'+seg(36,121),
 'q19':seg(36,116)+'\n'+seg(36,117),
 'q20':seg(36,118),
 'q21':seg(36,124),
 'q22':sub(36,125,'若比丘尼知比丘尼僧和合如法比尼作舉羯磨、未作如法，先不語僧自與捨','僧伽婆尸沙。」')+'\n'+seg(36,132),
 'q23':seg(36,134),
 'q24':sub(36,135,'若比丘尼無漏心','僧伽婆尸沙。」')+'\n'+seg(36,141),
 'q25':seg(36,142),
 'q26':sub(37,3,'佛語大愛道','僧伽婆尸沙。」'),
 'q27':seg(37,11),
 'q28':sub(37,28,'阿梨耶僧聽！已說十九','是事如是持。」'),
 'q29':sub(36,51,'若比丘尼明相出時','如比丘覆藏中廣說。'),
 'q30':sub(36,11,'若比丘尼共三種行婬','無罪。'),
}
for k in ['q%d'%i for i in range(1,31)]:
    print('=====',k,len(qs[k]))
    print(qs[k])
json.dump(qs,open('_q3637.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
