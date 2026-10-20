#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
func_status_scan.py — 依程式碼重掃 `共用函式對照表.md` 的 ✅/🚧 狀態

用途：對照表的狀態欄靠人工維護、會過時（如 CalcMasterMnyAsync 已實作仍標 🚧）。
本工具逐列取「C# 方法名」，到該段標題指定的 `Modules/FUNC/<檔>.cs` 找方法定義：
  - 找到定義且方法本體不含 NotImplementedException → 應為 ✅
  - 找不到定義，或本體 throw NotImplementedException  → 應為 🚧
只處理狀態為 ✅ / 🚧 的列；🔄 ➡️ ❌ 屬人工判斷，不動。
另檢查段標題的 .cs 檔是否存在（檔名寫錯會列出）。

用法（repo 根執行）：
  py .claude/SelfFolder/graph-engine/tools/func_status_scan.py            # 只列差異（dry-run）
  py .claude/SelfFolder/graph-engine/tools/func_status_scan.py --apply    # 寫回對照表
"""
import io
import re
import sys
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[4]
TABLE = ROOT / ".claude" / "SelfFolder" / "共用函式對照表.md"
FUNC_DIR = ROOT / "IKSERPPRJ" / "IKSERPAPI" / "Modules" / "FUNC"

SECTION = re.compile(r"^##\s+\S+\s*→\s*`([^`]+\.cs)`")
ROW = re.compile(r"^\|\s*`[^`]+`[^|]*\|\s*`([A-Za-z_]\w*)`\s*\|\s*(✅|🚧)\s*\|")


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def method_status(src: str, name: str):
    """回傳 'done' / 'stub' / 'missing'。"""
    m = re.search(r"\b(public|internal|private|protected)\b[^;{=]*?\b" + re.escape(name) + r"\s*(<[^>]*>)?\s*\(", src)
    if not m:
        return "missing"
    i = src.find("{", m.end())
    arrow = src.find("=>", m.end())
    if arrow != -1 and (i == -1 or arrow < i):
        body = src[arrow: src.find(";", arrow) + 1]
    else:
        depth, j = 0, i
        while j < len(src):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = src[i: j + 1]
    return "stub" if "NotImplementedException" in body else "done"


def main(argv):
    apply = "--apply" in argv
    lines = TABLE.read_text(encoding="utf-8").splitlines()
    cache, cur_file, changes, missing_files = {}, None, [], set()
    for idx, line in enumerate(lines):
        sm = SECTION.match(line)
        if sm:
            cur_file = sm.group(1)
            if cur_file not in cache:
                p = FUNC_DIR / cur_file
                if p.exists():
                    cache[cur_file] = strip_comments(p.read_text(encoding="utf-8-sig"))
                else:
                    cache[cur_file] = None
                    missing_files.add(cur_file)
            continue
        rm = ROW.match(line)
        if not rm or not cur_file or cache.get(cur_file) is None:
            continue
        name, mark = rm.group(1), rm.group(2)
        st = method_status(cache[cur_file], name)
        want = "✅" if st == "done" else "🚧"
        if want != mark:
            changes.append((idx + 1, cur_file, name, mark, want, st))
            if apply:
                lines[idx] = line.replace(f"| {mark} |", f"| {want} |", 1)

    for f in sorted(missing_files):
        print(f"[檔案不存在] 段標題指向 {f}，Modules/FUNC 找不到（請人工更正檔名）")
    for ln, f, n, a, b, st in changes:
        print(f"L{ln} {f} {n}: {a} → {b}（{st}）")
    print(f"共 {len(changes)} 列狀態需更新" + ("，已寫回" if apply and changes else ""))
    if apply and changes:
        TABLE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
