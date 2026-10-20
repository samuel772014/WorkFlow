# 範本 ④：dropform 雙表穿梭撥轉／轉單（原 selectform 已併入）── 大骨架

> **這是什麼**：一類**非 CRUD**的作業頁——「查詢候選 → 雙表穿梭挑選 → 批量設定 → 撥轉/轉單（確認）」。對應 Delphi `dropform`（對照表模式欄標記）及 `TfmBatchForm` / C210 / B407 這類「查詢候選 → 勾選搬移 → 確認轉單」表單。
> **藍本（權威參考頁）**：`SAL058 訂單撥轉採購單`（B407），版面比照 MPS024（生產計畫備料轉請購）。2026-09-22 由 SAL058 抽取（經使用者核可的方法論擴充）；2026-10-08 併入原 `selectform.md`。
> **鐵則**：商業邏輯（金額/稅/匯率/取價/撥轉寫入）**一律走 API 共用函式**，UI 只做挑選與顯示（CLAUDE.md 鐵則1）。不確定的欄位/邏輯先查 Delphi 或問，不推測（鐵則4）。新頁若出現藍本未涵蓋的結構 → 標特例、問，不自行設計。

---

## 什麼時候選這個範本（別跟主檔明細搞混）

| 特徵 | dropform（本範本） | 主檔明細（範本①） |
|------|----------------------|--------------------|
| 目的 | 查候選 → 勾選 → 搬移 → 確認轉單/撥轉 | 單一主表 + 其明細 CRUD |
| 兩個 Grid 關係 | 來源/目標（同層級穿梭） | 主檔 1 : 明細 N |
| 編輯 | 只有目標 Grid 少數欄可編（數量/單價/供應商…） | 主表單 + 明細 InCell |
| 「新增/存檔/取消」 | ❌ 無（改「顯示/清除/確認」） | ✅ 有完整 CRUD |
| Delphi 型別 | `dropform`／`TfmBatchForm`/穿梭 | `TFmXxxBase`（主檔明細） |

> Delphi 若是 `sbDown/sbUp/sbAllDown/sbAllUp`（穿梭鈕）＋ `cd`/`cd2` 雙 dataset＋`KButtonClick`（確認），就是本範本。判斷不了 → 回 `SKILL.md#範本清單` 重新判模式或問操作者。

---

## ⚠ 版面鐵則（做錯這條，grid 會整個看不到）

**外層一律 MPS024 的「垂直堆疊 flex column」，不做水平穿梭三欄版（左 grid｜中間鈕｜右 grid）。**
水平三欄版需要一堆自訂 CSS（`.xxx-shuttle` 等），這些 class 若沒進 `app.css`，grid 會塌成 0 高度→整頁看不到 grid（SAL058 舊版就是這樣壞掉）。

- 兩 Grid 上下排、各包 `.iks-master-frame`（`flex:0 0 auto; height:@_xHeight`）＋ grid `Height="100%"` ＋ `OnHeightChanged` 回寫高度（比照 MPS024/MPS034；見 `iks-scroll-modes`）。
- **不新增穿梭專屬的中間按鈕欄**；搬移鈕放下 Grid 的 `<HeaderExtra>`。版面只用既有共用 class：`.iks-master-frame`／`.iks-master-grid`、`.iks-filter-popup*`、`.iks-filter-grid`／`.iks-filter-row`、`.iks-fbtn`。
- **Grid 一進頁就在**（初始空資料、按「顯示」才填），不做「查詢後才出現 Grid」。

## ⚠ 動作面板分類鐵則（決定每個控制項擺哪）

進頁上方**不放**任何 inline 動作面板。所有非 grid 控制項歸到兩個彈窗之一，判斷準則只有一條——**這個設定會不會改到「將被寫入目標單據」的資料**：

