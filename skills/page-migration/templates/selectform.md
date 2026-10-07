# 範本 ④：穿梭選取轉單（selectform）── 大骨架

> 適用：**雙 Grid 穿梭批次轉單/挑選**，非 CRUD 維護頁。上 Grid＝候選/來源明細（唯讀，勾選多筆搬下）；下 Grid＝已選/目標明細（少數欄可 InCell 編輯，搬上/搬下）。「確認」把下 Grid 內容一次寫入目標單據。
> 對應 Delphi **`TfmBatchForm` / C210 / B407** 這類「查詢候選 → 勾選搬移 → 確認轉單」表單（**不是** 主檔明細維護）。
> 版面標準：**MPS024**（生產計畫備料轉請購，垂直堆疊雙 Grid）＝本範本的黃金範例；**SAL058**（訂單撥轉採購單）比照 MPS024 重建。邏輯來源：Delphi 常見繼承鏈，先問操作者（SKILL 來源讀取原則）。

---

## 什麼時候選這個範本（別跟主檔明細搞混）

| 特徵 | selectform（本範本） | 主檔明細（範本①） |
|------|----------------------|--------------------|
| 目的 | 查候選 → 勾選 → 搬移 → 確認轉單 | 單一主表 + 其明細 CRUD |
| 兩個 Grid 關係 | 來源/目標（同層級穿梭） | 主檔 1 : 明細 N |
| 編輯 | 只有目標 Grid 少數欄可編（數量/單價/供應商…） | 主表單 + 明細 InCell |
| 「新增/存檔/取消」 | ❌ 無（改「顯示/清除/確認」） | ✅ 有完整 CRUD |
| Delphi 型別 | `TfmBatchForm`/穿梭 | `TFmXxxBase`（主檔明細） |

> 判斷不了就問操作者。Delphi 若是 `sbDown/sbUp/sbAllDown/sbAllUp`（穿梭鈕）＋ `cd`/`cd2` 雙 dataset＋`KButtonClick`（確認），就是本範本。

---

## ⚠ 版面鐵則（做錯這條，grid 會整個看不到）

**外層一律 MPS024 的「垂直堆疊 flex column」，不做水平穿梭三欄版（左 grid｜中間鈕｜右 grid）。**
水平三欄版需要一堆自訂 CSS（`.xxx-shuttle` / `.xxx-shuttle-side` / `.xxx-shuttle-buttons`），這些 class 若沒進 `app.css`，grid 會塌成 0 高度→整頁看不到 grid（SAL058 舊版就是這樣壞掉）。

正確外層結構（照抄，`@_srcHeight`/`@_tgtHeight` 由 `OnHeightChanged` 回寫）：

```razor
<div id="local-content" style="display:flex; flex-direction:column; height:100%; padding:8px; gap:8px; box-sizing:border-box; overflow:hidden;">
    <div class="toolbar toolbar-field"> …工具列… </div>
    @* 可捲動 body：兩 grid 各包一層 .iks-master-frame，grid 本身 Height="100%" *@
    <div style="flex:1 1 auto; min-height:0; display:flex; flex-direction:column; overflow-y:auto; overflow-x:hidden; gap:8px;">
        <div class="iks-master-frame" style="flex:0 0 auto; height:@_srcHeight;">
            <div class="iks-master-grid"> <IksGrid_vnq … Height="100%" OnHeightChanged="@((string h)=>_srcHeight=h)" /> </div>
        </div>
        <div class="iks-master-frame" style="flex:0 0 auto; height:@_tgtHeight;">
            <div class="iks-master-grid"> <IksGrid_vnq … Height="100%" OnHeightChanged="@((string h)=>_tgtHeight=h)" /> </div>
        </div>
    </div>
</div>
```

**不新增穿梭專屬的中間按鈕欄。** 搬移鈕放下 Grid 的 `<HeaderExtra>`（見下）。版面只用既有共用 class：`.iks-master-frame`／`.iks-master-grid`（Grid frame）、`.iks-filter-popup*`（彈窗）、`.iks-filter-grid`／`.iks-filter-row`（彈窗欄位）、`.iks-fbtn`（frame-header/彈窗按鈕）。

---

