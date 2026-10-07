#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_state.py — run state 唯讀助手（graph-engine Step 6）

用途：續跑/巡檢時快速回答「現在在哪個 node、各 node 狀態、下一步可走哪些邊」。
**唯讀**（regex 解析，不需 pyyaml、不改檔）；state 的寫入由編排 agent 以 Edit
直接改 plans/<code>.md front-matter（LLM 處理 YAML 文字可靠，見 ORCHESTRATION.md）。

用法（repo 根執行）：
  py .claude/SelfFolder/graph-engine/tools/run_state.py show SAL084
  py .claude/SelfFolder/graph-engine/tools/run_state.py next SAL084
  py .claude/SelfFolder/graph-engine/tools/run_state.py show --file <任意.md>   # 測試用
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
GRAPH = Path(__file__).resolve().parents[1]
PLANS = ROOT / ".claude" / "SelfFolder" / "plans"
SPEC = GRAPH / "graph-spec.md"


def state_path(argv):
    if "--file" in argv:
        return Path(argv[argv.index("--file") + 1])
    code = argv[2].upper()
    return PLANS / f"{code}.md"


def front_matter(text: str) -> str:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    return m.group(1) if m else text


def cmd_show(path: Path):
    if not path.exists():
        print(f"[run_state] 找不到 {path}（新程式請由編排 agent 依 state-schema 建 front-matter）")
        return
    fm = front_matter(path.read_text(encoding="utf-8", errors="replace"))
    code = re.search(r"^code:\s*(\S+)", fm, re.M)
    stage = re.search(r"^stage:\s*(\S+)", fm, re.M)
    print(f"程式 : {code.group(1) if code else '?'}")
    print(f"stage: {stage.group(1) if stage else '?'}   ← 續跑從這裡接")
    print("nodes:")
    # 抓 nodes: 區塊內每行  <id>: {status: X, attempts: N}
    block = re.search(r"^nodes:\s*\n(.*?)(?=^\w|\Z)", fm, re.S | re.M)
    if block:
        for ln in block.group(1).splitlines():
            e = re.search(r"^\s+([\w.\-]+):\s*\{status:\s*(\w+),\s*attempts:\s*(\d+)", ln)
            if e:
                mark = {"done": "✓", "failed": "✗", "running": "▶",
                        "pending": "·", "blocked": "!", "skipped": "-"}.get(e.group(2), "?")
                print(f"  {mark} {e.group(1):<28} {e.group(2)} (attempts={e.group(3)})")
    # 待決摘要
    for ch in ("open_questions", "open_decisions"):
        m = re.search(rf"^{ch}:\s*(.+)$", fm, re.M)
        if m and m.group(1).strip() not in ("[]", ""):
            print(f"⚠ {ch}: {m.group(1).strip()}")


def cmd_next(argv):
    code = argv[2].upper()
    path = state_path(argv)
    stage = "?"
    if path.exists():
        st = re.search(r"^stage:\s*(\S+)", front_matter(path.read_text(encoding="utf-8", errors="replace")), re.M)
        stage = st.group(1) if st else "?"
    spec = SPEC.read_text(encoding="utf-8", errors="replace")
    print(f"{code} 目前 stage = {stage}；由此出發的邊（第一條成立者勝）：")
    found = False
    # from / to 都可能是 list 形式 [a, b, c]（fan-out / join）；用 (\[[^\]]*\]|[^,}]+) 完整吃下再拆。
    edge_re = re.compile(
        r"-\s*\{from:\s*(\[[^\]]*\]|[^,]+),\s*to:\s*(\[[^\]]*\]|[^,}]+)"
        r"(?:,\s*(?:when|type):\s*([^}]+))?\}"
    )
    for ln in spec.splitlines():
        e = edge_re.search(ln)
        if not e:
            continue
        frm_list = [x.strip() for x in e.group(1).strip().strip("[]").split(",") if x.strip()]
        if stage in frm_list:
            to_raw = e.group(2).strip()
            to_disp = " ∥ ".join(x.strip() for x in to_raw.strip("[]").split(",")) if to_raw.startswith("[") else to_raw
            cond = (e.group(3) or "（無條件）").strip()
            print(f"  → {to_disp:<40} when {cond}")
            found = True
    if not found:
        print("  （spec 無此 stage 的出邊，或 stage=DONE/human-review）")


def main(argv):
    if len(argv) < 3:
        print("用法: run_state.py <show|next> <SALxxx> | show --file <path>")
        sys.exit(2)
    cmd = argv[1]
    if cmd == "show":
        cmd_show(state_path(argv))
    elif cmd == "next":
        cmd_next(argv)
    else:
        print(f"未知指令 {cmd}")


if __name__ == "__main__":
    main(sys.argv)
