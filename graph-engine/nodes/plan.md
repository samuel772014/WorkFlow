# Node 契約 — plan（計畫，生成第一步）

> **這是什麼**：`plan` node 的執行契約。生成階段的**第一步就在這裡做完**——讀 Delphi(`.pas`)＋DFM，產出「大部分程式骨架」的**藍圖**與**分層／分頁／分功能**分解，交給 `gen-*` 第二步照著實作 fragment。
> **runner**：`thinking-planner`（Opus 4.8，只 Read/Grep/Glob）。**只產藍圖與計畫，不寫任何 code 檔**（thinking-planner 硬性限制）；藍圖寫進 `plans/<code>.md`（由主 session/編排落盤）。
> **規則來源**：`.claude/skills/page-migration/templates/`（範本骨架）＋ `details/page-shell.md`（前端外殼）；本檔只定「輸入/輸出/怎麼跑」，規則一律指回 skill。

---

## 為什麼骨架放在 plan（而非另開 gen-skeleton node）

- 骨架＝**分層分頁功能的分解決策**，本質是「想清楚結構」而非「寫功能」——正是 thinking-planner 的職責。
- 先把骨架定死，`gen-*` 的 map→reduce 才有穩定容器可填；fragment 之間不必再互相猜結構。
- thinking-planner 不寫檔，故 plan 產的是**藍圖（spec）**，不是實體 razor/cs；實體由 `gen-*` 第二步生成。

---

## 兩步關係（生成階段全貌）

```
plan（本 node，第一步）           gen-*（第二步）
  讀 pas+dfm                       gen-backend      → 依 skeleton.layers.backend 產三檔
  → skeleton 藍圖（分層/分頁/分功能） 組合:toolbar/grid/detail + 擇一:editwindow|tabview → 產片段(map)
  → acceptance_claims(S1–S9)        fragment-check(GATE0) → assemble(reduce) → razor
```

---

## 讀 / 寫

| | |
|---|---|
| 讀 | `code`、`mode`、`manifest`（extract 三 node 的事實層）、`sources.pas_path`／`sources.dfm_path` |
| 寫 | `skeleton`（骨架藍圖，見下）、`acceptance_claims`（S1–S9 逐項聲明）、`artifacts.plan`（=`plans/<code>.md`） |
| runner | `thinking-planner` |
| rules_ref | `skills/page-migration/templates/<mode>.md` ＋ `details/page-shell.md` |

> `manifest.fields`（dfm 欄位/欄序）與 `manifest.facts`（名稱/keycode/reuse_funcs）已是事實層；plan **在其上做結構決策**，不重查、不推測；缺事實者已在 `open_questions`（會被 extract 擋在 plan 之前）。

---

## skeleton 藍圖結構（本 node 的核心產出）

