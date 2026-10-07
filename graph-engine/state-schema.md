# State Schema — per-program run state（單一參考程式一份）

> **這是什麼**：graph engineering 的「共享狀態」定義——node 之間**唯一的傳話管道**，機器可讀。
> **存放**：實際 state 寫進 `plans/<code>.md` 的 YAML front-matter（本來就是 md 內嵌 yaml）；本檔是 schema 說明＋範本。
> **鐵律**：node 只讀自己 `reads` 宣告的欄、只寫自己 `writes` 宣告的欄（見 `graph-spec.md`）。
> **格式**：外層 md（分段說明）＋下方 ```yaml 範本（每段開頭有 `# ===== 這一段是XXX =====` 標示）。

---

## 各段落速查（人讀）

| 段落 | 這一段是什麼 | 誰寫 |
|---|---|---|
| 識別 | 程式代號/B代碼/正式名/模式 | route-mode |
| 來源檔 | dfm/pas 路徑、繼承 base | route-mode |
| 流程狀態 | `stage` + 每 node 狀態機（**續跑核心**） | 每個 node |
| 萃取產物 manifest | dfm 欄位、三方交叉、既有事實 | extract ×3 |
| 骨架藍圖 skeleton | 分層/分頁/分功能分解（生成第一步的容器） | plan |
| 前端片段 fragments | filter/edit/detail 片段（map→reduce 中間物） | gen-ui.* / assemble |
| 閘門與待決 | fragment_findings / findings / open_questions / decisions（**供路由讀**） | fragment-check / verify / fact-resolve / human |
| 產物指標 | plan/log/backend/ui 檔路徑 | plan / gen-* |
| 回饋閉環 | S1–S9 聲明、候選 skill diff | plan / human |
| reducer 約定 | state 怎麼合併，避免覆寫 | （規則，非資料） |

---

## State 範本（結構）

