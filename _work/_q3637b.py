# -*- coding: utf-8 -*-
import re, json
def load(f):
    d={}
    for l in open(f,encoding='utf-8').read().split('\n'):
        if not l.strip(): continue
        m=re.match(r'^(\d+)\t(.*)$', l)
        if m: d[int(m.group(1))]=m.group(2)
    return d
V={36:load('sengqi/vol36.txt'),37:load('sengqi/vol37.txt')}
QD={
 1:[(36,3,'爾時大愛道瞿曇彌白佛言','是名篤信善女人受持此比尼五事利益。」')],
 2:[(36,9,None,None)],
 3:[(36,10,None,None)],
 4:[(36,13,None,None)],
 5:[(36,21,None,None),(36,22,None,None)],
 6:[(36,29,None,None),(36,41,None,None)],
 7:[(36,30,None,None)],
 8:[(36,52,None,None)],
 9:[(36,53,'若比丘尼見他犯重罪','得偷蘭遮。')],
 10:[(36,58,'如法比尼者','邊見。')],
 11:[(36,63,None,None)],
 12:[(36,70,'若比丘尼諍訟相言','僧伽婆尸沙。」'),(36,74,None,None)],
 13:[(36,79,None,None)],
 14:[(36,81,'復次諸比丘尼道路行','佛言：「不欲，無罪。」')],
 15:[(36,86,None,None)],
 16:[(36,106,None,None)],
 17:[(36,109,None,None)],
 18:[(36,110,None,None),(36,111,None,None),(36,121,None,None)],
 19:[(36,116,None,None),(36,117,None,None)],
 20:[(36,118,None,None)],
 21:[(36,124,None,None)],
 22:[(36,125,'若比丘尼知比丘尼僧和合如法比尼作舉羯磨、未作如法，先不語僧自與捨','僧伽婆尸沙。」'),(36,132,None,None)],
 23:[(36,134,None,None)],
 24:[(36,135,'若比丘尼無漏心','僧伽婆尸沙。」'),(36,136,None,None),(36,137,None,None),(36,138,None,None),(36,139,None,None),(36,140,None,None),(36,141,None,None)],
 25:[(36,142,None,None)],
 26:[(37,3,'佛語大愛道','僧伽婆尸沙。」')],
 27:[(37,11,None,None)],
 28:[(37,28,'阿梨耶僧聽！已說十九','是事如是持。」')],
 29:[(37,13,'佛告大愛道：「依止舍衛城住比丘尼皆悉令集','僧伽婆尸沙。」')],
 30:[(37,24,'佛告大愛道：「依止迦維羅衛住比丘尼皆悉令集','僧伽婆尸沙。」')],
 31:[(36,54,'若不捨者，僧中應作求聽羯磨','僧今亦當三諫令捨此事。」')],
 32:[(36,18,'爾時世尊制戒不聽比丘尼阿練若處住','寄釋種家住')],
 33:[(36,75,None,None),(36,76,None,None)],
 34:[(36,48,None,None),(36,49,None,None),(36,50,None,None)],
 35:[(36,105,None,None)],
 36:[(36,120,None,None)],
 37:[(36,78,None,None)],
 38:[(36,12,None,None)],
 39:[(36,87,'佛住王舍城','取得羯暮女為婦。'),(36,101,'於迦葉佛前發願','如《七女經》中廣說。')],
 40:[(36,11,None,None)],
 41:[(36,51,'若比丘尼明相出時','如比丘覆藏中廣說。')],
 44:[(36,12,'云何受樂？','彼以食為樂。')],
 45:[(36,12,'又如破癰熱鐵烙身','不受樂者亦復如是。')],
 43:[(36,59,None,None),(36,60,None,None),(36,61,None,None)],
 42:[(36,31,'若比丘尼漏心，與漏心男子申手內住','不應共住。」'),(36,33,None,None),(36,34,None,None),(36,35,None,None),(36,36,None,None),(36,37,None,None),(36,38,None,None),(36,39,None,None)],
}
def get(vol,seg,a=None,b=None):
    t=V[vol][seg]
    i=t.index(a) if a else 0
    j=(t.index(b,i)+len(b)) if b else len(t)
    return t[i:j]
out={}; lens={}
for k,v in QD.items():
    parts=[]
    for (vol,seg,a,b) in v:
        parts.append((vol,seg,get(vol,seg,a,b)))
    out[str(k)]=parts
    lens[str(k)]=sum(len(p[2]) for p in parts)
json.dump(out,open('_q3637b.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
tot=0
for k in sorted(lens,key=int):
    print(k,lens[k]); tot+=lens[k]
print('TOTAL',tot)
