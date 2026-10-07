# 詳細規則：D. 進階篩選 Popup

> 骨架指標來源：`templates/single-file.md`、`templates/master-detail.md` D 區。
> **IKSERP 篩選統一規範**：篩選欄位一律放 `TelerikPopup`，不用展開/收合、不用常駐 `filter-field`。
> 來源：舊 skill `popup-filter` 彙整（對齊新 UI `iks-filter-popup` 外框）。

---

## 結構（新 UI）

1. **Grid 端**開篩選鈕：`ShowFilterButton="true"` + `OnFilterClick="ToggleFilterPopup"` + `FilterAnchorClass="xxx-filter-popup-target"`（或用 `GridToolBar` 放 `<TelerikButton Class="popup-target">`）。
2. **Popup 端**：`<TelerikPopup AnchorSelector=".xxx-filter-popup-target">` 對齊同一 class，內含 `iks-filter-popup`（head 標題+關閉 / body `iks-filter-grid` 篩選欄位 / actions 清除+查詢）。
3. **Popup 必須在 Grid 元件外部**（同層或其後），不可放 `GridToolBar` 內。多 Popup 用不同 class 區分。

**Width 建議**：欄位組數 × ~430px（2 組→860、3 組→1300）。篩選欄位排版見 `details/css-layout.md`（`iks-filter-grid`/`iks-filter-row` 整包寫法）。

---

## ⚠️ 核心陷阱：清除要各控件 `@ref` + `Reset()`

**`TelerikPopup` 開啟後內容固定渲染**，父頁 `StateHasChanged()` / `FilterPopupRef.Refresh()` **都不重繪 popup 子樹** → `Filter = new()` 後畫面殘留（記憶 `telerikpopup_refresh`）。

**唯一可靠解**：popup 內**每個篩選控件**都 `@ref`，清除時呼叫各自 `Reset()`（控件內部對自身 `StateHasChanged`，繞過不重繪）。

| 控件 | 清空方式 |
|------|----------|
| `IksTextBox` / `IksCodeComboBox` / `KeyCodeComboBox` / `EditPick` | `@ref` + `Reset()`（已內建；EditPick 另清 Keyword 欄位） |
| 原生 `TelerikDatePicker` | 無 Reset()：`@ref` + 綁定值設 null 後 `.Refresh()`（型別 `TelerikDatePicker<DateTime?>?`） |
| 原生 `TelerikTextBox`/`TelerikCheckBox`/`TelerikNumericTextBox` | **一律先轉 Iks 包裝**（IksTextBox/IksCheckBox/IksNumericTextBox）再 `@ref`+`Reset()`／`SetValue()`（這三個原生無自我重繪 API，`.Refresh()` 會 CS1061） |

> **markup 不寫 `@key`**（popup 內 @key 靠父層重繪才生效，無效；整體重建會閃）。非必填但預設有值的欄位清除後用 `SetValue(預設)` 帶回。

---

## ⚠️ 清除只清「非必填」欄位，必填欄位不動

「清除」語意 = 回到**可查詢的初始狀態**，**不是全空**。**必填欄位（`IksLabel Required="true"`）清除時保留現值不動**，只清非必填欄位；否則清除後直接查詢會撞必填驗證。

- **禁用 `Filter = new()`**：它會把必填欄位一起洗掉。改成**逐一**把非必填欄位設 `null`／預設，必填欄位完全不碰。
- **控件對應**：只有**非必填**控件才 `@ref` + `Reset()`；必填控件清除時**不呼叫 `Reset()`**（呼叫了就清空了）。
- 必填欄位若有預設語意（如單況預設 `OP`），維持現值即可，**不需 `SetValue(預設)` 帶回**（因為根本沒清它）。

```csharp
private void ClearFilter()
{
    // 只清非必填欄位；必填欄位（Required=true）保留現值不動，勿用 Filter = new()
    Filter.{{非必填F}} = null;   _{{非必填f}}Ctrl?.Reset();   // 每個「非必填」欄位補一行
    // 必填欄位與其控件一律不碰
}
```

---

