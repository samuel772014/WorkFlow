#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_static.py — static-verify(GATE 1) 的機器判子集（graph-engine Step 4）

給一支 SAL razor，機械化檢查「可重複性 bug」四類，回結構化 findings（JSON）。
這是 static-verify node 內部的『可腳本層』；需判斷/人眼的 S 項由 agent 依
acceptance-criteria.md 覆核（見 nodes/static-verify.md）。

檢查（對應本輪四類 bug）：
  C1 route/title       @page 路由 + <PageTitle> 含代號         （acceptance S1）
  C2 title-name        標題名稱 = 對照表正式名（非研判/ dfm caption）（S9）
  C3 xform-registered  razor 的 DisplayTransform(KeyCode) 屬性，其 KEY 在 index 有註冊
                       （找不到→跨模組查，建議正確模組；⚠同名≠同義，只建議不斷定）
  C4 display-wired     grid 綁 *_Display 欄，必有對應 *_Display 屬性且掛 transform
                       （運算式計算屬性 `=> ... switch` 視為已接，不誤報）

用法（repo 根執行）：
  py .claude/SelfFolder/graph-engine/tools/verify_static.py SAL084
  py .claude/SelfFolder/graph-engine/tools/verify_static.py SAL084 --pretty
輸出：{"code","pass":bool,"findings":[{category,verdict,area,line,summary}]}
verdict: CONFIRMED(機器可確定) | PLAUSIBLE(需人覆核)
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

ROOT = Path(__file__).resolve().parents[4]
INDEX = Path(__file__).resolve().parents[1] / "index.json"
PAGES = ROOT / "IKSERPPRJ" / "IKSERPUI" / "Components" / "Pages" / "SAL"


def norm(s: str) -> str:
    # 名稱比對：去空白與全/半形括號差異
    return re.sub(r"[\s（）()]", "", s or "")


def lineno(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def main(argv):
    if len(argv) < 2:
        print(json.dumps({"error": "用法: verify_static.py <SALxxx> [--pretty]"}, ensure_ascii=False))
        sys.exit(2)
    code = argv[1].upper()
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    razor = PAGES / f"{code}.razor"
    if not razor.exists():
        print(json.dumps({"code": code, "pass": False,
                          "findings": [{"category": "missing-file", "verdict": "CONFIRMED",
                                        "area": "-", "line": 0,
                                        "summary": f"{code}.razor 不存在"}]}, ensure_ascii=False))
        sys.exit(0)
    text = razor.read_text(encoding="utf-8", errors="replace")
    findings = []

    prog = next((p for p in idx["programs"] if p["sal"].upper() == code), None)
    kc = idx["display_transforms"]["keycode"]
    nm = idx["display_transforms"]["name"]

    # ---- C1 route/title ----
    if not re.search(rf'@page\s+"/SAL/{code}"', text, re.I):
        findings.append({"category": "route", "verdict": "CONFIRMED", "area": "shell", "line": 1,
                         "summary": f'缺 @page "/SAL/{code}" 路由'})
    pt = re.search(r"<PageTitle>(.*?)</PageTitle>", text, re.S)
    if not pt:
        findings.append({"category": "title", "verdict": "CONFIRMED", "area": "shell", "line": 1,
                         "summary": "缺 <PageTitle>"})
    elif code not in pt.group(1).upper():
        findings.append({"category": "title", "verdict": "CONFIRMED", "area": "shell",
                         "line": lineno(text, pt.start()),
                         "summary": f"PageTitle 未含代號 {code}"})

    # ---- C2 title-name = 對照表正式名 ----
    if pt and prog:
        title_txt = re.sub(r"\(?SAL\d+[A-Z]?\)?", "", pt.group(1))
        if prog["name"] and norm(prog["name"]) not in norm(title_txt):
            findings.append({"category": "title-name", "verdict": "PLAUSIBLE", "area": "shell",
                             "line": lineno(text, pt.start()),
                             "summary": f'標題「{title_txt.strip()}」≠ 對照表正式名「{prog["name"]}」（研判名/舊名?）'})

    # ---- C3 DisplayTransform 屬性的 KEY 需在 index 註冊（找不到→跨模組查，建議正確模組）----
    def find_elsewhere(key):
        """跨所有模組找同名 KEY 的註冊處，回 ['keycode@STK(table=PP_RCVM)', …]。"""
        hits = []
        for mod2, tbl in kc.items():
            if key in tbl:
                hits.append(f"keycode@{mod2}(table={tbl[key].get('table', '?')})")
        for mod2, tbl in nm.items():
            if key in tbl:
                hits.append(f"name@{mod2}(table={tbl[key].get('table', '?')})")
        return hits

    for m in re.finditer(r'\[DisplayTransform(KeyCode)?\("([^"]+)"\s*,\s*"([^"]+)"', text):
        is_kc, key, mod = bool(m.group(1)), m.group(2), m.group(3).upper()
        table = kc if is_kc else nm
        if mod != "COMMON" and key not in table.get(mod, {}):
            kind = "keycode" if is_kc else "name"
            elsewhere = find_elsewhere(key)
            # ⚠️ 同名≠同義：別模組同名 KEY 常是不同 table（不同語意），故只「建議」不「斷定換模組」
            hint = (f"；同名註冊於 {', '.join(elsewhere)}（⚠同名≠同義，須比對 table 是否同欄；"
                    f"多為應在 {mod} 補註冊、非換模組）") if elsewhere else "（各模組皆無 → 需補註冊或確認 KEY）"
            findings.append({"category": "xform-unregistered", "verdict": "CONFIRMED", "area": "dto",
                             "line": lineno(text, m.start()),
                             "summary": f'{kind} 屬性 "{key}"({mod}) 在 index 未註冊 → 會顯示原碼/查無{hint}'})

    # ---- C4 grid 綁 *_Display 欄，須有對應屬性（auto+transform 或 運算式計算屬性）----
    prop_auto = set(re.findall(r'public\s+string\??\s+(\w+_Display)\s*\{', text))          # auto-property（需掛 transform）
    prop_computed = set(re.findall(r'public\s+string\??\s+(\w+_Display)\s*=>', text))       # 運算式計算屬性（自算顯示，免 transform）
    attr_display = set(re.findall(r'\]\s*public\s+string\??\s+(\w+_Display)\s*\{', text))    # 前面帶 [屬性] 者
    for gm in re.finditer(r'Field\s*=\s*"(\w+_Display)"', text):
        fld = gm.group(1)
        if fld in prop_computed:
            continue                                                # 計算屬性已自行產生顯示，視為已接（避免 SAL074 TP_Display 誤報）
        if fld not in prop_auto:
            findings.append({"category": "display-wired", "verdict": "CONFIRMED", "area": "grid",
                             "line": lineno(text, gm.start()),
                             "summary": f'grid 綁 {fld} 但無對應 DTO 屬性（auto 或計算屬性）'})
        elif fld not in attr_display:
            findings.append({"category": "display-wired", "verdict": "PLAUSIBLE", "area": "grid",
                             "line": lineno(text, gm.start()),
                             "summary": f'{fld} 屬性未掛 [DisplayTransform*]，恐顯示空/原碼'})

    result = {"code": code, "pass": len(findings) == 0, "findings": findings}
    indent = 2 if "--pretty" in argv else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main(sys.argv)