| 分類 | 內容 | 放哪 | 由哪個 grid frame-header 觸發 |
|------|------|------|------------------------------|
| **查詢條件**（只影響撈哪些候選列） | 部門/業務/訂單別/客戶/單號/料號起迄/只顯示採購件… | **進階篩選** 彈窗（對應 Delphi `FilterPanel`） | **上 Grid** `HeaderButtons`（`Class="{{FORM}}-filter-popup-target"`） |
| **會改資料的參數**（搬下時套用、寫進目標列） | 指定供應商/指定幣別/需求部門/請購別/預入儲區/提前天數/指定日期… | **批量設定** 彈窗（對應 Delphi `pActionPanel`） | **下 Grid** `HeaderButtons`（`Class="{{FORM}}-batch-popup-target"`） |

- 兩個 Popup 結構同 `details/popup-filter.md`（`iks-filter-popup` 外框、`@ref`+`Reset()` 清除、必填不清）；開關直接呼叫 `Popup.Show()/Hide()`（子元件 frame-header 觸發不會自動連動父頁重繪）。
- 批量設定的 radio（如供應商「主供應商/指定」、幣別）用 `fieldset.iks-radio-group`＋`IksCodeComboBox`（指定時才 Enabled）；**radio 預設值以 Delphi 為準**（SAL058：指定供應商、依供應商幣別）。

---

## 區塊總覽（漸進式揭露，要動哪區才讀對應 details）

| 區 | 位置 | 詳細規則檔 |
|----|------|-----------|
| A | 頁首宣告 + 狀態（`_processing`、兩 Grid 高度） | `details/page-shell.md` |
| B | 工具列（顯示 / 清除 ‖ 確認/撥轉；**無 CRUD**） | `details/toolbar.md`（ribbon 寫法）、`btn-control.md`（Enabled 條件） |
| C | 上 Grid（候選/來源，唯讀，勾選多筆） | `details/grid-virtual.md`（用 `IksGrid_vnq`）、`multiselect-picker`（勾選穿梭） |
| D | 進階篩選 Popup（上 Grid 觸發） | `details/popup-filter.md`、`input-component-choice.md` |
| E | 下 Grid（目標，少數欄 InCell 可編＋連動重算）；搬移鈕在 `HeaderExtra` | `details/grid-incell.md`、`editor-template.md`、`field-change.md` |
| F | 批量設定 Popup（下 Grid 觸發） | `details/popup-filter.md`（同彈窗機制） |
| G | 穿梭邏輯（搬下/搬上；試算走後端） | `details/field-change.md`、`business-logic.md` |
| H | 確認/撥轉（一次寫目標單據，後端 transaction） | `details/crud-handlers.md`、`backend-sql.md` |
| I | DTO（來源列 / 目標列，皆為查詢投影類別） | `details/dto-display.md` |

> 控件選擇一律先過 `details/input-component-choice.md`（代碼欄兩欄→ComboBox，別用 EditPick）。
> 遇 Delphi 封裝函式：先查 `.claude/SelfFolder/共用函式對照表.md`，再查 `details/shared-functions.md` 取處理策略；查不到標 `[封裝商業邏輯]` 登記 `TODO彙整.md`，不自行重寫。

---

