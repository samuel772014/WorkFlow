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
  C5 css-class-defined razor 用到的 iks-* class 必須在 IKSERPUI 的 *.css 有定義
                       （擋「自創 class」：如 SAL074-076 iks-single-frame 無定義 → grid 無 Y 捲軸）
  C6 combobox-module   <IksCodeComboBox> 的 comboBoxCode 必須登記在所傳 module 的
                       ComboBoxService _handlers<MODULE>（擋 SAL073 ShpidComboBox 傳 SAL 實為 COMMON → 下拉無資料）
  C7 textbox           自閉合 <TelerikTextBox .../> 應改 IksTextBox（帶 SuffixTemplate 例外）   （CNV-03）
  C8 hardcoded-emply   寫死 "00001" 當登入者，應用 EmplyId                                        （CNV-05）
  C9 status-check      status == 0 / > 0 判成敗，成功一律 status == 1（PLAUSIBLE）                （CNV-07）
  C10 hardcoded-url    string _url = "…" 寫死，應用 IksPageBase 提供值                             （CNV-08）
  C11 deprecated       OnBeforeEdit、整表鎖欄樣板、JsonConverter(NewtonsoftDecimalToIntConverter)  （CNV-10）
  C12 loading-msgbox   遮罩內 await MsgBox／遮罩未解除（呼叫 review-engine/tools/lint_loading.py）  （CNV-13）

用法（repo 根執行）：
  py .claude/SelfFolder/graph-engine/tools/verify_static.py SAL084
  py .claude/SelfFolder/graph-engine/tools/verify_static.py SAL084 --pretty
