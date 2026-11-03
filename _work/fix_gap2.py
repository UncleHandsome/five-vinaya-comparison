# -*- coding: utf-8 -*-
"""Insert descriptive （中略：…） markers at the five unmarked jumps in the 五分 draft.

House style follows the existing instance in the corpus:
    （中略：段75末至段76，述貧人積足工資、設會供僧……）
i.e. give the skipped 段 range plus a one-clause summary of what is skipped.
"""
import os

W = os.path.dirname(os.path.abspath(__file__))

JOBS = [
    (24, '此比丘犯罪，非不犯罪',
     '  > （中略：段38～40，述彼比丘至僧中三乞解不見罪羯磨，及一比丘白二羯磨文、僧解羯磨還作和合竟之文。）',
     '段41：佛言'),
    (25, '時羅睺羅至那羅聚落',
     '  > （中略：段94～98，佛因是事而說偈，凡四句：王施無前後、致使鬼神忿、若隨愛行事、以是應捨愛。）',
     '段99：'),
    (28, '爾時拘舍彌有一長者',
     '  > （中略：段85，述羅睺羅遊迦維羅衛城，諸釋種女具說僧不和合六年之事，羅睺羅教以抱兒迎阿難、著地令啼、要其和合乃取兒之方便。）',
     '〔段86〕'),
    (29, '時有一婬女名半迦尸',
     '  > （中略：段80，羯磨師為從僧乞戒，白言「大德僧聽！某甲求某甲受具足戒……」，如是三乞。）',
     '段81：'),
    (29, '有比丘尼產一男兒',
     '  > （中略：段96～99，述僧中白二羯磨差一比丘尼伴之之文，及二比丘尼捉兒、共兒眠生疑，佛並言無犯。）',
     '段100：'),
]

for v, needle, mark, before in JOBS:
    path = os.path.join(W, 'findings/vol%02d.md' % v)
    lines = open(path, encoding='utf-8').read().split('\n')
    # locate the quote block containing the needle
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith('>') and needle in ln:
            start = i
            break
    if start is None:
        print('BLOCK NOT FOUND', v, needle)
        continue
    end = start
    while end + 1 < len(lines) and lines[end + 1].strip().startswith('>'):
        end += 1
    # the insertion point: the line inside the block that carries `before`
    pos = None
    for j in range(start + 1, end + 1):
        if before in lines[j]:
            pos = j
            break
    if pos is None:
        print('ANCHOR NOT FOUND', v, before)
        continue
    if '中略' in lines[pos - 1]:
        print('ALREADY MARKED', v, needle)
        continue
    lines.insert(pos, mark)
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    print('INSERT vol%02d line %d: %s' % (v, pos + 1, mark.strip()))
