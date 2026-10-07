# 版型 B 完整範本：查詢型 inline 篩選（SAL046D 藍本）

> 工具列 Query + inline `iks-filter-grid`（≤2 欄）+ Grid + 套用/取消。

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

    @* ── 工具列（查詢，固定頂部）── *@
    <div class="toolbar toolbar-field" style="flex-shrink:0;">
        <Toolbar OnAction="HandleToolbar">
            <ToolbarGroup>
                <ToolbarButton Action="Query" FontIcon="ti ti-search" Title="查詢">查詢</ToolbarButton>
            </ToolbarGroup>
        </Toolbar>
    </div>

    @* ── 可捲動內容（篩選 + Grid）── *@
    <div class="iks-edit-body" style="display:flex; flex-direction:column; gap:6px;">

    @* ── Inline 篩選（≤2 欄時用此；否則改版型 C 進階篩選 Popup）── *@
    <div class="iks-filter-grid">
        <div class="iks-filter-row">
            <IksLabel Key="Lb_F_{{F}}" DefaultText="{{中文}}" />
            <{{控件}} @bind-Value="_filter.{{F}}" ... />
        </div>
    </div>

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
                     Height="100%">
            <LeftColumnsTool></LeftColumnsTool>
        </IksGrid_vnq>
    </div>

    </div>@* /iks-edit-body *@

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

    public class TItem : IKSERPSHARE.Models.{{EFModel}}, IDisplayResolvable
    {
        public bool _Selected { get; set; }
    }

    private MessageBox MsgBox = default!;
    private string _url => iksService.ApiUrl;
    private IksGrid_vnq<TItem>? _grid;
    private List<TItem> _rows = new();

    // ── 篩選 ────────────────────────────────────────────────────────────────
    private class MyFilter { public string? {{F}} { get; set; } }
    private MyFilter _filter = new();

    // ── 全選 / 取消全選（HeaderButtons，放在 frameheader）────────────────────
    private List<IksGridHeaderButton> _headerButtons => new()
    {
        new() { Text = "全選",     Icon = "ti ti-checks", OnClick = SelectAllAsync },
        new() { Text = "取消全選", Icon = "ti ti-square",  OnClick = ClearSelectAsync },
    };
    private Task SelectAllAsync()  { _rows.ForEach(r => r._Selected = true);  _grid?.Rebind(_rows); return Task.CompletedTask; }
    private Task ClearSelectAsync(){ _rows.ForEach(r => r._Selected = false); _grid?.Rebind(_rows); return Task.CompletedTask; }

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

    // ── 工具列 ───────────────────────────────────────────────────────────────
    private async Task HandleToolbar(string action)
    {
        if (action == "Query") await Query();
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
        var selected = _rows.Where(r => r._Selected).ToList();
        if (!selected.Any()) { await MsgBox.Show("請先勾選資料", "{{功能}}", "warning"); return; }
        await OnConfirm.InvokeAsync(selected);
    }
}
```
