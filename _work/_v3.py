import re, io
def segs(f):
    d={}
    for line in io.open(f,encoding='utf-8'):
        m=re.match(r'\s*(\d+)\t(.*)',line.rstrip('\n'))
        if m: d[int(m.group(1))]=m.group(2)
    return d
v12=segs('sengqi/vol12.txt'); v13=segs('sengqi/vol13.txt')
def cjk(s): return len(re.findall(r'[\u4e00-\u9fff]',s))
keep12=[9,10,13,14,21,24,25,32,41,42,43,46]
keep13=[4,6,8,10,13,15,16,19,23,28,29,37,40]
s12=sum(cjk(v12[k]) for k in keep12 if k in v12)
s13=sum(cjk(v13[k]) for k in keep13 if k in v13)
print('v12 keep segs',s12,'of',sum(cjk(x) for x in v12.values()))
print('v13 keep segs',s13,'of',sum(cjk(x) for x in v13.values()))
print('total',s12+s13,'ratio %.1f%%'%(100.0*(s12+s13)/18403))
