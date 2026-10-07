# 版型 A 完整範本：純編輯型（SAL055A 藍本）

> 無查詢工具列。唯讀表頭 + InCell Grid 編輯 + 存檔/取消。

```razor
@using Telerik.Blazor
@using Telerik.Blazor.Components
@using System.Data
@using Newtonsoft.Json
@using IKSERPUI.Components.Services
@using IKSERPUI.Components.Attributes
@inject iksFoundationCore gQL
@inject iksService iksService
@inherits IksPageBase

@* SAL0XXA：{{功能說明}} *@

<div class="iks-edit-window" style="padding:8px;">
    <div class="iks-edit-body" style="display:flex; flex-direction:column; gap:6px;">

    @* ── 父明細表頭（唯讀顯示）── *@
    <div class="iks-edit-subhead">{{表頭標題}}</div>
    <div class="iks-edit-grid" style="grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); max-width:100%;">
        <div class="iks-edit-row">
            <span class="iks-edit-label"><IksLabel Key="Lb_{{F}}" DefaultText="{{中文}}" /></span>
            <span class="iks-edit-input"><IksTextBox Value="@_h("{{F}}")" ReadOnly="true" Width="130px" /></span>
        </div>
        @* ... 依 DFM Edit1~N 順序補齊欄位 ... *@
    </div>

    @* ── 明細 Grid ── *@
    <div class="iks-edit-subhead">{{明細標題}}</div>
    <div style="flex:1 1 auto; min-height:0;">
        <IksGrid_vnq @ref="_grid"
                     TItem="DetailRow"
                     GridData="@_rows"
                     Table_Name="SAL0XXA_Grid"
                     ApiUrl="@_url"
                     Columns="_columns"
                     OnUpdate="RowUpdateHandler"
                     ShowAdd="false"
                     ShowToolbar="false"
                     Height="100%">
            <LeftColumnsTool>
                @* 有刪除才加；本頁若 Delphi NewRecord/BeforeDelete abort 則不加 *@
                {{@* <GridCommandButton Command="Delete" Icon="@("ti ti-trash")" Title="刪除" /> *@}}
            </LeftColumnsTool>
        </IksGrid_vnq>
    </div>

    </div>@* /iks-edit-body *@

    @* ── 底部動作列（存檔/取消固定在底部）── *@
    <div class="iks-edit-actions">
        <TelerikButton ThemeColor="@ThemeConstants.Button.ThemeColor.Primary"
                       OnClick="SaveAsync" Enabled="@(!_saving)"
                       Icon="@("ti ti-device-floppy")">存檔</TelerikButton>
        <TelerikButton OnClick="@(() => OnCancel.InvokeAsync())"
                       Icon="@("ti ti-circle-x")">取消</TelerikButton>
    </div>
</div>

@* EditPick（若有挑選需求，頁面層級宣告）*@
@* <EditPick_Button @ref="_xxxPick" TItem="DetailRow" Url="@_url" OnApply="OnXxxPicked" /> *@

<MessageBox @ref="MsgBox" />

@code {
    // ── Parameters ──────────────────────────────────────────────────────────
    [Parameter] public string?  ORDERNO  { get; set; }
    [Parameter] public decimal  ORDERITM { get; set; }
    [Parameter] public EventCallback OnCancel { get; set; }

    protected override string FomId => "SAL0XX";

    // ── DTO ─────────────────────────────────────────────────────────────────
    public class DetailRow : IKSERPSHARE.Models.{{EFModel}}
    {
        public UState uState { get; set; } = UState.None;
    }

    // ── State ────────────────────────────────────────────────────────────────
    private MessageBox MsgBox = default!;
    private string _url => iksService.ApiUrl;
    private IksGrid_vnq<DetailRow>? _grid;
    private List<DetailRow> _rows = new();
    private Dictionary<string, object>? _header;
    private bool _saving = false;

    // ── 表頭欄位取值輔助 ─────────────────────────────────────────────────────
    private string _h(string k) =>
        _header != null && _header.TryGetValue(k, out var v) && v != null && v != DBNull.Value
        ? v.ToString() ?? "" : "";

    // ── Columns ──────────────────────────────────────────────────────────────
    private Dictionary<string, GridColumnConfig> _columns => new()
    {
        { "{{F}}", new GridColumnConfig { Field="{{F}}", Title="{{中文}}", Editable=false } },
        @* Editable=false → 唯讀；EditorTemplate → 自訂編輯控件 *@
    };

    // ── Lifecycle ─────────────────────────────────────────────────────────────
    protected override async Task OnInitializedAsync()
    {
        await LoadHeaderAsync();
        await LoadRowsAsync();
    }

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        await base.OnAfterRenderAsync(firstRender);
        if (firstRender && _grid != null) await _grid.Rebind(_rows);
    }

    // ── 載入 ──────────────────────────────────────────────────────────────────
    private async Task LoadHeaderAsync()
    {
        var r = await gQL.ApiCallAsync(_url, "query", "sal0xxa_Header_Query",
            new Dictionary<string, string> { ["ORDERNO"] = ORDERNO ?? "", ["ORDERITM"] = ORDERITM.ToString() });
        if (r?.records != null && r.records.Rows.Count > 0)
        {
            var row = r.records.Rows[0];
            _header = new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase);
            foreach (DataColumn c in r.records.Columns) _header[c.ColumnName] = row[c];
        }
    }

    private async Task LoadRowsAsync()
    {
        var r = await gQL.ApiCallAsync(_url, "query", "sal0xxa_Detail_Query",
            new Dictionary<string, string> { ["ORDERNO"] = ORDERNO ?? "", ["ORDERITM"] = ORDERITM.ToString() });
        _rows = r?.records != null && r.records.Rows.Count > 0
            ? JsonConvert.DeserializeObject<List<DetailRow>>(JsonConvert.SerializeObject(r.records)) ?? new()
            : new();
    }

    // ── InCell 編輯 ───────────────────────────────────────────────────────────
    private async Task RowUpdateHandler(GridCommandEventArgs args)
    {
        var item = (DetailRow)args.Item;
        if (item.uState != UState.Insert) item.uState = UState.Update;
        var idx = _rows.FindIndex(r => r.{{PK}} == item.{{PK}});
        if (idx >= 0) _rows[idx] = item;
        if (_grid != null) await _grid.RebindKeepState(_rows);
    }

    // ── 存檔 ──────────────────────────────────────────────────────────────────
    private async Task SaveAsync()
    {
        if (_grid != null) await _grid.ExitEditModeAsync();
        _saving = true;
        await InvokeAsync(StateHasChanged);
        try
        {
            var payload = new
            {
                ORDERNO,
                ORDERITM,
                Rows = _rows.Where(r => r.uState != UState.None).Cast<IKSERPSHARE.Models.{{EFModel}}>().ToList(),
            };
            var result = await gQL.MultipleDataApiCallAsync(_url, "mutation", "sal0xxa_Save",
                new Dictionary<string, string> { ["arg"] = JsonConvert.SerializeObject(payload) });
            if (result?.status == 1)
            {
                await LoadRowsAsync();
                if (_grid != null) await _grid.Rebind(_rows);
                await MsgBox.Show("存檔成功", "{{功能}}", "success");
            }
            else
                await MsgBox.Show($"存檔失敗：{result?.message ?? "未知錯誤"}", "{{功能}}", "error");
        }
        finally { _saving = false; await InvokeAsync(StateHasChanged); }
    }
}
```

## 呼叫端（主頁）

```razor
@* 在主頁 TelerikWindow 區塊 *@
@if (_xxxVisible && _xxxTarget != null)
{
    <TelerikWindow @bind-Visible="@_xxxVisible" Width="85%" Height="88%" Modal="true" Resizable="true" Draggable="true">
        <WindowTitle>(SAL0XXA){{功能}} - @(_xxxTarget.NSN ?? "")</WindowTitle>
        <WindowActions><WindowAction Name="Close" /></WindowActions>
        <WindowContent>
            <SAL0XXA ORDERNO="@(_xxxTarget.ORDERNO)" ORDERITM="@(_xxxTarget.ORDERITM)"
                     OnCancel="@(() => _xxxVisible = false)" />
        </WindowContent>
    </TelerikWindow>
}
```

```csharp
private bool _xxxVisible = false;
private {{Dq}} ? _xxxTarget;

private async Task OpenXxxCmd(GridCommandEventArgs args)
{
    if (args.Item is not {{Dq}} r) return;
    _xxxTarget = r;
    _xxxVisible = true;
    await InvokeAsync(StateHasChanged);
}
```
