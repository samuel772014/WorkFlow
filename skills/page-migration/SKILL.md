---
name: page-migration
description: IKSERP Delphi→Blazor 頁面轉譯／修正的規則來源（範本骨架＋details）。轉譯頁面、修改頁面、參考某頁新增頁面、提供 Delphi .pas/.dfm 時觸發；執行一律走 graph-engine（.claude/SelfFolder/graph-engine/ORCHESTRATION.md）。
---

# IKSERP Blazor 頁面轉譯流程（新 UI）

## ⚠️ 執行方式：一律走 graph-engine

**轉譯與修正工作不直接照本檔逐步做，一律由 graph-engine 編排**（CLAUDE.md 工作流）：
1. 主 session 當 orchestrator，讀 `.claude/SelfFolder/graph-engine/ORCHESTRATION.md` 主迴圈。
2. 載入或建立 state：`.claude/SelfFolder/plans/<程式代號>.md` front-matter（新程式先跑 `route-mode`）；中斷時從 `state.stage` 續跑。
3. 依 `graph-spec.md` 跑 node → 寫回 state → 依邊路由 → checkpoint；不得跳過 GATE1 `static-verify`、GATE2 `compile-gate`。
4. 本 skill 的角色＝**規則來源**：各 node 以 `rules_ref` 指到下方範本（`templates/*`）與 `details/*`；下方「範本清單」對應 `route-mode` node，「交付前檢查」對應 `static-verify`/`human-review`。產頁面、修頁面都由 graph-engine 驅動；查規則、回答問題時才直接讀 details。

> 本流程以 **for_github 美工新 UI** 為視覺與結構標準：左側 sidebar 版型、`ToolbarGroup` 群組化 ribbon 工具列（Tabler 純圖示 + tooltip）、主檔明細採 **`.cd-stack-top/-bottom` 垂直堆疊**（Mode C 堆疊式，`.cd-body` 自動捲動；**不用 `TelerikSplitter`**）+ 明細 `iks-mode-switch` 膠囊切換 + frame-header 內建於 Grid 元件、`IksGrid_*` 對外 API。

---

## 範本清單

> 本表是範本與 `mode` 值的唯一權威（graph-engine `route-mode` node 依此提案）。**範本一律由使用者選定**：route-mode 只產候選＋理由，經 human-review 確認。

| # | 範本 | `mode` | 適用情境 | 參考頁面 |
|---|------|--------|---------|---------|
| 1 | **主檔明細 堆疊式** | `master-detail` | 主表 + 多組明細（來源有 `AddDetail`，且確認明細仍在用），主/明細 `.cd-stack-top/-bottom` 垂直堆疊（`.cd-body` 自動捲，不用 Splitter）、明細 `iks-mode-switch` 膠囊切換、frame-header 內建於 Grid | `SAL021`／`SAL301` |
| 2 | **單檔 清單+彈窗** | `single-file` | 單一主表維護（含明細已無使用，如 B101），主查詢 Grid 點列開 `TelerikWindow` 單筆編輯（上/下一筆） | `SAL001` |
| 3 | **Excel 批次匯入** | `excel-import` | 從 Excel 批次讀入，`TelerikWindow` 內含 選檔 → 工作表 → 預覽 Grid → 驗證 → 批次匯入 | `SAL021A` |
| 4 | **dropform 雙表穿梭撥轉** | `dropform` | **非 CRUD**：查候選 → 雙 grid 穿梭挑選 → 批量設定 → 撥轉/轉單（工具列是動作非 CRUD） | `SAL058`（B407） |
| — | **特例** | `特例` | 不屬上列 → 標記後跳過，不自行設計解法（鐵則 2） | — |

> 📌 **單一主表維護一律用「範本 2 單檔 清單+彈窗」**（InCell 批次編輯已淘汰，不當頂層範本）。InCell 僅用於「主檔明細」範本裡的明細 grid。

---

## 來源檔讀取原則（所有範本適用）

讀 Delphi 來源時，先套這些通則（兩次 dry-run 萃取）：

1. **遇繼承鏈 → 先詢問轉譯操作者**。Delphi 常見 `TFmXxx = class(TFmXxxBase)`，真正欄位/明細/事件多在 base（如 `B301` 空殼→`B301Base`）。**不限主檔明細**，任何頁只要出現繼承就先問操作者怎麼處理（base 可能多支子類共用、客製差異需釐清），再往下讀。
2. **`.pas` 有邏輯 ≠ 畫面有顯示**：欄位「是否顯示」看 `.dfm` 的 `Visible`；`.pas` 有 pick/KeyCode 只代表「若顯示則用對應控件」。
3. **`.dfm` 是版面權威**：欄位 **Title** 來自 DFM `Caption` / Grid `Selected.Strings`；**欄位順序**依 DFM 控件 `Top` 座標（由上而下）。
   - ⚠ **grid 欄位必用 `tools/dfm_decode.py` 解碼核對**（DFM 中文是 Big5/`#NNNN`，手讀是亂碼）：`PYTHONIOENCODING=utf-8 py .claude/skills/page-migration/tools/dfm_decode.py <來源.dfm>` → 得「主 grid 與每個子 grid」的 FIELD/欄序/寬/中文標題。
   - ⚠ **每個 grid（主檔 + 每個 Dq）都要做「dfm 欄位 × SQL select × 該 grid 的 gettext(`_Display`)」三方交叉核對**；子表的 `_Display` 欄位集看 `FormCreate` 各自的 `AddFieldEvent(Self, DqN, 'F1;F2;…', …)`，**不是只有主檔 `MqyGetText`**。詳見 `details/delphi-reading.md` Step 2.0/2.1。
