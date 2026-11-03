# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout.reconfigure(encoding='utf-8')
P = {}
for l in io.open('shisong/vol61.txt', encoding='utf-8'):
    n, t = l.rstrip('\n').split('\t', 1)
    P[int(n)] = t

def seg(a, b=None, s=None, e=None):
    b = b or a
    t = ''.join(P[i] for i in range(a, b + 1))
    if s:
        i = t.index(s)
        t = t[i:]
    if e:
        j = t.index(e) + len(e)
        t = t[:j]
    return t

Q = {}
Q['K1'] = seg(15, 21)
Q['K2'] = seg(24)
Q['K3'] = seg(25, s='又問：「若一切比丘結界羯磨時')
Q['K4'] = seg(26, 27)
Q['K5'] = seg(28, s='佛言：「聽比丘，比丘尼前說比丘戒。')
Q['K6'] = seg(29, s='爾時阿難二請忘不與他一請。')
Q['K7'] = seg(30, s='佛言：「從今日先相嫌人')
Q['K8'] = seg(31, s='從今日聽，若有兩聚落界相連')
Q['K9'] = seg(32, s='佛言：「無罪。從今日不得為小因緣') + seg(33) + seg(48)
Q['K10'] = seg(34, s='佛言：「若賈客住') + seg(37)
Q['K11'] = seg(38) + seg(55) + seg(82)
Q['K12'] = seg(39) + seg(44, s='佛言：「一心生念如法懺悔', e='得生天上。」')
Q['K13'] = seg(46, s='佛言：「從今日若有相應罪') + seg(47)
Q['K14'] = seg(50) + seg(65) + seg(66)
Q['K15'] = seg(56) + seg(59) + seg(60) + seg(83)
Q['K16'] = seg(61) + seg(63) + seg(64)
Q['K17'] = seg(69) + seg(71) + seg(72)
Q['K18'] = seg(73) + seg(75)
Q['K19'] = seg(84, s='諸比丘不知云何？是事白佛，佛言：「受餘殘夜去') + seg(85, s='是事白佛，佛言：「聽受三十九夜去。')
Q['K20'] = seg(89) + seg(90) + seg(91) + seg(92)

tot = 0
for k, v in Q.items():
    print(k, len(v))
    tot += len(v)
print('TOTAL', tot, 'ratio', round(tot / 14574 * 100, 2))
json.dump(Q, io.open('q61.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
