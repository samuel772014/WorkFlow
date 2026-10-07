#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compile_gate.py — compile-gate(GATE 2) 的編譯檢查（graph-engine Step 5）

目的：攔生成後的 CS/RZ 型別/Razor 錯，且**不碰 IKSERPUI 工作目錄**（鐵則 6：
hot-reload 會鎖檔，shell build 會噴 MSB3021/3027 假錯）。做法＝在**隔離 git
worktree** 建一份複本、把未提交的產出檔覆蓋進去、在那裡 build，再清掉 worktree。

兩種模式：
  1. build（預設）：實際跑隔離 build（需 dotnet + 可達 nuget feed）
       py compile_gate.py build IKSERPUI --files <razor…>
  2. parse：解析既有 build log（IDE build 後貼出，或 CI 產物），只做錯誤過濾
       py compile_gate.py parse <build.log>

輸出：{"pass":bool,"compile_errors":[{file,line,code,msg}]}
過濾規則：只收 `error CS####` / `error RZ####`；**忽略 MSB3021/3027/3026**（檔案鎖，非編譯錯）。
"""
import io
import json
import re
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[4]
PROJECTS = {
    "IKSERPUI":  "IKSERPPRJ/IKSERPUI/IKSERPUI.csproj",
    "IKSERPAPI": "IKSERPPRJ/IKSERPAPI/IKSERPAPI.csproj",
}
IGNORE = re.compile(r"MSB302[167]")           # 檔案鎖假錯，忽略
ERR = re.compile(
    r"(?P<file>[^\(\n]+?)\((?P<line>\d+),\d+\):\s*error\s+(?P<code>(CS|RZ)\d+):\s*(?P<msg>.+?)\s*$")


def parse_errors(text: str) -> list:
    """從 build 輸出抽 CS/RZ 錯誤，去重、濾掉檔案鎖。"""
    seen, out = set(), []
    for ln in text.splitlines():
        if IGNORE.search(ln):
            continue
        m = ERR.search(ln)
        if not m:
            continue
        key = (m.group("file"), m.group("line"), m.group("code"))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "file": Path(m.group("file").strip()).name,
            "line": int(m.group("line")),
            "code": m.group("code"),
            "msg": m.group("msg").strip(),
        })
    return out


def emit(errors, pretty=False):
    print(json.dumps({"pass": len(errors) == 0, "compile_errors": errors},
                     ensure_ascii=False, indent=2 if pretty else None))


def cmd_parse(logpath, pretty):
    p = Path(logpath)
    if not p.exists():
        emit([{"file": "-", "line": 0, "code": "CS0000", "msg": f"log 不存在: {logpath}"}], pretty)
        return
    emit(parse_errors(p.read_text(encoding="utf-8", errors="replace")), pretty)


def cmd_build(project, files, pretty):
    if project not in PROJECTS:
        emit([{"file": "-", "line": 0, "code": "CS0000",
               "msg": f"未知專案 {project}，可選 {list(PROJECTS)}"}], pretty)
        return
    csproj_rel = PROJECTS[project]
    wt = Path(tempfile.mkdtemp(prefix=f"cgate_{project}_"))
    try:
        # 隔離 worktree（detached HEAD，共用 .git 物件庫，快）
        subprocess.run(["git", "worktree", "add", "--detach", str(wt), "HEAD"],
                       cwd=ROOT, check=True, capture_output=True)
        # 覆蓋未提交的產出檔（worktree 取的是 HEAD，故要把工作區改動疊進去）
        for f in files or []:
            src = ROOT / f
            dst = wt / f
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        # build（隔離目錄，無 hot-reload 鎖）
        r = subprocess.run(
            ["dotnet", "build", str(wt / csproj_rel), "-c", "Debug", "-v", "q", "-nologo"],
            cwd=wt, capture_output=True, text=True, encoding="utf-8", errors="replace")
        emit(parse_errors((r.stdout or "") + "\n" + (r.stderr or "")), pretty)
    except FileNotFoundError as e:
        emit([{"file": "-", "line": 0, "code": "CS0000",
               "msg": f"缺工具（dotnet/git?）：{e}"}], pretty)
    except subprocess.CalledProcessError as e:
        emit([{"file": "-", "line": 0, "code": "CS0000",
               "msg": f"worktree 建立失敗：{e.stderr.decode('utf-8','replace') if e.stderr else e}"}], pretty)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)


def main(argv):
    if len(argv) < 2:
        emit([{"file": "-", "line": 0, "code": "CS0000",
               "msg": "用法: compile_gate.py <build|parse> ..."}], "--pretty" in argv)
        sys.exit(2)
    pretty = "--pretty" in argv
    mode = argv[1]
    if mode == "parse":
        cmd_parse(argv[2], pretty)
    elif mode == "build":
        project = argv[2] if len(argv) > 2 else "IKSERPUI"
        files = []
        if "--files" in argv:
            files = [a for a in argv[argv.index("--files") + 1:] if not a.startswith("--")]
        cmd_build(project, files, pretty)
    else:
        emit([{"file": "-", "line": 0, "code": "CS0000", "msg": f"未知模式 {mode}"}], pretty)


if __name__ == "__main__":
    main(sys.argv)
