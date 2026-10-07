# 編排慣例 — 主 session 怎麼「跑這張圖」（Step 6）

> **這是什麼**：graph-engine 沒有程式 runtime——**主 session 就是 orchestrator**，依本檔的慣例讀 spec、跑 node、讀寫 state、依邊路由。
> **前置**：`graph-spec.md`（圖）、`state-schema.md`（狀態）、各 `nodes/*.md`（node 契約）、`tools/*.py`（工具）。
> **狀態存放**：`plans/<code>.md` 的 YAML front-matter（一支程式一份 run state）。

---

## 一次 run 的主迴圈（主 session 照此執行）

```
1. 載入 state（讀 plans/<code>.md front-matter）
   ← 新程式：用 run_state.py init 建初始 state
2. cur = state.stage                      # 目前該做的 node
3. 若 cur ∈ terminal(DONE) → 結束，寫 translation-log 收尾
4. 若 cur = human-review → 進入「人工暫停」流程（見下），停
5. 讀該 node 契約(nodes/*.md)：確認 reads 的 state 欄都齊
   ← 缺 → 回報缺什麼，停（不硬跑）
6. 執行 node：
     kind=pure  → 跑對應 tool（dfm_decode / query_index / verify_static / compile_gate）
     kind=agent → 委派對應 agent（見「node → runner 對應」）
7. 把 node 產出寫回 state.writes 宣告的欄；node status=done/failed；attempts += 1
8. checkpoint：存回 front-matter（斷點就在這，429/中斷都不失）
9. 依 graph-spec 的 edges 求值（見「路由求值」）決定下一個 node → 設 state.stage
10. 回到步驟 2
```

**續跑**：任何時候中斷（429、關機、被打斷）→ 重新載入 state、從 `state.stage` 接著跑。因為每個 node 完成即 checkpoint，最多重做「當前這一個」node。

---

## node → runner 對應（誰來跑每個 node）

| node | kind | runner |
|---|---|---|
| route-mode | agent | 主 session（讀來源判模式，提案）→ 交 human 確認 |
| extract.dfm-decode | pure | `tools/dfm_decode.py`（page-migration） |
| extract.field-cross-check | pure/agent | 依 `details/delphi-reading.md` |
| extract.fact-resolve | agent | `tools/query_index.py`（查表，見 nodes/extract.md） |
| plan | agent | `thinking-planner`（產計畫＋S1–S9 聲明） |
| gen-backend | agent | `migration-executor`（scope=backend） |
| gen-ui.toolbar / grid / detail | agent | `migration-executor`（scope=各片段，只產 fragment 不改檔；detail 於 no_detail 時 skip） |
| gen-ui.editwindow / tabview | agent | `migration-executor`（呈現模式擇一，依 view_mode 只啟動其一） |
| gen-ui.subwindow | agent | `migration-executor`（子視窗有才跑；popup/picker/excel 三型內部序理） |
| fragment-check | agent | 依片段對 page-migration details 檢查 |
| gen-ui.assemble | agent | `migration-executor`（scope=assemble，拼 razor＋一致性 checklist） |
| static-verify | agent | `tools/verify_static.py` ＋ agent 覆核 S2–S8 |
| compile-gate | pure | `tools/compile_gate.py` |
| human-review | human | 主 session 呈報、等使用者裁決 |

> migration-executor 既有 agent 沿用，以 scope 參數區分子職（backend / 片段 / assemble）。

---

## 路由求值（if-else，怎麼決定下一個 node）

1. 取 `graph-spec.edges` 中 `from == cur` 的所有邊，**照檔案順序**逐條看。
2. 用 mini-DSL 對 state 求值（運算子表見 graph-spec.md）：
   - `findings.none` / `.any` / `.any(area~grid)` / `attempts<max` / `and` / `<flag>` / `view_mode==tab-browse-detail`
3. **第一條成立的邊勝出** → 其 `to` 即下一個 node → 寫 `state.stage`。
4. fan-out（`type: fan-out`）：同時啟動多個 to（backend＋三片段可平行）。
5. join（`type: join`）：多個 from 皆 done 才進 to。
6. `attempts>=max` 的邊放最後當保險 → 反覆失敗一律升 human-review。

---

## 人工暫停（human-review）流程

進到 human-review（或 open_questions/open_decisions 非空）時：
1. 主 session **停下**，把三類彙整呈給使用者：
   - `open_questions`（事實不明，如 SAL087 跳號、某 keycode 未註冊）
   - `findings` / `compile_errors` 中的 PLAUSIBLE（需人判）
   - `open_decisions`（如 SAL083 REOP、SAL100 DB 方言）
2. 使用者裁決 → 寫 `state.decisions`，並視情形寫 `skill_diff_candidates`（閉環，Step 7）。
3. 依 human-review 出邊續跑：`decisions.reopen_facts` → 回 extract.fact-resolve；`decisions.accepted` → DONE。

---

## 一個真實 trace（SAL084 續跑示意）

```
載入 state → stage=static-verify, static-verify.attempts=1
執行 verify_static.py SAL084 → findings=[]（PASS）
寫回 findings=[]、static-verify.status=done → checkpoint
求值 edges(from=static-verify)：findings.none 成立 → stage=compile-gate
執行 compile_gate.py build IKSERPUI --files SAL084.razor → compile_errors=[]
求值 edges(from=compile-gate)：compile_errors.none 成立 → stage=human-review
human-review：無 open_*，呈報「全綠」→ 使用者 accept → decisions.accepted → DONE
收尾：translation-log/SAL084.md append 本次結果
```

---

## 小結
本檔把「圖怎麼被人開起來跑」講死：**載入 state → 跑 stage 的 node → 寫回 → 依邊求下一步 → checkpoint → 重複**。中斷從 stage 續跑，失敗依 area 退回，不確定升 human。搭配 `tools/run_state.py` 做機械化的 state 讀寫（見該檔）。
