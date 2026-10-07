# Graph Spec — Delphi→C# 單頁遷移工作流

> **這是什麼**：整張遷移圖的宣告式定義（nodes / edges / entrypoint / 條件路由 / 終止）。
> **載體**：每個 `kind: agent` 的 node 對應一支 `.claude` agent（或 migration-executor 帶參數）；主 session 依本檔編排。
> **規則不在此檔**——一律用 `rules_ref` 指回 `page-migration` skill；本檔只管「流程長怎樣」。
> **格式**：外層 md（給人讀的說明）＋下方 ```yaml 區塊（給 agent／未來程式讀的結構）。

---

## 圖總覽

```
route-mode
 → extract.dfm-decode → extract.field-cross-check → extract.fact-resolve
 → plan               (生成第一步：讀 pas+dfm 產骨架藍圖 skeleton，分層/分頁/分功能)
 → fan-out:           (plan 跑完、骨架就緒才展開)
      ├─ gen-backend                              (第二步/後端：照 skeleton 產 Repository/Service/Resolver 三檔)
      ├─ 組合類全跑: gen-ui.toolbar ∥ gen-ui.grid ∥ gen-ui.detail?   (照 skeleton.fragments 各產片段，不改檔；detail 有明細才跑)
      ├─ 呈現模式擇一(依 view_mode): editwindow | tabview | (incell→無)   (互斥，只啟動其一)
      └─ 子視窗(有才跑): gen-ui.subwindow   (skeleton.pages.subwindows 非空時；多個內部序理)
             → fragment-check   (GATE 0：片段先過一次 skill 檢查)
             → gen-ui.assemble  (reduce：把片段拼成 SAL0XX.razor)
 → static-verify   (GATE 1：整體 S1–S9)
 → compile-gate    (GATE 2：隔離 worktree build)
 → human-review    (GATE 3 + interrupt：park/待決/範本確認/候選 skill diff)
 → DONE
```

**兩層檢查（依你的決定）**
- **GATE 0 `fragment-check`**：toolbar/grid/detail 及（依 view_mode 啟動的）editwindow|tabview 各自產出片段後，**先各自對 page-migration skill 檢查一次**；某片段不過只重跑該片段 node（targeted retry），不影響其他。
- **GATE 1 `static-verify`**：片段 assemble 成完整 razor 後，**再做整體 S1–S9**（跨片段一致性、與 backend 的對應）。

**設計要點**
- 萃取切細（純／可快取／擋推測）；UI 生成採 **map→reduce**（區塊平行產片段 → assemble 合併）；驗證分片段層與整體層兩關。
- 「禁推測」化成流程：`fact-resolve` 查不到事實 → 寫 `open_questions` → 條件邊去 `human-review`，不讓 agent 猜。
- 失敗不新增 node：檢查結果寫進 `findings`，**由 edge 依 findings 路由回既有 gen node**；修不好（attempts≥max）才升 `human-review`。

---

## Node 一覽（人讀）

| id | kind | 職責 | 對應現有資產 |
|---|---|---|---|
| `route-mode` | agent | 判範本模式，提案＋理由 | SKILL.md 步驟1 |
| `extract.dfm-decode` | pure | DFM 解碼：欄位/欄序/寬/標題 | `tools/dfm_decode.py` |
| `extract.field-cross-check` | pure | dfm × SQL × gettext 三方交叉 | `details/delphi-reading.md` |
| `extract.fact-resolve` | agent | 查知識圖譜：名稱/keycode/name-map/FUNC | Step 2 的 `index.json` |
| `plan` | agent | **生成第一步**：讀 pas+dfm 產骨架藍圖(分層/分頁/分功能)＋S1–S9 聲明 | `thinking-planner` |
| `gen-backend` | agent | **第二步**：照 skeleton 產 Repository/Service/Resolver（三檔獨立，免拼裝） | executor（後端子職） |
| `gen-ui.toolbar` | agent | 工具列 ribbon + 按鈕權限片段 | `details/toolbar.md`、`btn-control.md` |
| `gen-ui.grid` | agent | 主 grid：filter 區 + 欄位 + InCell + 主表 DTO（非 tab 模式） | `details/grid-virtual.md` |
| `gen-ui.detail` | agent | 明細 grid + InCell + 明細 DTO（多組內部處理；無明細則不啟動） | `details/grid-incell.md` |
| `gen-ui.editwindow` | agent | **模式擇一**：TelerikWindow 單筆編輯（讀 grid 的 DTO） | `details/edit-window.md` |
| `gen-ui.tabview` | agent | **模式擇一**：瀏覽↔明細資料分頁（本模式統一宣告主表 DTO） | `details/editor-template.md` |
| `gen-ui.subwindow` | agent | **有才跑**：彈出子視窗/子元件（多個內部序理；如 SAL046 Dq4備註窗/Excel匯入窗、SAL0XXA/B/D） | `popup-window`／`multiselect-picker`／`templates/excel-import.md` |
| `fragment-check` | agent | **GATE 0**：各片段對 skill 檢查（逐 area 清單見 `nodes/fragment-check.md`） | page-migration details |
| `gen-ui.assemble` | agent | **reduce**：片段拼成 SAL0XX.razor（一致性 checklist） | `details/final-dfm-check.md` |
| `static-verify` | agent | **GATE 1**：整體 S1–S9 → findings | `acceptance-criteria.md` |
| `compile-gate` | pure | **GATE 2**：隔離 worktree build（收 CS/RZ） | `details/final-dfm-check.md` |
| `human-review` | human | **GATE 3**＋interrupt：裁決/park/候選 skill diff | translation-log |

> **明細多組**（M/D*4）：`gen-ui.detail` **一個 node 內部**依序處理各組明細片段，不每組再開 node（避免節點爆炸）；未來若某頁明細特別重，可再 fan-out 為 `detail.dq1/dq2…`。

---

## 條件路由 mini-DSL（運算子清單）

> 條件**只讀 state**。載體是 agent，故限定下列運算子，agent 照表求值 → 路由可預測、可重現。

| 運算子 | 意義 | 例 |
|---|---|---|
| `<flag>` | 布林為真 | `mode_confirmed` |
| `.none` / `.any` | 清單空 / 非空 | `findings.none` |
| `.any(<attr>~<val>)` | 清單中有元素其屬性符合（`~`＝包含/glob） | `findings.any(area~grid)` |
| `attempts < max` / `attempts >= max` | 重試煞車（max＝`policy.max_node_attempts`） | `attempts < max` |
| `<field> == <val>` | 純量相等（用於 view_mode 等單值） | `skeleton.pages.view_mode == telerik-window` |
| `not <expr>` | 取反 | `not skeleton.pages.panes.no_detail` |
| `and` | 且 | `findings.any(file~backend) and attempts<max` |

---

## 圖定義（結構）

```yaml
version: 2
name: page-migration-graph
entrypoint: route-mode
description: >
  單一參考程式（SALxxx）從 Delphi 讀取到 C# 產出、檢察、編譯、人工收尾的圖。
  萃取切細；UI 生成 map→reduce（區塊片段→assemble）；驗證分片段(GATE0)與整體(GATE1)兩關。