## ⚠ 動作面板分類鐵則（決定每個控制項擺哪）

進頁上方**不放**任何 inline 動作面板。所有非 grid 控制項一律歸到兩個彈窗之一，判斷準則只有一條——**這個設定會不會改到「將被寫入目標單據」的資料**：

| 分類 | 內容 | 放哪 | 由哪個 grid frame-header 觸發 |
|------|------|------|------------------------------|
| **查詢條件**（只影響「撈哪些候選列」，不改資料） | 部門/業務/訂單別/客戶/單號/料號起迄/只顯示採購件… | **進階篩選** 彈窗 | **上 Grid** `HeaderButtons`（`Class="{{FORM}}-filter-popup-target"`） |
| **會改資料的參數**（搬下時套用、寫進目標列） | 指定供應商/指定幣別/需求部門/請購別/預入儲區/提前天數/指定日期… | **批量設定** 彈窗 | **下 Grid** `HeaderButtons`（`Class="{{FORM}}-batch-popup-target"`） |

> 「批量設定」錨在**下 Grid** 的 frame-header，視覺上就落在上下兩個 grid 之間，對應 Delphi `pActionPanel`（搬移時套用的預設值）。「進階篩選」對應 Delphi `FilterPanel`（DisplayButtonClick 的查詢條件）。

---

## 怎麼用這份骨架（漸進式揭露）

只放**大骨架**（畫面 + `@code` 欄位 + 生命週期），要動哪區才讀對應 `details/*.md`。

| 區 | 位置 | 詳細規則檔 |
|----|------|-----------|
| A | 頁首宣告 + 狀態（`_processing`、兩 Grid 高度） | `details/page-shell.md` |
| B | 工具列（顯示 / 清除 / 確認；**無 CRUD**） | `details/toolbar.md` |
| C | 上 Grid（候選/來源，唯讀，勾選多筆） | `details/grid-virtual.md`（用 `IksGrid_vnq`） |
| D | 進階篩選 Popup（查詢條件；由**上 Grid** frame-header 觸發） | `details/popup-filter.md` |
| E | 下 Grid（已選/目標，少數欄 InCell 可編）；搬移鈕在**下 Grid** frame-header（`HeaderExtra`） | `details/grid-incell.md`、`editor-template.md` |
| F | 批量設定 Popup（搬下時套用的參數；由**下 Grid** frame-header 觸發） | `details/popup-filter.md`（同彈窗機制） |
| G | 穿梭邏輯（搬下 CdToCd2 / 搬上 Cd2ToCd；試算走後端） | `details/field-change.md`、`business-logic.md` |
| H | 確認（一次寫目標單據，後端 transaction） | `details/crud-handlers.md`、`backend-sql.md` |
| I | DTO（來源列 / 目標列，皆為**查詢投影類別**，非單一 EF Model） | `details/dto-display.md` |

> 控件選擇一律先過 `details/input-component-choice.md`（代碼欄兩欄→ComboBox，別用 EditPick）。
> ⚠ 遇 Delphi 封裝函式（ERPFunc/SALFunc/MPSFunc…）：先查 `details/delphi-func-lookup.md` 對應 C# 方法，再查 `details/shared-functions.md` 取處理策略。

---

## 四個關鍵版面決策（本範本的核心）

1. **外層垂直堆疊**（見上「版面鐵則」）：兩 Grid 上下排、各包 `.iks-master-frame`（`flex:0 0 auto; height:@_xHeight`）+ grid `Height="100%"` + `OnHeightChanged` 回寫高度（比照 MPS024/MPS034）。**Grid 一進頁就在**（初始空資料、按「顯示」才填），不做「查詢後才出現 Grid」。
2. **篩選 → 進階篩選 Popup，由「上 Grid」frame-header `HeaderButtons` 觸發**：`new(){ Text="進階篩選", Icon="ti ti-filter", Class="{{FORM}}-filter-popup-target", OnClick=ToggleFilterPopupAsync }`；`TelerikPopup` 的 `AnchorSelector` 對應該 class。**開關直接呼叫 `Popup.Show()/Hide()`**（子元件 frame-header 觸發不會自動連動父頁重繪，記憶 `feedback_child_triggered_popup_visibility`）。
3. **「會改資料的參數」→ 批量設定 Popup，由「下 Grid」frame-header `HeaderButtons` 觸發**：`new(){ Text="批量設定", Icon="ti ti-adjustments-horizontal", Class="{{FORM}}-batch-popup-target", OnClick=ToggleBatchPopupAsync }`。搬下時把這些參數套進新建的目標列。
4. **搬移鈕放「下 Grid」的 `<HeaderExtra>`**：搬下選取/全部搬下/搬上選取/全部搬上四顆（對應 Delphi sbDown/sbAllDown/sbUp/sbAllUp），比照 MPS024 排在下 Grid frame-header。

