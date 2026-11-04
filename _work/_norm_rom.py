# -*- coding: utf-8 -*-
"""統一白話夾註中的羅馬字轉寫。

同一術語在不同卷帙間或作 IAST、或作 ASCII、或取巴利語形，讀者每疑為二字。
此處一律歸於梵語 IAST 一式；複合詞中之後支仍用小寫（如 Jñapticaturtha-karma）。
只改夾註，不改譯文；只改有異寫之詞，單一寫法者仍其舊。
"""
import json, io, re, collections, sys

MAP = {
    # 罪名
    'Dushkrita': 'Duṣkṛta', 'Duskrita': 'Duṣkṛta', 'Duskṛta': 'Duṣkṛta',
    'Dukkaṭa': 'Duṣkṛta', 'Dukkata': 'Duṣkṛta',
    'Pacittiya': 'Pāyattika', 'Pācittiya': 'Pāyattika',
    'Patayantika': 'Pāyattika', 'pācittiya': 'Pāyattika',
    'Thullaccaya': 'Sthūlātyaya', 'Sthulatyaya': 'Sthūlātyaya',
    'Sanghavasesa': 'Saṃghāvaśeṣa', 'Sanghadisesa': 'Saṃghāvaśeṣa',
    'Samghavasesa': 'Saṃghāvaśeṣa',
    'Parajika': 'Pārājika',
    # 眾別
    'Sramanerika': 'Śrāmaṇerikā', 'Sramanera': 'Śrāmaṇera', 'Samanera': 'Śrāmaṇera',
    'Bhikshuni': 'Bhikṣuṇī', 'Bhikkhuni': 'Bhikṣuṇī',
    'Bhikshu': 'Bhikṣu', 'Bhikkhu': 'Bhikṣu',
    'Upasaka': 'Upāsaka', 'Upasika': 'Upāsikā',
    'Siksamana': 'Śikṣamāṇā', 'Shikshamana': 'Śikṣamāṇā',
    # 僧團法制
    'Sanghakamma': 'Saṃghakarma', 'Sangharama': 'Saṃghārāma',
    'Sanghati': 'Saṃghāṭī', 'Samghati': 'Saṃghāṭī',
    'Sangha': 'Saṃgha',
    'Uposatha': 'Upoṣadha', 'Posadha': 'Upoṣadha', 'Poṣadha': 'Upoṣadha',
    'Patimokkha': 'Prātimokṣa',
    'Nissaggiya': 'Naiḥsargika', 'Nisaggiya': 'Naiḥsargika',
    'Manatta': 'Mānatta',
    'Parivasa': 'Parivāsa',
    'Jnatticatuttha': 'Jñapticaturtha', 'Jnapti': 'Jñapti',
    'Karman': 'Karma', 'Kamma': 'Karma', 'kamma': 'karma',
    # 行法與名物
    'Sramana': 'Śramaṇa',
    'Dhutanga': 'Dhūta', 'Dhuta': 'Dhūta',
    'Danapati': 'Dānapati',
    'Aranya': 'Araṇya',
    'Acarya': 'Ācārya',
    'Upadhyaya': 'Upādhyāya', 'Upajjhaya': 'Upādhyāya',
    'Brahmacariya': 'Brahmacarya', 'Brahmacaryā': 'Brahmacarya',
    'Asrava': 'Āsrava',
    'Pamsukula': 'Pāṃśukūla',
    'Patra': 'Pātra',
    'Nirvana': 'Nirvāṇa',
    'Tathagata': 'Tathāgata',
    'Vassa': 'Varṣā',
    'Kathina': 'Kaṭhina',
    'Samadhi': 'Samādhi',
    'Prajna': 'Prajñā',
    'Sutra': 'Sūtra',
    'Bimbisara': 'Bimbisāra',
}

LET = 'A-Za-zĀāĪīŪūṚṛṂṃḤḥŚśṢṣṬṭḌḍṆṇÑñ'
KEYS = sorted(MAP, key=len, reverse=True)
PAT = re.compile('(?<![%s])(%s)(?![%s])' % (LET, '|'.join(map(re.escape, KEYS)), LET))


def norm(s):
    return PAT.sub(lambda m: MAP[m.group(1)], s or '')


def main(write=False):
    p = 'sifen_plain.json'
    raw = io.open(p, 'rb').read().decode('utf-8')
    d = json.loads(raw)
    cnt = collections.Counter()
    hit = {}
    for k, v in list(d.items()):
        nv = norm(v)
        for m in PAT.finditer(v or ''):
            cnt[m.group(1)] += 1
            hit.setdefault(m.group(1), k)
        if nv != (v or ''):
            d[k] = nv
    for k, n in cnt.most_common():
        print('%4d  %-16s -> %-16s  例 %s' % (n, k, MAP[k], hit[k]))
    print('合計', sum(cnt.values()), '處；涉', len(set(hit.values())), '段')
    if write:
        s = json.dumps(d, ensure_ascii=False, indent=0).replace('\n', '\r\n')
        io.open(p, 'wb').write(s.encode('utf-8'))
        print('已寫回', p)


if __name__ == '__main__':
    main('--write' in sys.argv)
