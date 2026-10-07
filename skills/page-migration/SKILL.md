---
name: page-migration
description: IKSERP Blazor 頁面轉譯流程的統一入口。當使用者說「幫我轉譯這個頁面」「幫我修改頁面」「參考 XXX 新增頁面」，或提供 Delphi 程式要轉成 Blazor 時觸發。以 for_github 美工新 UI 為標準（sidebar、ToolbarGroup ribbon、Splitter frame-header 主檔明細、IksGrid 對外 API）。
---

# IKSERP Blazor 頁面轉譯流程（新 UI）

> 本流程以 **for_github 美工新 UI** 為視覺與結構標準：左側 sidebar 版型、`ToolbarGroup` 群組化 ribbon 工具列（Tabler 純圖示 + tooltip）、主檔明細採 **`.cd-stack-top/-bottom` 垂直堆疊**（Mode C 堆疊式，`.cd-body` 自動捲動；**不用 `TelerikSplitter`**）+ 明細 `iks-mode-switch` 膠囊切換 + frame-header 內建於 Grid 元件、`IksGrid_*` 對外 API。

## 觸發時機

使用者說「幫我轉譯這個頁面」、「幫我修改這個頁面」、「參考 XXX 新增頁面」，或提供 Delphi 程式要轉成 Blazor。

---

## 步驟 1：選擇使用範本

> ⚠️ **一律「問使用者選」，流程不自動判斷**。讀完來源檔後，把下列範本清單列給使用者，請對方指定要用哪一種，再往下走。

### 可用範本（4 種）

| # | 範本 | 適用情境 | 參考頁面 |
|---|------|---------|---------|
| 1 | **主檔明細 堆疊式** | 主表 + 多組明細，主/明細 `.cd-stack-top/-bottom` 垂直堆疊（`.cd-body` 自動捲，不用 Splitter）、明細 `iks-mode-switch` 膠囊切換、frame-header 內建於 Grid | `SAL021`／`SAL301` |
| 2 | **單檔 清單+彈窗** | 單一主表維護，主查詢 Grid 點列開 `TelerikWindow` 單筆編輯（上/下一筆） | `SAL001` |
| 3 | **Excel 批次匯入** | 從 Excel 批次讀入，`TelerikWindow` 內含 選檔 → 工作表 → 預覽 Grid → 驗證 → 批次匯入 | `SAL021A` |
| 4 | **dropform 雙表穿梭撥轉** | **非 CRUD**：查候選 → 雙 grid 穿梭挑選 → 批量設定 → 撥轉/轉單（工具列是動作非 CRUD） | `SAL058` |

> 📌 **不提供「單檔 InCell 格內編輯」當頂層範本**：單一主表維護已淘汰 InCell 批次編輯，一律改用「範本 2 單檔 清單+彈窗」。InCell 僅用於「主檔明細」範本裡的明細 grid。

### 這一步要做什麼

1. 讀取使用者提供的來源檔（Delphi `.pas` / `.dfm` 或既有頁面）。
2. 把上表範本列給使用者，說明各自適用情境。
3. 由**使用者指定**要用哪一種範本。
4. 記下選定的範本，進入下一步（骨架建立 —— 待後續步驟補齊）。

---

## 來源檔讀取原則（所有範本適用）

讀 Delphi 來源時，先套這些通則（兩次 dry-run 萃取）：

1. **遇繼承鏈 → 先詢問轉譯操作者**。Delphi 常見 `TFmXxx = class(TFmXxxBase)`，真正欄位/明細/事件多在 base（如 `B301` 空殼→`B301Base`）。**不限主檔明細**，任何頁只要出現繼承就先問操作者怎麼處理（base 可能多支子類共用、客製差異需釐清），再往下讀。
2. **`.pas` 有邏輯 ≠ 畫面有顯示**：欄位「是否顯示」看 `.dfm` 的 `Visible`；`.pas` 有 pick/KeyCode 只代表「若顯示則用對應控件」。
3. **`.dfm` 是版面權威**：欄位 **Title** 來自 DFM `Caption` / Grid `Selected.Strings`；**欄位順序**依 DFM 控件 `Top` 座標（由上而下）。
   - ⚠ **grid 欄位必用 `tools/dfm_decode.py` 解碼核對**（DFM 中文是 Big5/`#NNNN`，手讀是亂碼）：`PYTHONIOENCODING=utf-8 py .claude/skills/page-migration/tools/dfm_decode.py <來源.dfm>` → 得「主 grid 與每個子 grid」的 FIELD/欄序/寬/中文標題。
   - ⚠ **每個 grid（主檔 + 每個 Dq）都要做「dfm 欄位 × SQL select × 該 grid 的 gettext(`_Display`)」三方交叉核對**；子表的 `_Display` 欄位集看 `FormCreate` 各自的 `AddFieldEvent(Self, DqN, 'F1;F2;…', …)`，**不是只有主檔 `MqyGetText`**。詳見 `details/delphi-reading.md` Step 2.0/2.1。
