# 詳細規則：C. 主檔清單 Grid（IksGrid_Virtual）＋ 鍵盤控制 / OnRowFocus

> 骨架指標來源：`templates/*` C 區（主檔清單）。
> 對應 Delphi：`MDBGrid`（主表瀏覽）。可編輯明細用 `IksGrid_vnq` → `details/grid-incell.md`。
> **RowKeyField + OnRowFocus 鍵盤機制四個 grid 共用**（IksGrid_Virtual / IksGrid_vnq / IksGrid_nq / IksGridview）。

---

## 參數一覽（IksGrid_Virtual）

**資料來源**
| 參數 | 說明 |
|------|------|
| `ApiName` | 查詢 endpoint（如 `{form}_M_Query`）；伺服器端分頁 |
| `ApiUrl` | `@_url` |
| `Table_Name` | grid 識別名（欄位設定 key、focus zone 前綴） |
| `Columns` | `Dictionary<string, GridColumnConfig>`（Field/Title/Width/Order/Editable） |
| `WhereParameters` | `Dictionary<string,object>` 查詢條件；改後 `Rebind()` |
| `sortKey` / `PageSize` / `Height` | 排序欄 / 每頁筆數 / 高度（frame 內用 `100%`） |

**frame-header / 工具列**（新 UI）
| 參數 | 說明 |
|------|------|
| `ShowFrameHeader="true"` | 啟用內建 frame-header（欄位/筆數/自訂鈕） |
| `ShowFilterButton="true"` + `OnFilterClick` + `FilterAnchorClass` | 進階篩選鈕（→ `details/popup-filter.md`） |
| `FilterActive` / `FilterButtonText` | 篩選啟用態 / 鈕文字 |
| `ShowAddButton` + `AddButtonEnabled` | 「+」新增列（明細用；綁 `_dqEditEnabled`） |
| `HeaderButtons` | `List<IksGridHeaderButton>`（整批操作鈕，Text/Icon/Enabled/OnClick） |
| `FrameHeaderExtra` | `RenderFragment`：頁面自訂的 **非按鈕** header 內容（渲染在 HeaderButtons 之後、`iks-fspacer`＋筆數之前）。用途＝**唯讀合計 / 狀態標記**（見下節）。`IksGrid_vnq` **沒有**此參數 |
| `ShowBuiltInToolbar`(預設true) / `ShowAdd` / `ShowToolbar` | 舊內建工具列/新增（`<GridToolBarTemplate>` 那條 table）。**用新 frame-header 時一律 `ShowBuiltInToolbar="false"`** 關掉舊工具列，否則新舊並存 |
| `OnHeightChanged` | frame-header「設定高度」combo 選值時回拋新高度給頁面（master-detail 主檔用：handler 寫進 `_mqyHeight`→frame 高度）。未綁時 combo 改 grid 自身 `_gridHeight` |
| `LeftColumnsTool` | 自訂欄（`GridCommandColumn` 修改/刪除/詳細） |
| `GridToolBar` | 自訂 grid 工具列（另一種放篩選鈕的位置） |

> **frame-header 通則**：凡用新 frame-header（`ShowFrameHeader="true"`）的 grid，**都要 `ShowBuiltInToolbar="false"`** 關掉舊工具列（主檔清單、明細 InCell、Excel 預覽皆同）。
> **高度 combo（欄位模式最右）自動顯示條件**：`OnHeightChanged` 有綁 **或** `Height` 是固定 px。填滿頁（`Height="100%"` 且未綁 `OnHeightChanged`，如 SAL001）會**自動隱藏**（避免強制 px 撐破 overflow:hidden 外層冒捲軸）。`IksGrid_Virtual` 與 `IksGrid_vnq` 行為一致。

**列事件**
| 參數 | 說明 |
|------|------|
| `OnSelect` `EventCallback<TItem>` | 選取（點擊/程式化）觸發 |
| `OnRowClick` / `OnRowDoubleClick` | 點/雙擊列 |
| `RowKeyField` + `OnRowFocus` | **鍵盤/滑鼠 focus 即回呼**（見下節） |
| `OnUpdate` / `OnDelete` / `OnAdd` | InCell 編輯（明細；`details/grid-incell.md`） |
| `OnTotalCountChanged` `EventCallback<int>` | 總筆數變更 |

