#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pas_extract.py — .pas 輔助擷取（graph-engine，輔助 extract.field-cross-check）

用途：把 field-cross-check 需要的三方來源中「來自 .pas」的兩項機械化擷取，
省去人工翻 Delphi：
  1. AddFieldEvent(Self, Dqn, 'F1;F2;…')  → in_gettext（各 grid 的顯示欄清單）
  2. 欄位 picker 呼叫（KeyCodePick / KeyCodeValidate / EditPick / EditMemo） → 輔助 input-component-choice 決策樹
  3. SQL select 子句（best-effort）        → in_sql（**模糊，agent 需覆核**）

**定位**：輔助工具，非權威。輸出 UTF-8 JSON；SQL 擷取為 best-effort，
`decision` 仍由 agent 依 `details/delphi-reading.md` 三方交叉判定（鐵則4，不推測）。

用法：
  py .claude/SelfFolder/graph-engine/tools/pas_extract.py <B代碼.pas 路徑> [--pretty]
"""
import io
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass


def read_pas(path: Path) -> str:
    """Delphi .pas 常為 Big5(cp950)；utf-8 → cp950 → latin-1 逐層退。"""
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("latin-1", errors="replace")


def extract_addfieldevent(text: str):
    """AddFieldEvent(Self, Dqn, 'F1;F2;…', ...) → {grid: [fields]}。權威度高。"""
    out = {}
    # 第 2 引數＝grid 識別（Dq1/Self/…），第 3 引數＝分號分隔欄位清單
    pat = re.compile(r"AddFieldEvent\s*\(\s*[^,]+,\s*(\w+)\s*,\s*'([^']*)'", re.I)
    for m in pat.finditer(text):
        grid = m.group(1).strip()
        fields = [f.strip() for f in m.group(2).split(";") if f.strip()]
        out.setdefault(grid, [])
        for f in fields:
            if f not in out[grid]:
                out[grid].append(f)
    return out


def extract_pickers(text: str):
    """picker/memo 呼叫 → 輔助 input-component-choice。回 [{kind, field}]。"""
    kinds = {
        "KeyCodePick": "KeyCodeComboBox",
        "KeyCodeValidate": "KeyCodeComboBox",
        "EditPick": "EditPick(看欄數:≤2→IksCodeComboBox / ≥3→EditPick)",
        "EditMemo": "PopUpText",
    }
    out = []
    for kind, suggest in kinds.items():
        # 例：KeyCodePick(Sender, 'STATUS', ...) / EditPick(..., 'CUSTMER', ...)
        for m in re.finditer(rf"\b{kind}\b\s*\(([^)]*)\)", text, re.I):
            args = m.group(1)
            fields = re.findall(r"'([A-Za-z_]\w*)'", args)
            out.append({"kind": kind, "suggest": suggest,
                        "fields": fields, "raw_args": args.strip()[:120]})
    return out


def extract_sql_selects(text: str):
    """best-effort：把連續單引號字串片段接起來，抓 select … from 的欄位清單。**agent 需覆核**。"""
    # 收集所有單引號字串字面，串成一條「SQL 文字流」
    literals = re.findall(r"'([^']*)'", text)
    blob = " ".join(literals)
    selects = []
    for m in re.finditer(r"\bselect\b(.*?)\bfrom\b", blob, re.I | re.S):
        cols_raw = m.group(1)
        # 去掉別名/函式雜訊只做粗切；保留原字串供人看
        cols = [c.strip() for c in cols_raw.split(",") if c.strip()]
        selects.append({"columns_raw": cols_raw.strip()[:400],
                        "columns_guess": [re.split(r"\s+", c)[-1] for c in cols][:60]})
    return selects


def main(argv):
    if len(argv) < 2:
        print("用法: pas_extract.py <路徑.pas> [--pretty]")
        sys.exit(2)
    path = Path(argv[1])
    if not path.exists():
        print(json.dumps({"error": f"找不到 {path}"}, ensure_ascii=False))
        sys.exit(1)
    text = read_pas(path)
    result = {
        "file": str(path),
        "note": "輔助擷取；in_sql 為 best-effort，decision 由 agent 依 delphi-reading.md 三方交叉判定（不推測）",
        "addfieldevent": extract_addfieldevent(text),   # in_gettext（權威度高）
        "pickers": extract_pickers(text),                # 輔助 input-component-choice
        "sql_selects": extract_sql_selects(text),        # in_sql（模糊，需覆核）
    }
    indent = 2 if "--pretty" in argv else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main(sys.argv)