4. **先找共用函式**：Delphi 參考函式先查 `Modules/FUNC` 是否已有 C# 共用函式，勿重寫 SQL（記憶 `reuse_func_modules`）。

## 已建範本骨架（漸進式揭露）

| 範本 | 大骨架檔 | 說明 |
|------|---------|------|
| ② 單檔 清單+彈窗 | `templates/single-file.md` | 已完成（A~J 全頁骨架＋指標） |
| ① 主檔明細 堆疊式 | `templates/master-detail.md` | 已落地（SAL021；堆疊式 + 明細膠囊切換） |
| ④ dropform 雙表穿梭 | `templates/dropform.md` | 由 SAL058 抽取（B工具列/C來源grid/D篩選/E目標grid InCell/F批量設定） |

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
| 遇到含業務規則的邏輯段（判斷落點：共用函式/計算/填值/DB） | `business-logic` |
| 欄位連動/計算 | `field-change` |
| 編輯表單/View | `edit-window` |
| 明細 InCell | `grid-incell` |
| CRUD/後端 | `crud-handlers`、`backend-sql`、`shared-functions` |
| DTO/顯示 | `dto-display` |
| 附件 PDF | `attachment` |
| 排版 CSS | `css-layout` |
| 上/下一筆 | `row-navigate` |
| 頁面殼/狀態/生命週期 | `page-shell` |
| 最後檢查（DFM×razor 三方比對） | `final-dfm-check` |

## 交付前檢查（所有範本適用）

0. **最後檢查 DFM × razor 三方比對（必做，見 `details/final-dfm-check.md`）**：頁面寫完後，用 `tools/dfm_audit.py`＋`tools/dfm_decode.py`＋TLabel `FocusControl`，把 razor 逐項對回 `.dfm`/`.pas` 權威——
   - **① 篩選區**：預設文字（DFM TLabel Caption，勿臆測簡化）、順序（`top,left` 由上到下由左到右）、FilterDblClick/Validate 規則、`Visible=False` 的篩選不顯示。
   - **② 明細切頁**：頁籤名稱與順序＝base `.dfm` TTabSheet Caption 與檔案順序。
   - **③ 主/明細欄位 × 顯示狀態**：`dfm_decode` 欄位/欄序 × SQL select × 各 grid `AddFieldEvent` 的 `MqyGetText/DqNGetText`（`GetNoDESCPT`→名稱、`GetKeyCodeDESCPT`→KeyCode 文字，缺 map 補 `DisplayTransformService.SAL.cs`）。
   > 繼承鏈頁面：篩選/頁籤對 **base `.dfm`**，grid 欄位對「子類覆寫 + base 未覆寫」。
1. **UI 編譯檢查（必做）**：razor 錯誤（如 EditorTemplate 回傳型別、型別錯配）常在 executor 只 build API 時未被發現，直到手動 build 才爆。交付前對 UI 做一次編譯掃描：
   ```
   dotnet build IKSERPUI.csproj -c Debug -v q -nologo 2>&1 \
     | grep -iE "error (CS|RZ)" | grep -viE "MSB3021|MSB3027|MSB3026"
   ```
   只看 `CS`/`RZ` 錯誤；`MSB3021/3027`（hot reload 檔案鎖）**不是**程式錯誤，忽略（勿因此硬 build，記憶 `no_build_running_app`）。掃出 0 筆才算過。
2. **存檔欄位對 Delphi**：`BuildXxxArgs` 的欄位**依 Delphi 該表單實際存的欄位為準**，不是後端 UPDATE 全欄、也不是畫面全欄（見 `details/crud-handlers.md`）。

<!-- 後續步驟（範本③ Excel 匯入、其餘 details 補齊）待與使用者逐步共構後補上 -->
