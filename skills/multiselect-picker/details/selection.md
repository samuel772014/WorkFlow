# 選取行為（selection）

多選選擇器的選取是最容易踩雷的地方，因為 `IksGrid_vnq` 是 **`EditMode=Incell`**。

## 核心規則

1. **點列身不觸發 native 選取** → 靠 `SelectedItems` 變動的 `OnSelect` 在點列時**不會發**（只有點「選取欄 checkbox」才發）。所以「點列即選取」**一律用 `OnRowClick`**（不受 InCell 影響，一定會發）。
2. 因 InCell 下點列不做 native 取代選取，`OnRowClick` 內可**直接 toggle `_grid.SelectedItems`**（不需影子清單），與 checkbox 共用同一份選取集合。
3. **欄位 checkbox 是 native 單筆 toggle，不支援 Shift 範圍**；頁面攔不到它的點擊、也拿不到 Shift 鍵。→ 要 Shift 連續多選只能在**列身**上點。
4. **Shift 區間自己做**：`args.EventArgs as MouseEventArgs` 讀 `ShiftKey`，記錄「錨點」（上一次非 Shift 點的列），用**本地清單 index** 算 `GetRange` union 進選取。**不受虛擬捲動限制**（Telerik 原生 Shift 只涵蓋已渲染列，自己算就整包都能選）。

## 標準 handler

```csharp
private PickRow? _anchor;

private async Task OnRowClick(GridRowClickEventArgs args)
{
    if (_grid == null || args.Item is not PickRow row) return;
    var set = _grid.SelectedItems?.ToList() ?? new List<PickRow>();
    bool shift = (args.EventArgs as MouseEventArgs)?.ShiftKey == true;
    int anchorIdx = _anchor != null ? _data.IndexOf(_anchor) : -1;
    int curIdx = _data.IndexOf(row);

    if (shift && anchorIdx >= 0 && curIdx >= 0)
    {
        var range = _data.GetRange(Math.Min(anchorIdx, curIdx), Math.Abs(anchorIdx - curIdx) + 1);
        foreach (var r in range) if (!set.Contains(r)) set.Add(r);   // union 併入，不清現有
        // Shift 不更新錨點，維持原錨點供連續延伸
    }
    else
    {
        if (!set.Remove(row)) set.Add(row);   // toggle：已選→取消、未選→加入
        _anchor = row;                         // 非 Shift 才設錨點
    }
    _grid.SelectedItems = set;
    await InvokeAsync(StateHasChanged);
}
```

- 需 `@using Microsoft.AspNetCore.Components.Web`（`MouseEventArgs`；多半 _Imports 已全域匯入）。
- 全選/取消全選走 frame-header `HeaderButtons` → `_grid.SelectAll()` / `_grid.ClearSelection()`。
- 重新查詢/rebind 後把 `_anchor = null`（避免指向已不存在的列；`IndexOf` 回 -1 也會自動退回單列 toggle）。
- `List.Remove`/`Contains`/`IndexOf` 走參考相等；`args.Item` 與 `_data`/`SelectedItems` 是同一批實例，比對沒問題。

> 對應記憶：`reference_vnq_incell_row_selection`。

## 批次帶值 / 清除篩選 時的選取保留

批次選取頁常有一個「批次帶值欄」（結案原因 CLOSETP、指定專案代號 PJID…）+「整批設定」鈕：把該欄值套進所有選取列。兩條必守規則：

1. **整批設定後維持原本勾選** → 套完值重繪一律用 **`RebindKeepState(_data)`，不要用 `Rebind(_data)`**。
   `Rebind` 會把 `SelectedItems` 清空（見 `details/grid.md`）→ 使用者剛挑好的列被清掉；`RebindKeepState` 會保留選取集合，同時讓 `_Display` 重新解析。
   ```csharp
   foreach (var r in _grid.SelectedItems) if (string.IsNullOrWhiteSpace(r.XXX)) r.XXX = _batchValue.Trim();
   if (_grid != null) await _grid.RebindKeepState(_data);   // ✅ 保留勾選；❌ 勿用 Rebind
   ```
   ⚠ 例外：**重新「查詢」載入新資料**時本就該 `Rebind`（清掉舊選取，資料換了）——別把這條誤套到查詢。

2. **「清除篩選」不可清掉批次帶值欄** → 批次帶值欄是「動作用值」**不是查詢條件**，`ClearFilter` 必須跳過它：
   - **不要**呼叫它的 combo `.Reset()`；
   - 重建 filter 物件時**保留**它的值（先存起來再帶回）。
   ```csharp
   private void ClearFilter()
   {
       string keepBatch = _f.XXX;                       // 批次帶值欄先留著
       _f = new Filter { /*…其他預設…*/ XXX = keepBatch };  // 重建時帶回
       _otherCombo?.Reset();                            // 只 Reset 真正的查詢欄
       // ❌ 不要 _batchCombo?.Reset();
   }
   ```

> 範例：SAL059（訂單結案，結案原因 CLOSETP + 整批設定）。
