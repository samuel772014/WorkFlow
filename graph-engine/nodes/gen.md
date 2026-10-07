# Node 契約 — gen-*（生成第二步：實作功能 fragment）

> **這是什麼**：生成階段**第二步**的執行契約，涵蓋整個生成家族：`gen-backend`（後端一檔）＋前端 map→reduce（組合類 `gen-ui.toolbar/grid/detail` ＋ 呈現模式類 `gen-ui.editwindow|tabview` ＋ 子視窗類 `gen-ui.subwindow`（有才跑）→ `fragment-check` GATE0 → `gen-ui.assemble`）。
> **前置**：`plan`（第一步）已產 `skeleton` 藍圖（分層/分頁/分功能）。本步**只填功能，不再決定結構**——結構照 skeleton，事實照 manifest，兩者皆不推測（鐵則4）。
> **runner**：`migration-executor`，以 scope 參數分子職（backend / 各片段 / assemble）。
> **規則來源**：`.claude/skills/page-migration/details/*`（各片段對應檔已在各 node 標 `rules_ref`）。

---

## 觸發時機（承 plan）

`plan` 執行完畢、`skeleton` 就緒 → 展開。**兩種關係、兩種邊**：
```
組合類（fan-out，全跑，平行）:
  gen-backend  ┐
  gen-ui.toolbar│
  gen-ui.grid  │  ← 平行（policy.parallelism）
  gen-ui.detail┘  （skeleton.pages.panes.no_detail=true 時不啟動）

呈現模式類（條件邊，依 view_mode 擇一啟動，其餘根本不啟動）:
  view_mode=telerik-window   → gen-ui.editwindow
  view_mode=tab-browse-detail→ gen-ui.tabview
  view_mode=incell           → （無，編輯留在 gen-ui.grid 內）

子視窗類（條件邊，有才跑，非互斥）:
  skeleton.pages.subwindows 非空 → gen-ui.subwindow（多個子視窗於 node 內序理）

  └─ 實際啟動的片段 join → fragment-check (GATE 0) → gen-ui.assemble (reduce)
gen-backend + assemble 完成 → join → static-verify (GATE 1)
```
> 骨架未就緒不得展開（plan 是唯一上游）。**組合 vs 擇一是刻意分兩種邊**：組合類是「全都要」用 fan-out；呈現模式互斥是「只要一種」用條件邊，避免產空 node（見 graph-spec 設計要點）。GATE0 在本頁「實際啟動」的片段都 done 後才 join。

---

## 後端一檔 — `gen-backend`

| | |
|---|---|
| 讀 | `plan_ref`、`skeleton.layers.backend`、`manifest` |
| 寫 | `artifacts.backend`（Repository / Service / Resolver 三檔） |
| scope | `migration-executor scope=backend` |
| 特性 | `idempotent`（worktree 隔離，重跑不汙染）；三檔天然獨立,**一個 node 一次產出、免拼裝** |
| rules_ref | `details/crud-handlers.md`、`details/backend-sql.md`、`details/business-logic.md` |

「一檔」＝後端這一支 node 一次把三檔都產完（非分三個 node）；業務邏輯一律落在此層（鐵則1）。

---

## 前端 map（組合類，fan-out 全跑）— `toolbar` / `grid` / `detail`

各讀 `skeleton.fragments.<自己那格>` ＋ `manifest`，**只產片段(fragment)、不改檔**；重跑只覆蓋自己那格（`fragments.*` reducer=replace，互不影響）。

| node | 寫 | 產什麼 | rules_ref |
|---|---|---|---|
| `gen-ui.toolbar` | `fragments.toolbar` | 工具列 ribbon ToolbarGroup 指令 + 按鈕權限閘門 | `details/toolbar.md`、`details/btn-control.md` |
| `gen-ui.grid`    | `fragments.grid`    | 主 grid：**filter 區** + 欄位顯示 + InCell 編輯（含選單/連動）；**非 tab 模式時宣告主表 DTO** | `details/grid-virtual.md`、`details/grid-incell.md`、`details/input-component-choice.md`、`details/field-change.md` |
| `gen-ui.detail`  | `fragments.detail`  | 明細 grid + InCell + 明細 DTO（多組明細**於 node 內部依序**產）；`no_detail` 時不啟動 | `details/grid-incell.md`、`details/detail-display-settings.md` |

## 前端 map（呈現模式類，條件邊擇一）— `editwindow` / `tabview`

依 `skeleton.pages.view_mode` **只啟動其一**（`incell` 則兩者皆不啟動，編輯留在 `grid`）。

