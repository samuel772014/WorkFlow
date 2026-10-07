# 詳細規則：G. 按鈕控制 btnControl

> 骨架指標來源：`templates/single-file.md`、`templates/master-detail.md` G 區。
> 對應 Delphi：`ToggleControl`（各狀態按鈕啟用/停用）。
> 來源：舊 skill `btn-control` 彙整 + 本專案 dry-run 規則（單檔 View、明細雙態）。

---

## 通則
- **`btnControl()` 只設 bool 旗標，不呼叫 `StateHasChanged`**（由外層統一觸發重繪）。
- **統一在 `HandleToolbar` 末尾呼叫** `btnControl()`。
- 額外呼叫時機：
  | 時機 | 模式 | 說明 |
  |------|------|------|
  | 開編輯窗/Tab 後（Add/Edit/OnRowEdit/詳細資料） | 全 | 鎖定/更新旗標 |
  | 關窗（X）/Cancel | 全 | 解鎖 |
  | 選取列 OnMqyRowClick | 明細 | 依 STATUS 更新 Copy/Edit 可用 |
  | Save 成功後（回 query） | 全 | 解鎖 |
  | OnRowDelete（不開窗、不改 pageStatus） | 單檔 | **不呼叫** |
- **沒有的按鈕就不宣告對應旗標**，不留佔位符。
- **業務條件**：明細常帶單況條件，如 `_EditEnabled = MqySelect?.STATUS == "OP"`。
- `Edit()` 若先檢查選取失敗（`MqySelect == null`）直接 return，**不呼叫 btnControl()**。

---

## 模式一：單檔 清單+彈窗（single-file）

**旗標**（工具列只 新增/查詢；修改/刪除/詳細資料在 grid 指令欄，靠 `_formReadonly`/pageStatus 控制）
```csharp
private bool _AddEnabled   = true;
private bool _QueryEnabled = true;
```
**btnControl**
```csharp
private async Task btnControl() {
    switch (pageStatus) {
        case "Add": case "Edit": case "View":   // 開窗態
            _AddEnabled = false; _QueryEnabled = false; break;
        default:                                  // "query"
            _AddEnabled = true;  _QueryEnabled = true;  break;
    }
    await Task.CompletedTask;
}
```
> View（詳細資料）＝重用編輯窗唯讀（`_formReadonly => pageStatus=="View"`，隱藏存檔）；上/下一筆在 Edit+View 皆可（見 `details/edit-window.md`）。

---

## 模式二：主檔明細（master-detail）

**旗標**（完整；模式膠囊 Read=瀏覽/DetailRead=表單）
```csharp
private bool _ReadEnabled, _DetailReadEnabled, _AddEnabled, _CopyEnabled,
             _EditEnabled, _SaveEnabled, _CancelEnabled, _QueryEnabled;
private bool _dqEditEnabled => pageStatus is "Add" or "Edit";   // 明細 grid 編輯鎖定
```
**btnControl（pageStatus × ActiveTabId 雙態）**
```csharp
private async Task btnControl() {
    bool editing = pageStatus is "Add" or "Edit";
    // 模式膠囊：編輯中不可切換模式
    _ReadEnabled       = !editing;                 // 切到瀏覽(query)
    _DetailReadEnabled = !editing;                 // 切到表單(edit)
    // CRUD
    _AddEnabled    = !editing;
    _CopyEnabled   = !editing && MqySelect != null;
    _EditEnabled   = !editing && MqySelect != null && MqySelect.STATUS == "OP";  // 業務條件
    _SaveEnabled   = editing;
    _CancelEnabled = editing;
    _QueryEnabled  = !editing;
    await Task.CompletedTask;
}
```
> `ActiveTabId`(query/edit) 由 `HandleToolbar("Read"/"DetailRead")` 切；明細列指令與「+」新增鈕 `Enabled` 綁 `_dqEditEnabled`（query/瀏覽態鎖定，見 `details/grid-incell.md`）。

---

## 【骨架程式碼】

```csharp
@* 旗標：只宣告本頁有的按鈕 *@
private bool _AddEnabled = true, _QueryEnabled = true /*, …依模式增*/;

private async Task btnControl() {
    bool editing = pageStatus is "Add" or "Edit";   // (View 視需要併入開窗態)
    // {{依模式設各旗標；明細帶業務條件如 STATUS=="OP"}}
    await Task.CompletedTask;
}

private async Task HandleToolbar(string action) {
    await (action switch { "Add" => Add(), "Query" => Query(), /*…*/ _ => Task.CompletedTask });
    await btnControl();   // 末尾統一呼叫
}
```

---

## B101 / B301 對應
- Delphi `ToggleControl` → `btnControl()`（狀態驅動旗標）。
- 單檔 B101：只 新增/查詢兩顆需控。
- 明細 B301：完整按鈕 + 模式膠囊；`_EditEnabled` 等帶單況業務條件（`STATUS`）。

## 指路
- 工具列/按鈕位置 → `details/toolbar.md`
- 明細編輯鎖定 `_dqEditEnabled` → `details/grid-incell.md`
- View 唯讀 → `details/edit-window.md`
