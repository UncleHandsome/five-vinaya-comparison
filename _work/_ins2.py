# -*- coding: utf-8 -*-
import re, io
p='findings_mk/vol12-13.md'
s=io.open(p,encoding='utf-8').read()
cut=s.index('## 敘事抽取')
head, tail = s[:cut], s[cut:]

new = u"""### 7. 諍事「三處起、三處捨、三處取、三處滅」之法數，三律俱無
- 位置：卷12·段42、卷13·段13
- 四分律對照：遍查未見（查詢詞：「三處起」、「三處捨」；sifen 全庫零筆）
- 五分律對照：遍查未見（查詢詞：「三處起」、「三處捨」；wufen 全庫零筆）
- 十誦律對照：遍查未見（查詢詞：「三處起」、「三處捨」；shisong 全庫零筆）
- 差異說明：本律於現前毘尼、多覓毘尼二處，皆以「諍事有三處起——若一人、若眾多、若僧；亦應三處捨、三處取、三處滅」為總綱，把諍事之發起、棄捨、領取、息滅一律歸約為「一人／眾多／僧」三格。三律於滅諍但言「應集僧」、「現前」等，無此三格之對稱結構，亦無「三處捨、三處取」之說。
- 原文：
  > 〔卷12·段42〕優波離！諍事有三處起：若一人、若眾多、若僧，亦應三處捨、三處取、三處滅。
- 白話：
  優波離！諍事有三處生起：或者一人、或者眾多人、或者僧團；也就應當在三處棄捨、在三處領取、在三處息滅。

"""
marker = u'### 7. 滅諍人五法為'
assert marker in head
head = head.replace(marker, new + marker, 1)

# sequential renumber within 保留項 section
cnt=[0]
def ren(m):
    cnt[0]+=1
    return '### %d. '%cnt[0]
head = re.sub(r'^### \d+\. ', ren, head, flags=re.M)
print('items:', cnt[0])
tail = tail.replace(u'保留項 14', u'保留項 15')
head = head.replace(u'保留項 14', u'保留項 15')
io.open(p,'w',encoding='utf-8').write(head+tail)
