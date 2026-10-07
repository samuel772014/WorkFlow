#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
golden_check.py — golden set 回歸（graph-engine Step 7，閉環守門）

規則精進後跑這支：對 goldenset.md 每一頁重跑 verify_static，任一 FAIL＝回歸，
擋下該次規則變更（缺口 #6）。也可在 build_index.py 重建後跑，確認 index 改動沒破壞既有頁。

用法（repo 根執行）：
  py .claude/SelfFolder/graph-engine/tools/golden_check.py
  py .claude/SelfFolder/graph-engine/tools/golden_check.py --verbose   # 印出每頁 findings

退出碼：0＝全數 PASS（無回歸）；1＝有回歸（列出 FAIL 頁與 findings）。
"""
import io
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

GRAPH = Path(__file__).resolve().parents[1]
GOLDEN = GRAPH / "golden" / "goldenset.md"
VERIFY = GRAPH / "tools" / "verify_static.py"


def load_codes():
    if not GOLDEN.exists():
        return []
    return re.findall(r"^-\s*(SAL\d+[A-Z]?)\s*$", GOLDEN.read_text(encoding="utf-8"), re.M)


def run_verify(code):
    r = subprocess.run([sys.executable, str(VERIFY), code],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"code": code, "pass": False,
                "findings": [{"summary": "verify_static 輸出無法解析", "verdict": "CONFIRMED"}]}


def main(argv):
    verbose = "--verbose" in argv
    codes = load_codes()
    if not codes:
        print("[golden_check] goldenset.md 無樣本")
        sys.exit(0)
    regressed = []
    print(f"[golden_check] 回歸 {len(codes)} 頁…")
    for c in codes:
        res = run_verify(c)
        ok = res.get("pass")
        print(f"  {'✓' if ok else '✗'} {c}")
        if not ok:
            regressed.append(res)
            if verbose:
                for f in res.get("findings", []):
                    print(f"      - [{f.get('verdict','?')}] {f.get('summary','')}")
    print()
    if regressed:
        print(f"❌ 回歸 {len(regressed)}/{len(codes)} 頁 —— 擋下本次規則/index 變更，先修上列再套用")
        if not verbose:
            print("   （加 --verbose 看 findings）")
        sys.exit(1)
    print(f"✅ golden set 全數 PASS（{len(codes)} 頁）—— 無回歸，規則/index 變更安全")
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