```yaml
skeleton:                        # 「大部分程式骨架」——分層 / 分頁 / 分功能三層分解
  layers:                        # 分層：這頁要生成哪些檔（對應鐵則1 分層原則）
    backend:                     # 後端一檔家族（三檔天然獨立，gen-backend 一個 node 產出）
      - {file: SALRepository.<code>.cs, role: 資料存取}
      - {file: SALService.<code>.cs,    role: 業務邏輯}
      - {file: <code>Query.cs,          role: GraphQL resolver}
    ui_shell:                    # 前端外殼（gen-ui.assemble 的容器；@page/標題/sidebar/toolbar/splitter）
      file: SAL<code>.razor
      shell_ref: details/page-shell.md
  pages:                         # 分頁：版型與主檔明細結構（css-layout / scroll-modes）
    layout_mode: master-detail   # single-file | master-detail | excel-import | selectform | dropform
    scroll_mode: C               # A/B/C（見 iks-scroll-modes）
    view_mode: incell            # 呈現模式(擇一)：incell | telerik-window | tab-browse-detail → 決定啟動 editwindow/tabview 哪支
    panes:
      no_detail: false           # true＝單一主表 → gen-ui.detail 不啟動
      list: [master, detail.dq1, detail.dq2]
    subwindows: []               # 子視窗清單 [{name, kind(popup|picker|excel), separate_migration?}]；非空才啟動 gen-ui.subwindow
  fragments:                     # 分功能：每個 fragment 要實作什麼（供 gen-ui.* 第二步 map）
    toolbar: {commands: [], gated: [], note: 工具列指令+按鈕權限}
    grid:    {fields: [], filter_fields: [], incell: true, dto: <code>Mqy, note: 主grid(filter區+欄位+InCell；非tab模式含主表DTO)}
    detail:  {grids: [dq1, dq2], incell: true, note: 明細(no_detail 時免)}
    editwindow: {note: 僅 view_mode=telerik-window 用}
    tabview:    {note: 僅 view_mode=tab-browse-detail 用；統一宣告主表 DTO}
    subwindow:  {note: 僅 subwindows 非空才用；多個內部序理}
  functions:                     # 功能清單：工具列/handler 對應（gen 實作、verify 覆核 S3–S8）
    - {name: 新增, handler: OnAdd,    where: grid}
    - {name: 編輯, handler: InCell/editwindow/tabview（依 view_mode）}
    - {name: 刪除, handler: OnDelete}
    - {name: 匯出, handler: null, gated: BUYxxx.EXPO?}   # 權限相關留 open_decisions
```

**分層／分頁／分功能三問**（plan 必須答完，答不出＝事實不足，退 extract 補）：
1. **分層**：後端要哪幾檔？各檔職責？（業務邏輯一律後端，鐵則1）
2. **分頁**：版型是哪個範本？scroll mode？主檔明細有幾組 pane/明細？**呈現模式(view_mode)是哪一種**（決定 editwindow/tabview 擇一，或 incell 都不開）？
3. **分功能**：工具列有哪些指令？各對應什麼 handler？哪些受權限閘門？**有無子視窗（彈出編輯/多選 picker/Excel 匯入）→ 填 `subwindows`？**

---

## acceptance_claims（S1–S9 聲明，供 static-verify 比對）

plan 對 `checklist/acceptance-criteria.md` 的 S1–S9 **逐項聲明「本頁怎麼滿足」**，寫入 `acceptance_claims`。這是 GATE 1（static-verify）機器/agent 覆核的比對基準——聲明與產物不符即成 findings。

---

## 執行流程

1. 讀 `manifest`（已萃取事實）＋ `sources.pas_path`/`dfm_path`（結構/功能語意）。
2. 依 `mode` 取對應 `templates/<mode>.md` 骨架，套 `manifest.fields` 決定 pane/欄位分佈 → 填 `skeleton.layers` / `skeleton.pages`。
3. 逐工具列/事件盤點功能 → 填 `skeleton.fragments` / `skeleton.functions`；權限/方言等未定者 → `open_decisions`。
4. 對 S1–S9 逐項聲明 → `acceptance_claims`。
5. 藍圖與聲明落盤 `plans/<code>.md` front-matter（由編排 session 寫，thinking-planner 只回報內容）。

## 路由（見 graph-spec.md）

- `plan` → **fan-out（組合類全跑）** `[gen-backend, gen-ui.toolbar, gen-ui.grid]`＋`gen-ui.detail`（`not no_detail` 時）。
- `plan` → **條件邊（呈現模式擇一）**：`view_mode==telerik-window`→`gen-ui.editwindow`；`view_mode==tab-browse-detail`→`gen-ui.tabview`；`incell`→兩者皆不啟動。
- `plan` → **條件邊（子視窗，有才跑）**：`subwindows.any`→`gen-ui.subwindow`。
- plan 若答不出「三問」（含 view_mode）或發現新事實缺口 → 寫 `open_questions`／`open_decisions`，退 `human-review`（不推測，鐵則4）。
