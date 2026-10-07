# 範本：dropform（雙表穿梭撥轉作業頁）

> **這是什麼**：一類**非 CRUD**的作業頁——「查詢候選 → 雙表穿梭挑選 → 批量設定 → 撥轉/轉單」。對應 Delphi `dropform`（對照表模式欄標記）。
> **藍本（權威參考頁）**：`SAL058 訂單撥轉採購單`（B407）。本範本從其定案版抽取；轉譯新 dropform 頁時比照。
> **與單檔/明細的差別**：沒有主檔明細關係、沒有編輯 Window、工具列不是 CRUD。核心是**兩個並列 grid**（來源候選 ↔ 目標待轉）＋穿梭鈕＋批量參數。
> **鐵則**：商業邏輯（金額/稅/匯率/取價/撥轉寫入）**一律走 API 共用函式**，UI 只做挑選與顯示（CLAUDE.md 鐵則1）。不確定的欄位/邏輯先查 Delphi 或問，不推測（鐵則4）。

---

## 何時用 dropform

來源 Delphi 是 `dropform`（非 `TfmEditForm`／非明細維護），畫面特徵：
- 上下（或左右）**兩個 grid**：上＝可轉的來源明細（唯讀、勾選），下＝已挑選待轉（少數欄可改）。
- 動作是**動詞**（顯示/查詢、清除、撥轉/轉單、搬上、搬下），不是新增/修改/刪除。
- 撥轉時可帶**批量參數**（指定供應商/幣別/需求部門…）。

→ 不符 → 回 `SKILL.md 步驟1` 重新判模式；若介於之間，**問轉譯操作者**。

---

## 區塊總覽（沿用區碼慣例；藍本 SAL058 即此分區）

| 區 | 內容 | 對應 Delphi | 重用 details |
|---|---|---|---|
| **B** | 工具列 Ribbon：查詢/清除 ‖ 撥轉（**無 CRUD**） | 動作按鈕 | `details/toolbar.md`（僅取 ribbon 寫法）、`btn-control.md`（Enabled 條件）|
| **C** | 上 grid（來源候選）：唯讀、`ShowCheckbox` 勾選多筆、frame-header 全選/取消/進階篩選 | 上 `DDBGrid`（cd） | `grid-virtual.md`／`grid-incell.md`（唯讀清單）、`multiselect-picker`（勾選穿梭） |
| **D** | 進階篩選 Popup（查詢條件） | 篩選欄位 | `popup-filter.md`、`input-component-choice.md` |
| **E** | 下 grid（目標待轉）：少數欄 InCell 可編＋連動重算；HeaderExtra 放穿梭鈕 | 下 `DDBGrid`（cd2）＋ Change 事件 | `grid-incell.md`、`field-change.md` |
| **F** | 批量設定 Popup（撥轉參數：供應商/幣別/需求部門） | 撥轉前選項（RadioGroup） | `popup-filter.md`（popup 外框）、`input-component-choice.md` |

> 兩 grid 各包 `.iks-master-frame`（`flex:0 0 auto`＋`height` 由 `OnHeightChanged` 回寫），外層 flex column body 可捲動（比照 MPS024/MPS034 版型；見 `iks-scroll-modes`）。

---

## B. 工具列（無 CRUD）

```razor
<div class="toolbar toolbar-field">
    <Toolbar OnAction="HandleToolbar">
        <ToolbarGroup>
            <ToolbarButton Action="Query" Enabled="@(!_processing)" FontIcon="ti ti-search" Title="顯示" />
            <ToolbarButton Action="Clear" Enabled="@(!_processing)" FontIcon="ti ti-trash"  Title="清除" />
        </ToolbarGroup>
        <ToolbarGroup>
            @* 撥轉：目標表有資料且非處理中才可按 *@
            <ToolbarButton Action="Transfer" Enabled="@(_cd2Data.Count > 0 && !_processing)" FontIcon="ti ti-transfer-in" Title="確認撥轉" />
        </ToolbarGroup>
    </Toolbar>
</div>
```
- `_processing` 旗標貫穿全頁（第二顆 `TelerikLoaderContainer Text="處理中…"`）；查詢/撥轉時鎖鈕。
- 純圖示＋`Title`＋`TelerikTooltip`（同 ribbon 慣例）。

## C. 上 grid（來源候選，唯讀勾選）

```razor
<div class="iks-master-frame" style="flex:0 0 auto; height:@_cdHeight;">
  <div class="iks-master-grid">
    <IksGrid_vnq @ref="_cdGrid" TItem="CdRow" GridData="@_cdData" Table_Name="XXXcd"
                 ApiUrl="@_url" Columns="_cdColumns"
                 ShowAdd="false" ShowBuiltInToolbar="false" ShowFrameHeader="true"
                 ShowCheckbox="true" ShowSelectAll="false" HeaderButtons="@_cdHeaderButtons"
                 OnRowClick="OnCdRowClick"
                 OnRowDoubleClick="@(async (GridRowClickEventArgs a) => await TransferDownAsync(new List<CdRow>{ (CdRow)a.Item }))"
                 OnHeightChanged="@((string h) => _cdHeight = h)" Height="100%" />
  </div>
</div>
```
- `HeaderButtons`：全選 / 取消全選（`OnCdSelectAll` / `OnCdClearSelection`）＋進階篩選鈕（錨 `.xxx-filter-popup-target`）。
- 雙擊列＝單筆搬下（快捷）。

