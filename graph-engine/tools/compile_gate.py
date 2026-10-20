#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compile_gate.py — compile-gate(GATE 2) 的編譯檢查（graph-engine Step 5）

目的：攔生成後的 CS/RZ 型別/Razor 錯，且**不碰 IKSERPUI 工作目錄**（鐵則 6：
hot-reload 會鎖檔，shell build 會噴 MSB3021/3027 假錯）。做法＝在**隔離 git
worktree** 建一份複本、把未提交的產出檔覆蓋進去、在那裡 build，再清掉 worktree。

兩種模式：
  1. build（預設）：實際跑隔離 build
       py compile_gate.py build IKSERPUI --files <razor…>
       py compile_gate.py build IKSERPAPI --changed        # 疊入 git 工作區全部改動（含未追蹤檔）
       py compile_gate.py build IKSERPUI --changed --restore   # 改走線上 restore（需可達 nuget feed）
  2. parse：解析既有 build log（IDE build 後貼出，或 CI 產物），只做錯誤過濾
       py compile_gate.py parse <build.log>

隔離 build 細節：
  - gitignore 的 nuget.config（IKSERPPRJ/nuget.config 等）會一併複製進 worktree。
  - 預設 `--no-restore`：把主 checkout 各專案 obj/ 的還原資產（project.assets.json、*.nuget.g.props/targets、
    project.nuget.cache、*.nuget.dgspec.json）複製進 worktree，套件取自全域 NuGet 快取，不需連內部 feed／Telerik feed。
    目標專案 obj 沒有 project.assets.json（從未在 IDE restore 過）時自動改走線上 restore。
  - dotnet 結束碼非 0 但抽不到 CS/RZ（如 NU1301 feed 不通、NETSDK1004 缺資產）→ 一律判失敗（code 取原錯誤碼，file="-"），
    不再誤判 pass。

