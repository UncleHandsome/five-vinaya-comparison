#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把各稿對照欄的引用標記統一為讀者可用之形式。

  四分：`NNN` 段M   （篇號，因本書按四分篇次組織）
  五分：五分 卷N 段M
  十誦：十誦 卷N 段M

原則：只改「標記」不改「引文」。標記限於開頭或「；」「。」之後的定位語。
"""
import re

# 內部路徑（全字串移除，含 `_work/` 前綴與反引號）
PATH_ANY = re.compile(r'`?(?:_work/)?(?:sifen_chunks|sifen|wufen|shisong|sengqi|genben)/`?')

# 四分篇名檔：必須含「_」後接篇名，避免把「段172」的 172 誤認為篇號
SIFEN_FILE = re.compile(r'`?(\d{3})_+[A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff]{0,18}_*(?:\.txt)?`?')
SIFEN_PREFIX = re.compile(r'四分\s*(\d{3})_+[A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff]{0,18}')
CHUNK = re.compile(r'`?(?:shoujie|shuojie|anju|zizi)(?:_\d+)?(?:\.txt)?`?')
# 開頭 NNN-M（NNN 為篇號，2–74）
SIFEN_DASH = re.compile(r'^`?(\d{3})-(\d{1,3})`?')

# 他律 volNN
VOL = re.compile(r'`?vol(\d{1,2})(?:[-–](\d{1,2}))?\.txt`?')
VOL2 = re.compile(r'`?vol(\d{1,2})(?:[-–](\d{1,2}))?`?(?=[·\s段：:])')
# 律名後緊接 N-M（如「五分11-81」）
NAMED_DASH = re.compile(r'(五分|十誦|僧祇|根有)\s*(\d{1,2})-(\d{1,3})(?![\d])')
# 開頭 N-M（N 為卷）
VOL_DASH = re.compile(r'^(\d{1,2})-(\d{1,3})(?![\d])')


def _juan(n):
    return str(int(n))


def normalize(s, kind):
    """kind: '四分' / '五分' / '十誦'"""
    if not s or not s.strip():
        return s or ''
    s = s.strip()

    # 1) 全字串去內部路徑
    s = PATH_ANY.sub('', s)
    # 原始檔名「01-10原文.txt」→「卷1–10原檔」
    s = re.sub(r'(\d{1,2})-(\d{1,2})\s*原文\.txt',
               lambda m: f'卷{int(m.group(1))}–{int(m.group(2))}原檔', s)
    s = re.sub(r'(\d{1,2})\s*原文\.txt', lambda m: f'卷{int(m.group(1))}原檔', s)

    if kind == '四分':
        s = CHUNK.sub('`038`', s)
        s = SIFEN_PREFIX.sub(lambda m: f'`{m.group(1)}`', s)
        s = SIFEN_FILE.sub(lambda m: f'`{m.group(1)}`', s)
        # 篇號範圍 NNN-NNN → `NNN`、`NNN`（須先於「篇-段」判定，否則 059 被誤為段號）
        s = re.sub(r'^`?(\d{3})[-–](\d{3})`?(?![-\d])',
                   lambda m: f'`{m.group(1)}`、`{m.group(2)}`', s)
        # 開頭 NNN-M → `NNN` 段M
        s = SIFEN_DASH.sub(lambda m: f'`{m.group(1)}` 段{m.group(2)}', s)
        # 篇名替換後殘留的 `NNN`-M → `NNN` 段M
        s = re.sub(r'(`\d{3}`)-(\d{1,3})(?![\d])', lambda m: f'{m.group(1)} 段{m.group(2)}', s)
        # 開頭無篇名的 NNN 段M / NNN段M → `NNN` 段M
        s = re.sub(r'^(\d{3})\s*段\s*(\d{1,3})', lambda m: f'`{m.group(1)}` 段{m.group(2)}', s)
    else:
        name = kind
        s = VOL.sub(lambda m: f'卷{_juan(m.group(1))}' + (f'–{_juan(m.group(2))}' if m.group(2) else ''), s)
        s = VOL2.sub(lambda m: f'卷{_juan(m.group(1))}' + (f'–{_juan(m.group(2))}' if m.group(2) else ''), s)
        # 律名後緊接 N-M → 律名 卷N 段M
        s = NAMED_DASH.sub(lambda m: f'{m.group(1)} 卷{_juan(m.group(2))} 段{m.group(3)}', s)
        # 開頭 N-M → 卷N 段M
        s = VOL_DASH.sub(lambda m: f'卷{_juan(m.group(1))} 段{m.group(2)}', s)
        # 卷N·段M → 卷N 段M
        s = re.sub(r'卷(\d{1,2})[·・]\s*段?(\d{1,3})', lambda m: f'卷{m.group(1)} 段{m.group(2)}', s)
        s = re.sub(r'卷(\d{1,2})[·・]', lambda m: f'卷{m.group(1)} ', s)
        # 補律名
        if not s.startswith(name) and not s.startswith('遍查') and not s.startswith('全無') and not s.startswith('全庫'):
            s = f'{name} {s}'

    # 收尾清理
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'`\s+`', '` `', s)
    s = s.replace('``', '`')
    # 保險：若反引號總數為奇數，移除最靠近「段」的那個孤立反引號
    if s.count('`') % 2 == 1:
        s = re.sub(r'`(?=\s*段)', '', s, count=1)
    if s.count('`') % 2 == 1:
        s = re.sub(r'`(?=\s*[～~–—-])', '', s, count=1)
    if s.count('`') % 2 == 1:
        s = re.sub(r'`(?=\s*$)', '', s, count=1)
    return s


if __name__ == '__main__':
    import json, random
    d = json.load(open('matrix_built.json', encoding='utf-8'))
    random.seed(11)
    for kind, key in [('四分', 'ref4'), ('五分', 'ref5'), ('十誦', 'ref10')]:
        print(f'===== {kind} / {key} =====')
        vals = [r.get(key, '') for r in d if (r.get(key) or '').strip()]
        for v in random.sample(vals, min(10, len(vals))):
            print('  前:', v[:78].replace('\n', ' '))
            print('  後:', normalize(v, kind)[:78].replace('\n', ' '))
            print()