> **全選/取消全選**：兩個 Grid 都設 `ShowCheckbox="true" ShowSelectAll="false"`，改用各自 frame-header 的 `HeaderButtons` 呼叫元件 `SelectAll()/ClearSelection()`（對整份本地清單生效）。虛擬捲動 grid 的表頭內建全選只勾得到「已渲染列」，故隱藏、不用。

---

## 大骨架（單一 .razor，結構同 MPS024）

```razor
@* ══ A. 頁首宣告 ══  → details/page-shell.md *@
@page "/{{MODULE}}/{{FORM}}"
@inherits IksPageBase
@inject iksFoundationCore gQL
@inject TokenStorage Token
@using Telerik.Blazor
@using Telerik.Blazor.Components
@using System.Data
@using Newtonsoft.Json
@using IKSERPUI.Components.Services
@using IKSERPUI.Components.Shared.Toolbar
@using IKSERPSHARE.Models
@using IKSERPUI.Components.Attributes
<PageTitle>({{FORM}}){{頁面標題}}</PageTitle>
<TelerikLoaderContainer Visible="@IsPageLoading" Text="載入中..." Size="@ThemeConstants.Loader.Size.Large" />
<TelerikLoaderContainer Visible="@_processing" Text="處理中，請稍後..." OverlayThemeColor="dark" Size="@ThemeConstants.Loader.Size.Large" />

<div id="local-content" style="display:flex; flex-direction:column; height:100%; padding:8px; gap:8px; box-sizing:border-box; overflow:hidden;">

    @* ══ B. 工具列（顯示/清除 ‖ 確認；無 CRUD）══  → details/toolbar.md *@
    <div class="toolbar toolbar-field">
        <Toolbar OnAction="HandleToolbar">
            <ToolbarGroup>
                <ToolbarButton Action="Query" Enabled="@(!_processing)" FontIcon="ti ti-search" Title="顯示" />
                <ToolbarButton Action="Clear" Enabled="@(!_processing)" FontIcon="ti ti-trash"  Title="清除" />
            </ToolbarGroup>
            <ToolbarGroup>
                <ToolbarButton Action="Confirm" Enabled="@(_targetData.Count > 0 && !_processing)" FontIcon="ti ti-check" Title="確認" />
            </ToolbarGroup>
        </Toolbar>
    </div>
    <TelerikTooltip TargetSelector=".toolbar-field [title]" Position="@TooltipPosition.Bottom" />

    @* 可捲動 flex column body：兩 Grid 各 .iks-master-frame + 頁面欄位控高度（OnHeightChanged 回寫）*@
    <div style="flex:1 1 auto; min-height:0; display:flex; flex-direction:column; overflow-y:auto; overflow-x:hidden; gap:8px;">

        @* ══ C. 上 Grid：候選/來源（唯讀、勾選多筆搬下）══  → details/grid-virtual.md
           ⚠ 虛擬捲動 grid 表頭全選只勾已渲染列 → ShowSelectAll="false"，改用 frame-header
             HeaderButtons 呼叫元件 SelectAll()/ClearSelection()（對整份本地清單生效）。 *@
        <div class="iks-master-frame" style="flex:0 0 auto; height:@_srcHeight;">
            <div class="iks-master-grid">
                <IksGrid_vnq @ref="_srcGrid" TItem="SrcRow" GridData="@_srcData"
                             Table_Name="{{FORM}}src" ApiUrl="@_url" Columns="@_srcColumns"
                             ShowAdd="false" ShowBuiltInToolbar="false" ShowFrameHeader="true"
                             ShowCheckbox="true" ShowSelectAll="false"
                             HeaderButtons="@_srcHeaderButtons"
                             OnSelectedItemsChanged="@((IEnumerable<SrcRow> items) => _selectedSrc = items.ToList())"
                             OnRowDoubleClick="@(async (GridRowClickEventArgs a) => await TransferDownAsync(new List<SrcRow>{ (SrcRow)a.Item }))"
                             OnHeightChanged="@((string h) => _srcHeight = h)"
                             Height="100%" />
            </div>
        </div>

        @* ══ E. 下 Grid：已選/目標（少數欄 InCell 可編）══  → details/grid-incell.md、editor-template.md
           frame-header HeaderButtons：全選/取消全選 + 批量設定（錨定 Popup）
           HeaderExtra：搬下選取/全部搬下/搬上選取/全部搬上（對應 sbDown/sbAllDown/sbUp/sbAllUp）*@
        <div class="iks-master-frame" style="flex:0 0 auto; height:@_tgtHeight;">
            <div class="iks-master-grid">
                <IksGrid_vnq @ref="_tgtGrid" TItem="TgtRow" GridData="@_targetData"
                             Table_Name="{{FORM}}tgt" ApiUrl="@_url" Columns="@_tgtColumns"
                             ShowAdd="false" ShowBuiltInToolbar="false" ShowFrameHeader="true"
                             ShowCheckbox="true" ShowSelectAll="false"
                             HeaderButtons="@_tgtHeaderButtons"
                             OnRowClick="OnTgtRowClick"
                             OnHeightChanged="@((string h) => _tgtHeight = h)"
                             Height="100%">
                    <HeaderExtra>
                        <button class="iks-fbtn primary" title="搬下選取" disabled="@_processing" @onclick="TransferDownSelectedAsync"><i class="ti ti-chevron-down"></i></button>
                        <button class="iks-fbtn"         title="全部搬下" disabled="@_processing" @onclick="TransferAllDownAsync"><i class="ti ti-chevrons-down"></i></button>
                        <button class="iks-fbtn"         title="搬上選取" disabled="@_processing" @onclick="TransferUpSelectedAsync"><i class="ti ti-chevron-up"></i></button>
                        <button class="iks-fbtn"         title="全部搬上" disabled="@_processing" @onclick="TransferAllUpAsync"><i class="ti ti-chevrons-up"></i></button>
                    </HeaderExtra>
                </IksGrid_vnq>
            </div>
        </div>

    </div>
</div>

@* ══ D. 進階篩選 Popup（查詢條件；由上 Grid frame-header 觸發）══  → details/popup-filter.md *@
<TelerikPopup @ref="@FilterPopupRef" AnchorSelector=".{{FORM}}-filter-popup-target"
              AnimationType="@AnimationType.SlideDown" AnimationDuration="200" Width="900px">
    <div class="iks-filter-popup" aria-label="進階篩選">
        <div class="iks-filter-popup-head">
            <span class="iks-filter-popup-title">進階篩選</span>
            <button class="iks-fbtn ghost iks-filter-close" @onclick="ToggleFilterPopup" title="關閉篩選"><i class="ti ti-circle-x"></i></button>
        </div>
        <div class="iks-filter-popup-body">
            <div class="iks-filter-grid">
                @* {{查詢欄位：iks-filter-row × N；只放「不改資料」的查詢條件}} *@
            </div>
        </div>
        <div class="iks-filter-popup-actions">
            <button class="iks-fbtn" @onclick="ClearFilter"><i class="ti ti-trash"></i>清除</button>
            <button class="iks-fbtn primary" @onclick="ApplyFilterAsync"><i class="ti ti-search"></i>顯示</button>
        </div>
    </div>
</TelerikPopup>

@* ══ F. 批量設定 Popup（搬下時套用、會改目標列資料的參數；由下 Grid frame-header 觸發）══ *@
<TelerikPopup @ref="@BatchPopupRef" AnchorSelector=".{{FORM}}-batch-popup-target"
              AnimationType="@AnimationType.SlideDown" AnimationDuration="200" Width="560px">
    <div class="iks-filter-popup" aria-label="批量設定">
        <div class="iks-filter-popup-head">
            <span class="iks-filter-popup-title">批量設定</span>
            <button class="iks-fbtn ghost iks-filter-close" @onclick="ToggleBatchPopup" title="關閉"><i class="ti ti-circle-x"></i></button>
        </div>
        <div class="iks-filter-popup-body">
            <div class="iks-filter-grid">
                @* {{會改資料的參數：供應商/幣別/儲區/請購別/需求部門/提前天數/指定日期…}} *@
            </div>
        </div>
    </div>
</TelerikPopup>

<MessageBox @ref="MsgBox" />

@code {
    @* ── A. 狀態 ──  details/page-shell.md ── *@
    protected override string FomId => "{{FORM}}";
    private MessageBox MsgBox = default!;
    private bool _processing = false;
    private string _srcHeight = "300px";   // 上 Grid 高度（OnHeightChanged 回寫）
    private string _tgtHeight = "300px";   // 下 Grid 高度

    @* ── C/E. 雙 Grid + 資料 ── *@
    private IksGrid_vnq<SrcRow>? _srcGrid;
    private IksGrid_vnq<TgtRow>? _tgtGrid;
    private List<SrcRow> _srcData     = new();
    private List<SrcRow> _selectedSrc = new();
    private List<TgtRow> _targetData  = new();

    @* ── C/E. frame-header 按鈕：全選/取消全選（+ 上 Grid「進階篩選」、下 Grid「批量設定」錨定 Popup）── *@
    private List<IksGridHeaderButton> _srcHeaderButtons => new()
    {
        new() { Text = "全選",     Icon = "ti ti-checkbox", OnClick = OnSrcSelectAll },
        new() { Text = "取消全選", Icon = "ti ti-x",        OnClick = OnSrcClearSelection },
        new() { Text = "進階篩選", Icon = "ti ti-filter",   Class = "{{FORM}}-filter-popup-target", OnClick = ToggleFilterPopupAsync },
    };
    private List<IksGridHeaderButton> _tgtHeaderButtons => new()
    {
        new() { Text = "全選",     Icon = "ti ti-checkbox", OnClick = OnTgtSelectAll },
        new() { Text = "取消全選", Icon = "ti ti-x",        OnClick = OnTgtClearSelection },
        new() { Text = "批量設定", Icon = "ti ti-adjustments-horizontal", Class = "{{FORM}}-batch-popup-target", OnClick = ToggleBatchPopupAsync },
    };
    private async Task OnSrcSelectAll()      { _selectedSrc = _srcData.ToList(); if (_srcGrid != null) await _srcGrid.SelectAll(); }
    private async Task OnSrcClearSelection() { _selectedSrc = new();            if (_srcGrid != null) await _srcGrid.ClearSelection(); }
    private async Task OnTgtSelectAll()      { if (_tgtGrid != null) await _tgtGrid.SelectAll();      await InvokeAsync(StateHasChanged); }
    private async Task OnTgtClearSelection() { if (_tgtGrid != null) await _tgtGrid.ClearSelection(); await InvokeAsync(StateHasChanged); }

    @* ── D. 篩選 Popup ── *@
    private TelerikPopup? FilterPopupRef;
    private bool _filterPopupVisible = false;
    @* {{篩選欄位 + 其 combo @ref（Clear 時 Reset()）}} *@
    private Task ToggleFilterPopupAsync() { ToggleFilterPopup(); return Task.CompletedTask; }   // HeaderButton OnClick 用（Func<Task>）
    private void ToggleFilterPopup() { _filterPopupVisible = !_filterPopupVisible; if (_filterPopupVisible) FilterPopupRef?.Show(); else FilterPopupRef?.Hide(); }
    private void ClearFilter() { /* 篩選欄位歸零 + 有 Reset() 的 combo 呼叫 Reset(); 尾端 StateHasChanged() */ }
    private async Task ApplyFilterAsync() { await QueryAsync(); _filterPopupVisible = false; FilterPopupRef?.Hide(); }

    @* ── F. 批量設定 Popup ── *@
    private TelerikPopup? BatchPopupRef;
    private bool _batchPopupVisible = false;
    @* {{會改資料的參數欄位 + 其 @ref}} *@
    private Task ToggleBatchPopupAsync() { ToggleBatchPopup(); return Task.CompletedTask; }
    private void ToggleBatchPopup() { _batchPopupVisible = !_batchPopupVisible; if (_batchPopupVisible) BatchPopupRef?.Show(); else BatchPopupRef?.Hide(); }

    @* ── B. 工具列分派 ── *@
    private async Task HandleToolbar(string action)
    {
        await (action switch
        {
            "Query"   => QueryAsync(),
            "Clear"   => ClearAllAsync(),
            "Confirm" => ConfirmAsync(),
            _         => Task.CompletedTask
        });
    }

    @* ── 顯示：填上 Grid、清空下 Grid（對應 Delphi DisplayButtonClick/OpenPick）── *@
    private async Task QueryAsync()
    {
        _processing = true;
        try
        {
            @* {{組 args → gQL.MultipleDataApiCallAsync(_url, "query", "{{form}}_Query", …) → _srcData}} *@
            _selectedSrc = new(); _targetData = new();
            if (_srcGrid != null) await _srcGrid.Rebind(_srcData);
            if (_tgtGrid != null) await _tgtGrid.Rebind(_targetData);
        }
        finally { _processing = false; }
    }

    @* ── 清除：清空篩選 + 兩 Grid（對應 Delphi ClearBitBtnClick）── *@
    private async Task ClearAllAsync()
    {
        ClearFilter();
        _srcData = new(); _targetData = new(); _selectedSrc = new();
        if (_srcGrid != null) await _srcGrid.Rebind(_srcData);
        if (_tgtGrid != null) await _tgtGrid.Rebind(_targetData);
    }

    @* ── G. 穿梭：搬下（勾選/全部；試算走後端 CalcRow）──  details/field-change.md、business-logic.md ── *@
    private async Task TransferDownSelectedAsync()
    {
        if (_selectedSrc.Count == 0) { await MsgBox.Show("請至少勾選一筆上方資料列", "提示", "warning"); return; }
        await TransferDownAsync(_selectedSrc.ToList());
    }
    private async Task TransferAllDownAsync() { if (_srcData.Count > 0) await TransferDownAsync(_srcData.ToList()); }
    private async Task TransferDownAsync(List<SrcRow> rows)
    {
        if (rows.Count == 0) return;
        @* {{批量設定必填檢核（如需求部門/供應商/幣別）→ MsgBox 擋下}} *@
        _processing = true;
        try
        {
            foreach (var r in rows)
            {
                @* {{後端試算單價/計價量/金額（{{form}}_CalcRow）→ 建 TgtRow 加進 _targetData}} *@
            }
            _srcData = _srcData.Where(r => !rows.Contains(r)).ToList();
            _selectedSrc = new();
            if (_srcGrid != null) await _srcGrid.ClearSelection();
            if (_srcGrid != null) await _srcGrid.Rebind(_srcData);
            if (_tgtGrid != null) await _tgtGrid.Rebind(_targetData);
        }
        finally { _processing = false; }
    }

    @* ── G. 穿梭：搬上（勾選/全部；把目標列還原回來源）── *@
    private async Task TransferUpSelectedAsync()
    {
        var rows = _tgtGrid?.SelectedItems?.ToList() ?? new List<TgtRow>();
        if (rows.Count == 0) { await MsgBox.Show("請至少勾選一筆下方資料列", "提示", "warning"); return; }
        await TransferUpAsync(rows);
    }
    private async Task TransferAllUpAsync() { if (_targetData.Count > 0) await TransferUpAsync(_targetData.ToList()); }
    private async Task TransferUpAsync(List<TgtRow> rows) { /* 還原欄位建 SrcRow 加回 _srcData；從 _targetData 移除；ClearSelection + 兩 Grid Rebind */ }

    @* ── E. 下 Grid InCell：EditorTemplate + ValueChanged 直接寫回列，改後呼叫後端重算 + RebindKeepState ──
       details/grid-incell.md、editor-template.md
       ⚠ 不用 OnUpdate / OnBeforeEdit（已淘汰）。比照 MPS024：
         private RenderFragment<TgtRow> XxxEditor => item =>
             @<TelerikNumericTextBox Value="@item.XXX" ValueExpression="@(() => item.XXX)" Width="100%"
                                      ValueChanged="@((decimal? v) => OnXxxChanged(item, v))" />;
       欄位設定：{ "XXX", new GridColumnConfig{ … Editable=true, EditorTemplate=(ctx)=>XxxEditor((TgtRow)ctx) } } ── *@
    private async Task RecalcTgtAsync(TgtRow row) { /* {{form}}_CalcMny → 回寫該列計價量/金額 → _tgtGrid?.RebindKeepState(_targetData) */ }
    private async Task OnTgtRowClick(GridRowClickEventArgs _) => await InvokeAsync(StateHasChanged);   // 讓勾選變動即時反映

    @* ── H. 確認（一次寫目標單據，後端 transaction）──  details/crud-handlers.md、backend-sql.md ── *@
    private async Task ConfirmAsync()
    {
        if (_targetData.Count == 0) return;
        if (_tgtGrid != null) await _tgtGrid.ExitEditModeAsync();
        @* {{必填檢核 + MsgBox.Confirm}} *@
        _processing = true;
        try
        {
            @* {{payload（含 _targetData 全列 + 表頭參數 + EmplyId）→ gQL.MultipleDataApiCallAsync(_url,"mutation","{{form}}_Confirm",…)}} *@
            @* {{成功 → MsgBox + 重新 QueryAsync（清空重查）}} *@
        }
        finally { _processing = false; }
    }

    @* ── I. DTO（皆為查詢投影類別，非單一 EF Model；_Display 走 DisplayResolver）──  details/dto-display.md ── *@
    public class SrcRow : IDisplayResolvable { /* 來源候選欄位 + [DisplayTransform]/[DisplayTransformKeyCode] _Display */ }
    public class TgtRow : IDisplayResolvable { /* 目標待轉欄位（含可編輯：數量/單價/供應商…）+ _Display */ }

    @* ── C/E. 欄位設定（來源多唯讀；目標少數欄 Editable=true + EditorTemplate）── *@
    private Dictionary<string, GridColumnConfig> _srcColumns => new() { /* Editable=false 為主 */ };
    private Dictionary<string, GridColumnConfig> _tgtColumns => new() { /* 少數 Editable=true（數量/單價/供應商…）配 EditorTemplate */ };
}
```

