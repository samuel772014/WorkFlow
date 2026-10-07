# Node 契約 — fragment-check（GATE 0：片段層檢查）

> **這是什麼**：生成第二步各 fragment 產出後、assemble 之前的**片段層守門**。每個片段**各自對 page-migration 對應 details 檢查一次**，產 `fragment_findings`（帶 `area`），供條件邊 targeted retry 只退回不過的那支。
> **與 GATE 1 分工**：本關只看**單一片段自身**是否合規（片段內規則）；跨片段一致性、與 backend 對應、整體 S1–S9 留給 `static-verify`（GATE 1）。
> **runner**：agent 依各片段 `rules_ref` 檢查。`retryable:false`（檢查本身不重試自己）。
> **規則來源**：每條檢查後標注的 `details/*.md` 為權威；本檔只把「檢查什麼」列清楚。

---

## fragment_findings 結構

```yaml
fragment_findings:
  - area:     grid              # toolbar | grid | detail | editwindow | tabview | subwindow → 路由回該片段 node
    category: incell-lock       # 檢查類別（見各表）
    verdict:  CONFIRMED         # CONFIRMED(機器/規則可確定) | PLAUSIBLE(需人覆核)
    file:     SAL0XX.razor
    line:     0
    summary:  明細用整表鎖欄樣板，違反全域閘門通則
```
`area` = 條件邊 `fragment_findings.any(area~grid)` 退回 `gen-ui.grid` 的依據。

---

## 檢查清單（依 area 分）

### area: `toolbar` — `details/toolbar.md`、`details/btn-control.md`
| category | 檢查項 | 依據 |
|---|---|---|
| btn-order | 按鈕順序＝`CRUD → 查詢查看 → 特殊功能` | toolbar 通則 |
| btn-placement | 單檔:工具列＝新增→查詢,修改/刪除/詳細資料在 grid 指令欄;明細:主檔所有操作放工具列 | toolbar 按鈕配置決策 |
| rownav-not-in-toolbar | 上/下一筆**不放工具列**（只在編輯/詳細 Window 右側） | toolbar 通則 |
| ribbon-style | 純 Tabler 圖示 + tooltip、扁平 ribbon（`ToolbarGroup` 分組） | toolbar 二 |
| btncontrol-flag-only | `btnControl()` 只設 bool 旗標、**不呼叫 `StateHasChanged`**，統一在 `HandleToolbar` 末尾呼叫 | btn-control 通則 |
| no-placeholder-flag | 沒有的按鈕不宣告對應旗標（不留佔位符） | btn-control 通則 |

### area: `grid` — `grid-virtual.md`、`grid-incell.md`、`popup-filter.md`、`input-component-choice.md`、`field-change.md`
| category | 檢查項 | 依據 |
|---|---|---|
| frameheader-toolbar | `ShowFrameHeader="true"` 時必 `ShowBuiltInToolbar="false"`（否則新舊工具列並存） | grid-virtual frame-header 通則 |
| filter-popup | 篩選欄位一律放 `TelerikPopup`（不用展開/收合、不用常駐 filter-field），Popup 在 **Grid 元件外部** | popup-filter |
| filter-clear-ref | 清除：每個**非必填**控件 `@ref`+`Reset()`；**禁 `Filter=new()`**；**必填欄位不清** | popup-filter 核心陷阱 |
| input-choice | 輸入元件依決策樹:KeyCode→KeyCodeComboBox、EditPick≤2欄→IksCodeComboBox、≥3欄→EditPick、EditMemo→PopUpText、純文字→IksTextBox | input-component-choice |
| field-change | 連動用 `@bind-Value:after`;**計算一律後端**;handler 開頭防呆 | field-change 通則 |
| incell-lock | InCell 編輯鎖定**只用全域閘門**（`OnAfterRender` 每次渲染冪等 `EnterEdit()`/`ExitEdit()`）;**不寫整表鎖欄樣板**（`LockDqGridColumns`/`SetColumnEditable` 逐欄跑） | grid-incell 通則1 |
| static-editable | 「永遠不可編」欄（PK/計算欄/顯示欄）在 `GridColumnConfig` 設 `Editable=false`（靜態） | grid-incell 通則1 |
| incell-add | 新增列用 `ShowAddButton`+`OnAdd`,`uState=Insert` 寫在 **`OnAdd`**（不用 `OnCreate`） | grid-incell 通則3 |
| col-from-dfm | 欄位/欄序/寬/Title 依 DFM（`Selected.Strings` / Top 座標） | dto-display 三 |