```yaml
# ===== 這一段是「識別」：程式是誰、用哪個範本 =====
code: SAL084                     # 畫面代號（主鍵）
b_code: B715                     # 對照表原程式代號（route/extract 帶入，不推測）
title: 銷貨明細查詢               # 來源：SAL程式編號對照表（權威），非 dfm caption
mode: master-detail             # single-file | master-detail | excel-import | selectform | dropform | 特例
mode_confirmed: false           # route-mode 提案後、human 確認前為 false

# ===== 這一段是「來源檔」：extract 要讀的 Delphi 原件 =====
sources:
  dfm_path: D:\ikserp\MT\SAL\B715.dfm
  pas_path: D:\ikserp\MT\SAL\B715.pas
  base_pas: null                # 有繼承鏈時填 base（B301Base 之類）；有值→route 先問

# ===== 這一段是「流程狀態」：斷點續跑核心（缺口 #4）=====
stage: static-verify            # 目前所在 node id（中斷後從此續跑）
nodes:                          # 每 node 的狀態機
  route-mode:                {status: done,    attempts: 1}
  extract.dfm-decode:        {status: done,    attempts: 1, cache_hit: true}
  extract.field-cross-check: {status: done,    attempts: 1}
  extract.fact-resolve:      {status: done,    attempts: 1}
  plan:                      {status: done,    attempts: 1}   # 生成第一步：骨架藍圖
  gen-backend:               {status: done,    attempts: 1}   # 後端三檔
  gen-ui.toolbar:            {status: done,    attempts: 1}   # 組合：工具列
  gen-ui.grid:               {status: done,    attempts: 1}   # 組合：主 grid（filter+欄位+InCell+DTO）
  gen-ui.detail:             {status: done,    attempts: 2}   # 組合：明細（no_detail 時 skipped）
  gen-ui.editwindow:         {status: skipped, attempts: 0}   # 模式擇一：非 window 模式 → skipped
  gen-ui.tabview:            {status: skipped, attempts: 0}   # 模式擇一：非 tab 模式 → skipped
  gen-ui.subwindow:          {status: skipped, attempts: 0}   # 有才跑：subwindows 空 → skipped
  fragment-check:            {status: done,    attempts: 1}   # GATE 0：片段層檢查
  gen-ui.assemble:           {status: done,    attempts: 1}   # reduce：拼成 razor
  static-verify:             {status: failed,  attempts: 1}   # GATE 1：整體
  compile-gate:              {status: pending, attempts: 0}   # GATE 2
  human-review:              {status: pending, attempts: 0}   # GATE 3 + interrupt
# status 值域: pending | running | done | failed | blocked | skipped

# ===== 這一段是「萃取產物 manifest」：事實層，擋「推測」=====
manifest:
  fields:                       # dfm-decode：每 grid 的欄位/欄序/寬/中文標題
    main:   []                  # [{field, title, width, top}]
    detail: {}                  # {dqName: [...]}
  crosscheck: []                # field-cross-check：dfm × SQL select × gettext 三方交叉結果
  facts:                        # fact-resolve：查 index.json 得到的既有事實
    keycode_maps:  []           # 已註冊 _kcMapSAL 的 key（缺者進 open_questions）
    name_maps:     []           # 已註冊 _mapSAL 的 key
    reuse_funcs:   []           # Modules/FUNC 已有的共用函式（勿重寫）

# ===== 這一段是「骨架藍圖」：生成第一步(plan/thinking-planner)產，gen-* 第二步的容器 =====
skeleton:                       # 讀 pas+dfm 的分層/分頁/分功能分解（不含實體 code，只是藍圖）
  layers:                       # 分層：後端要哪幾檔＋前端外殼
    backend: []                 # [{file, role}] Repository/Service/Resolver
    ui_shell: {file: null, shell_ref: details/page-shell.md}
  pages:                        # 分頁：版型與主檔明細結構
    layout_mode: null           # single-file | master-detail | excel-import | selectform | dropform
    scroll_mode: null           # A/B/C
    view_mode: null             # 呈現模式(擇一)：incell | telerik-window | tab-browse-detail
    panes:                      # 主檔明細結構
      no_detail: false          # true＝單一主表(無明細) → gen-ui.detail 不啟動
      list: []                  # [master, detail.dq1, …]
    subwindows: []              # 子視窗清單：[{name, kind(popup|picker|excel), 說明}] → 非空才啟動 gen-ui.subwindow
  fragments:                    # 分功能：各 fragment 要實作什麼（供 gen-ui.* map）
    toolbar: {}                 #   工具列指令/按鈕權限
    grid:    {}                 #   主 grid：filter 區/欄位/InCell（非 tab 模式時含主表 DTO）
    detail:  {}                 #   明細各 grid（no_detail 時免）
    editwindow: {}              #   view_mode=telerik-window 才用
    tabview:    {}              #   view_mode=tab-browse-detail 才用（統一宣告主表 DTO）
    subwindow:  {}              #   subwindows 非空才用（多個子視窗於 node 內序理）
  functions: []                 # 功能清單：[{name, handler, where, gated?}]（gen 實作、verify 覆核）

# ===== 這一段是「前端片段」：map→reduce 的中間產物（不直接改檔）=====
fragments:                      # gen-ui.* 各產片段；gen-ui.assemble 讀它拼成 razor
  # 組合類（fan-out 全跑）
  toolbar: null                 # 工具列 ribbon + 按鈕權限
  grid:    null                 # 主 grid：filter 區 + 欄位 + InCell +（非 tab 模式）主表 DTO
  detail:  null                 # 明細 grid + InCell + 明細 DTO（多組內含；no_detail 時為 null）
  # 呈現模式類（依 view_mode 擇一，另一支恆 null）
  editwindow: null              # view_mode=telerik-window：TelerikWindow 單筆編輯（讀 grid 的 DTO）
  tabview:    null              # view_mode=tab-browse-detail：瀏覽↔明細資料分頁（統一宣告主表 DTO）
  # 子視窗類（有才跑）
  subwindow:  null              # 彈出子視窗/子元件（inline TelerikWindow + 引用 SAL0XXA/B/D；subwindows 空時為 null）

# ===== 這一段是「閘門與待決」：findings 是 first-class state，供條件邊路由 =====
fragment_findings: []          # GATE 0(fragment-check) 產：[{area(toolbar/grid/detail/editwindow/tabview/subwindow),file,line,verdict,summary}]
findings: []                   # GATE 1(static-verify) 產：[{category,area,file,line,verdict,summary}]
compile_errors: []             # GATE 2(compile-gate) 產：[{file,line,code(CS/RZ),msg}]
open_questions: []             # 事實不明（名稱/keycode/表名）→ 不推測，路由去 human
open_decisions: []             # 需使用者拍板（如 REOP-null 語意、DB 方言）
decisions: []                  # human-review 已裁決：[{id, choice, date}]
# 註：findings/fragment_findings 的 area 欄，就是條件邊 findings.any(area~grid) 路由回該片段 node 的依據。

# ===== 這一段是「產物指標」：實際檔案落點 =====
artifacts:
  plan:    plans/SAL084.md
  log:     translation-log/SAL084.md     # append-only reducer（不覆寫）
  backend: [Modules/SAL/SALRepository.SAL084.cs, Modules/SAL/SALService.SAL084.cs, Resolvers/SAL/SAL084Query.cs]
  ui:      [Components/Pages/SAL/SAL084.razor]   # 由 gen-ui.assemble 從 fragments 拼成

# ===== 這一段是「回饋閉環」：規則精進（缺口 #6）=====
acceptance_claims: {}          # plan 產：S1–S9 逐項聲明「本頁怎麼滿足」，供 verifier 比對
skill_diff_candidates: []      # human-review 產：可套用的 page-migration 精進，待核可
```

---

## Reducer 約定（state 怎麼被合併，避免覆寫）

> 這一段是**規則**，不是資料——說明各欄位在多次寫入時如何合併。

```yaml
reducers:
  translation-log: append-only          # 只追加逐次紀錄，永不刪舊（沿用現行 _TEMPLATE.md）
  TODO彙整: derived                      # 不再人工維護：由各 <code> 的 open_decisions/open_questions reduce 而成
  nodes.*.attempts: increment           # 重試累加，供路由判 attempts>=max
  manifest.*: replace_on_input_change   # 輸入(dfm/pas)未變則沿用快取，變了才重算
  fragments.*: replace                  # 某片段 node 重跑只覆蓋自己那格（toolbar/grid/detail/editwindow/tabview/subwindow 互不影響）
  findings / fragment_findings / compile_errors: replace   # 每次該 gate 重跑覆蓋（非累加）
```