## 大骨架（單一 .razor，結構同 MPS024 / SAL058）

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
                @* 目標表有資料且非處理中才可按 *@
                <ToolbarButton Action="Confirm" Enabled="@(_targetData.Count > 0 && !_processing)" FontIcon="ti ti-transfer-in" Title="確認撥轉" />
            </ToolbarGroup>
        </Toolbar>
    </div>
    <TelerikTooltip TargetSelector=".toolbar-field [title]" Position="@TooltipPosition.Bottom" />

    @* 可捲動 flex column body：兩 Grid 各 .iks-master-frame + 頁面欄位控高度（OnHeightChanged 回寫）*@
    <div style="flex:1 1 auto; min-height:0; display:flex; flex-direction:column; overflow-y:auto; overflow-x:hidden; gap:8px;">

        @* ══ C. 上 Grid：候選/來源（唯讀、勾選多筆搬下；雙擊列＝單筆搬下）══
           ⚠ 虛擬捲動 grid 表頭全選只勾已渲染列 → ShowSelectAll="false"，改用 frame-header
             HeaderButtons 呼叫元件 SelectAll()/ClearSelection()（對整份本地清單生效）。 *@
        <div class="iks-master-frame" style="flex:0 0 auto; height:@_srcHeight;">
            <div class="iks-master-grid">
                <IksGrid_vnq @ref="_srcGrid" TItem="SrcRow" GridData="@_srcData"
                             Table_Name="{{FORM}}src" ApiUrl="@_url" Columns="@_srcColumns"
                             ShowAdd="false" ShowBuiltInToolbar="false" ShowFrameHeader="true"
                             ShowCheckbox="true" ShowSelectAll="false"
                             HeaderButtons="@_srcHeaderButtons"
                             OnRowClick="OnSrcRowClick"
                             OnRowDoubleClick="@(async (GridRowClickEventArgs a) => await TransferDownAsync(new List<SrcRow>{ (SrcRow)a.Item }))"
                             OnHeightChanged="@((string h) => _srcHeight = h)"
                             Height="100%" />
            </div>
        </div>

        @* ══ E. 下 Grid：已選/目標（少數欄 InCell 可編）══  → details/grid-incell.md、editor-template.md
           HeaderButtons：全選/取消全選 + 批量設定（錨定 Popup）
           HeaderExtra：搬下選取/全部搬下/搬上選取/全部搬上（對應 sbDown/sbAllDown/sbUp/sbAllUp）*@
        <div class="iks-master-frame" style="flex:0 0 auto; height:@_tgtHeight;">
            <div class="iks-master-grid">
                <IksGrid_vnq @ref="_tgtGrid" TItem="TgtRow" GridData="@_targetData"
                             Table_Name="{{FORM}}tgt" ApiUrl="@_url" Columns="@_tgtColumns"
                             ShowAdd="false" ShowBuiltInToolbar="false" ShowFrameHeader="true"
                             ShowCheckbox="true" ShowSelectAll="false"
                             HeaderButtons="@_tgtHeaderButtons"
                             OnUpdate="Tgt_UpdateHandler"
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
                @* {{會改資料的參數：供應商/幣別/儲區/請購別/需求部門/提前天數/指定日期…；radio 預設依 Delphi}} *@
            </div>
        </div>
    </div>
</TelerikPopup>

<MessageBox @ref="MsgBox" />

