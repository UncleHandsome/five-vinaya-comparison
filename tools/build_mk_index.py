#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""僧祇戒本對照表：四分比丘戒 → 摩訶僧祇律大比丘戒本（T22 no. 1426）戒序。

僧祇廣律無「學處第N」之目，戒本次序又與四分不同，故開遮表僧祇欄長期
只能「未比」。今取 CBETA 戒本（_work/_1426.xml）為據：
  - 單提（波夜提）92 條，依戒本起句逐條與四分 90 條對位；
  - 波羅夷 4 條、僧殘前 10 條同序，逕對；
  - 捨墮、提舍尼戒本分段未能盡合（缺 4 條、1 條），暫不列，寧缺不強配。

產出：_work/mk_index.json、_work/appendix7.md
"""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, '_work')
XML = os.path.join(WORK, '_1426.xml')

# 四分單提序 → 僧祇戒本單提序（None 為未能確定）
MK_DAN = {
    1: 1, 2: 2, 3: 3, 4: 69, 5: 42, 6: 6, 7: 8, 8: 7, 9: 5, 10: 73,
    11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18,
    19: 19, 20: 20, 21: 21, 22: 22, 23: 24, 24: 28, 25: 29, 26: 25,
    27: 26, 28: 27, 29: 30, 30: 68, 31: 31, 32: 32, 33: 40, 34: 38,
    35: 33, 36: 34, 37: 36, 38: 37, 39: 35, 40: 39, 41: 52, 42: 81,
    43: 53, 44: 54, 45: 70, 46: 44, 47: 74, 48: 55, 49: 56, 50: 57,
    51: 76, 52: 66, 53: 67, 54: 75, 55: 65, 56: 50, 57: 41, 58: 64,
    59: 63, 60: 48, 61: 61, 62: 51, 63: 62, 64: 60, 65: 71, 66: 4,
    67: 72, 68: 45, 69: 46, 70: 47, 71: None, 72: 10, 73: None, 74: None,
    75: 79, 76: 43, 77: 78, 78: 58, 79: 59, 80: 90, 81: 82, 82: 49,
    83: 80, 84: 84, 85: 85, 86: 83, 87: 86, 88: 87, 89: 88, 90: 89,
}


def body_text():
    s = open(XML, encoding='utf-8').read()
    b = s.split('<body>')[1].split('</body>')[0]
    b = re.sub(r'<note[^>]*>.*?</note>', '', b, flags=re.S)
    b = re.sub(r'<[^>]+>', '', b)
    return re.sub(r'\s+', '', b)


def main():
    t = body_text()
    # 戒本分節位置（單提：4673–7686；波羅夷、僧殘另取）
    dan = [p[:34] for p in t[4673:7686].split('若比丘')[1:]]
    print('單提戒本條數', len(dan))

    import sifen_src as S
    names = json.load(open(os.path.join(WORK, 'jie_names.json'), encoding='utf-8'))

    def nm(fam, i):
        v = names.get('%s|%d' % (fam, i)) or ''
        return re.sub(r'^[一二三四五六七八九十百]+、', '', v)

    # 四分 90 條 → 篇／節
    units = {}
    for no in range(13, 22):
        for u in S.units(no):
            if u.get('cn') and S.jie_family(no, u) == '比丘單提':
                lab = S.unit_label(u, no) or ''
                m = re.match(r'([一二三四五六七八九十百]+)、', lab)
                if m:
                    units[len(units) + 1] = (no, u['cn'])

    rows = []
    for i in range(1, 91):
        j = MK_DAN.get(i)
        no, cn = units.get(i, ('', ''))
        rows.append({
            '四分序': i, '篇': no, '節': cn, '四分戒名': nm('比丘單提', i),
            '僧祇序': j, '僧祇起句': dan[j - 1] if j and j <= len(dan) else '',
        })

    idx = {
        '波羅夷': {i: i for i in range(1, 5)},
        '僧殘': {i: i for i in range(1, 11)},
        '單提': {i: j for i, j in MK_DAN.items() if j},
        '來源': 'T22 no. 1426 摩訶僧祇律大比丘戒本',
    }
    with open(os.path.join(WORK, 'mk_index.json'), 'w', encoding='utf-8',
              newline='\n') as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)

    L = ['### 附錄七　僧祇戒本對照表（比丘單提）', '',
         '> **用途**：僧祇廣律無「學處第N」之目，戒本次序又與四分不同，'
         '故開遮表僧祇欄多作「未比」。此表以《摩訶僧祇律大比丘戒本》'
         '（T22 no. 1426）為據，逐條對位，供回原典覆核。',
         '>',
         '> **判準**：依戒本起句與四分戒名對讀；同名同制者逕列，'
         '次序不同者按內容對位。四分 71、73、74 三條未能確定，留空不強配。'
         '僧祇戒本單提 92 條，較四分多二條（迴僧物與人、不白入尼住處），'
         '為僧祇獨有，不入此表。',
         '',
         '| 四分 | 四分戒名 | 僧祇戒本 | 僧祇起句 |',
         '|---|---|---|---|']
    for r in rows:
        if not r['僧祇序']:
            continue
        L.append('| %03d-%s | %s | 第 %d 條 | %s |' %
                 (r['篇'], r['節'], r['四分戒名'], r['僧祇序'],
                  re.sub(r'^[，。、；：]', '', r['僧祇起句']).replace('|', '／')))
    L += ['', '> 共 **%d** 條對位。波羅夷 4 條、僧殘前 10 條與四分同序，'
          '開遮表補比時一併採用；捨墮、提舍尼之戒本分段未能盡合，暫缺。'
          % sum(1 for r in rows if r['僧祇序']), '']

    with open(os.path.join(WORK, 'appendix7.md'), 'w', encoding='utf-8',
              newline='\n') as f:
        f.write('\n'.join(L))
    print('對位', sum(1 for r in rows if r['僧祇序']), '條 → appendix7.md')


if __name__ == '__main__':
    import sys
    sys.path.insert(0, WORK)
    main()
