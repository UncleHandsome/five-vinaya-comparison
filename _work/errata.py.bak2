#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
勘誤表：原稿個別斷言經覆核有誤者，於此覆蓋。

原則：不改 matrix_built.json（原始數據），只在渲染時套用，
以存可追溯。對照本與矩陣皆引用本模組，避免二書不一致。
"""

# 覆蓋欄位：title / diff_full / ref4 / st / lv
ERRATA = {
    'M-1913': {
        'st': 'A',
        'lv': '制度',
        'title': '卷首別立〈毘奈耶序〉長篇讚律，四分律僅有卷首短偈八句',
        'diff_full': '根本說以五言、七言偈頌另立〈毘奈耶序〉一篇（段3–76），明言三藏以律為首、'
                     '律住則正法不滅、律如大海漂屍擯破戒者。四分律卷首雖有五言偈八句'
                     '（「稽首禮諸佛，及法比丘僧，今演毘尼法，令正法久住」以下），'
                     '然僅為通序，無「毘奈耶為首」「正法藏不滅」「大海漂屍」諸喻；'
                     '其後逕入舍利弗請結戒之長行。故所異在序頌之篇幅與內容，非有無。',
        'ref4': '四分律卷首（000 篇段3–9）有五言偈：「稽首禮諸佛，及法比丘僧，今演毘尼法，'
                '令正法久住。優波離為首，及餘身證者，今說戒要義，諸賢咸共聽。」'
                '（段7–9 續云「今欲說深戒」「今說十句義」等）。然無根有〈毘奈耶序〉之長篇'
                '與諸喻，段4–5 逕以長行敘未結戒則法不久住。',
        'cells': {'v4': '有'},   # v4=四分。改判 A，四分欄由「無」改「有」
        '_note': '原稿作「四分律無序頌」「遍查未見（查詞：稽首）」，'
                 '然四分律卷首實有五言偈八句含「稽首」，故正之。',
    },
}

# 改判後之歸位（原判 C，實有對應，改入第一部）
ERRATA_POS = {
    'M-1913': (0, 3),
}


def apply(r):
    """就地覆蓋渲染用欄位，回傳新 dict（不改原物件）"""
    e = ERRATA.get(r['id'])
    if not e:
        return r
    r = dict(r)
    for k, v in e.items():
        if k.startswith('_'):
            continue
        if k == 'cells':
            for ck, cv in v.items():
                r[ck] = cv
            continue
        r[k] = v
    return r


def dedup_xref(x):
    """補證欄常有「……（同樣內容）」的重複，去其重複括號（可多處）"""
    import re
    if not x:
        return x
    out = x
    for _ in range(6):
        changed = False
        for m in re.finditer(r'（([^（）]{12,})）', out):
            if m.group(1)[:20] in out[:m.start()]:
                out = out[:m.start()] + out[m.end():]
                changed = True
                break
        if not changed:
            break
    return re.sub(r'\s+', ' ', out).strip()


def note(rid):
    """取勘誤說明（若有）"""
    e = ERRATA.get(rid, {})
    return e.get('_note', '')