@code {
    @* ── A. 狀態 ── *@
    protected override string FomId => "{{FORM}}";
    private MessageBox MsgBox = default!;
    private bool _processing = false;
    private string _srcHeight = "300px";
    private string _tgtHeight = "300px";

    @* ── C/E. 雙 Grid + 資料 ── *@
    private IksGrid_vnq<SrcRow>? _srcGrid;
    private IksGrid_vnq<TgtRow>? _tgtGrid;
    private List<SrcRow> _srcData    = new();
    private List<TgtRow> _targetData = new();
    private SrcRow? _anchor;   // Shift 區間錨點

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
    private async Task OnSrcSelectAll()      { if (_srcGrid != null) await _srcGrid.SelectAll(); }
    private async Task OnSrcClearSelection() { if (_srcGrid != null) await _srcGrid.ClearSelection(); }
    private async Task OnTgtSelectAll()      { if (_tgtGrid != null) await _tgtGrid.SelectAll();      await InvokeAsync(StateHasChanged); }
    private async Task OnTgtClearSelection() { if (_tgtGrid != null) await _tgtGrid.ClearSelection(); await InvokeAsync(StateHasChanged); }

    @* ── C. 上 Grid 點列多選 + Shift 區間（範式見 details/grid-virtual.md「點列多選」）；讀取選取一律 _srcGrid.SelectedItems ── *@
    private async Task OnSrcRowClick(GridRowClickEventArgs args) { /* MouseEventArgs 才切換；Shift 依 _anchor 區間 */ }

    @* ── D. 篩選 Popup ── *@
    private TelerikPopup? FilterPopupRef;
    private bool _filterPopupVisible = false;
    private Task ToggleFilterPopupAsync() { ToggleFilterPopup(); return Task.CompletedTask; }   // HeaderButton OnClick 用（Func<Task>）
    private void ToggleFilterPopup() { _filterPopupVisible = !_filterPopupVisible; if (_filterPopupVisible) FilterPopupRef?.Show(); else FilterPopupRef?.Hide(); }
    private void ClearFilter() { /* 只清非必填篩選欄 + 各控件 Reset() */ }
    private async Task ApplyFilterAsync() { await QueryAsync(); _filterPopupVisible = false; FilterPopupRef?.Hide(); }

    @* ── F. 批量設定 Popup ── *@
    private TelerikPopup? BatchPopupRef;
    private bool _batchPopupVisible = false;
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
            _targetData = new(); _anchor = null;
            if (_srcGrid != null) await _srcGrid.Rebind(_srcData);
            if (_tgtGrid != null) await _tgtGrid.Rebind(_targetData);
        }
        finally { _processing = false; }
    }

    @* ── 清除：清空篩選 + 兩 Grid（對應 Delphi ClearBitBtnClick）── *@
    private async Task ClearAllAsync()
    {
        ClearFilter();
        _srcData = new(); _targetData = new(); _anchor = null;
        if (_srcGrid != null) await _srcGrid.Rebind(_srcData);
        if (_tgtGrid != null) await _tgtGrid.Rebind(_targetData);
    }

    @* ── G. 穿梭：搬下（勾選/全部；帶批量參數打後端取供應商/幣別/取價/稅額 {{form}}_CalcRow）── *@
    private async Task TransferDownSelectedAsync()
    {
        var rows = _srcGrid?.SelectedItems?.ToList() ?? new List<SrcRow>();
        if (rows.Count == 0) { await MsgBox.Show("請至少勾選一筆上方資料列", "提示", "warning"); return; }
        await TransferDownAsync(rows);
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
                @* {{後端試算（{{form}}_CalcRow）→ 建 TgtRow 加進 _targetData}} *@
            }
            _srcData = _srcData.Where(r => !rows.Contains(r)).ToList();
            if (_srcGrid != null) { await _srcGrid.ClearSelection(); await _srcGrid.Rebind(_srcData); }
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

    @* ── E. 下 Grid InCell：OnUpdate 依 args.Field 分派（藍本 SAL058 Cd2_UpdateHandler）──
       details/grid-incell.md、field-change.md 第 9 點
       ⚠ args.Item 是編輯複本 → 先用鍵值到 _targetData 找回實際列再寫回，否則 RebindKeepState 後值會被還原。
       ⚠ OnUpdate 內不可呼叫 ExitEditModeAsync（會遞迴回 OnUpdate）。不用已淘汰的 OnBeforeEdit。 *@
    private async Task Tgt_UpdateHandler(GridCommandEventArgs args)
    {
        var edited = (TgtRow)args.Item;
        var gd = _targetData.FirstOrDefault(r => r.{{KEY}} == edited.{{KEY}});
        if (gd == null) return;
        switch (args.Field)
        {
            case "{{數量/單價等}}": gd.{{F}} = edited.{{F}}; await RecalcTgtAsync(gd); break;   // 改值 → 後端重算金額
            case "{{不需重算欄}}":   gd.{{F}} = edited.{{F}}; if (_tgtGrid != null) await _tgtGrid.RebindKeepState(_targetData); break;
        }
    }
    private async Task RecalcTgtAsync(TgtRow row) { /* {{form}}_CalcMny（API 共用函式）→ 回寫 MNY/TMNY → _tgtGrid?.RebindKeepState(_targetData) */ }
    private async Task OnTgtRowClick(GridRowClickEventArgs _) => await InvokeAsync(StateHasChanged);   // 讓勾選變動即時反映

    @* ── H. 確認/撥轉（一次寫目標單據，後端 transaction；共用撥轉函式）── *@
    private async Task ConfirmAsync()
    {
        if (_targetData.Count == 0) return;
        if (_tgtGrid != null) await _tgtGrid.ExitEditModeAsync();   // 提交當前編輯格（使用者動作 handler 可呼叫）
        @* {{必填檢核 + MsgBox.Confirm}} *@
        _processing = true;
        try
        {
            @* {{payload（_targetData 全列 + 批量參數 + EmplyId）→ gQL.MultipleDataApiCallAsync(_url,"mutation","{{form}}_Confirm",…)}} *@
            @* {{成功 → MsgBox + 清表重查}} *@
        }
        finally { _processing = false; }
    }

    @* ── I. DTO：皆為查詢投影類別（非單一 EF Model），inline 宣告在 @code、不共用 → details/dto-display.md ── *@
    public class SrcRow : IDisplayResolvable { /* 來源候選欄位 + [DisplayTransform] _Display */ }
    public class TgtRow : IDisplayResolvable { /* 目標待轉欄位（可編：數量/單價/供應商…）+ _Display */ }

    @* ── 欄位設定：來源多 Editable=false；目標少數 Editable=true（配 EditorTemplate 時見 editor-template.md）；永遠不可編欄 Editable=false，不寫整表鎖欄樣板 ── *@
    private Dictionary<string, GridColumnConfig> _srcColumns => new() { };
    private Dictionary<string, GridColumnConfig> _tgtColumns => new() { };
}
```

---

## 與其他範本的關鍵差異

1. **不是 CRUD**：工具列是 **顯示 / 清除 / 確認（撥轉）**，沒有新增/存檔/取消/修改；無編輯 Window、無 view_mode。
2. **兩個 Grid 同層級穿梭**（來源上 / 目標下，**垂直堆疊**），用 `IksGrid_vnq`，DTO 是查詢投影類別。
3. **面板分類**：查詢條件→**進階篩選** Popup（上 Grid 觸發）；會改目標列資料的參數→**批量設定** Popup（下 Grid 觸發）。上方不放 inline 面板。
4. **搬移鈕**放「下 Grid」`HeaderExtra`；**不新增**穿梭專屬中間按鈕欄。
5. **全選/取消全選**用元件 `SelectAll()/ClearSelection()`（`ShowSelectAll="false"`）；讀取選取一律 `SelectedItems`（有 InCell 時以 key 去重回 `_data` 取權威列，見 `details/grid-virtual.md`）。
6. **下 Grid InCell 用 `OnUpdate` 依 `args.Field` 分派**（與 `details/grid-incell.md` 一致、藍本 SAL058）；試算與寫入一律走後端（`{{form}}_CalcRow`／`{{form}}_CalcMny`／`{{form}}_Confirm`），前端只暫存 `_targetData`。
7. **`OnHeightChanged` 回寫兩 Grid 高度**，使用者可各自調高度。

## 對照 acceptance-criteria（dropform 版調整，`.claude/SelfFolder/checklist/acceptance-criteria.md`）

- **無 S4（新增/編輯/刪除 handler）**：改檢查「查詢/清除/穿梭/撥轉」動作齊備。
- **S2 欄位/欄序**：兩 grid 各依 Delphi 兩個 `DDBGrid` 的欄位（cd 唯讀清單、cd2 可編集合）。
- **S6 輸入元件**：批量/篩選走決策樹；cd2 可編欄 InCell。
- 其餘（S1 路由標題、S9 標題＝對照表名、_Display 接上）照舊。

> Delphi 邏輯若在 base（繼承鏈），先問操作者（SKILL 來源讀取原則）。
