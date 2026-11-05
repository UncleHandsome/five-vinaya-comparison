#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二輪戒類標註：只處理 s_class.json 中「未分類」者。

第一輪（build_sclass.py）以戒類關鍵詞、本稿原文、ref4 篇段三路判定，
餘 411 項無戒類可歸——多為制度、事件、法數，本不屬於某一戒條。
本輪改以「主題」分類（受戒、安居、衣鉢、食藥、僧團程序……），
仍守「不補造」：主題詞須見於標題，逐筆記依據；無詞可據者留「未分類」。

不動既有 258 項之標註，不動 st、項號、篇段。
產出：_work/s_class.json（就地更新）、_work/審閱/再分類台帳.csv
"""
import os, re, csv, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
OUT = os.path.join(WORK, '審閱')

# 主題詞。順序即優先序：先具體後泛；「衣」須排除白衣、毛衣、皮衣。
TOPICS = [
    ('受戒與師資', r'受具|受戒|和尚|阿闍梨|依止|度人|出家|沙彌|式叉摩那|戒臘|僧次|本法|學戒|剃髮'),
    ('安居・自恣・布薩', r'安居|自恣|布薩|說戒|結界|大界|戒壇|界相'),
    ('僧團程序・羯磨', r'羯磨|僧事|擯|舉罪|諫|懺|悔|滅諍|和合|別眾|與欲|白四|白二|單白'),
    ('衣・鉢・坐具', r'三衣|法衣|糞掃衣|迦絺那|尼師壇|坐具|臥具|革屣|鉢|衣價|浣衣|染衣|縫衣|(?<![白毛皮])衣'),
    ('食・藥', r'淨食|受食|食法|粥|餅|肉|酥|蜜|漿|藥|飲食|噉食|乞食'),
    ('尼眾・女眾', r'比丘尼|尼眾|式叉|沙彌尼|女眾'),
    ('王臣・俗眾・外道', r'沙彌|外道|居士|白衣|國王|王法|大臣|賊|刑|獄'),
    ('因果・本生故事', r'本生|宿因|佛記|因緣|故事|夢|餓鬼|譬喻'),
    ('住處・房舍', r'房舍|屋舍|住處|僧坊|精舍|園林|寺|塔|牀|臥|樹下'),
    ('法數・名相', r'法數|幾種|四句|三種|二種|五種|名義|釋名|得名'),
    ('神通・瑞應', r'神變|神通|光明|夢|瑞|放光'),
]


def topic_of(title):
    for name, pat in TOPICS:
        m = re.search(pat, title or '')
        if m:
            return name, '主題詞「%s」' % m.group()
    return None, ''


def main():
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(WORK, 's_class.json')
    s = json.load(open(p, encoding='utf-8'))
    before = collections.Counter(v['類'] for v in s.values())
    print('原有：未分類 %d／%d' % (before.get('未分類', 0), len(s)))

    ledger = []
    for mid, v in s.items():
        if v.get('類') != '未分類':
            continue
        cls, why = topic_of(v.get('title'))
        if not cls:
            continue
        v['類'] = cls
        v['依據'] = why
        ledger.append((mid, v.get('canon'), v.get('層'), v.get('title', '')[:56], cls, why))

    json.dump(s, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    q = os.path.join(OUT, '再分類台帳.csv')
    with open(q, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(('項號', '所屬律', '層', '標題', '新類', '依據'))
        w.writerows(ledger)

    after = collections.Counter(v['類'] for v in s.values())
    print('本輪改註 %d 項' % len(ledger))
    print('未分類 %d → %d（%.1f%% → %.1f%%）' % (
        before.get('未分類', 0), after.get('未分類', 0),
        100 * before.get('未分類', 0) / len(s), 100 * after.get('未分類', 0) / len(s)))
    for k, n in after.most_common():
        print('  %-16s %d' % (k, n))


if __name__ == '__main__':
    main()