**公開成員**：`GridRef`（TelerikGrid）、`GridData`（List<TItem>）、`SelectedItems`、`SelectRowAsync(item)`、`Rebind()`。

---

## 🖱️ 點列多選 + Shift 區間 + 整列標示（穿梭／轉單頁 checkbox grid）

**適用**：批次勾選轉單/撥轉頁（SAL053 銷退轉單、SAL058 訂單撥轉採購單、多選 picker）——要「整列點擊即選取、Shift 連續區間、選取列高亮」。

**設定**：`ShowCheckbox="true"` + `ShowSelectAll="false"`（表頭全選對虛擬捲動只勾已渲染列 → 改用自訂「全選/取消」frame-header 鈕呼叫元件 `SelectAll()`/`ClearSelection()` 對整份清單生效）+ `OnRowClick="OnRowClick"`。選取集合即由 `SelectedItems` 高亮標示，不需另寫 CSS。

**handler 範式**（比照 SAL053；`_anchor` 為頁面欄位記住上次點擊列）：
```csharp
private {{Row}}? _anchor;
private async Task OnRowClick(GridRowClickEventArgs args)
{
    if (_grid == null || args.Item is not {{Row}} row) return;
    // ⚠ 鍵盤導覽（UpData/DownData）也呼叫本方法但 EventArgs=null；只有滑鼠點列才切換選取
    if (args.EventArgs is not MouseEventArgs mouse) return;
    var set = _grid.SelectedItems?.ToList() ?? new List<{{Row}}>();
    int a = _anchor != null ? _data.IndexOf(_anchor) : -1;
    int c = _data.IndexOf(row);
    if (mouse.ShiftKey && a >= 0 && c >= 0)
    {   // Shift：a→c 區間全選（不受虛擬化限制，直接對 _data 算）
        foreach (var r in _data.GetRange(Math.Min(a, c), Math.Abs(a - c) + 1))
            if (!set.Contains(r)) set.Add(r);
    }
    else { if (!set.Remove(row)) set.Add(row); _anchor = row; }  // 一般點擊：toggle 並移動 anchor
    _grid.SelectedItems = set;
    await InvokeAsync(StateHasChanged);
}
```

**眉角**
- 讀取選取一律 `_grid.SelectedItems`（穿梭鈕/確認轉單）；勿依賴 `OnSelectedItemsChanged`（無法支援 Shift 區間）。
- 有 InCell 可編欄時，`SelectedItems` 可能同時殘留「真實列」與「編輯複本」（同 key、不同參考）→ 確認轉單時以 **key 去重**並回 `_data` 取權威列（見 [[reference_vnq_incell_row_selection]]／`grid-incell.md`）。
- InCell 改值回顯用 `_grid.GridRef.Rebind()`（**非**元件 `Rebind()`/`RebindKeepState()`，那些會清掉 `@bind-SelectedItems` 的勾選）。

---

## 💰 唯讀合計欄放哪（Delphi 唯讀 ButtonEdit 的金額加總）

**來源特徵**：Delphi 用 `TRzDBButtonEdit`（或 `TRzDBEdit`）+ `ReadOnly=True` 顯示金額加總／筆數合計——**它不是輸入欄，是計算結果的展示位**。按鈕只是「看明細」，沒有 pick 語意。

**規則：不要照 `TRzDBButtonEdit` 對照表做成 `IksTextBox`+Picker，也不要放進編輯表單當欄位**，改依層級擺：

| 合計屬於誰 | 去向 | 寫法 |
|-----------|------|------|
| **主檔清單 grid**（整份查詢結果的合計、狀態標記） | `IksGrid_Virtual` 的 **`FrameHeaderExtra`** | 見下方骨架 |
| **明細 grid**（該張單所有明細列的合計） | 明細 grid **下方合計列** `.iks-total-bar` | 見 `details/css-layout.md`；`IksGrid_vnq` 無 `FrameHeaderExtra` |