# ---- 全域策略 ----
policy:
  max_node_attempts: 2          # 單 node 失敗重試上限；超過 → 升 human-review
  checkpoint: after_each_node   # 每個 node 完成後寫回 state（斷點續跑依據）
  parallelism:
    - [gen-backend, gen-ui.toolbar, gen-ui.grid, gen-ui.detail]  # plan 之後組合類可平行；呈現模式類(editwindow/tabview)由條件邊擇一啟動
  on_tool_error:                # 429 / 工具失敗的 fallback（缺口 #4）
    action: checkpoint_and_pause
    resumable: true

# ---- 節點 ----
# kind: pure(純函式/可快取) | agent(委派 .claude agent) | human(interrupt 暫停)
nodes:

  - id: route-mode
    kind: agent
    reads: [code, sources]
    writes: [mode, mode_confirmed, open_questions]
    rules_ref: skills/page-migration/SKILL.md#步驟1-選擇使用範本
    note: 依鐵則「一律問使用者選範本」：產出候選模式＋理由，最終選擇走 human-review 確認。契約見 nodes/route-mode.md。

  - id: extract.dfm-decode
    kind: pure
    reads: [code, dfm_path]
    writes: [manifest.fields]
    tool: skills/page-migration/tools/dfm_decode.py
    retryable: true
    cache: true                 # dfm 未變即跳過

  - id: extract.field-cross-check
    kind: pure
    reads: [manifest.fields, pas_path]
    writes: [manifest.crosscheck]
    rules_ref: skills/page-migration/details/delphi-reading.md
    retryable: true
    cache: true

  - id: extract.fact-resolve
    kind: agent
    reads: [code, manifest.crosscheck]
    writes: [manifest.facts, open_questions]   # 缺 map/名稱不明 → 進 open_questions
    depends_on_step: 2          # 需 index.json；未建前降級為人工查檔
    rules_ref: CLAUDE.md#鐵則4-禁止推測
    retryable: true

  - id: plan
    kind: agent                       # 生成第一步：讀 pas+dfm 產「骨架藍圖」＋分層/分頁/分功能
    reads: [code, mode, manifest, sources]
    writes: [plan_ref, skeleton, acceptance_claims]   # skeleton＝gen-* 第二步的容器
    rules_ref: skills/page-migration/templates
    note: thinking-planner 產藍圖(不寫 code)；骨架就緒才 fan-out。契約見 nodes/plan.md。
    retryable: true

  # ---- 生成第二步（gen-*）：照 skeleton 藍圖實作功能。契約見 nodes/gen.md ----
  # ---- 後端：三檔天然獨立，一個 node 產出、免拼裝（skeleton.layers.backend）----
  - id: gen-backend
    kind: agent
    reads: [plan_ref, skeleton, manifest]
    writes: [artifacts.backend]      # Repository / Service / Resolver
    rules_ref: skills/page-migration/details/crud-handlers.md
    retryable: true
    idempotent: true                 # worktree 隔離，重跑不汙染

  # ---- 前端：map（依 skeleton.fragments 各產片段，不改檔）→ reduce（assemble）----
  # 組合類（fan-out 全跑）：toolbar / grid / detail
  - id: gen-ui.toolbar
    kind: agent
    reads: [plan_ref, skeleton, manifest]
    writes: [fragments.toolbar]      # ribbon ToolbarGroup 指令 + 按鈕權限閘門
    rules_ref: skills/page-migration/details/toolbar.md
    retryable: true

  - id: gen-ui.grid
    kind: agent
    reads: [plan_ref, skeleton, manifest]
    writes: [fragments.grid]         # 主 grid：filter 區 + 欄位 + InCell 編輯 +（非 tab 模式時）主表 DTO
    rules_ref: skills/page-migration/details/grid-virtual.md
    retryable: true

  - id: gen-ui.detail
    kind: agent
    reads: [plan_ref, skeleton, manifest]
    writes: [fragments.detail]       # 明細 grid：欄位 + InCell + 明細 DTO（多組於 node 內序理）
    rules_ref: skills/page-migration/details/grid-incell.md
    retryable: true
    skip_when: skeleton.pages.panes.no_detail   # 無明細（單一主表）→ 不啟動

  # 呈現模式類（條件邊擇一，依 view_mode 只啟動其一；incell 則不啟動任何一支）
  - id: gen-ui.editwindow
    kind: agent
    reads: [plan_ref, skeleton, manifest]
    writes: [fragments.editwindow]   # TelerikWindow 單筆編輯（讀 grid 宣告的主表 DTO，不重宣告）
    rules_ref: skills/page-migration/details/edit-window.md
    retryable: true

  - id: gen-ui.tabview
    kind: agent
    reads: [plan_ref, skeleton, manifest]
    writes: [fragments.tabview]      # 瀏覽↔明細資料分頁（本模式由 tabview 統一宣告主表 DTO）
    rules_ref: skills/page-migration/details/editor-template.md
    retryable: true

  # 子視窗類（條件邊：skeleton 宣告子視窗才啟動；多個於 node 內部序理）
  - id: gen-ui.subwindow
    kind: agent
    reads: [plan_ref, skeleton, manifest]
    writes: [fragments.subwindow]    # 彈出子視窗/子元件（inline TelerikWindow + 引用獨立子元件如 SAL0XXA/B/D）
    rules_ref: skills/popup-window                     # 另按類型：multiselect-picker（穿梭）、page-migration/templates/excel-import.md（Excel 匯入窗）
    retryable: true

  - id: fragment-check
    kind: agent                      # GATE 0：各片段先對 skill 檢查（片段層）。逐 area 檢查清單見 nodes/fragment-check.md
    reads: [fragments, manifest]
    writes: [fragment_findings]      # 帶 area(toolbar/grid/detail/editwindow/tabview/subwindow)，供路由回該片段 node
    rules_ref: skills/page-migration/details
    retryable: false

  - id: gen-ui.assemble
    kind: agent                      # reduce：片段拼成 razor
    reads: [fragments, manifest]
    writes: [artifacts.ui]           # SAL0XX.razor
    rules_ref: skills/page-migration/details/final-dfm-check.md
    checklist:                       # assemble 一致性（拼裝時必核）
      - 欄位順序依 dfm Top 座標
      - DTO 去重（同名屬性/_Display 不重複宣告）
      - @using / @inject 去重
      - GridColumnConfig 綁對 _Display 欄
    retryable: true

  - id: static-verify
    kind: agent                      # GATE 1：整體 S1–S9（拼裝後）
    reads: [artifacts, manifest, acceptance_claims]
    writes: [findings]               # {category, area, file, line, verdict, summary}
    rules_ref: checklist/acceptance-criteria.md
    retryable: false

  - id: compile-gate
    kind: pure                       # GATE 2：隔離 worktree build
    reads: [artifacts]
    writes: [compile_errors]         # 只收 CS/RZ；忽略 MSB3021/3027
    rules_ref: skills/page-migration/details/final-dfm-check.md
    note: 不在 IKSERPUI 工作目錄 build（鐵則 6）；用 git worktree 複本。
    retryable: true

  - id: human-review
    kind: human                      # GATE 3 + interrupt
    reads: [findings, fragment_findings, open_questions, open_decisions, compile_errors]
    writes: [decisions, skill_diff_candidates]
    note: 可暫停/續跑；未決事項留 state，續跑回到此 node。

