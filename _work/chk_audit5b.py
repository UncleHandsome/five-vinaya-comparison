# -*- coding: utf-8 -*-
"""查證第五輪報告（十二案）於《五分律去重白話》：
每案三問——①底本（_work/wufen）有無其語 ②本書（含正文與附錄一）有無 ③附錄一原標何語。"""
import io, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, '五分律_去重白話')
WF = os.path.join(ROOT, '_work', 'wufen')
SF = os.path.join(ROOT, '_work', 'sifen')

BOOK = ''
for f in sorted(os.listdir(D)):
    if f.endswith('.md'):
        BOOK += io.open(os.path.join(D, f), encoding='utf-8').read()


def wf_paras(v):
    d = {}
    p = os.path.join(WF, 'vol%02d.txt' % v)
    if not os.path.exists(p):
        return d
    for ln in io.open(p, encoding='utf-8'):
        a, sep, b = ln.rstrip('\n').partition('\t')
        if a.strip().isdigit():
            d[int(a)] = b
    return d


def sf_text(pat):
    out = ''
    for p in glob.glob(os.path.join(SF, pat)):
        out += io.open(p, encoding='utf-8').read()
    return out


CASES = [
    ('1 似人四十九日', 2, (14, 22), ['四十九', '似人', '七日', '堕胎', '歌罗', '羯羅藍'], '002_*.txt', ['初託胎', '人者']),
    ('2 五大賊', 2, (48, 60), ['大賊', '五賊', '賊'], '002_*.txt', ['大賊']),
    ('3 八敬法訴訟權', 29, (6, 12), ['呵責羯磨', '不見罪', '不懺悔', '遮', '自恣', '八'], '058_*.txt', ['罵詈', '說比丘過']),
    ('4 塔物僧物', 26, (78, 90), ['塔', '僧物', '生財'], '064_*.txt', ['塔物', '貸']),
    ('5 十事定罪', 30, (30, 56), ['鹽', '兩指', '求聽', '日時', '復坐', '鬱多', '不離'], '067_*.txt', ['十']),
    ('6 失夜斷夜', 28, (38, 46), ['失', '斷夜', '不數', '夜'], '02[01]_*.txt', ['失夜', '斷夜']),
    ('7 差受請人', 22, (82, 90), ['受請', '差'], '*.txt', ['差受請', '次請人']),
    ('8 四諍配七滅', 23, (8, 56), ['言諍', '二滅', '五滅', '三滅', '一滅', '滅'], '*.txt', ['言諍']),
    ('9 房舍專用權', 25, (58, 92), ['房', '舍', '某甲', '安居'], '*.txt', ['與某甲']),
    ('10 邊地四至', 21, (73, 82), ['邊', '中國', '東至'], '041_*.txt', ['娑羅林', '中國']),
    ('11 五淨', 22, (52, 114), ['火淨', '刀淨', '爪淨', '啄', '爛', '蟲'], '046_*.txt', ['火淨', '刀淨']),
    ('12 四阿含定義', 30, (14, 20), ['阿含', '不高不下', '兩兩', '三三'], '07[0-9]_*.txt', ['阿含']),
]

print('%-16s %-22s %-22s %s' % ('案', '底本所見（卷·段）', '本書命中', '四分所見'))
for tag, v, (a, b), terms, sfpat, sfterms in CASES:
    d = wf_paras(v)
    found = []
    for t in terms:
        hit = [n for n in range(a, b + 1) if t in d.get(n, '')]
        if hit:
            found.append('%s@%s' % (t, ','.join(map(str, hit[:6]))))
    bk = ['%s×%d' % (t, BOOK.count(t)) for t in terms if BOOK.count(t)]
    st = sf_text(sfpat)
    sfh = ['%s×%d' % (t, st.count(t)) for t in sfterms if st.count(t)]
    print('%-16s %-22s %-22s %s' % (tag, '; '.join(found)[:100] or '底本此區間無',
                                     '; '.join(bk)[:60] or '本書無',
                                     '; '.join(sfh)[:40] or '無'))