**眉角**
- **一律唯讀**：`FrameHeaderExtra` 內只放 `<span>` 純文字，**不放輸入控件**（Delphi 端本來就 ReadOnly）。
- **值一律走後端算**，頁面只負責顯示（同 `details/field-change.md`：金額計算不在前端加總）。
- 只是資訊、不是操作 → **不要塞進 `HeaderButtons`**（那是按鈕）；順序上 header 已保證排在筆數之前。
- 金額格式比照欄位規則：`#,##0.######`（→ 本頁「其他 grid 眉角」）。

```razor
<IksGrid_Virtual @ref="{{Grid}}" ... ShowFrameHeader="true" ShowBuiltInToolbar="false">
    <FrameHeaderExtra>
        @* Delphi {{DFM 控件名}}（ReadOnly ButtonEdit）金額加總 → 唯讀顯示，值由後端帶回 *@
        <span class="iks-fcount">合計金額：@_sumMny.ToString("#,##0.######")</span>
    </FrameHeaderExtra>
    <LeftColumnsTool>...</LeftColumnsTool>
</IksGrid_Virtual>
```

---

## 🔑 鍵盤控制 / OnRowFocus（focus 即選取）

**原理**：設 `RowKeyField`（列唯一鍵屬性名）+ `OnRowFocus` 後，**focus（鍵盤上下鍵移動 / 滑鼠）落到某列就回呼該列，不需點擊、不需進編輯**。元件自管 JS 監聽，頁面只給 handler。

**內建機制**（`IksRowFocusTracker` + `wwwroot/js/pageJs.js` 的 `iksRowFocusInterop`）：
- 每列 render 附 `iks-rk-{鍵值}` class（`OnRowRenderHandler`）；grid 根元素 `tabindex="0"`。
- JS 監聽 zone 的 `focusin` → 解析 row-key → `[JSInvokable] OnFocus(key)` → 從 `GridData` 找列 → 呼叫 `OnRowFocus`。
- 生命週期自管：`firstRender` `StartAsync()`、`Dispose` 釋放、**`Rebind()` 內自動 `ResetAsync()`**。

**「focus＝選取」模式**（master-detail 主檔用）：在 `OnRowFocus` handler 內呼叫 `SelectRowAsync(row)` → 高亮 + 觸發 `OnSelect`。這樣**鍵盤上下鍵移動 = 移動即選取即載入明細**（記憶 `grid_focus_masterdetail`）。

```csharp
private void OnMqySelect(Mqy item) => MqySelect = item;   // OnSelect
private async Task OnMqyRowFocus(Mqy row) {               // OnRowFocus
    if (row == null) return;
    if (MqySelect != null && MqySelect.{{KEY}} == row.{{KEY}}) return;  // 去重：同列不重觸發
    if ({{Grid}} != null) await {{Grid}}.SelectRowAsync(row);          // focus→選取（→ 載入明細）
}
```

**眉角**
- **Rebind 去重**：Blazor 依位置重用 `<tr>`，主檔切換/重查後第一個 `<tr>` 仍是同一顆；不清除會讓點回該列被去重吃掉（OnRowFocus 第一次不觸發）→ 元件已在 `Rebind()` 內 `ResetAsync()`，頁面免處理。
- **handler 內去重比對**：如上，`MqySelect` 與 row 主鍵相同就 return，避免重覆載入明細。
- **虛擬捲動捲頂重置**：換較少列的查詢條件時，捲到底會卡列補骨架 → `Rebind` 前先 `scrollGridTopNow` 歸零（元件已內建；記憶 `grid_virtual_scroll_reset`；nq/一般捲動無此問題）。
- 頁面**不需**寫 `[JSInvokable]` / 註冊監聽，只給 `RowKeyField` + `OnRowFocus`。

---

## Grid 生命週期綁定（master / 明細 / 附件）

> 統一慣例（參考 SAL021；SAL041/042/044 主明細、SAL045A/043A 彈窗附件已對齊）。目的：**自動欄寬正常 + 不重複綁定**。

**兩種 Rebind 行為（記憶 `vnq_rebind_reload_colwidth`）**
- **無參數 `Rebind()`**：`firstLoad=true` → 下次 `OnRead` 重跑 `GetTableSetting()`，**重載欄位設定（含 ColWidth 自動欄寬）**。
- **`Rebind(list)`**：只換 `GridData` 資料，**不重載欄位設定**。

