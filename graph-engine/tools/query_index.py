#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
query_index.py — 查知識圖譜 index.json（graph-engine Step 3）

extract.fact-resolve node 用它「查事實」而非推測（鐵則 4）。
每個查詢固定回 JSON：命中回事實、查無回 {"found": false, ...}，
fact-resolve 依 found=false 寫進 state.open_questions → 條件邊轉 human（不猜）。

用法（repo 根執行）：
  py .claude/SelfFolder/graph-engine/tools/query_index.py prog SAL097
  py .claude/SelfFolder/graph-engine/tools/query_index.py prog B905
  py .claude/SelfFolder/graph-engine/tools/query_index.py keycode SAL CLAS
  py .claude/SelfFolder/graph-engine/tools/query_index.py name SAL SALETP
  py .claude/SelfFolder/graph-engine/tools/query_index.py func GetMRate
  py .claude/SelfFolder/graph-engine/tools/query_index.py page SAL087
  py .claude/SelfFolder/graph-engine/tools/query_index.py resolve SAL097   # 一次取該頁所有基本事實
輸出一律 UTF-8 JSON（避開 Windows cp950 亂碼）。
"""
import io
import json
import sys
from pathlib import Path

# 讓 stdout 走 UTF-8，Windows 終端才不亂碼
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

INDEX = Path(__file__).resolve().parents[1] / "index.json"


def load():
    if not INDEX.exists():
        die(f"index.json 不存在：{INDEX}；先跑 build_index.py")
    return json.loads(INDEX.read_text(encoding="utf-8"))


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg):
    out({"error": msg})
    sys.exit(2)


def q_prog(idx, key):
    key = key.upper()
    for p in idx["programs"]:
        if p["sal"].upper() == key or p["b_code"].upper() == key:
            return {"found": True, **p}
    return {"found": False, "query": key,
            "hint": "不在 SAL程式編號對照表 → 可能跳號/未指派，不可自行推測 B 代碼或功能名"}


def q_keycode(idx, module, key):
    m = idx["display_transforms"]["keycode"].get(module.upper(), {})
    e = m.get(key)
    if e:
        return {"found": True, "module": module.upper(), "key": key, **e}
    return {"found": False, "module": module.upper(), "key": key,
            "hint": "keycode 未註冊 → 顯示會是原碼；需在 _kcMap* 補註冊，勿直接輸出原碼當名稱"}


def q_name(idx, module, key):
    m = idx["display_transforms"]["name"].get(module.upper(), {})
    e = m.get(key)
    if e:
        return {"found": True, "module": module.upper(), "key": key, **e}
    return {"found": False, "module": module.upper(), "key": key,
            "hint": "name 映射未註冊 → 需在 _map* 補註冊或確認來源表/欄"}


def q_func(idx, substr):
    s = substr.lower()
    hits = []
    for fname, info in idx["func_reuse"].items():
        for m in info.get("methods", []):
            if s in m.lower():
                hits.append({"file": fname, "method": m})
    return {"found": bool(hits), "query": substr, "matches": hits,
            "hint": "命中 → 勿重寫，重用既有函式（reuse_func_modules）" if hits
                    else "查無同名 → 確認真的沒有再新建"}


def q_page(idx, sal):
    exists = sal.upper() in [p.upper() for p in idx["existing_pages"]]
    return {"found": exists, "sal": sal.upper(), "page_exists": exists}


def q_resolve(idx, sal):
    """fact-resolve 一次取該頁基本事實（程式身分 + 是否已存在）。"""
    prog = q_prog(idx, sal)
    page = q_page(idx, sal)
    open_q = []
    if not prog["found"]:
        open_q.append(f"{sal} 不在對照表：功能名/B代碼未知，需人工確認（勿推測）")
    return {"sal": sal.upper(), "program": prog, "page": page, "open_questions": open_q}


def main(argv):
    if len(argv) < 2:
        die("用法：query_index.py <prog|keycode|name|func|page|resolve> args...")
    idx = load()
    cmd = argv[1]
    a = argv[2:]
    try:
        if cmd == "prog":     out(q_prog(idx, a[0]))
        elif cmd == "keycode":out(q_keycode(idx, a[0], a[1]))
        elif cmd == "name":   out(q_name(idx, a[0], a[1]))
        elif cmd == "func":   out(q_func(idx, a[0]))
        elif cmd == "page":   out(q_page(idx, a[0]))
        elif cmd == "resolve":out(q_resolve(idx, a[0]))
        else: die(f"未知指令：{cmd}")
    except IndexError:
        die(f"指令 {cmd} 參數不足")


if __name__ == "__main__":
    main(sys.argv)
