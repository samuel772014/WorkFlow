---
name: popup-window
description: 建立 IKSERP Blazor「彈出視窗子元件」的骨架與規則。當使用者說「建立彈出視窗」「做一個 popup」「做一個 SAL0XXA/B 子視窗」，或需要在 TelerikWindow 內嵌的子元件（非獨立頁面）時觸發。以 SAL055A（純編輯型）/ SAL046D（查詢型）為藍本。
---

# IKSERP 彈出視窗子元件（Popup Window Component）

> 「彈出視窗子元件」= 被 `TelerikWindow` 包裹、透過 `OnCancel`/`OnConfirm`/`OnClose` 與呼叫端溝通的 Razor 子元件（`.razor`，非獨立 `@page`）。

## 何時用 / 何時不用

- ✅ **用**：從主頁或明細 Grid 列指令開啟一個輔助視窗（套件明細、客供品、期款設定、裝櫃量查詢…）。
- ❌ **不用**：
  - 獨立瀏覽頁面（有 `@page` 路由）→ 走 `page-migration`。
  - 多選挑料號/客戶等通用清單選擇器 → 走 `multiselect-picker`。

---

## 三種版型

| 版型 | 特徵 | 參考頁 |
|------|------|--------|
| **A - 純編輯型** | 唯讀表頭 + Grid，無查詢工具列 | SAL055A |
| **B - 查詢型（內嵌篩選）** | 工具列 Query + inline `iks-filter-grid`，篩選欄不多 | SAL046D |

---

## 鐵則（所有版型共用）

### 動作鈕位置

```
存檔 / 套用 / 確認 / 取消 → <div class="iks-edit-actions">（固定在底部）
查詢                       → <Toolbar> 工具列（頂部，版型 B 才有）
```

⚠ **存檔/執行與查詢絕對不共存同一列**——查詢只在有主動觸發查詢的版型（B）出現。

### Grid 進階篩選

- 有篩選欄位 → 使用popup：`ShowFilterButton="true"` + `TelerikPopup`（規則見 `details/popup-filter.md`）。

### 全選 / 取消全選

- 有 Checkbox 多選需求時，**一律放 Grid `HeaderButtons`**（frameheader 區），不放底部動作列。

```csharp
private List<IksGridHeaderButton> _headerButtons => new()
{
    new() { Text = "全選",     Icon = "ti ti-checks",       OnClick = SelectAllAsync },
    new() { Text = "取消全選", Icon = "ti ti-square",        OnClick = ClearSelectAsync },
};
```

### TelerikWindow 呼叫端

- 一律 `@bind-Visible` + `<WindowActions><WindowAction Name="Close" /></WindowActions>`（內建 X 鈕，不自訂 OnClick）。
- 子元件的 `OnCancel`/`OnClose` 接 `@(() => _xxxVisible = false)`。

---

## 版型 A 骨架（純編輯型，SAL055A 藍本）

完整範本見 `templates/type-a.md`。

```
iks-edit-window (padding:8px)
├── iks-edit-body (flex column, gap:6px)
│   ├── iks-edit-subhead「表頭標題」
│   ├── iks-edit-grid (max-width:100%)   ← 唯讀表頭欄位
│   ├── iks-edit-subhead「明細標題」
│   └── div (flex:1 1 auto; min-height:0)
│       └── IksGrid_vnq Height="100%"
└── iks-edit-actions
    └── [存檔] [取消]
```

重點：
- `iks-edit-grid` 加 `max-width:100%`，防止彈窗產生橫向 scrollbar。
- Grid wrapper `flex:1 1 auto; min-height:0` 讓 grid 撐滿剩餘高度。
- `IksGrid_vnq` 設 `Height="100%"` 自行管理內部捲動。

---

## 版型 B 骨架（查詢型 inline 篩選，SAL046D 藍本）

完整範本見 `templates/type-b.md`。

```
iks-edit-window (padding:8px)
├── toolbar toolbar-field (flex-shrink:0)  ← 查詢工具列
│   └── Toolbar > ToolbarButton Action="Query"
├── iks-edit-body (flex column, gap:6px)
│   ├── iks-filter-grid                   ← inline 篩選（≤2 欄）
│   └── div (flex:1 1 auto; min-height:0)
│       └── IksGrid_vnq Height="100%"
│           ShowCheckbox / ShowSelectAll="false"
│           HeaderButtons（全選/取消全選）
└── iks-edit-actions
    └── [套用/確認] [取消]
```

---

#

## @code 宣告位置

```csharp
// ── Parameters ───────────────────────────────────────────────────
[Parameter] public string?  KEY_FIELD { get; set; }    // 篩選主鍵
[Parameter] public EventCallback OnCancel  { get; set; }   // 取消/關閉
[Parameter] public EventCallback OnConfirm { get; set; }   // 確認帶回（若有）

protected override string FomId => "SAL0XX";           // 頁面權限代號（同主頁）

// ── Refs & State ────────────────────────────────────────────────
private MessageBox MsgBox = default!;
private string _url => iksService.ApiUrl;
private IksGrid_vnq<TItem>? _grid;
private List<TItem> _rows = new();
private bool _saving = false;

// 版型 B：篩選
private TelerikPopup? FilterPopupRef;                  // Popup使用
private bool _filterPopupVisible = false;              // Popup使用
private MyFilter _filter = new();

// ── Columns ─────────────────────────────────────────────────────
private Dictionary<string, GridColumnConfig> _columns => new() { ... };

// ── Lifecycle ────────────────────────────────────────────────────
protected override async Task OnInitializedAsync() { await LoadAsync(); }
protected override async Task OnAfterRenderAsync(bool firstRender)
{
    await base.OnAfterRenderAsync(firstRender);
    if (firstRender && _grid != null) await _grid.Rebind(_rows);
}
```

---

## details 索引

| 需求 | 檔 |
|------|----|
| 進階篩選 Popup 完整規則（含 Reset 陷阱） | `details/popup-filter.md`（page-migration skill） |
| Grid 欄寬 / Rebind | `details/grid-incell.md` |
| 輸入控件選擇 | `details/input-component-choice.md` |
| 呼叫端 TelerikWindow 接線 | 本文「TelerikWindow 呼叫端」段落 |
