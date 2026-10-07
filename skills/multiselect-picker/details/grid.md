# Grid 欄寬 / Rebind 眉角

## IksGrid_vnq 對外參數（picker 用）

| 參數 | picker 值 | 說明 |
|------|-----------|------|
| `TItem` | DTO | 清單型別 |
| `GridData` | `@_data` | 本地清單（picker 一次全撈） |
| `Table_Name` | 唯一字串 | 欄位設定存檔 key（每個 picker 要不同） |
| `ShowCheckbox` | `true` | 顯示選取欄 |
| `ShowSelectAll` | `false` | **隱藏表頭全選**：虛擬捲動下表頭全選只勾渲染列、會誤導；改用 frame-header 自訂全選鈕 |
| `ShowFrameHeader` | `true` | 顯示 frame-header（放 HeaderButtons、筆數） |
| `HeaderButtons` | 全選/取消 | 呼叫 `SelectAll()`/`ClearSelection()`（選全部資料，非只渲染列） |
| `OnRowClick` | handler | 選取（見 `selection.md`） |
| `Height` | 如 `360px` | 固定高 |

## 欄寬異常 → 用無參數 `Rebind()`

- **無參數 `Rebind()`**：把 `firstLoad=true`，下次 `OnRead` 會重跑 `GetTableSetting()` → **重新載入欄位設定（含 ColWidth 欄寬）**。**自動欄寬異常 / 欄位設定沒套用時用它。**
- **`Rebind(List, keepScrollTop)`**：只換 `GridData` 資料，**不重載欄位設定**。
- ⚠ 「rebind 兩次 + Task.Delay」救不了欄寬（因為 `Rebind(list)` 根本不重載設定）。
- 用法：資料先設好（`GridData` 綁的清單）並 `StateHasChanged` 推給 grid，再呼叫無參數 `Rebind()`。

```csharp
_data = await LoadFromApi();
await InvokeAsync(StateHasChanged);      // 先把 _data 推給 GridData 參數
if (_grid != null) await _grid.Rebind(); // 重載欄寬
```

## 虛擬捲動殘留

資料由多變少時（重查/移除），rebind 帶 `keepScrollTop: true`，重讀前先把捲動歸零，避免「捲軸還在但沒資料、上方補空骨架」。純 picker 每次重查用 `Rebind(_data, keepScrollTop: true)` 或無參數 `Rebind()` 皆可視情況。

> 對應記憶：`reference_vnq_rebind_reload_colwidth`、`reference_grid_virtual_scroll_reset`、`reference_vnq_no_oncheckboxchange`。
