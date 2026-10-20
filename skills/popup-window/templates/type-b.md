# 版型 B 完整範本：查詢型（篩選 Popup）

> Grid frame-header 篩選鈕 → 進階篩選 Popup（清除/查詢）+ Grid + 套用/取消。篩選一律 Popup（`page-migration/details/popup-filter.md`），不用 inline 篩選。
> 註：藍本 SAL046D 目前仍是舊 inline 寫法，已列入待改清單。

```razor
@using Telerik.Blazor
@using Telerik.Blazor.Components
@using Newtonsoft.Json
@using IKSERPUI.Components.Services
@using IKSERPUI.Components.Shared.Toolbar
@inject iksFoundationCore gQL
@inject iksService iksService
@inherits IksPageBase

@* SAL0XXB：{{功能說明}} *@

<div class="iks-edit-window" style="padding:8px;">

    @* ── 可捲動內容（Grid；篩選走 frame-header 篩選鈕 → Popup）── *@
    <div class="iks-edit-body" style="display:flex; flex-direction:column; gap:6px;">

    @* ── Grid（成長填滿）── *@
    <div style="flex:1 1 auto; min-height:0;">
        <IksGrid_vnq @ref="_grid"
                     TItem="TItem"
                     GridData="@_rows"
                     Table_Name="SAL0XXB_Grid"
                     ApiUrl="@_url"
                     Columns="_columns"
                     ShowToolbar="false"
                     ShowCheckbox="true"
                     ShowSelectAll="false"
                     ShowFrameHeader="true"
                     HeaderButtons="@_headerButtons"
                     ShowFilterButton="true" OnFilterClick="ToggleFilterPopup"
                     FilterAnchorClass="sal0xxb-filter-popup-target"
                     Height="100%">
            <LeftColumnsTool></LeftColumnsTool>
        </IksGrid_vnq>
    </div>

    </div>@* /iks-edit-body *@

    @* ── 進階篩選 Popup（Grid 外部；清除只清非必填、各控件 @ref+Reset()）→ page-migration/details/popup-filter.md ── *@
    <TelerikPopup @ref="@FilterPopupRef" AnchorSelector=".sal0xxb-filter-popup-target" Width="{{組數×430}}px">
        <div class="iks-filter-popup">
            <div class="iks-filter-popup-head"><span class="iks-filter-popup-title">進階篩選</span>
                <button class="iks-fbtn ghost iks-filter-close" @onclick="ToggleFilterPopup" title="關閉篩選"><i class="ti ti-circle-x"></i></button></div>
            <div class="iks-filter-popup-body"><div class="iks-filter-grid">
                <div class="iks-filter-row"><IksLabel Key="Lb_F_{{F}}" DefaultText="{{中文}}" />
                    <{{控件}} @ref="_{{f}}Ctrl" @bind-Value="_filter.{{F}}" ... /></div>
            </div></div>
            <div class="iks-filter-popup-actions">
                <button class="iks-fbtn" @onclick="ClearFilter"><i class="ti ti-trash"></i>清除</button>
                <button class="iks-fbtn primary" @onclick="ApplyFilter"><i class="ti ti-search"></i>查詢</button>
            </div>
        </div>
    </TelerikPopup>

    @* ── 底部動作列（套用/確認 + 取消，固定底部）── *@
    <div class="iks-edit-actions">
        <TelerikButton ThemeColor="@ThemeConstants.Button.ThemeColor.Primary"
                       OnClick="ConfirmAsync" Icon="@("ti ti-circle-check")">套用</TelerikButton>
        <TelerikButton OnClick="@(() => OnCancel.InvokeAsync())"
                       Icon="@("ti ti-circle-x")">取消</TelerikButton>
    </div>

</div>
<MessageBox @ref="MsgBox" />

@code {
    [Parameter] public EventCallback<List<TItem>> OnConfirm { get; set; }
    [Parameter] public EventCallback OnCancel { get; set; }

    protected override string FomId => "SAL0XX";

    public class TItem : IKSERPSHARE.Models.{{EFModel}}, IDisplayResolvable { }   // 勾選狀態不放 DTO，一律讀 _grid.SelectedItems

    private MessageBox MsgBox = default!;
    private string _url => iksService.ApiUrl;
    private IksGrid_vnq<TItem>? _grid;
    private List<TItem> _rows = new();

    // ── 篩選 ────────────────────────────────────────────────────────────────
    private class MyFilter { public string? {{F}} { get; set; } }
    private MyFilter _filter = new();
    private TelerikPopup? FilterPopupRef;
    private bool _filterPopupVisible = false;
    private void ToggleFilterPopup() { _filterPopupVisible = !_filterPopupVisible; if (_filterPopupVisible) FilterPopupRef?.Show(); else FilterPopupRef?.Hide(); }
    private void ClearFilter() { _filter.{{非必填F}} = null; _{{f}}Ctrl?.Reset(); }   // 只清非必填
    private async Task ApplyFilter() { await Query(); _filterPopupVisible = false; FilterPopupRef?.Hide(); }

    // ── 全選 / 取消全選（HeaderButtons，放在 frameheader）────────────────────
    private List<IksGridHeaderButton> _headerButtons => new()
    {
        new() { Text = "全選",     Icon = "ti ti-checks", OnClick = SelectAllAsync },
        new() { Text = "取消全選", Icon = "ti ti-square",  OnClick = ClearSelectAsync },
    };
    private async Task SelectAllAsync()  { if (_grid != null) await _grid.SelectAll(); }        // 元件方法，對整份清單生效
    private async Task ClearSelectAsync(){ if (_grid != null) await _grid.ClearSelection(); }

    // ── Columns ──────────────────────────────────────────────────────────────
    private Dictionary<string, GridColumnConfig> _columns => new()
    {
        { "{{F}}", new GridColumnConfig { Field="{{F}}", Title="{{中文}}", Editable=false } },
    };

    // ── Lifecycle ─────────────────────────────────────────────────────────────
    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        await base.OnAfterRenderAsync(firstRender);
        if (firstRender) { await Query(); await InvokeAsync(StateHasChanged); }
    }

    // ── 查詢 ──────────────────────────────────────────────────────────────────
    private async Task Query()
    {
        var r = await gQL.ApiCallAsync(_url, "query", "sal0xxb_Query",
            new Dictionary<string, string> { ["{{F}}"] = _filter.{{F}} ?? "" });
        _rows = r?.records != null && r.records.Rows.Count > 0
            ? JsonConvert.DeserializeObject<List<TItem>>(JsonConvert.SerializeObject(r.records)) ?? new()
            : new();
        if (_grid != null) await _grid.Rebind(_rows);
    }

    // ── 確認帶回 ──────────────────────────────────────────────────────────────
    private async Task ConfirmAsync()
    {
        var selected = _grid?.SelectedItems.ToList() ?? new List<TItem>();   // 勾選來源＝元件 SelectedItems（同 SAL046D）
        if (!selected.Any()) { await MsgBox.Show("請先勾選資料", "{{功能}}", "warning"); return; }
        await OnConfirm.InvokeAsync(selected);
    }
}
```