**規則**
1. **master grid → 無參數 `Rebind()`**（firstRender、查詢 `Query`、CRUD 後）——靠它載欄位設定/自動欄寬。
2. **明細 / 附件 grid → `Rebind(list)`**（只換資料）。
3. **`OnAfterRenderAsync` firstRender**：綁 master（無參數）＋**各明細一次**（`Rebind(list)`），讓明細首次渲染即取得欄寬：
   ```csharp
   if (firstRender) {
       {{Mqy}}?.Rebind();                                        // master：載欄位設定/自動欄寬
       {{Dq1}}?.Rebind({{Dq1_GD}}); {{Dq2}}?.Rebind({{Dq2_GD}});  // 各明細一次（list）
       await btnControl(); await InvokeAsync(StateHasChanged);
   }
   ```
4. **載入明細**：設好各 `_GD` 後**每格 `Rebind(list)` 一次**（「載一個綁一個」或「全載後各綁一次」皆可，重點是**每格單次**）。勿在 `LoadAllDetailAsync` 綁完後、caller 又對同一格 `Rebind`。
5. **拷貝（主檔）**：先 `LoadDetailAsync` 取資料**但不 Rebind** → 改 `uState=Insert`/清主鍵 → **最後只綁一次**（否則 load 內綁一次＋事後又綁＝二次綁定）。
6. **彈窗附件**：`LoadAttAsync` 載完 `Rebind(list)` 一次；InCell 更新用 `RebindKeepState`、刪除 `Rebind(list)`——皆單次。

⚠ **二次綁定救不了欄寬**（`Rebind(list)` 不重載設定；rebind 兩次＋`Task.Delay` 無效）。欄寬異常 → 確保 master 走**無參數 `Rebind()`**、且該格沒被重複綁定。相關：`grid_virtual_scroll_reset`（keepScrollTop 是另一件事）。

---

## 其他 grid 眉角（彙整記憶，實作必看）

- **儲存格單行省略**：四個 grid 統一「單行 + `…` 省略、hover 顯示 `title`」——虛擬捲動固定列高必需，否則長字撐高列高會亂。CSS `.iks-grid-ellipsis`（含 `!important`）放 **app.css**，改後 Ctrl+F5。（原記憶 `grid_cell_ellipsis`）
- **Virtual grid TItem 勿用 `[JsonProperty]` 改名**：`IksGrid_Virtual` 走 `ToList<T>()` 反射比對「屬性名」，不吃 `[JsonProperty]`；若用 JsonProperty 改名，數值欄 `_Int` 會恆為 0。改用 `get/set` 包裝 `base`（數值欄 `_Int`、日期直接綁 `DateTime?`）。（原記憶 `virtual_grid_no_jsonproperty`、`displaytransform_keycode_alias`）
- **金額欄格式**：`TelerikNumericTextBox` 金額用 `Format="#,##0.######"`（千分位＋小數最多 6 位）；固定 6 位才用 `N6`。（原記憶 `numeric_format_money`）
- **numeric(10,0) 整數欄**：JSON 轉換統一用 `IKSERPSHARE.Converters.NewtonsoftDecimalToIntConverter`，UI 層勿重複定義；`decimal?` nullable 不標記。（原記憶 `decimal_to_int_converter`）
- **bool 欄鎖定**：`IksGrid_Virtual` 的 bool 欄 `Editable=false` 元件內部會覆蓋、無法真鎖（限制）；`IksGrid_vnq` 可用 `SetColumnEditable`。（→ `details/shared-input-components.md`）
- **可編輯欄淡紫底 `HighlightEditableCells` 是 `IksGrid_vnq` 專屬**，`IksGrid_Virtual` 沒有此參數（Virtual 是唯讀清單，不需標示）。用法/開啟門檻 → `details/grid-incell.md` 通則 7。
- **指令欄按鈕走純圖示 + Title**（同工具列 ribbon）：`GridCommandButton` 的 `Icon` 傳 Tabler class 字串（`Icon="@("ti ti-pencil")"`）、`Title` 當提示、**不放文字**；指令欄寬度可縮小（3 鈕≈130px、4 鈕≈170px）。
  - **tooltip 靠 `Title` 的原生 HTML tooltip 即可**（hover 顯示）。**勿**用廣義 `<TelerikTooltip TargetSelector=".k-grid [title]">`——儲存格單行省略會替每格加 `title`，廣義選擇器會掛滿整個 grid。要美化就把選擇器**限縮到指令欄**（如自訂 class）。