---

## 與其他範本的關鍵差異

1. **不是 CRUD**：工具列是 **顯示 / 清除 / 確認**，沒有 新增/存檔/取消/修改。
2. **兩個 Grid 同層級穿梭**（來源上 / 目標下，**垂直堆疊**，不做水平三欄），用 `IksGrid_vnq`，DTO 是查詢投影類別（非單一 EF Model）。
3. **面板分類**：查詢條件（不改資料）→**進階篩選** Popup（上 Grid 觸發）；會改目標列資料的參數→**批量設定** Popup（下 Grid 觸發，落在上下 Grid 之間）。上方**不放** inline 面板。
4. **搬移鈕**放「下 Grid」`HeaderExtra`（搬下/全下/搬上/全上四顆）；**不新增**穿梭專屬中間按鈕欄。
5. **Grid 預設顯示**：一進頁就在（空資料），按顯示才填；**不做「查詢後才出現 Grid」**。
6. **全選/取消全選**用元件 `SelectAll()/ClearSelection()`（`ShowSelectAll="false"`），不用虛擬 grid 內建表頭全選（只勾已渲染列）。
7. **下 Grid InCell 用 EditorTemplate + ValueChanged + `RebindKeepState`**（比照 MPS024），**不用 OnUpdate / OnBeforeEdit**（已淘汰）；試算與寫入一律走後端（`{{form}}_CalcRow`／`{{form}}_CalcMny`／`{{form}}_Confirm`），前端只暫存 `_targetData`。
8. **`OnHeightChanged` 回寫兩 Grid 高度**（比照 MPS024/MPS034），使用者可各自調高度。

> Delphi 邏輯若在 base（繼承鏈），先問操作者（SKILL 來源讀取原則）。參考頁：**MPS024**（備料轉請購，黃金範例）、**SAL058**（訂單撥轉採購單，比照 MPS024 重建）。
