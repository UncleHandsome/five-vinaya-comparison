# -*- coding: utf-8 -*-
"""Build the five-canon comparison matrix from matrix_rows.json.

Each row of matrix_rows.json is one retained item of one draft.  This script
turns it into a matrix row: five canon columns (有/無/未比), a status letter,
and a level.  It never invents a cell: an empty comparison field becomes 未比.
"""
import json, re, csv, os
from collections import Counter

W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(W, 'matrix_rows.json'), encoding='utf-8'))

ABSENT = ('遍查未見', '全無', '無此', '未見', '不見', '無對應', '俱無', '皆無', '並無')
CANONS = ['四分', '五分', '十誦', '僧祇', '根有']


def cell(field, is_main):
    if is_main:
        return '有'
    if not field:
        return '未比'
    return '無' if any(k in field for k in ABSENT) else '有'


def level(title, diff):
    s = title + diff
    if re.search(r'戒|波羅夷|僧殘|僧伽婆尸沙|波逸提|波夜提|捨墮|尼薩耆|單提|偷蘭遮|突吉羅|悔過', s):
        if re.search(r'羯磨|結界|安居|自恣|布薩|受戒|度人|差|擯|別住|摩那埵|出罪', s):
            return '制度'
        return '戒條'
    if re.search(r'羯磨|結界|安居|自恣|布薩|受戒|擯|別住|摩那埵|出罪|衣法|藥法|房舍|臥具|威儀', s):
        return '制度'
    if re.search(r'本生|因緣|故事|過去世|宿世|王|夫人|居士', s):
        return '事件'
    if re.search(r'種|法數|五法|十法|三法|二法|名數|列', s):
        return '法數'
    return '事件'


def status(r):
    if r['absent4']:
        return 'C'
    d = r['diff']
    if re.search(r'開緣|不犯|聽許|開聽', d):
        return 'B'
    if re.search(r'減略|較略|從略|無此|不載', d):
        return 'D'
    return 'A'


# 五分稿的 C 項以人工核定的清單為準（關鍵詞法在此稿有 6 處誤判）
import os as _os
_wc = json.load(open(_os.path.join(W, 'wufen_C_items.json'), encoding='utf-8'))
WUFEN_C = {(x['vol'], x['no']) for x in _wc}


def clean_diff(s):
    s = s or ''
    s = re.split(r'-\s*原文|原文：|-\s*白話|白話：', s)[0]
    return re.sub(r'\s+', '', s)


def short(s, n=70):
    s = clean_diff(s)
    return s[:n] + ('…' if len(s) > n else '')


out = []
# 交叉引用補格：各稿刪除表已記明對應卷段者，直接據以填「有」，不待重查
_ovp = os.path.join(W, 'cell_overrides.json')
_OV = json.load(open(_ovp, encoding='utf-8')) if os.path.exists(_ovp) else {}
_xp = os.path.join(W, 'cell_xref_log.json')
_XL = json.load(open(_xp, encoding='utf-8')) if os.path.exists(_xp) else []
# 人工核定（十組碰撞的未比格）：後套用，優先於交叉引用
_mp = os.path.join(W, 'cell_overrides_manual.json')
if os.path.exists(_mp):
    for _k, _d in json.load(open(_mp, encoding='utf-8')).items():
        _OV.setdefault(_k, {}).update(_d)
_mx = os.path.join(W, 'cell_xref_log_manual.json')
if os.path.exists(_mx):
    _XL = list(_XL) + json.load(open(_mx, encoding='utf-8'))
XF = {}
CELLNAME = {'v4': '四分', 'v5': '五分', 'v10': '十誦', 'vMK': '僧祇', 'vGU': '根有'}
for _x in _XL:
    XF.setdefault(_x['key'], []).append('%s稿刪除表記 %s（%s）' % (
        _x['by'], _x['ref'], _x['reason']))

for r in rows:
    canon = r['canon']
    vals = {}
    for c in CANONS:
        if c == canon:
            vals[c] = '有'
        elif c == '四分':
            vals[c] = cell(r['ref4'], False)
        elif c == '五分':
            vals[c] = cell(r['ref5'], False)
        elif c == '十誦':
            vals[c] = cell(r['ref10'], False)
        else:
            vals[c] = '未比'
    st = status(r)
    if canon == '五分':
        st = 'C' if (int(r['unit'][3:5]), r['no']) in WUFEN_C else ('A' if st == 'C' else st)
    if canon == '五分':
        vals['四分'] = '無' if st == 'C' else '有'
    _k = '%s|%s|%d' % (canon, r['unit'], r['no'])
    for _c, _v in _OV.get(_k, {}).items():
        vals[CELLNAME.get(_c, _c)] = _v
    out.append({
        'canon': canon, 'unit': r['unit'], 'no': r['no'], 'title': r['title'],
        'pos': r['pos'], 'lv': level(r['title'], r['diff']), 'st': st,
        'v4': vals['四分'], 'v5': vals['五分'], 'v10': vals['十誦'],
        'vMK': vals['僧祇'], 'vGU': vals['根有'],
        'xref': '；'.join(XF.get(_k, [])),
        'diff': short(r['diff']), 'diff_full': clean_diff(r['diff']),
        'ref4': r['ref4'], 'ref5': r['ref5'], 'ref10': r['ref10'],
    })

for i, o in enumerate(out, 1):
    o['id'] = 'M-%04d' % i

# ---- CSV (full) ----
csvp = os.path.join(W, '五部律綜合異同矩陣.csv')
with open(csvp, 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['編號', '主稿', '證據', '層級', '狀態', '主題',
                '四分', '五分', '十誦', '僧祇', '根有', '位置', '實質差異',
                '四分對照', '五分對照', '十誦對照', '補證'])
    for o in out:
        w.writerow([o['id'], o['canon'], '%s#%d' % (o['unit'], o['no']), o['lv'], o['st'],
                    o['title'], o['v4'], o['v5'], o['v10'], o['vMK'], o['vGU'],
                    o['pos'], o['diff_full'], o['ref4'], o['ref5'], o['ref10'],
                    o.get('xref', '')])

json.dump(out, open(os.path.join(W, 'matrix_built.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

st = Counter((o['canon'], o['st']) for o in out)
print('rows', len(out))
for c in CANONS[:1]:
    pass
for canon in ['五分', '十誦', '僧祇', '根有']:
    sub = [o for o in out if o['canon'] == canon]
    print(canon, len(sub), dict(Counter(o['st'] for o in sub)))
print('level', dict(Counter(o['lv'] for o in out)))
print('cells', {k: dict(Counter(o[k] for o in out)) for k in ['v4', 'v5', 'v10', 'vMK', 'vGU']})
print('written', csvp)