---

## 【範例程式碼】(SAL001 主檔清單)
```razor
<IksGrid_Virtual @ref="{{Grid}}" TItem="Mqy" ApiName="{{form}}_M_Query" ApiUrl="@_url"
                 Table_Name="{{Grid}}" Columns="{{ColConfig}}" WhereParameters="{{parameter}}"
                 sortKey="{{KEY}}" Height="100%" PageSize="20"
                 ShowFrameHeader="true" ShowFilterButton="true"
                 FilterAnchorClass="mqy-filter-popup-target" OnFilterClick="ToggleFilterPopup"
                 ShowBuiltInToolbar="false" ShowAdd="false"
                 OnSelect="OnMqySelect" RowKeyField="{{KEY}}" OnRowFocus="OnMqyRowFocus">
    <LeftColumnsTool>
        @* 純 Tabler 圖示 + Title(tooltip)，同工具列 ribbon 風格；不放文字 *@
        @* 順序＝CRUD→查詢：拷貝 → 修改 → 刪除 → 詳細資料（handler → details/crud-handlers.md）*@
        <GridCommandButton Icon="@("ti ti-copy")"   OnClick="@OnRowCopy"   Title="拷貝" />
        <GridCommandButton Icon="@("ti ti-pencil")" OnClick="@OnRowEdit"   Title="修改" />
        <GridCommandButton Icon="@("ti ti-trash")"  OnClick="@OnRowDelete" Title="刪除" />
        <GridCommandButton Icon="@("ti ti-eye")"    OnClick="@OnRowDetail" Title="詳細資料" />
    </LeftColumnsTool>
</IksGrid_Virtual>
```
```csharp
protected override async Task OnAfterRenderAsync(bool firstRender) {
    await base.OnAfterRenderAsync(firstRender);
    if (firstRender) {{Grid}}?.Rebind();   // firstRender 才首讀
}
```

## 【骨架程式碼】
```razor
<IksGrid_Virtual @ref="{{Grid}}" TItem="Mqy" ApiName="{{form}}_M_Query" ApiUrl="@_url"
                 Table_Name="{{Grid}}" Columns="{{ColConfig}}" WhereParameters="{{parameter}}"
                 sortKey="{{KEY}}" RowKeyField="{{KEY}}" Height="100%" ShowAdd="false"
                 ShowFrameHeader="true" ShowFilterButton="true" ShowBuiltInToolbar="false"
                 FilterAnchorClass="{{grid}}-filter-popup-target" OnFilterClick="ToggleFilterPopup"
                 OnSelect="OnMqySelect" OnRowFocus="OnMqyRowFocus">
    <LeftColumnsTool>@* 針對列：拷貝/修改/刪除/詳細（CRUD→查詢）→ details/toolbar.md *@</LeftColumnsTool>
</IksGrid_Virtual>
```
```csharp
private void OnMqySelect(Mqy item) => MqySelect = item;
private async Task OnMqyRowFocus(Mqy row) {
    if (row == null || (MqySelect != null && MqySelect.{{KEY}} == row.{{KEY}})) return;
    await {{Grid}}!.SelectRowAsync(row);   // focus=選取（主檔明細：接著載明細 + Rebind）
}
```

## 指路
- 進階篩選 → `details/popup-filter.md`；列指令按鈕位置 → `details/toolbar.md`
- 合計列 class（`.iks-total-bar`）→ `details/css-layout.md`
- 可編輯明細 InCell（同 RowKeyField/OnRowFocus 機制）→ `details/grid-incell.md`
- 欄位設定/顯示（ColConfig/_Display）→ `details/dto-display.md`
- 上/下一筆導覽 → `details/row-navigate.md`