輸出：{"code","pass":bool,"findings":[{category,verdict,area,line,summary}]}
verdict: CONFIRMED(機器可確定) | PLAUSIBLE(需人覆核)
"""
import importlib.util
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
UI_ROOT = ROOT / "IKSERPPRJ" / "IKSERPUI"
COMBO_DIR = ROOT / "IKSERPPRJ" / "IKSERPAPI" / "Modules" / "COMMON"


def css_defined_classes() -> set:
    """IKSERPUI 下所有自有 *.css（排除 bin/obj/lib）中定義的 iks-* class。"""
    out = set()
    for f in UI_ROOT.rglob("*.css"):
        if any(p in ("bin", "obj", "lib") for p in f.parts):
            continue
        out |= set(re.findall(r"\.(iks-[\w-]+)", f.read_text(encoding="utf-8", errors="replace")))
    return out


def combobox_registry() -> dict:
    """解析 ComboBoxService*.cs 的 _handlers<MODULE> 字典 → {MODULE: {code,...}}。"""
    reg = {}
    for f in COMBO_DIR.glob("ComboBoxService*.cs"):
        src = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"_handlers(\w+)\s*=\s*new\(\)\s*\{(.*?)\n\s*\};", src, re.S):
            reg.setdefault(m.group(1).upper(), set()).update(
                re.findall(r'^\s*\["(\w+)"\]\s*=', m.group(2), re.M))
    return reg


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

    # ---- C5 iks-* class 必須在 css 有定義（擋自創 class）----
    defined = css_defined_classes()
    seen = set()
    for cm in re.finditer(r'\b[cC]lass\s*=\s*"([^"]*)"', text):
        for cls in re.findall(r"\biks-[\w-]+", cm.group(1)):
            if cls in defined or cls in seen:
                continue
            seen.add(cls)
            findings.append({"category": "css-class-undefined", "verdict": "CONFIRMED", "area": "layout",
                             "line": lineno(text, cm.start()),
                             "summary": f'class "{cls}" 在 IKSERPUI *.css 無定義（自創 class？版面不會生效'
                                        + ('；單一清單頁外框應用 iks-master-frame > iks-master-grid' if 'frame' in cls else '')
                                        + '）'})

    # ---- C6 IksCodeComboBox 的 comboBoxCode 必須登記在所傳 module ----
    reg = combobox_registry()
    for tm in re.finditer(r"<IksCodeComboBox\b(.*?)/>", text, re.S):
        attrs = tm.group(1)
        cm_ = re.search(r'comboBoxCode\s*=\s*"(\w+)"', attrs)
        mm_ = re.search(r'\bmodule\s*=\s*"(\w+)"', attrs)
        if not cm_:
            continue                                                # 動態 code（@變數）略過
        ccode = cm_.group(1)
        if not mm_:
            findings.append({"category": "combobox-module", "verdict": "PLAUSIBLE", "area": "input",
                             "line": lineno(text, tm.start()),
                             "summary": f'IksCodeComboBox {ccode} 未傳 module（必傳路由）'})
            continue
        mod = mm_.group(1).upper()
        if ccode in reg.get(mod, set()):
            continue
        where = [m for m, codes in reg.items() if ccode in codes]
        hint = f"；實際登記於 {', '.join(where)} → 改 module=\"{where[0]}\"" if where else "；各模組皆未登記 → 需補 ComboBoxService"
        findings.append({"category": "combobox-module", "verdict": "CONFIRMED", "area": "input",
                         "line": lineno(text, tm.start()),
                         "summary": f'comboBoxCode "{ccode}" 未登記在 module="{mm_.group(1)}"（下拉會無資料）{hint}'})

    # ---- C7–C11 跨區通用慣例（review-conventions 可機械判的子集）----
    conv_rules = [
        ("textbox", "CONFIRMED", "input",
         r"<TelerikTextBox\b(?:(?!SuffixTemplate)[^>])*/>", "自閉合 TelerikTextBox → 改用 IksTextBox"),
        ("hardcoded-emply", "CONFIRMED", "shell",
         r'"00001"', '寫死 "00001" 當登入者 → 用 EmplyId（OnInitializedAsync await base 之後）'),
        ("status-check", "PLAUSIBLE", "logic",
         r"\bstatus\s*(?:==\s*0|>\s*0)\b", "以 status == 0 / > 0 判成敗 → 成功一律 status == 1（2 需確認、3 部分成功）"),
        ("hardcoded-url", "CONFIRMED", "shell",
         r'string\s+_url\s*=\s*"', "寫死 _url → 用 IksPageBase 提供值"),
        ("deprecated", "CONFIRMED", "grid",
         r"\b(?:OnBeforeEdit|LockDqGridColumns|UnlockDqGridColumns|ApplyDqLock|SetDqColumnsLocked)\b",
         "已淘汰寫法（OnBeforeEdit／整表鎖欄樣板）→ 全域閘門 EnterEdit/ExitEdit＋靜態 Editable=false"),
        ("deprecated", "CONFIRMED", "dto",
         r"JsonConverter\s*\(\s*typeof\s*\(\s*NewtonsoftDecimalToIntConverter",
         "已淘汰 [JsonProperty]＋Converter 的 _Int → get/set 包裝 base（dto-display.md）"),
    ]
    for cat, verdict, area, pat, msg in conv_rules:
        for m in re.finditer(pat, text):
            findings.append({"category": cat, "verdict": verdict, "area": area,
                             "line": lineno(text, m.start()), "summary": msg})

    # ---- C12 遮罩內 await 訊息框／遮罩未解除（重用 lint_loading.scan）----
    lint_path = Path(__file__).resolve().parents[2] / "review-engine" / "tools" / "lint_loading.py"
    if lint_path.exists():
        spec = importlib.util.spec_from_file_location("lint_loading", lint_path)
        lint = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint)
        for ln, kind, src in lint.scan(razor):
            findings.append({"category": kind, "verdict": "CONFIRMED", "area": "shell", "line": ln,
                             "summary": f"{kind}：{src[:80]}（遮罩蓋住訊息框→畫面卡死；見 page-shell.md）"})

    result = {"code": code, "pass": len(findings) == 0, "findings": findings}
    indent = 2 if "--pretty" in argv else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main(sys.argv)