## E. 下 grid（目標待轉，InCell 可編＋連動）

```razor
<div class="iks-master-frame" style="flex:0 0 auto; height:@_cd2Height;">
  <div class="iks-master-grid">
    <IksGrid_vnq @ref="_cd2Grid" TItem="Cd2Row" GridData="@_cd2Data" Table_Name="XXXcd2"
                 ApiUrl="@_url" Columns="_cd2Columns"
                 ShowAdd="false" ShowBuiltInToolbar="false" ShowFrameHeader="true"
                 ShowCheckbox="true" ShowSelectAll="false" HeaderButtons="@_cd2HeaderButtons"
                 OnRowClick="OnCd2RowClick" OnHeightChanged="@((string h) => _cd2Height = h)" Height="100%">
      <HeaderExtra>
        <button class="iks-fbtn primary iks-transfer-down" title="搬下選取" disabled="@_processing" @onclick="ShuttleDown"><i class="ti ti-chevron-down"></i></button>
        <button class="iks-fbtn iks-transfer-up"   title="搬上選取" disabled="@_processing" @onclick="ShuttleUp"><i class="ti ti-chevron-up"></i></button>
      </HeaderExtra>
    </IksGrid_vnq>
  </div>
</div>
```
- 可編欄（如數量/換算率/單價/含稅單價）用 `EditorTemplate` 內 `TelerikNumericTextBox`＋`ValueChanged`→`OnXxxChanged(row, v)`；**計算一律送後端**重算金額（`RecalcCd2MnyAsync` → API 共用函式，如 `CalcuMnyTax`/`GetNUp`/`Get_MRATE`）。見 `details/field-change.md`。
- **永遠不可編欄**在 `GridColumnConfig` 設 `Editable=false`（PK/計算欄/顯示欄）；不寫整表鎖欄樣板。

## 穿梭 / 撥轉邏輯（樣式，非商業規則）

| 方法 | 職責 |
|---|---|
| `ShuttleDown` / `ShuttleUp` | 取勾選列 → 呼 `TransferDownAsync` / `TransferUpAsync`（搬移 cd↔cd2；套 F 批量參數） |
| `TransferDownAsync(rows)` | 逐列 `CdToCd2`：**帶批量參數打後端**取供應商/幣別/取價/稅額 → 加進 `_cd2Data` |
| `TransferAsync`（撥轉） | 目標表整批**送後端寫採購單**（共用撥轉函式）；成功後清表、回報結果 |
| `RecalcCd2MnyAsync(row)` | InCell 改值 → 送後端重算 MNY/TMNY |

> 撥轉寫入、取價、稅額、匯率 **一律後端共用函式**；前端只組參數與顯示（鐵則1）。查得到就重用、查不到標 `[封裝商業邏輯]`（`details/shared-functions.md`），不自行重寫。

## D/F. 兩個 Popup

- 結構同 `details/popup-filter.md`（`iks-filter-popup` 外框、`@ref`+`Reset()` 清除、必填不清）。
- **D 進階篩選**：查詢條件（部門/業務/訂單別/客戶/受訂單號 EditPick 連動/料號範圍/只顯示採購件 checkbox）。
- **F 批量設定**：撥轉參數（供應商 radio「主供應商/指定」、幣別 radio、需求部門必填）；`fieldset.iks-radio-group`＋`IksCodeComboBox`（指定時才 Enabled）。**radio 預設值以 Delphi 為準**（SAL058：指定供應商、依供應商幣別）。

## DTO

- `CdRow` / `Cd2Row`：`class Xxx : IDisplayResolvable`，**inline 宣告在 @code、不共用**（`dto-display.md`）。dropform 常是跨表組合查詢結果、未必對單一 EF Model → 屬「特殊情況」時照實建、必要時問。

---

## 對照 acceptance-criteria（dropform 版調整）

- **無 S4（新增/編輯/刪除 handler）**：改檢查「查詢/清除/穿梭/撥轉」動作齊備。
- **S2 欄位/欄序**：兩 grid 各依 Delphi 兩個 `DDBGrid` 的欄位（cd 唯讀清單、cd2 可編集合）。
- **S6 輸入元件**：批量/篩選走決策樹；cd2 可編欄 InCell。
- 其餘（S1 路由標題、S9 標題＝對照表名、_Display 接上）照舊。

> **本範本為方法論擴充（經使用者核可，2026-XX 由 SAL058 抽取）**。新 dropform 頁若出現藍本未涵蓋的結構 → 標特例、問，不自行設計。
