import io,sys
sys.stdout.reconfigure(encoding='utf-8')
def load(f):
    d={}
    for line in io.open(f,encoding='utf-8'):
        p=line.rstrip('\n').split('\t',1)
        if len(p)<2:continue
        try: d[int(p[0])]=p[1]
        except: pass
    return d
V10=load('sengqi/vol10.txt'); V11=load('sengqi/vol11.txt')
def frag(vol,n,start,end,tag):
    t=vol[n]; i=t.find(start)
    if i<0: print('!!NS',tag,start); return
    j=t.find(end,i)
    if j<0: print('!!NE',tag,end); return
    s=t[i:j+len(end)]
    print('### %s [段%d] len=%d\n%s\n'%(tag,n,len(s),s))
frag(V10,13,'此金銀、若錢','不得食用。','R3e')
frag(V10,28,'即往至祇洹精舍上座前','須者來取。」','R12a2')
frag(V10,28,'時比丘或取一','法豫作不供。','R12a3')
frag(V10,56,'畜藥利畜藥利相污','比丘利污比丘利。','R18a')
frag(V10,56,'有食間非受間','是名不畜藥利不畜藥利不相污。','R18b')
frag(V10,16,'及浴金銀菩薩形像','比丘不得先捉後放。','R6c')
frag(V11,62,'即語言：「如我先出家長宿比丘','為眾所識。」','S17a')
frag(V11,62,'去已優婆夷作是思惟','亦復不與。」','S17b')
frag(V11,62,'佛言：「此是惡事，有二不可','受者失衣。」','S17c')
frag(V11,3,'爾時長老難陀、優波難陀冬盛寒時','彼即脫衣著地而去。','S0')
frag(V11,50,'是比丘從三月十六日','當白僧：「某甲住處，有爾許房舍床褥，與上座隨意取。」','S12e')
frag(V11,50,'爾時應隨上座處分','不得與沙彌二房。','S12a2')
