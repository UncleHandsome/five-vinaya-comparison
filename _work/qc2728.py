# -*- coding: utf-8 -*-
import io, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))

def load(vol):
    d = {}
    p = os.path.join(BASE, 'sengqi', 'vol%02d.txt' % vol)
    for ln in io.open(p, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' in ln:
            k, t = ln.split('\t', 1)
            d[int(k)] = t
    return d

V = {27: load(27), 28: load(28)}

md = io.open(os.path.join(BASE, 'findings_mk', 'vol27-28.md'), encoding='utf-8').read()
lines = md.split('\n')

pat = re.compile(r'^> 〔卷(\d+)·段(\d+)〕(.*)$')
bad = []
qchars = 0
qlist = []
for i, ln in enumerate(lines):
    m = pat.match(ln)
    if not m:
        if ln.startswith('>'):
            bad.append((i + 1, 'BAD LABEL: ' + ln[:60]))
        continue
    vol, seg, txt = int(m.group(1)), int(m.group(2)), m.group(3)
    src = V[vol].get(seg, '')
    if txt not in src:
        j = len(txt)
        while j > 0 and txt[:j] not in src:
            j -= 1
        bad.append((i + 1, 'NOT FOUND seg%d (match %d/%d): %s' % (seg, j, len(txt), txt[max(0, j - 10):j + 20])))
    else:
        qchars += len(txt)
        qlist.append((vol, seg, txt))

print('quotes=%d  quoted chars=%d' % (len(qlist), qchars))
print('BAD=%d' % len(bad))
for b in bad:
    print('  line %d: %s' % b)

def section(name):
    i = md.find('## ' + name)
    if i < 0:
        return ''
    j = md.find('\n## ', i + 3)
    return md[i:j if j > 0 else len(md)]

keep = section('保留項')
delete = section('刪除項（彙總）')
story = section('敘事抽取')
allsets = {}
for nm, sec in [('keep', keep), ('del', delete), ('story', story)]:
    s = set()
    for m in re.finditer(r'〔卷(\d+)·段(\d+)〕', sec):
        s.add((int(m.group(1)), int(m.group(2))))
    for m in re.finditer(r'卷(\d+)·段(\d+)～(\d+)', sec):
        v = int(m.group(1)); a = int(m.group(2)); b = int(m.group(3))
        for x in range(a, b + 1):
            s.add((v, x))
    for m in re.finditer(r'卷(\d+)段(\d+)～(\d+)', sec):
        v = int(m.group(1)); a = int(m.group(2)); b = int(m.group(3))
        for x in range(a, b + 1):
            s.add((v, x))
    for m in re.finditer(r'卷(\d+)段(\d+)(?![\d～])', sec):
        s.add((int(m.group(1)), int(m.group(2))))
    for m in re.finditer(r'位置：段(\d+)～(\d+)', sec):
        a, b = int(m.group(1)), int(m.group(2))
        for x in range(a, b + 1):
            s.add((27, x))
    for m in re.finditer(r'位置：段(\d+)、段(\d+)', sec):
        for g in (1, 2):
            s.add((27, int(m.group(g))))
    for m in re.finditer(r'位置：卷(\d+)·段(\d+)～(\d+)', sec):
        v = int(m.group(1)); a = int(m.group(2)); b = int(m.group(3))
        for x in range(a, b + 1):
            s.add((v, x))
    allsets[nm] = s

allseg = set((27, i) for i in range(1, 82)) | set((28, i) for i in range(1, 80))
u = allsets['keep'] | allsets['del'] | allsets['story']
missing = sorted(allseg - u)
extra = sorted(u - allseg)
dup = []
for a in (27, 28):
    for s in range(1, 82):
        n = sum(1 for k in allsets if (a, s) in allsets[k])
        if n > 1:
            dup.append((a, s, [k for k in allsets if (a, s) in allsets[k]]))
print('missing=%s' % missing)
print('extra=%s' % extra)
print('dup=%s' % dup[:20])

tot = sum(len(t) for t in V[27].values()) + sum(len(t) for t in V[28].values())
print('total chars=%d, quoted=%d, ratio=%.1f%%' % (tot, qchars, 100.0 * qchars / tot))

# simplified char scan: characters that only exist in simplified form
SIMP = (
    '这应说门开兴计与么价处头对录怀户扩时来约节装让论话还进随项须风龄众会学国点无发为见观义语体实职业务单经济历产权条边连结东车轮转运输达过爱乐书习气万与丑专业丛东丝丢两严丧个丰临为丽举旧义乌乔乡买乱争于亏云亚亩亲亿仅从仑仓仪们优伙伛伟传伤伥伦伪伫余佣佥侠侣侥侦侧侨侩侪侬俣俦俨俩俪俭债倾偬偻偾偿傥傧储傩儿兑兖党兰兹养兽冁内冈册写军农冢冯冲决况冻净凄凉减凑凛几凤凫凭凯击凼凿刍划刘则刚创删别刬刭刽刿剀剂剐剑剥剧劝办务动励劲劳势勋勐勚匀匦匮区医华协卖卢卤卫却厅厉压厌厕厢厣厦厨厩厮县参双变叙叠叶号叹叽吁后吓吕吗吣吨听启吴呐呒呓呕呖呗员呙呛呜咏咙咛咝咤响哑哒哓哔哕哗哙哜哝哟唛唝唠唡唢唣唤啧啬啭啮啰啴啸喷喽喾嗫嗳嘘嘤嘱噜噼嚣园囱围囵图圆圣场坂坏块坚坛坜坝坞坟坠垄垅垆垒垦垩垫垭垯垱垲垴埘埙埚埝埯堑堕塆墙壮声壳壶壸备复够夸夹夺奁奂奋奖奥妆妇妈妩妪妫姗姜娄娅娆娇娈娱娲娴婳婴婵婶媪嫒嫔嫱嬷孙孪宁宝宠审宪宫宽宾寝寻导寿将尔尘尝尧尸尽层屃屉届属屡屦屿岁岂岖岗岘岚岛岭岳岽岿峃峄峡峣峤峥峦崂崃崄崭嵘嵚嵛嵝嵴巅巩巯币帅师帏帐帘帜带帮帱帻帼幂幞广庄庆庐庑库庙庞废庼廪异弃张弥弪弯弹强归当录彟彦彻径徕御忆忏忧忾态怂怃怄怅怆怜总怼怿恋恒恳恸恹恺恻恼恽悦悫悬悭悯惊惧惨惩惫惬惭惮惯愍愠愤愦愿慑慭懑懒懔戆戋戏戗战戬扑执扩扪扫扬扰抚抛抟抠抡抢护报担拟拢拣拥拦拧拨择挂挚挛挜挝挞挟挠挡挢挣挤挥挦捞损捡换捣据捻掳掴掷掸掺掼揽揿搀搁搂搅携摄摅摆摇摈摊撄撑撵撷撸撺擞攒敌敛数斋斓斗斩断旧旷旸昙昼昽显晋晒晓晔晕晖暂暧札术朴机杀杂权杨杩杰极构枞枢枣枥枧枨枪枫枭柜柠柽标栈栉栊栋栌栎栏树栖样栾桊桠桡桢档桤桥桦桧桨桩梦梼梾检棂椁椟椠椤椭楼榄榇榈榉槚槛槟槠横樯樱橥橱橹橼檐檩欢欤欧歼殁殇残殒殓殚殡殴毁毂毕毙毡毵氇氢氩氲汇汉污汤汹沓沟没沣沤沥沦沧沨沩沪沵泞泪泶泷泸泺泻泼泽泾洁洒洼浃浅浆浇浈浉浊测浍济浏浐浑浒浓浔浕涂涌涛涝涞涟涠涡涣涤润涧涨涩淀渊渌渍渎渐渑渔渖渗温湾湿溃溅溆溇滗滚滞滟滠满滢滤滥滦滨滩滪漤潆潇潋潍潜潴澜濑濒灏灭灯灵灾灿炀炉炖炜炝炼炽烁烂烃烛烟烦烧烨烩烫烬热焕焖焘煅煳熘爷牍牦牵牺犊犋犟犷犹狈狍狝狞独狭狮狯狰狱狲猃猎猕猡猪猫猬献獭玑玙玚玛玮环现玱玺珉珏珐珑珰珲琎琏琐琼瑶瑷璎瓒瓮瓯电画畅畲畴疖疗疟疠疡疬疮疯疱疴痈痉痒痖痨痪痫瘅瘆瘗瘘瘪瘫瘾瘿癞癣癫皑皱皲盏盐监盖盗盘眍眦眬着睁睐睑瞒瞩矫矶矾矿砀码砖砗砚砜砺砻砾础硁硕硖硗硙硚确硷碍碛碜碱碹磙礼祎祢祯祷祸禀禄禅离秃秆种积称秽秾稆税稣稳穑穷窃窍窎窑窜窝窥窦窭竖竞笃笋笔笕笺笼笾筑筚筛筜筝筹筼签简箓箦箧箨箩箪箫篑篓篮篱簖籁籴类籼粜粝粤粪粮糁糇紧絷纟纠纡红纣纤纥级纨纩纪纫纬纭纮纯纰纱纲纳纴纵纶纷纸纹纺纻纼纽纾线绀绁绂练组绅细织终绉绊绋绌绍绎绐绑绒结绔绕绖绗绘给绚绛络绝绞统绠绡绢绣绤绥绦继绨绩绪绫绬续绮绯绰绱绲绳维绵绶绷绸绹绺绻综绽绾绿缀缁缂缃缄缅缆缇缈缉缊缋缌缍缎缏缐缑缒缓缔缕编缗缘缙缚缛缜缝缞缟缠缡缢缣缤缥缦缧缨缩缪缫缬缭缮缯缰缱缲缳缴缵罂网罗罚罢罴羁羟羡翘耢耧耸耻聂聋职聍联聩聪肃肠肤肷肾肿胀胁胆胜胧胨胪胫胶脉脍脏脐脑脓脔脚脱脶脸腊腌腘腭腻腼腽腾膑臜舆舣舰舱舻艰艳艹艺芈芗芜芦苁苇苈苋苌苍苎苏苘苹茎茏茑茔茕茧荆荐荙荚荛荜荞荟荠荡荣荤荥荦荧荨荩荪荫荬荭荮药莅莱莲莳莴莶获莸莹莺莼萚萝萤营萦萧萨葱蒇蒉蒋蒌蓝蓟蓠蓣蓥蓦蔷蔹蔺蔼蕲蕴薮藁藓虏虑虚虫虬虮虽虾虿蚀蚁蚂蚕蚝蚬蛊蛎蛏蛮蛰蛱蛲蛳蛴蜕蜗蜡蝇蝈蝉蝎蝼蝾螀螨蟏衅衔补衬衮袄袅袆袜袭袯裆裈裢裣裤裥褛褴襁襕觃规觅视觇览觉觊觋觌觍觎觏觐觑觞触觯詟誉誊讠计订讣认讥讦讧讨讪讫训议讯记讱讲讳讴讵讶讷许讹论讻讼讽设访诀证诂诃评诅识诇诈诉诊诋诌词诎诏诐译诒诓诔试诖诗诘诙诚诛诜诞诟诠诡询诣诤该详诧诨诩诪诫诬诮误诰诱诲诳诵诶请诸诹诺读诼诽课诿谀谁谂调谄谅谆谇谈谊谋谌谍谎谏谐谑谒谓谔谕谖谗谘谙谚谛谜谝谞谟谠谡谢谣谤谥谦谧谨谩谪谫谬谭谮谯谰谱谲谳谴谵谶谷豮贝贞负贠贡财责贤败账货质贩贪贫贬购贮贯贰贱贲贳贴贵贶贷贸费贺贻贼贽贾贿赀赁赂赃资赅赆赇赈赉赊赋赌赍赎赏赐赑赒赓赔赕赖赗赘赙赚赛赜赝赞赟赠赡赢赣赪赵赶趋趱趸跃跄跖跞践跶跸跹跻踊踌踪踬踯蹑蹒蹰蹿躁躏躜躯轧轨轩轪轫转轭软轰轱轲轳轴轵轶轷轸轹轺轻轼载轾轿辀辁辂较辄辅辆辇辈辉辊辋辌辍辎辏辐辑辒输辔辕辖辗辘辙辚辞辩辫辽迁迈运违连迟迩迳迹适选逊递逦逻遗遥邓邝邬邮邹邺邻郁郄郏郐郑郓郦郧郸酂酝酦酱酽酾酿释鉴銮錾钅钆钇针钉钊钋钌钍钎钏钐钑钒钓钔钕钖钗钘钙钚钛钝钞钟钠钡钢钣钤钥钦钧钨钩钪钫钬钭钮钯钰钱钲钳钴钵钷钹钺钻钼钽钾钿铀铁铂铃铄铅铆铈铉铊铋铌铍铎铏铐铑铒铕铖铗铙铚铛铜铝铞铟铠铡铢铣铤铥铧铨铩铪铫铬铭铮铯铰铱铲铳铴铵银铷铸铹铺铻铼铽链铿销锁锂锃锄锅锆锇锈锉锊锋锌锍锎锏锐锑锒锓锔锕锖锗锘错锚锛锜锝锞锟锠锡锢锣锤锥锦锨锩锪锫锬锭键锯锰锱锲锳锴锵锶锷锸锹锺锻锼锽锾锿镀镁镂镃镄镅镆镇镈镉镊镋镌镍镎镏镐镑镒镓镔镕镖镗镘镙镚镛镜镝镞镟镠镡镢镣镤镥镦镧镨镩镪镫镬镭镮镯镰镱镲镳镴镶长闩闪闫闬闭问闯闰闱闲闳间闵闶闷闸闹闺闻闼闽闾闿阀阁阂阃阄阅阆阇阈阉阊阋阌阍阎阏阐阑阒阓阔阕阖阗阘阙阚阛队阳阴阵阶际陆陇陈陉陕陧陨险隐隶隽难雏雠雳雾霁霉霭靓静靥鞑鞒鞯鞴韦韧韨韩韪韫韬韵页顶顷顸项顺顼顽顾顿颀颁颂颃预颅领颇颈颉颊颋颌颍颎颏颐频颒颓颔颕颖颗题颙颚颛颜额颞颟颠颡颢颤颥颦颧飏飐飑飒飓飔飕飖飗飘飙飚飞飨餍饤饥饦饧饨饩饪饫饬饭饮饯饰饱饲饳饴饵饶饷饸饹饺饻饼饽饾饿馀馁馂馃馄馅馆馇馈馉馊馋馌馍馎馏馐馑馒馓馔馕驭驮驯驰驱驲驳驴驵驶驷驸驹驺驻驼驽驾驿骀骁骂骃骄骅骆骇骈骉骊骋验骍骎骏骐骑骒骓骔骕骖骗骘骙骚骛骜骝骞骟骠骡骢骣骤骥骦骧髅髋髌鬓魇魉鱼鲁鲂鲄鲅鲆鲇鲈鲉鲊鲋鲌鲍鲎鲏鲐鲑鲒鲓鲔鲕鲖鲗鲘鲙鲚鲛鲜鲝鲞鲟鲠鲡鲢鲣鲤鲥鲦鲧鲨鲩鲪鲫鲬鲭鲮鲯鲰鲱鲲鲳鲴鲵鲶鲷鲸鲹鲺鲻鲼鲽鲾鲿鳀鳁鳂鳃鳄鳅鳆鳇鳈鳉鳊鳋鳌鳍鳎鳏鳐鳑鳒鳓鳔鳕鳖鳗鳘鳙鳛鳜鳝鳞鳟鳠鳡鳢鳣鸟鸠鸡鸢鸣鸤鸥鸦鸧鸨鸩鸪鸫鸬鸭鸮鸯鸰鸱鸲鸳鸴鸵鸶鸷鸸鸹鸺鸻鸼鸽鸾鸿鹀鹁鹂鹃鹄鹅鹆鹇鹈鹉鹊鹋鹌鹍鹎鹏鹐鹑鹒鹓鹔鹕鹖鹗鹘鹙鹚鹛鹜鹝鹞鹟鹠鹡鹢鹣鹤鹥鹦鹧鹨鹩鹪鹫鹬鹭鹯鹰鹱鹲鹳鹴鹾麦麸黄黉黡黩黪黾鼋鼍鼗鼹齄齐齑齿龀龁龂龃龅龆龇龈龉龊龋龌龙龚龛龟'
)

simp = ''.join(ch for ch in SIMP if ch in md)
print('simp chars found: %s' % (''.join(sorted(set(simp))) or '(none)'))
for ch in sorted(set(simp)):
    i = md.find(ch)
    print('  %s at %s | %s' % (ch, i, md[max(0, i - 20):i + 20].replace('\n', ' ')))
