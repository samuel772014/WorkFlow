# 詳細規則：F. 上/下一筆導覽（IksUiFunc.NavigateGridAsync）

> 骨架指標來源：`templates/*` F 區。對應 Delphi：`RzDBNav` 巡覽列的上/下筆。
> **只出現在編輯畫面與詳細資料(View)畫面內**（Window/Edit Tab 右側導覽鈕），不放工具列（`details/toolbar.md`）。

---

## 共用函式（`IKSERPUI.iksUiFunc.IksUiFunc`，靜態、`_Imports` 已全域）

```csharp
Task<TItem?> IksUiFunc.NavigateGridAsync<TItem>(
    List<TItem>? gridData,        // grid 資料（用 {Grid}.GridData）
    TelerikGrid<TItem> gridRef,   // grid 參照（用 {Grid}.GridRef）
    TItem? current,               // 目前選取列
    string direction)             // "first" | "prev" | "next" | "last"
    where TItem : class, new();
```
- **回傳目標列**；已在邊界或 grid 無資料回 **`null`**（不移動）。
- 內部：`GetDisplayedList` 依 grid 目前 **sort/filter 取畫面實際顯示順序**（篩掉的列不進導覽路徑）→ `GetNavTarget` 算 index±1（邊界 null）→ 更新 grid 視覺選取（`SetStateAsync`）。
- 頁面收到回傳值後，**只需更新自身表單狀態**（grid 高亮已由函式處理）。

> `{Grid}.GridData`（`List<TItem>`）與 `{Grid}.GridRef`（`TelerikGrid<TItem>`）是 IksGrid_Virtual 的公開成員（見 `details/grid-virtual.md`）。

---

## 按鈕位置與啟用
- 放編輯/詳細 Window（或 master-detail Edit Tab）**右側**上（`prev`）/下（`next`）鈕。
- **`Enabled` 在 `Edit` 與 `View`（詳細）皆可**（單檔決策；`details/edit-window.md`）；`Add`/`query` 態停用。

---

## 【範例程式碼】(SAL001)
```razor
<TelerikButton FillMode="@ThemeConstants.Button.FillMode.Flat" Icon="@SvgIcon.ArrowUp"
               Enabled="@(pageStatus is \"Edit\" or \"View\")" OnClick="@(() => NavigateRow(\"prev\"))" title="上一列" />
<TelerikButton FillMode="@ThemeConstants.Button.FillMode.Flat" Icon="@SvgIcon.ArrowDown"
               Enabled="@(pageStatus is \"Edit\" or \"View\")" OnClick="@(() => NavigateRow(\"next\"))" title="下一列" />
```
```csharp
private async Task NavigateRow(string direction) {
    if (SAL001Mqy == null) return;
    var target = await IksUiFunc.NavigateGridAsync(SAL001Mqy.GridData, SAL001Mqy.GridRef, MqySelect, direction);
    if (target == null) return;                 // 邊界不移動
    MqySelect  = target;
    currentMqy = new Mqy { SALEREP = target.SALEREP, SARPNM = target.SARPNM, /* …複製顯示欄位… */ };
    await InvokeAsync(StateHasChanged);
}
```

## 【骨架程式碼】
```razor
<TelerikButton Icon="@SvgIcon.ArrowUp"   Enabled="@(pageStatus is \"Edit\" or \"View\")" OnClick="@(() => NavigateRow(\"prev\"))" title="上一列" />
<TelerikButton Icon="@SvgIcon.ArrowDown" Enabled="@(pageStatus is \"Edit\" or \"View\")" OnClick="@(() => NavigateRow(\"next\"))" title="下一列" />
```
```csharp
private async Task NavigateRow(string direction) {
    if ({{Grid}} == null) return;
    var target = await IksUiFunc.NavigateGridAsync({{Grid}}.GridData, {{Grid}}.GridRef, MqySelect, direction);
    if (target == null) return;
    MqySelect = target;
    current{{Master}} = new Mqy { /* 複製 target 顯示欄位到編輯表單 */ };
    // master-detail：切到該筆後還要重載明細（載明細 + Rebind，details/grid-incell.md）
    await InvokeAsync(StateHasChanged);
}
```

## 眉角
- 導覽順序**依畫面 sort/filter**，不是原始 GridData 順序——排序/篩選後上下筆走的是可見順序。
- `first`/`last` 也支援（跳首/尾筆），需要時直接傳。
- master-detail 導覽到新主檔後，記得**重載明細並顯式 `Rebind`**（否則殘留上一筆，`details/grid-incell.md`、記憶 `detail_rebind_add_save`）。
- 與 `OnRowFocus`（鍵盤上下鍵 focus 即選取）互補：清單態用 OnRowFocus，編輯/檢視態用 NavigateRow（`details/grid-virtual.md`）。

## 指路
- grid 公開成員/焦點 → `details/grid-virtual.md`
- 按鈕位置/啟用 → `details/toolbar.md`、`details/btn-control.md`
- 編輯/View 表單 → `details/edit-window.md`
