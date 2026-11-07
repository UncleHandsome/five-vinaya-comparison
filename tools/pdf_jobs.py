#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增量 PDF 建置：只重建內容有變的冊；分卷並行，合冊預設延後。

為什麼要這支：
  全量 32 冊約 35 分鐘，但九成時間花在「合冊」的單進程排版
  （Chrome 2,611 頁約 4.5 分、xelatex 3,153 頁約 10 分）。
  日常改一句話、改一個分卷，其實只需重排該卷（幾秒～2 分）。
  本工具以「源內容指紋」判斷，未變者一律跳過；分卷以多進程並行。

用法：
  python tools/pdf_jobs.py --plan            # 只列計畫與預估，不生成
  python tools/pdf_jobs.py --status          # 列出每冊狀態與上次耗時
  python tools/pdf_jobs.py                   # 增量：分卷並行；合冊延後
  python tools/pdf_jobs.py --include-full    # 連合冊一併生成
  python tools/pdf_jobs.py --force           # 全量重建
  python tools/pdf_jobs.py --only 卷三十一    # 只做名稱含此字串的冊
  python tools/pdf_jobs.py --jobs 3          # 並行數（預設 3）
  python tools/pdf_jobs.py --parallel-full   # 合冊也並行（記憶體要夠）

指紋＝源 MD（精簡版為 strip_lean 後文本）＋ 三支生成腳本 ＋ 參數。
清單存 _work/_pdf_jobs.json（不入版控）。
"""
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, '_work'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_pdf as P          # noqa: E402
import build_tex as T          # noqa: E402
import build_lean as L         # noqa: E402

SRC = P.SRC
WORK = os.path.join(ROOT, '_work')
MANIFEST = os.path.join(WORK, '_pdf_jobs.json')
TMP = os.path.join(WORK, '_pdf_jobs_tmp')

TITLE = '五部律差異對照本'
LEAN_TITLE = TITLE + '（精簡版）'
LEAN_SUB = '精簡版　去白話、去四分律原文'


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _gen_hash():
    """生成器指紋：三支腳本任一改動，全部重算。"""
    h = hashlib.sha256()
    for f in (os.path.join(WORK, 'build_pdf.py'),
              os.path.join(WORK, 'build_tex.py'),
              os.path.join(ROOT, 'tools', 'build_lean.py')):
        with open(f, 'rb') as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def _jobs():
    """定義 32 冊。回傳 (jobs, lean_texts)。"""
    gen = _gen_hash()
    jobs = []
    lean_texts = {}

    full_md = os.path.join(SRC, P.FULL)
    raw = open(full_md, encoding='utf-8').read()
    lean_full, _, _ = L.strip_lean(raw)

    # 完整版
    for jname, fn in P.JUAN:
        src = os.path.join(SRC, fn)
        jobs.append(dict(key='full-chrome-' + jname, kind='full', engine='chrome',
                         vol=jname, src=src, out=os.path.join(P.OUT, fn.replace('.md', '.pdf')),
                         title=f'{TITLE}　{jname}', md_text=None, gen=gen))
        jobs.append(dict(key='full-tex-' + jname, kind='full', engine='tex',
                         vol=jname, src=src, out=os.path.join(T.OUT, fn.replace('.md', '.pdf')),
                         title=f'{TITLE}　{jname}', md_text=None, gen=gen))
    for engine in ('chrome', 'tex'):
        out_dir = P.OUT if engine == 'chrome' else T.OUT
        jobs.append(dict(key='full-%s-合冊' % engine, kind='full', engine=engine,
                         vol='合冊', src=full_md,
                         out=os.path.join(out_dir, P.FULL.replace('.md', '.pdf')),
                         title=TITLE, md_text=None, gen=gen, is_full=True))

    # 精簡版
    lean_path_full = os.path.join(SRC, L.LEAN)
    for jname, fn in P.JUAN:
        src = os.path.join(SRC, fn)
        raw_j = open(src, encoding='utf-8').read()
        lean_j, _, _ = L.strip_lean(raw_j)
        lean_texts[jname] = lean_j
        tmp = os.path.join(TMP, fn)
        os.makedirs(TMP, exist_ok=True)
        with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(lean_j)
        for engine in ('chrome', 'tex'):
            jobs.append(dict(
                key='lean-%s-%s' % (engine, jname), kind='lean', engine=engine,
                vol=jname, src=tmp, out=os.path.join(
                    L.OUT, '五部律差異對照本_精簡_%s_%s.pdf'
                    % (jname, 'Chrome' if engine == 'chrome' else 'LaTeX')),
                title='%s　%s' % (LEAN_TITLE, jname), md_text=lean_j, gen=gen))
    lean_texts['合冊'] = lean_full
    with open(lean_path_full, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(lean_full)
    for engine in ('chrome', 'tex'):
        jobs.append(dict(
            key='lean-%s-合冊' % engine, kind='lean', engine=engine, vol='合冊',
            src=lean_path_full,
            out=os.path.join(L.OUT, '五部律差異對照本_精簡_%s.pdf'
                             % ('Chrome' if engine == 'chrome' else 'LaTeX')),
            title=LEAN_TITLE, md_text=lean_full, gen=gen, is_full=True))

    for j in jobs:
        text = j['md_text'] if j['md_text'] is not None else open(j['src'], encoding='utf-8').read()
        j['fp'] = _sha((j['gen'] + '|' + j['key'] + '|' + j['title']).encode()) + '-' + _sha(text.encode())[:20]
    return jobs


def _load():
    try:
        return json.load(open(MANIFEST, encoding='utf-8'))
    except Exception:
        return {'jobs': {}}


def _save(man):
    os.makedirs(WORK, exist_ok=True)
    with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)


def _fmt(sec):
    if not sec:
        return '—'
    return '%.0fs' % sec if sec < 90 else '%.1f分' % (sec / 60)


def _plan(jobs, man, force=False, only=None, include_full=False):
    """回傳 (todo, skip)；並印出表格。"""
    todo, skip = [], []
    for j in jobs:
        if only and only not in j['key'] and only not in j['vol']:
            continue
        if j.get('is_full') and not include_full and not force:
            skip.append((j, '合冊延後'))
            continue
        rec = man['jobs'].get(j['key'], {})
        exists = os.path.exists(j['out'])
        fresh = exists and rec.get('fp') == j['fp']
        if not force and fresh:
            skip.append((j, '最新'))
        else:
            why = '缺檔' if not exists else ('強制' if force else '內容已變')
            todo.append((j, why, rec.get('seconds')))
    return todo, skip


def _run_one(j):
    t0 = time.time()
    if j['engine'] == 'chrome':
        meta = None
        if j['kind'] == 'lean':
            meta = ['— 精簡版%s —' % ('' if j['vol'] == '合冊' else '・' + j['vol']),
                    '只存差異條列與本稿原文',
                    'A4 · 內文 12pt · 緊湊排版']
        ok = P.md_to_pdf(j['src'], j['out'], j['title'],
                         md_text=j['md_text'], subtitle=(LEAN_SUB if j['kind'] == 'lean' else None),
                         meta_lines=meta)
    else:
        ok = T.build(j['src'], j['out'], j['title'],
                     tmp_dir=os.path.join(TMP, 'tex_' + j['key']))
    return ok, time.time() - t0


def main():
    args = sys.argv[1:]
    do_plan = '--plan' in args
    do_status = '--status' in args
    force = '--force' in args
    include_full = '--include-full' in args
    parallel_full = '--parallel-full' in args
    jobs_n = 3
    for i, a in enumerate(args):
        if a.startswith('--jobs='):
            jobs_n = max(1, int(a.split('=', 1)[1]))
        elif a == '--jobs' and i + 1 < len(args):
            jobs_n = max(1, int(args[i + 1]))
    only = None
    for i, a in enumerate(args):
        if a == '--only' and i + 1 < len(args):
            only = args[i + 1]

    jobs = _jobs()
    man = _load()
    # 首次建立清單：沿用現有 PDF（以合冊 MD 的 mtime 為參考，免把剛寫出的精簡 MD 誤判為新源）
    if not man.get('jobs'):
        ref = os.path.getmtime(os.path.join(SRC, P.FULL))
        adopted = 0
        for j in jobs:
            if os.path.exists(j['out']) and os.path.getmtime(j['out']) >= ref - 60:
                man['jobs'][j['key']] = {'fp': j['fp'], 'seconds': 0, 'adopted': True,
                                         'at': time.strftime('%Y-%m-%d %H:%M')}
                adopted += 1
        _save(man)
        print('首次建立清單：沿用現有 %d 冊，指紋已記錄。\n' % adopted)
    todo, skip = _plan(jobs, man, force, only, include_full)

    if do_status or do_plan:
        print('%-26s %-10s %-8s %s' % ('冊', '狀態', '上次', '檔案'))
        for j, why, sec in todo:
            print('%-26s %-10s %-8s %s' % (j['key'], why, _fmt(sec), '有' if os.path.exists(j['out']) else '缺'))
        for j, why in skip:
            rec = man['jobs'].get(j['key'], {})
            print('%-26s %-10s %-8s %s' % (j['key'], why, _fmt(rec.get('seconds')), '有' if os.path.exists(j['out']) else '缺'))
        est = sum((s or (25 if j['engine'] == 'chrome' else 110)) for j, _w, s in todo)
        print('\n需重建 %d 冊，跳過 %d 冊；串行估計 %.1f 分，%d 路並行約 %.1f 分'
              % (len(todo), len(skip), est / 60, jobs_n,
                 (est / max(1, min(jobs_n, max(1, len(todo))))) / 60))
        if do_plan:
            return

    if not todo:
        print('全部最新，無需重建。')
        return

    # 分卷並行；合冊串行（可用 --parallel-full 一起並行）
    vols = [(j, w) for j, w, _s in todo if not j.get('is_full')]
    fulls = [(j, w) for j, w, _s in todo if j.get('is_full')]
    t_all = time.time()
    done = 0
    if vols:
        print('分卷並行（%d 路）：' % min(jobs_n, len(vols)))
        with ThreadPoolExecutor(max_workers=min(jobs_n, len(vols))) as ex:
            futs = {ex.submit(_run_one, j): (j, w) for j, w in vols}
            for f in as_completed(futs):
                j, w = futs[f]
                try:
                    ok, sec = f.result()
                except Exception as e:      # noqa: BLE001
                    ok, sec = False, 0
                    print('  ✗ %s：%s' % (j['key'], e))
                done += 1
                print('  [%d/%d] %-24s %s %s' % (done, len(vols), j['key'],
                                                 'OK ' if ok else 'FAIL', _fmt(sec)))
                if ok:
                    man['jobs'][j['key']] = {'fp': j['fp'], 'seconds': round(sec, 1),
                                             'size': os.path.getsize(j['out']),
                                             'at': time.strftime('%Y-%m-%d %H:%M')}
                    _save(man)

    if fulls and parallel_full:
        print('合冊並行：')
        with ThreadPoolExecutor(max_workers=min(2, len(fulls))) as ex:
            futs = {ex.submit(_run_one, j): (j, w) for j, w in fulls}
            for f in as_completed(futs):
                j, w = futs[f]
                ok, sec = f.result()
                print('  %-24s %s %s' % (j['key'], 'OK ' if ok else 'FAIL', _fmt(sec)))
                if ok:
                    man['jobs'][j['key']] = {'fp': j['fp'], 'seconds': round(sec, 1),
                                             'size': os.path.getsize(j['out']),
                                             'at': time.strftime('%Y-%m-%d %H:%M')}
                    _save(man)
    elif fulls:
        print('合冊（串行，較久；可加 --include-full 之外的日常改動不必跑）：')
        for j, w in fulls:
            print('  %-24s …' % j['key'], end=' ', flush=True)
            ok, sec = _run_one(j)
            print('%s %s' % ('OK' if ok else 'FAIL', _fmt(sec)))
            if ok:
                man['jobs'][j['key']] = {'fp': j['fp'], 'seconds': round(sec, 1),
                                         'size': os.path.getsize(j['out']),
                                         'at': time.strftime('%Y-%m-%d %H:%M')}
                _save(man)

    print('\n完成，共 %.1f 分。' % ((time.time() - t_all) / 60))
    stale = [j for j in jobs if j.get('is_full')
             and man['jobs'].get(j['key'], {}).get('fp') != j['fp']]
    if stale:
        print('提醒：合冊有 %d 冊已落後（本次延後），定稿時跑 --include-full。' % len(stale))


if __name__ == '__main__':
    main()
