#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""補入四分律卷37「自恣揵度之一」。

底本 31-37 原文.txt 止於「(安居揵度竟)」，卷37 末自恣揵度之一全缺
（約 3,337 字），而白話四分律/31-37.txt 實已譯出此段，致 038-330 的
白話吞入自恣開頭。今自 CBETA T22n1428 XML 補回原文。

來源：https://raw.githubusercontent.com/cbeta-org/xml-p5/master/T/T22/T22n1428.xml
"""
import re, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
XML = os.path.join(BASE, '_1428.xml')

RAW1 = os.path.join(ROOT, '01_原文', '四分律', '31-37 原文.txt')
RAW2 = os.path.join(ROOT, '白話四分律', '31-37 原文.txt')
SEG38 = os.path.join(BASE, 'sifen', '038__開頭_.txt')


def extract():
    d = open(XML, encoding='utf-8').read()
    i = d.find('<cb:juan n="037"')
    j = d.find('<cb:juan n="038"')
    seg = d[i:j]
    k = seg.find('<head>', seg.find('自恣揵度') - 200)
    out = []
    for p in re.findall(r'<p[^>]*>(.*?)</p>', seg[k:], flags=re.S):
        t = re.sub(r'<note[^>]*>.*?</note>', '', p, flags=re.S)
        t = re.sub(r'<[^>]+>', '', t)
        t = re.sub(r'\s', '', t)
        if t:
            out.append(t)
    return out


def main():
    paras = extract()
    assert len(paras) == 18, len(paras)
    txt = ''.join(paras)
    print('段數 %d，字數 %d' % (len(paras), len(txt)))

    # 1) 原始檔（二處同源，須一致）
    for p in (RAW1, RAW2):
        d = open(p, encoding='utf-8').read()
        if '自恣揵度' in d or paras[0][:20] in d:
            print('  已補，略過：%s' % p)
            continue
        add = '\n'.join(paras) + '\n'
        open(p, 'w', encoding='utf-8').write(d.rstrip('\n') + '\n\n' + add)
        print('  補入 %s（+%d 字）' % (os.path.basename(p), len(txt)))

    # 2) 段分檔：續編 331 起
    lines = [l.rstrip('\n') for l in open(SEG38, encoding='utf-8') if l.strip()]
    have = max(int(l.split('\t', 1)[0]) for l in lines)
    if have >= 331:
        print('  段檔已續編至 %d，略過' % have)
        return
    assert have == 330, have
    with open(SEG38, 'a', encoding='utf-8') as fh:
        for n, t in enumerate(paras, have + 1):
            fh.write('%d\t%s\n' % (n, t))
    print('  段檔續編 %d–%d' % (have + 1, have + len(paras)))


if __name__ == '__main__':
    main()