4. **先找共用函式**：Delphi 參考函式先查 `Modules/FUNC` 是否已有 C# 共用函式，勿重寫 SQL（見 details/shared-functions.md）。

## 已建範本骨架（漸進式揭露）

| 範本 | 大骨架檔 | 說明 |
|------|---------|------|
| ② 單檔 清單+彈窗 | `templates/single-file.md` | 已完成（A~J 全頁骨架＋指標） |
| ① 主檔明細 堆疊式 | `templates/master-detail.md` | 已落地（SAL021；堆疊式 + 明細膠囊切換） |
| ③ Excel 批次匯入 | `templates/excel-import.md` | 主檔批次匯入 / 明細回填兩種模式（SAL041A、SAL021A、SAL025A） |
| ④ dropform 雙表穿梭 | `templates/dropform.md` | 由 SAL058 抽取（B工具列/C來源grid/D篩選/E目標grid InCell/F批量設定）；原 selectform 已併入 |

> 骨架只放結構與擺放位置，各區細節在 `details/*.md`，要做哪區才讀哪支。

## details 索引（要做哪區才讀哪支）

| 階段/區 | details |
|---------|---------|
| Phase 0 讀來源 | `delphi-reading`（.dfm→.pas 逐層、產出順序、Service 範本） |
| 命名 | `naming` |
| 工具列/按鈕 | `toolbar`、`btn-control` |
| 主檔清單 grid + 鍵盤/OnRowFocus | `grid-virtual` |
| 進階篩選 | `popup-filter` |
| 明細顯示設定（checkbox 類顯示/動作開關，與 SQL WHERE 無關） | `detail-display-settings` |
| 控件選擇/用法 | `input-component-choice`、`shared-input-components`、`editor-template` |
| 長文字放大編輯（Delphi `EditMemo`） | `popuptext` |
| 遇到含業務規則的邏輯段（判斷落點：共用函式/計算/填值/DB） | `business-logic` |
| Delphi 共用函式 → C# 方法名/狀態 | `.claude/SelfFolder/共用函式對照表.md`（權威；`delphi-func-lookup` 僅指路） |
| 欄位連動/計算 | `field-change` |
| 編輯表單/View | `edit-window` |
| 明細 InCell | `grid-incell` |
| CRUD/後端 | `crud-handlers`、`backend-sql`、`shared-functions` |
| DTO/顯示 | `dto-display` |
| 附件 PDF | `attachment` |
| 排版 CSS | `css-layout` |
| 上/下一筆 | `row-navigate` |
| 頁面殼/狀態/生命週期 | `page-shell` |
| 頁面標題（`(程式代號)程式名稱`，名稱照對照表） | `title` |
| 最後檢查（DFM×razor 三方比對） | `final-dfm-check` |

## 交付前檢查（所有範本適用）

0. **最後檢查 DFM × razor 三方比對（必做，見 `details/final-dfm-check.md`）**：頁面寫完後，用 `tools/dfm_audit.py`＋`tools/dfm_decode.py`＋TLabel `FocusControl`，把 razor 逐項對回 `.dfm`/`.pas` 權威——
   - **① 篩選區**：預設文字（DFM TLabel Caption，勿臆測簡化）、順序（`top,left` 由上到下由左到右）、FilterDblClick/Validate 規則、`Visible=False` 的篩選不顯示。
   - **② 明細切頁**：頁籤名稱與順序＝base `.dfm` TTabSheet Caption 與檔案順序。
   - **③ 主/明細欄位 × 顯示狀態**：`dfm_decode` 欄位/欄序 × SQL select × 各 grid `AddFieldEvent` 的 `MqyGetText/DqNGetText`（`GetNoDESCPT`→名稱、`GetKeyCodeDESCPT`→KeyCode 文字，缺 map 補 `DisplayTransformService.SAL.cs`）。
   - **④ 明細必填欄位**：可編輯＋`sNotNullFields` 的欄，DTO 有欄、存檔前有驗、INSERT 有寫。
   > 繼承鏈頁面：篩選/頁籤對 **base `.dfm`**，grid 欄位對「子類覆寫 + base 未覆寫」。
1. **UI 編譯檢查（必做，交使用者）**：UI 編譯交使用者 IDE／hot reload（鐵則 6），回報 `CS`/`RZ` 錯誤再修；razor 錯誤（如 EditorTemplate 回傳型別、型別錯配）常只在 UI 編譯時才出現，務必提醒。
2. **存檔欄位對 Delphi**：`BuildXxxArgs` 的欄位**依 Delphi 該表單實際存的欄位為準**，不是後端 UPDATE 全欄、也不是畫面全欄（見 `details/crud-handlers.md`）。
