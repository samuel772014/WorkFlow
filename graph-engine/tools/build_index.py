#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index.py — 知識圖譜 index 產生器（graph-engine Step 2）

掃描專案既有事實，產出單一可查 index.json，餵給 graph 的 extract.fact-resolve node，
讓 AI「查事實」而非「推測」（CLAUDE.md 鐵則 4）。這輪你遇到的四類 bug
（研判功能名 / _Display 漏接 / keycode 未註冊 / 方言）全源於「事實沒被索引」。

索引四類事實：
  1. programs        SAL ↔ B 代碼 ↔ 功能名（權威：SAL程式編號對照表.md）
  2. display_transforms  已註冊的 keycode(_kcMap*) 與 name(_map*) 映射（避免漏接/撞名）
  3. func_reuse      Modules/FUNC/*.cs 既有共用函式（勿重寫，記憶 reuse_func_modules）
  4. existing_pages  已存在的 SAL razor（避免重複、可當 golden set 候選）

用法：
  PYTHONIOENCODING=utf-8 py .claude/SelfFolder/graph-engine/tools/build_index.py
  （於 repo 根目錄執行；輸出 .claude/SelfFolder/graph-engine/index.json）
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---- 路徑（相對 repo 根；此檔在 .claude/SelfFolder/graph-engine/tools/）----
ROOT = Path(__file__).resolve().parents[4]          # repo 根
GRAPH_DIR = Path(__file__).resolve().parents[1]      # graph-engine/
MAP_MD = ROOT / ".claude" / "SelfFolder" / "SAL程式編號對照表.md"
COMMON_DIR = ROOT / "IKSERPPRJ" / "IKSERPAPI" / "Modules" / "COMMON"
FUNC_DIR = ROOT / "IKSERPPRJ" / "IKSERPAPI" / "Modules" / "FUNC"
SAL_PAGES = ROOT / "IKSERPPRJ" / "IKSERPUI" / "Components" / "Pages" / "SAL"
OUT = GRAPH_DIR / "index.json"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


# ---- 1. programs：解析對照表 markdown 表格 ----
def parse_programs() -> list:
    rows = []
    for line in read(MAP_MD).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        sal = cells[0]
        # 只收資料列：新程式編號欄形如 SAL001
        if not re.fullmatch(r"SAL\d+[A-Z]?", sal):
            continue
        rows.append({
            "sal": sal,
            "b_code": cells[1] if len(cells) > 1 else "",
            "name": cells[2] if len(cells) > 2 else "",
            "parent": cells[3] if len(cells) > 3 else "",
            "ui_type": cells[4] if len(cells) > 4 else "",
        })
    return rows


# ---- 2. display_transforms：解析 _kcMap* / _map* 字典 ----
DICT_DECL = re.compile(r"_(kcMap|map)([A-Za-z]+)\s*=\s*new\(\)")
KC_ENTRY = re.compile(r'\["([^"]+)"\]\s*=\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)')
NAME_ENTRY = re.compile(r'\["([^"]+)"\]\s*=\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)')
LINE_COMMENT = re.compile(r"//\s*(.+?)\s*$")


def _block(text: str, start: int) -> str:
    """從 dict 宣告處抓到對應 };（淺層，字典內無巢狀 { }）。"""
    end = text.find("};", start)
    return text[start: end if end != -1 else len(text)]


def parse_display_transforms() -> dict:
    keycode, name = {}, {}
    files = list(COMMON_DIR.glob("DisplayTransformService*.cs"))
    for f in files:
        text = read(f)
        for m in DICT_DECL.finditer(text):
            kind, module = m.group(1), m.group(2).upper()
            block = _block(text, m.end())
            for ln in block.splitlines():
                note_m = LINE_COMMENT.search(ln)
                note = note_m.group(1) if note_m else ""
                if kind == "kcMap":
                    e = KC_ENTRY.search(ln)
                    if e:
                        keycode.setdefault(module, {})[e.group(1)] = {
                            "table": e.group(2), "field": e.group(3),
                            "note": note, "file": f.name,
                        }
                else:  # map → name transform（3-tuple）
                    e = NAME_ENTRY.search(ln)
                    if e:
                        name.setdefault(module, {})[e.group(1)] = {
                            "table": e.group(2), "keyField": e.group(3),
                            "nmField": e.group(4), "note": note, "file": f.name,
                        }
    return {"keycode": keycode, "name": name}


# ---- 3. func_reuse：FUNC 公開方法（best-effort）----
PUBLIC_METHOD = re.compile(
    r"public\s+(?:static\s+)?(?:async\s+)?[\w<>,\.\?\[\]\s]+?\s+([A-Za-z_]\w*)\s*\(")
PUBLIC_RECORD = re.compile(r"public\s+record\s+([A-Za-z_]\w*)")


def parse_func_reuse() -> dict:
    out = {}
    for f in sorted(FUNC_DIR.glob("*.cs")):
        text = read(f)
        methods, records = set(), set()
        for m in PUBLIC_METHOD.finditer(text):
            nm = m.group(1)
            if nm and nm[0].isupper():          # 過濾建構式/雜訊，方法多為大駝峰
                methods.add(nm)
        for m in PUBLIC_RECORD.finditer(text):
            records.add(m.group(1))
        # 建構式與類名同名者移除
        cls = f.stem
        methods.discard(cls)
        if methods or records:
            out[f.name] = {
                "methods": sorted(methods),
                "records": sorted(records),
            }
    return out


# ---- 4. existing_pages ----
def parse_existing_pages() -> list:
    if not SAL_PAGES.exists():
        return []
    return sorted(p.stem for p in SAL_PAGES.glob("SAL*.razor"))


def main():
    index = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": "graph-engine/tools/build_index.py",
            "repo_root": str(ROOT),
            "note": "事實地基，供 extract.fact-resolve 查詢；勿手改，重跑本 script 重建。",
        },
        "programs": parse_programs(),
        "display_transforms": parse_display_transforms(),
        "func_reuse": parse_func_reuse(),
        "existing_pages": parse_existing_pages(),
    }
    OUT.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = index["display_transforms"]
    kc = sum(len(v) for v in dt["keycode"].values())
    nm = sum(len(v) for v in dt["name"].values())
    fn = sum(len(v["methods"]) for v in index["func_reuse"].values())
    print(f"[build_index] 輸出 {OUT}")
    print(f"  programs        : {len(index['programs'])}")
    print(f"  keycode maps    : {kc}  (modules: {', '.join(dt['keycode'])})")
    print(f"  name maps       : {nm}  (modules: {', '.join(dt['name'])})")
    print(f"  func methods    : {fn}  (files: {len(index['func_reuse'])})")
    print(f"  existing pages  : {len(index['existing_pages'])}")


if __name__ == "__main__":
    sys.exit(main())
