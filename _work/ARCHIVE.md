# 腳本現況（2026-11-06 整理）

`_work/` 與 `tools/` 合計 **155** 支 Python 腳本。依 `rebuild_all.py` 的十步流程，
加上各附錄／專題表工具、其自訂 import 閉包，以及 `交接.md` 明列之資料生成腳本，
判定 **25 支活躍**；其餘 **130 支為歷史批次**
（`build_vol*`、`match*`、`qc_*`、`audit*`、`assemble*` 等）。

## 為什麼不實體搬進 `archive/`

歷史腳本多以 `__file__` 定位 `_work`（`W = os.path.dirname(__file__)`，
再由此讀 `sifen/`、`*.json`、`findings/`）。一旦移到子目錄，路徑全斷；
逐支改路徑牽動百餘檔，且這些腳本已不參與建置，故**保留原位**。

改以「版控歸檔」處理：歷史腳本自 git 索引移除（`git rm --cached`），
檔案仍留在磁碟；往後由 `.gitignore` 排除，新 clone 只取活躍腳本。
舊版可自遠端 `backup-before-rewrite-20261106` 分支或本機 mirror 備份還原。

## 活躍腳本（25）

- `_work/align_sifen2.py`
- `_work/build_compare.py`
- `_work/build_html.py`
- `_work/build_matrix_html.py`
- `_work/build_pdf.py`
- `_work/build_tex.py`
- `_work/diff_fmt.py`
- `_work/diff_rewrite.py`
- `_work/errata.py`
- `_work/fix_csv.py`
- `_work/locate_sifen.py`
- `_work/matrix_md.py`
- `_work/norm_ref.py`
- `_work/rebuild_all.py`
- `_work/section_intro.py`
- `_work/sifen_src.py`
- `tools/build_appendices.py`
- `tools/build_jie_names.py`
- `tools/build_merge_place.py`
- `tools/build_mk_index.py`
- `tools/build_sclass.py`
- `tools/build_tables_html.py`
- `tools/fill_mk_gu.py`
- `tools/reclass_sclass.py`
- `tools/verify_integrity.py`

## 歷史腳本（130，節錄）

- `_work/add_zizi1.py`
- `_work/assemble.py`
- `_work/assemble2.py`
- `_work/assemble_mk.py`
- `_work/assemble_ss.py`
- `_work/audit_all.py`
- `_work/audit_precise.py`
- `_work/build_2021.py`
- `_work/build_index.py`
- `_work/build_ss.py`
- `_work/build_two.py`
- `_work/build_vol0405.py`
- `_work/build_vol1112.py`
- `_work/build_vol21_ss.py`
- `_work/build_vol35.py`
- `_work/build_vol4445.py`
- `_work/build_vol51b.py`
- `_work/build_vol52.py`
- `_work/build_vol53.py`
- `_work/build_vol55.py`
- `_work/build_vol56.py`
- `_work/build_vol57.py`
- `_work/build_vol58.py`
- `_work/build_vol61a.py`
- `_work/check_cites.py`
- …其餘 105 支見 `script_map.json`