# ---- 邊（if-else 條件路由）----
edges:
  # 進入 + 萃取
  - {from: route-mode,                to: extract.dfm-decode,       when: mode_confirmed}
  - {from: route-mode,                to: human-review,             when: mode_ambiguous}
  - {from: extract.dfm-decode,        to: extract.field-cross-check}
  - {from: extract.field-cross-check, to: extract.fact-resolve}
  - {from: extract.fact-resolve,      to: plan,                     when: open_questions.none}
  - {from: extract.fact-resolve,      to: human-review,             when: open_questions.any}   # 不推測，先問

  # 計畫 → fan-out（組合類：後端 + toolbar + grid + detail 平行全跑）
  - {from: plan, to: [gen-backend, gen-ui.toolbar, gen-ui.grid], type: fan-out}
  - {from: plan, to: gen-ui.detail, type: fan-out, when: "not skeleton.pages.panes.no_detail"}   # 有明細才跑
  # 計畫 → 呈現模式（條件邊擇一：依 view_mode 只啟動其一；incell 不另啟動）
  - {from: plan, to: gen-ui.editwindow, when: "skeleton.pages.view_mode == telerik-window"}
  - {from: plan, to: gen-ui.tabview,    when: "skeleton.pages.view_mode == tab-browse-detail"}
  # 子視窗（條件邊，非互斥；有宣告就跑）
  - {from: plan, to: gen-ui.subwindow,  when: "skeleton.pages.subwindows.any"}

  # 前端片段 → GATE 0（join：等本頁「實際啟動」的片段都 done）
  - {from: [gen-ui.toolbar, gen-ui.grid, gen-ui.detail, gen-ui.editwindow, gen-ui.tabview, gen-ui.subwindow], to: fragment-check, type: join}
  - {from: fragment-check, to: gen-ui.assemble,   when: fragment_findings.none}
  - {from: fragment-check, to: gen-ui.toolbar,    when: "fragment_findings.any(area~toolbar) and attempts<max"}
  - {from: fragment-check, to: gen-ui.grid,       when: "fragment_findings.any(area~grid) and attempts<max"}
  - {from: fragment-check, to: gen-ui.detail,     when: "fragment_findings.any(area~detail) and attempts<max"}
  - {from: fragment-check, to: gen-ui.editwindow, when: "fragment_findings.any(area~editwindow) and attempts<max"}
  - {from: fragment-check, to: gen-ui.tabview,    when: "fragment_findings.any(area~tabview) and attempts<max"}
  - {from: fragment-check, to: gen-ui.subwindow,  when: "fragment_findings.any(area~subwindow) and attempts<max"}
  - {from: fragment-check, to: human-review,      when: attempts>=max}

  # 後端 + assemble 後的 UI → GATE 1（整體）
  - {from: [gen-backend, gen-ui.assemble], to: static-verify, type: join}
  - {from: static-verify, to: compile-gate,      when: findings.none}
  - {from: static-verify, to: gen-backend,       when: "findings.any(file~backend) and attempts<max"}
  - {from: static-verify, to: gen-ui.toolbar,    when: "findings.any(area~toolbar) and attempts<max"}
  - {from: static-verify, to: gen-ui.grid,       when: "findings.any(area~grid) and attempts<max"}
  - {from: static-verify, to: gen-ui.detail,     when: "findings.any(area~detail) and attempts<max"}
  - {from: static-verify, to: gen-ui.editwindow, when: "findings.any(area~editwindow) and attempts<max"}
  - {from: static-verify, to: gen-ui.tabview,    when: "findings.any(area~tabview) and attempts<max"}
  - {from: static-verify, to: gen-ui.subwindow,  when: "findings.any(area~subwindow) and attempts<max"}
  - {from: static-verify, to: human-review,      when: attempts>=max}

  # GATE 2 編譯
  - {from: compile-gate, to: human-review, when: compile_errors.none}
  - {from: compile-gate, to: gen-backend,      when: "compile_errors.any(file~cs) and attempts<max"}
  - {from: compile-gate, to: gen-ui.assemble,  when: "compile_errors.any(file~razor) and attempts<max"}

  # 人工收尾
  - {from: human-review, to: extract.fact-resolve, when: decisions.reopen_facts}
  - {from: human-review, to: DONE,                 when: decisions.accepted}

# ---- 終止 ----
terminal:
  - DONE                        # 人工接受，寫入 translation-log 收尾
```