### area: `detail` — `grid-incell.md`、`detail-display-settings.md`
| category | 檢查項 | 依據 |
|---|---|---|
| incell-lock | 同 grid：全域閘門、不寫整表鎖欄樣板 | grid-incell 通則1 |
| capsule-gate | 多組明細用 `iks-mode-switch` 膠囊+`@if`（取代 TabStrip）;膠囊切換會重建 grid → `OnAfterRender` 冪等同步閘門 | grid-incell 通則1 ⚠️ |
| row-cmd-icon | 列指令鈕純圖示+`Title`（不放文字、不用 `@FontIcon`） | grid-incell 通則2 |
| btn-position | 針對「該列」→列指令欄;整批→grid 工具列/`HeaderButtons` | grid-incell 通則2 |

### area: `editwindow` — `details/edit-window.md`（僅 view_mode=telerik-window）
| category | 檢查項 | 依據 |
|---|---|---|
| field-order-dfm | 欄位順序＝DFM 各控件 `Top` 座標由上而下 | edit-window 通則1 |
| pk-readonly | 主鍵 `Add` 可設、`Edit`/`View` 唯讀;**不移植 `cbEditKeyFields`** | edit-window 通則4 |
| view-reuse | View 唯讀重用同一 Window（所有輸入唯讀、隱藏存檔鈕）;`pageStatus` 擴 `query/Add/Edit/View` | edit-window 通則5 |
| rownav | 上/下一筆在 `Edit` 與 `View` 皆可用 | edit-window 通則5 |
| required-manual | `Required` 由操作者設定、不自動推導 | edit-window 通則3 |
| dto-reuse | 讀 `grid` 宣告的主表 DTO、**不重宣告** | 本專案 DTO 單一來源 |

### area: `tabview` — `details/editor-template.md`（僅 view_mode=tab-browse-detail）
| category | 檢查項 | 依據 |
|---|---|---|
| dto-single-source | 本模式由 tabview **統一宣告主表 DTO**（grid 瀏覽頁讀用不重宣告） | 本專案 DTO 單一來源 |
| editpick-button | 明細 EditorTemplate 內 pick 用 `EditPick_Button`+頁面層級 `@ref`;**禁在 EditorTemplate 內 inline 宣告 Picker** | editor-template |
| renderfragment-type | 方法帶額外參數的 template 回傳 **`RenderFragment`（非泛型）**（否則 CS1061/CS0029/CS1643） | editor-template ⚠️ |

### area: `subwindow` — `popup-window`／`multiselect-picker`／`templates/excel-import.md`（有子視窗才檢）
| category | 檢查項 | 依據 |
|---|---|---|
| child-not-page | 子元件是 TelerikWindow 內嵌**子元件**（非獨立 @page）;完整一頁者標 `separate_migration` 另立 migration | popup-window |
| picker-shuttle | 多選 picker 走穿梭結構（IksGrid_vnq 多選＋OnRowClick+Shift＋OnConfirm/OnClose＋載入遮罩＋iks-fbtn） | multiselect-picker |
| excel-flow | Excel 匯入窗：選檔→工作表→預覽 Grid→驗證→批次匯入齊備 | templates/excel-import.md |
| dto-boundary | 子視窗用自己的契約型別;主頁 DTO 在**開窗邊界**轉換（如 BuildDq2Record→SA_CASECRMDto），不共用型別 | dto-display 1b |

---

## 跨片段共用檢查（各片段皆適用，findings.area 記所屬片段）
| category | 檢查項 | 依據 |
|---|---|---|
| dto-inherit | DTO `partial class Xxx : EFModel, IDisplayResolvable`,只加 `_Int/_Bool/_Display/uState`;**不用 `[JsonProperty]` 改名** | dto-display 通則1 |
| dto-inline | DTO 宣告在該頁 `.razor @code`（`#region`）、**不跨頁共用型別** | dto-display 通則1b |
| display-by-gettext | `_Display` 依 Delphi `GetText`（`GetNoDESCPT`/`GetKeyCodeDESCPT`）判斷;已是實欄或 DFM `Visible=False` 者免 | dto-display 通則2 |
| combobox-naming | ComboBox 欄位大駝峰 + `ComBox` 後綴命名 | CLAUDE.md 元件慣例 |

---

## 路由（見 graph-spec.md）
- `fragment_findings.none` → `gen-ui.assemble`
- `fragment_findings.any(area~toolbar/grid/detail/editwindow/tabview/subwindow)` 且 `attempts<max` → 退對應 `gen-ui.*`（**只退不過的那支**）
- `attempts>=max` → `human-review`
- `PLAUSIBLE`（需人覆核，如「Required 哪些欄」「輸入元件特殊情況」）：不自動退回，彙整到 `human-review` 由人裁決

> **禁推測（鐵則4）**：檢查遇「特殊情況/不確定」（input-choice 特殊取值、Required 欄位、無對應 EF Model 的 DTO）→ 開 `PLAUSIBLE` finding 或寫 `open_questions`，**不自行判定過關**。