輸出：{"pass":bool,"compile_errors":[{file,line,code,msg}],"exit_code":int}
過濾規則：只收 `error CS####` / `error RZ####`；**忽略 MSB3021/3027/3026**（檔案鎖，非編譯錯）。
"""
import io
import json
import os
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
# 非 CS/RZ 的 build 失敗（NU/NETSDK/MSB…），只在結束碼非 0 時採計
OTHER_ERR = re.compile(r":\s*error\s+(?P<code>[A-Z]+\d+):\s*(?P<msg>.+?)\s*(\[[^\]]*\])?\s*$")
# gitignore、但 build/restore 需要的設定檔
IGNORED_BUILD_FILES = ["nuget.config", "IKSERPPRJ/nuget.config",
                       "IKSERPPRJ/IKSERPUI/nuget.config", "IKSERPPRJ/IKSERPAPI/nuget.config"]
RESTORE_ASSETS = ("project.assets.json", ".nuget.g.props", ".nuget.g.targets",
                  "project.nuget.cache", ".nuget.dgspec.json")


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


def other_errors(text: str) -> list:
    """結束碼非 0 但沒有 CS/RZ 時，抽 NU/NETSDK/MSB… 錯誤當失敗原因（去重、濾檔案鎖）。"""
    seen, out = set(), []
    for ln in text.splitlines():
        if IGNORE.search(ln):
            continue
        m = OTHER_ERR.search(ln)
        if not m:
            continue
        key = (m.group("code"), m.group("msg"))
        if key in seen:
            continue
        seen.add(key)
        out.append({"file": "-", "line": 0, "code": m.group("code"), "msg": m.group("msg").strip()})
    return out


def emit(errors, pretty=False, exit_code=None):
    res = {"pass": len(errors) == 0, "compile_errors": errors}
    if exit_code is not None:
        res["exit_code"] = exit_code
    print(json.dumps(res, ensure_ascii=False, indent=2 if pretty else None))


def changed_files() -> list:
    """git 工作區相對 HEAD 的全部改動（修改＋新增未追蹤；刪除檔另行處理）。"""
    mod = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8").stdout.split("\n")
    new = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8").stdout.split("\n")
    return [f for f in mod + new if f.strip()]


def copy_restore_assets(wt: Path) -> None:
    """把主 checkout 各專案 obj/ 的 NuGet 還原資產複製進 worktree（供 --no-restore）。"""
    for p in (ROOT / "IKSERPPRJ").rglob("obj"):
        if not p.is_dir() or "bin" in p.parts:
            continue
        for a in p.iterdir():
            if a.is_file() and a.name.endswith(RESTORE_ASSETS):
                dst = wt / a.relative_to(ROOT)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(a, dst)


def cmd_parse(logpath, pretty):
    p = Path(logpath)
    if not p.exists():
        emit([{"file": "-", "line": 0, "code": "CS0000", "msg": f"log 不存在: {logpath}"}], pretty)
        return
    emit(parse_errors(p.read_text(encoding="utf-8", errors="replace")), pretty)


def cmd_build(project, files, pretty, online_restore=False):
    if project not in PROJECTS:
        emit([{"file": "-", "line": 0, "code": "CS0000",
               "msg": f"未知專案 {project}，可選 {list(PROJECTS)}"}], pretty)
        return
    csproj_rel = PROJECTS[project]
    wt = Path(tempfile.mkdtemp(prefix=f"cgate_{project}_")) / "wt"
    try:
        # 隔離 worktree（detached HEAD，共用 .git 物件庫，快）
        subprocess.run(["git", "worktree", "add", "--detach", str(wt), "HEAD"],
                       cwd=ROOT, check=True, capture_output=True)
        # 覆蓋未提交的產出檔（worktree 取的是 HEAD，故要把工作區改動疊進去）；工作區已刪的檔同步刪
        for f in files or []:
            src = ROOT / f
            dst = wt / f
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            elif dst.exists():
                dst.unlink()
        # gitignore 的 nuget.config（含 feed 與認證）
        for f in IGNORED_BUILD_FILES:
            if (ROOT / f).exists():
                (wt / f).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / f, wt / f)
        # 預設離線：帶主 checkout 的 obj 還原資產跑 --no-restore；目標專案沒有資產才走線上 restore
        assets = ROOT / Path(csproj_rel).parent / "obj" / "project.assets.json"
        no_restore = not online_restore and assets.exists()
        if no_restore:
            copy_restore_assets(wt)
        cmd = ["dotnet", "build", str(wt / csproj_rel), "-c", "Debug", "-v", "q", "-nologo"]
        if no_restore:
            cmd.append("--no-restore")
        # build（隔離目錄，無 hot-reload 鎖）；英文訊息避免 cp950 亂碼
        env = dict(os.environ, DOTNET_CLI_UI_LANGUAGE="en", VSLANG="1033")
        r = subprocess.run(cmd, cwd=wt, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        errors = parse_errors(out)
        if r.returncode != 0 and not errors:
            errors = other_errors(out) or [{"file": "-", "line": 0, "code": "BUILD",
                                            "msg": f"dotnet build 結束碼 {r.returncode}，未抽到錯誤行：{out.strip()[-500:]}"}]
        emit(errors, pretty, r.returncode)
    except FileNotFoundError as e:
        emit([{"file": "-", "line": 0, "code": "CS0000",
               "msg": f"缺工具（dotnet/git?）：{e}"}], pretty)
    except subprocess.CalledProcessError as e:
        emit([{"file": "-", "line": 0, "code": "CS0000",
               "msg": f"worktree 建立失敗：{e.stderr.decode('utf-8','replace') if e.stderr else e}"}], pretty)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)
        shutil.rmtree(wt.parent, ignore_errors=True)


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
        if "--changed" in argv:
            files = list(dict.fromkeys(files + changed_files()))
        cmd_build(project, files, pretty, online_restore="--restore" in argv)
    else:
        emit([{"file": "-", "line": 0, "code": "CS0000", "msg": f"未知模式 {mode}"}], pretty)


if __name__ == "__main__":
    main(sys.argv)
