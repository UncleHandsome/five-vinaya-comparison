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


# ── 第二輪：人地名與其餘名相（2026-11-04）──────────────────────────
# 同一詞在諸卷之間或作巴利、或作 ASCII、或漏一變音符，前輪未及者，此處補之。
MAP.update({
    # 人地名
    'Rajagaha': 'Rājagṛha', 'Kassapa': 'Kāśyapa', 'Uruvela': 'Uruvilvā',
    'Kitagiri': 'Kīṭāgiri', 'Sakra': 'Śakra', 'Devanam': 'Devānāṃ',
    'Candala': 'Caṇḍāla', 'Panca': 'Pañca', 'Yasa': 'Yaśas',
    'Brahmin': 'Brāhmaṇa', 'Jivaka': 'Jīvaka', 'Kosambi': 'Kosambī',
    'Manava': 'Māṇava', 'Upali': 'Upāli', 'Visakha': 'Visākhā',
    'Varanasi': 'Vārāṇasī', 'Amrapali': 'Āmrapālī', 'Ananda': 'Ānanda',
    'Abhavana': 'Abhavana', 'Abhavāna': 'Abhavana', 'Abhāvāna': 'Abhavana',
    # 名相
    'Bhagavan': 'Bhagavān', 'Dhyana': 'Dhyāna', 'Samyojana': 'Saṃyojana',
    'Kasaya': 'Kāṣāya', 'Kaṣāya': 'Kāṣāya',
    'Nisidana': 'Niṣīdana', 'Nisīdana': 'Niṣīdana', 'Nivasana': 'Nivāsana',
    'Antaravasaka': 'Antarvāsa', 'Sankaksika': 'Saṃkakṣikā',
    'Uttarasanga': 'Uttarāsaṅga', 'Pandaka': 'Paṇḍaka',
    'Parinirvana': 'Parinirvāṇa',
    'Pāṃśūkūla': 'Pāṃśukūla', 'Pāṃsukūla': 'Pāṃśukūla',
    'Sima': 'Sīmā', 'Stupa': 'Stūpa', 'Tirthika': 'Tīrthika',
    'Sravaka': 'Śrāvaka', 'Sramaneri': 'Śrāmaṇerī',
    'Srotapanna': 'Srotāpanna', 'Sakrdagamin': 'Sakṛdāgāmin',
    'Anagamin': 'Anāgāmin', 'Adhimana': 'Adhimāna',
    'Anuvada': 'Anuvāda', 'Amrta': 'Amṛta',
    'Pratityasamutpada': 'Pratītyasamutpāda', 'Trayastrimsa': 'Trāyastriṃśa',
    'Jambudvipa': 'Jambudvīpa', 'Salaka': 'Śalākā', 'Salākā': 'Śalākā',
    'Sarpirmanda': 'Sarpirmaṇḍa', 'Khadaniya': 'Khādanīya',
    'Amudha-vinaya': 'Amūḍha-vinaya',
    # 僧團法制（補前輪未及之巴利形與漏符者）
    'Pavarana': 'Pravāraṇā', 'Pavāraṇā': 'Pravāraṇā',
    'Pravārana': 'Pravāraṇā', 'Pravarana': 'Pravāraṇā',
    'Patidesaniya': 'Prātideśanīya', 'Pātidesaniya': 'Prātideśanīya',
    'Pāṭidesanīya': 'Prātideśanīya', 'Pratidesaniya': 'Prātideśanīya',
    'Pratideśanīya': 'Prātideśanīya',
    'Pārisuddhi': 'Pāriśuddhi', 'Pariśuddhi': 'Pāriśuddhi',
    'Upasampada': 'Upasaṃpadā',
    'Sanghādisesa': 'Saṃghāvaśeṣa', 'Saṅghādisesa': 'Saṃghāvaśeṣa',
    'Saṅghāvaśeṣa': 'Saṃghāvaśeṣa', 'Sanghāvaśeṣa': 'Saṃghāvaśeṣa',
    'Śikṣamānā': 'Śikṣamāṇā', 'Saṃghāṭi': 'Saṃghāṭī',
    'Samgharama': 'Saṃghārāma', 'Āraṇya': 'Araṇya', 'Bhiksu': 'Bhikṣu',
    'nisraya': 'Niśraya', 'Jnaptidvitiya-karman': 'Jñaptidvitīya-karman',
    'Kappiya-karaka': 'Kalpika-kāraka', 'Kappiya-kāraka': 'Kalpika-kāraka',
    'Kappiya-bhūmi': 'Kalpika-bhūmi', 'Kappiya': 'Kalpika',
    'Uttarimanussadhamma': 'Uttarimanuṣyadharma',
    'Uttari-manussa-dhamma': 'Uttarimanuṣyadharma',
    'Viraja-dhamma-cakkhu': 'Viraja-dharma-cakṣu',
    'Samyak-sambodhi': 'Samyak-saṃbodhi', 'Samyak-sambuddha': 'Samyak-saṃbuddha',
})

LET = 'A-Za-zĀāĪīŪūṚṛṂṃḤḥŚśṢṣṬṭḌḍṆṇÑñṄṅ'
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