| node | 啟動條件 | 產什麼 | rules_ref |
|---|---|---|---|
| `gen-ui.editwindow` | `view_mode==telerik-window` | TelerikWindow 單筆編輯區 | `details/edit-window.md` |
| `gen-ui.tabview`    | `view_mode==tab-browse-detail` | 瀏覽↔明細資料分頁 | `details/editor-template.md` |

## 前端 map（子視窗類，條件邊「有才跑」）— `subwindow`

`skeleton.pages.subwindows` 非空才啟動；多個子視窗**於 node 內部依序產**（比照 detail）。三種子視窗類型：

| kind | 產什麼 | rules_ref |
|---|---|---|
| `popup` | 純編輯/查詢型彈出子元件（TelerikWindow 內嵌，如 SAL046D、SAL055A） | `popup-window` skill |
| `picker` | 多選穿梭選擇器（篩選→勾選→帶回，如 SAL027A） | `multiselect-picker` skill |
| `excel` | Excel 批次匯入窗（選檔→工作表→預覽→驗證→匯入，如 SAL046 Dq1 匯入、對應 B301Base.btnExcelClick） | `templates/excel-import.md` |

> 獨立子元件（自有 .razor，如 SAL0XXA/B/D）：subwindow 產「內嵌引用＋子元件骨架」；若該子元件本身是完整一頁，視為**另一支參考程式**另立 migration（skeleton.subwindows 標 `separate_migration:true`）。

### 主表 DTO 單一來源（assemble 一律去重，確保只留一份）

| view_mode | 主表 DTO 宣告者 | 其他 node |
|---|---|---|
| `incell` | `gen-ui.grid` | — |
| `telerik-window` | `gen-ui.grid` | `editwindow` 讀用、**不重宣告** |
| `tab-browse-detail` | **`gen-ui.tabview` 統一宣告** | `grid`（瀏覽頁）讀用、**不重宣告** |

> tab 模式下欄位編輯器集中在「明細資料」分頁，故由 `tabview` 統一宣告主表 DTO；其餘模式歸 `grid`。明細 DTO 一律由 `gen-ui.detail` 宣告。

---

## GATE 0 — `fragment-check`

| | |
|---|---|
| 讀 | `fragments`、`manifest` |
| 寫 | `fragment_findings`（帶 `area`＝filter/edit/detail，供路由回該片段 node） |
| 特性 | `retryable:false`（本身是檢查，不重試自己） |

本頁實際啟動的片段 join 後**各自對 page-migration details 檢查一次**（片段層）。某片段不過 → 只重跑該片段 node（targeted retry），不影響其他。**逐 area 的完整檢查清單見 `nodes/fragment-check.md`。**

**路由**（見 graph-spec.md）：
- `fragment_findings.none` → `gen-ui.assemble`
- `fragment_findings.any(area~toolbar/grid/detail/editwindow/tabview/subwindow)` 且 `attempts<max` → 退對應 `gen-ui.*`
- `attempts>=max` → `human-review`

---

## reduce — `gen-ui.assemble`

| | |
|---|---|
| 讀 | `fragments`（三格）、`manifest`、`skeleton.layers.ui_shell` |
| 寫 | `artifacts.ui`（`SAL<code>.razor`） |
| rules_ref | `details/final-dfm-check.md`、`details/page-shell.md` |

把片段拼進骨架外殼成完整 razor。**拼裝一致性 checklist（必核）**：
- 欄位順序依 dfm `Top` 座標
- DTO 去重（同名屬性／`_Display` 不重複宣告）
- `@using` / `@inject` 去重
- `GridColumnConfig` 綁對 `_Display` 欄

---

## 生成家族路由總表（見 graph-spec.md edges）

| from | 條件 | to |
|---|---|---|
| plan | fan-out | gen-backend ∥ gen-ui.toolbar ∥ gen-ui.grid |
| plan | `not no_detail`（fan-out） | gen-ui.detail |
| plan | `view_mode==telerik-window` | gen-ui.editwindow |
| plan | `view_mode==tab-browse-detail` | gen-ui.tabview |
| plan | `subwindows.any` | gen-ui.subwindow |
| 已啟動片段 | join | fragment-check |
| fragment-check | `fragment_findings.none` | gen-ui.assemble |
| fragment-check | `.any(area~X) and attempts<max` | 退 gen-ui.X |
| gen-backend + gen-ui.assemble | join | static-verify (GATE 1) |

> 失敗**不新增 node**：檢查結果寫 findings，由 edge 依 `area` 路由退回既有 gen node；`attempts>=max` 才升 `human-review`。
