# -*- coding: utf-8 -*-
"""Define the 22 comparison units of the Mahasamghika Vinaya (摩訶僧祇律)."""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '_work')

U = [
    ('vol01-02', [1, 2], '四波羅夷法之一、二（婬戒）'),
    ('vol03', [3], '四波羅夷法之三（盜戒之餘）'),
    ('vol04-05', [4, 5], '四波羅夷法之四、五（殺戒・大妄語）'),
    ('vol06-07', [6, 7], '僧殘法・二不定法'),
    ('vol08-09', [8, 9], '三十尼薩耆波夜提法之一、二'),
    ('vol10-11', [10, 11], '三十尼薩耆波夜提法之三、四'),
    ('vol12-13', [12, 13], '單提九十二事法之一、二'),
    ('vol14-15', [14, 15], '單提九十二事法之三、四'),
    ('vol16-17', [16, 17], '單提九十二事法之五、六'),
    ('vol18-19', [18, 19], '單提九十二事法之七、八'),
    ('vol20-21', [20, 21], '單提九十二事法之九、十・眾學法之初'),
    ('vol22', [22], '眾學法之餘'),
    ('vol23-24', [23, 24], '雜誦跋渠法之一、二'),
    ('vol25-26', [25, 26], '雜誦跋渠法之三、四'),
    ('vol27-28', [27, 28], '雜誦跋渠法之五、六'),
    ('vol29-30', [29, 30], '雜誦跋渠法之七、八'),
    ('vol31-32', [31, 32], '雜誦跋渠法之九、十'),
    ('vol33', [33], '雜誦跋渠法之十一'),
    ('vol34-35', [34, 35], '威儀法之一、二'),
    ('vol36-37', [36, 37], '尼八波羅夷法・十九僧殘法・一百四十一波夜提法之一'),
    ('vol38-39', [38, 39], '尼一百四十一波夜提法之二、三'),
    ('vol40', [40], '尼一百四十一波夜提法之餘・八提舍尼法・雜跋渠法'),
]

units = [{'unit': u, 'vols': v, 'title': t} for u, v, t in U]
json.dump(units, open(os.path.join(W, 'mk_units.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

idx = {x['v']: x for x in json.load(open(os.path.join(W, 'sengqi_index.json'), encoding='utf-8'))}
cover = sorted({v for _, vs, _ in U for v in vs})
print('units', len(units), 'vols covered', len(cover), 'missing', [v for v in range(1, 41) if v not in cover])
print('src chars total', sum(idx[v]['chars'] for v in range(1, 41)))
