#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""審校報告所指文字訛誤與白話註釋，一次改定。

原文三處同源，須一致：
  01_原文/四分律/31-37 原文.txt
  白話四分律/31-37 原文.txt
  _work/sifen/038__開頭_.txt
白話：_work/sifen_plain.json
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

RAW = [os.path.join(ROOT, '01_原文', '四分律', '31-37 原文.txt'),
       os.path.join(ROOT, '白話四分律', '31-37 原文.txt'),
       os.path.join(BASE, 'sifen', '038__開頭_.txt')]
PLAIN = os.path.join(BASE, 'sifen_plain.json')

# 原文訂正（依 CBETA T22n1428 校正）
ORIG_FIX = [
    ('舉訶波羅那', '摩訶波羅那', '卷31 佛傳世系：「波羅那王有子，名摩訶波羅那」，底本訛「摩」為「舉」'),
    ('根裁', '根栽', '卷31 彌却摩納本生：「我欲作佛種無上根栽」，底本訛「栽」為「裁」'),
]

# 白話訂正與補註
PLAIN_FIX = {
    '038-3': [('伽兔支', '伽㝹支', '原文作「伽[少/兔]支」，組字式已代「㝹」，白話仍作「兔」')],
    '038-18': [('另一位名叫優波離，',
                '另一位名叫優波離（註：此是商人名，梵語 Bhallika，他經譯作「波利」；'
                '與下文「持律第一」的優波離 Upāli 同名異人），',
                '二賈客之優波離非持律第一之優波離，易混，加註別之')],
    '038-21': [('國王的第一夫人懷孕了。懷孕的婦女有三種如實不虛的世俗認知：'
                '一是自己知道已經懷孕，二是知道這胎兒是從誰而得，三是知道這男子對自己有愛意。',
                '國王的第一夫人便懷了孕。孕婦於三事能如實自知：'
                '一是自知已經受胎，二是知道這胎兒從誰而得，三是知道那男子對自己有情意。',
                '原譯「懷孕的婦女……知道自己已經懷孕」同義反覆，改「受胎」以避')],
    '038-36': [('回到了鉢摩大國，',
                '回到了鉢摩大國（梵語 Padma，意為「蓮花」，即蓮花城），',
                '「鉢摩」為音譯，讀者難解，補其義')],
}


def main():
    for old, new, why in ORIG_FIX:
        n = 0
        for p in RAW:
            d = open(p, encoding='utf-8').read()
            c = d.count(old)
            if c:
                open(p, 'w', encoding='utf-8').write(d.replace(old, new))
                n += c
        print('原文 %s→%s：%d 處（%s）' % (old, new, n, why))

    plain = json.load(open(PLAIN, encoding='utf-8'))
    for k, subs in PLAIN_FIX.items():
        v = plain.get(k, '')
        for old, new, why in subs:
            if old not in v:
                print('  ✗ %s 未命中：%s' % (k, old[:20]))
                continue
            v = v.replace(old, new, 1)
            print('白話 %s：%s' % (k, why))
        plain[k] = v
    json.dump(plain, open(PLAIN, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('已寫 %s' % PLAIN)


if __name__ == '__main__':
    main()