## 【範例程式碼】(SAL001，2 欄)
```razor
@* Grid 端 *@
<IksGrid_Virtual ... ShowFilterButton="true" OnFilterClick="ToggleFilterPopup"
                 FilterAnchorClass="mqy-filter-popup-target" />
@* Popup 端 *@
<TelerikPopup @ref="@FilterPopupRef" AnchorSelector=".mqy-filter-popup-target"
              AnimationType="@AnimationType.SlideDown" AnimationDuration="160" Width="900px">
  <div class="iks-filter-popup" aria-label="進階篩選">
    <div class="iks-filter-popup-head">
      <span class="iks-filter-popup-title">進階篩選</span>
      <button class="iks-fbtn ghost iks-filter-close" @onclick="ToggleFilterPopup" title="關閉篩選"><i class="ti ti-circle-x"></i></button>
    </div>
    <div class="iks-filter-popup-body">
      <div class="iks-filter-grid">
        <div class="iks-filter-row">
          <IksLabel Key="Lb_F_Salerep" DefaultText="業務人員" />
          <IksCodeComboBox @ref="_salerepCombo" @bind-Value="@MqyFilter.SALEREP" _url="@_url" module="SAL" comboBoxCode="SalerepComoBox" />
        </div>
      </div>
    </div>
    <div class="iks-filter-popup-actions">
      <button class="iks-fbtn" @onclick="ClearFilter"><i class="ti ti-trash"></i>清除</button>
      <button class="iks-fbtn primary" @onclick="ApplyFilter"><i class="ti ti-search"></i>查詢</button>
    </div>
  </div>
</TelerikPopup>
```
```csharp
private TelerikPopup? FilterPopupRef; private bool _filterPopupVisible = false;
private IksCodeComboBox? _salerepCombo;   // 每個篩選控件一個 @ref
private void ToggleFilterPopup() { _filterPopupVisible = !_filterPopupVisible; if (_filterPopupVisible) FilterPopupRef?.Show(); else FilterPopupRef?.Hide(); }
// 本例無必填欄位，故可 MqyFilter = new()；若有必填欄位改逐欄清（見上方「清除只清非必填」規則）
private void ClearFilter()  { MqyFilter = new(); _salerepCombo?.Reset(); /* 每個控件 Reset() */ }
private async Task ApplyFilter() { await Query(); _filterPopupVisible = false; FilterPopupRef?.Hide(); }
```

## 【骨架程式碼】
```razor
<TelerikPopup @ref="@FilterPopupRef" AnchorSelector=".{{grid}}-filter-popup-target" Width="{{組數×430}}px">
  <div class="iks-filter-popup">
    <div class="iks-filter-popup-head"><span class="iks-filter-popup-title">進階篩選</span>
      <button class="iks-fbtn ghost" @onclick="ToggleFilterPopup"><i class="ti ti-circle-x"></i></button></div>
    <div class="iks-filter-popup-body"><div class="iks-filter-grid">
      @* 每個篩選欄位一列；控件過 input-component-choice 決策；每個都 @ref 供 Reset() *@
      <div class="iks-filter-row"><IksLabel Key="Lb_F_{{F}}" DefaultText="{{中文}}" />
        <{{控件}} @ref="_{{f}}Ctrl" @bind-Value="@Filter.{{F}}" ... /></div>
    </div></div>
    <div class="iks-filter-popup-actions">
      <button class="iks-fbtn" @onclick="ClearFilter"><i class="ti ti-trash"></i>清除</button>
      <button class="iks-fbtn primary" @onclick="ApplyFilter"><i class="ti ti-search"></i>查詢</button>
    </div>
  </div>
</TelerikPopup>
```
```csharp
// 清除只清「非必填」欄位；必填欄位（Required=true）保留現值不動，勿用 Filter = new()
private void ClearFilter() { Filter.{{非必填F}} = null; _{{非必填f}}Ctrl?.Reset(); /* 每個「非必填」欄位補一行；必填欄位不碰 */ }
private async Task ApplyFilter() { await Query(); _filterPopupVisible = false; FilterPopupRef?.Hide(); }
```

## ⚠️ 勿與「明細顯示設定」混用

讀 Delphi 畫面時若遇到 **checkbox（RzCheckBox / CheckBox）**，先判斷它改的是什麼：

| 特徵 | 歸屬 |
|------|------|
| 改變 SQL WHERE 條件（需重新查詢才有效） | 進階篩選 → 本文件 |
| 只影響前端顯示（UI show/hide）或批次動作參數，**勾選即時生效、不需重查** | 明細顯示設定 → `details/detail-display-settings.md` |

典型「明細顯示設定」範例：「顯示虛階或零需求料品」「顯示備料明細」「更新待確認製令用料」。這類 checkbox **不放進進階篩選 Popup**，改用 `popup-target-detail` 錨點的獨立 Popup，且不含清除/查詢動作按鈕。

---

## 指路
- 篩選欄位控件選擇 → `details/input-component-choice.md`；用法 → `details/shared-input-components.md`
- 排版 class（iks-filter-grid/row）→ `details/css-layout.md`
- 連動（如 OBJTP→CUSTMER 的 Args）→ `details/field-change.md`
- checkbox 類顯示/動作開關 → `details/detail-display-settings.md`
