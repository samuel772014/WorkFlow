# 多選選擇器 骨架範本（picker）

> 複製到 `Components/Shared/XxxPicker.razor`（或頁面資料夾），改元件名後把 **TODO** 補齊：
> `FomId`、`Table_Name`、DTO、`_columns`、篩選控件、`LoadAsync` 查詢 API。
>
> 細節規則：選取 → `details/selection.md`；代碼欄顯示名稱 → `details/display.md`；
> 欄寬/Rebind → `details/grid.md`；呼叫端接線 → `details/wiring.md`。

```razor
@using Telerik.Blazor
@using Telerik.Blazor.Components
@using System.Data
@using Newtonsoft.Json
@using Microsoft.AspNetCore.Components.Web
@using IKSERPUI.Components.Services
@using IKSERPUI.Components.Attributes
@using IKSERPUI.iksUiFunc
@inject iksFoundationCore gQL
@inherits IksPageBase

<TelerikLoaderContainer Visible="@IsPageLoading"
                        Text="資料處理中..."
                        OverlayThemeColor="dark"
                        Size="@ThemeConstants.Loader.Size.Large" />

<div style="display:flex; flex-direction:column; height:100%; padding:8px; gap:8px; box-sizing:border-box; overflow-y:auto;">


    @* ── 清單（多選）── *@
    <div style="flex-shrink:0; display:flex; flex-direction:column;">
        <IksGrid_vnq @ref="_grid"
                     TItem="PickRow"
                     GridData="@_data"
                     Table_Name="XxxPicker"
                     ApiUrl="@_url"
                     Columns="_columns"
                     ShowAdd="false"
                     ShowToolbar="false"
                     ShowCheckbox="true"
                     ShowSelectAll="false"
                     ShowFrameHeader="true"
                     HeaderButtons="@_headerButtons"
                     ShowFilterButton="true" OnFilterClick="ToggleFilterPopup"
                     FilterAnchorClass="xxxpicker-filter-popup-target"
                     OnRowClick="OnRowClick"
                     Height="360px" />
    </div>

    @* ── 篩選：一律進階篩選 Popup（Grid 外部；page-migration/details/popup-filter.md）── *@
    <TelerikPopup @ref="@FilterPopupRef" AnchorSelector=".xxxpicker-filter-popup-target" Width="430px">
        <div class="iks-filter-popup">
            <div class="iks-filter-popup-head"><span class="iks-filter-popup-title">進階篩選</span>
                <button class="iks-fbtn ghost iks-filter-close" @onclick="ToggleFilterPopup" title="關閉篩選"><i class="ti ti-circle-x"></i></button></div>
            <div class="iks-filter-popup-body"><div class="iks-filter-grid">
                <div class="iks-filter-row"><IksLabel Key="Lb_F_KEYWORD" DefaultText="關鍵字" />
                    @* TODO：文字用 IksTextBox；代碼用 IksCodeComboBox；多欄過濾用 EditPick（控件選擇同 page-migration） *@
                    <IksTextBox @ref="_keywordCtrl" @bind-Value="_keyword" /></div>
            </div></div>
            <div class="iks-filter-popup-actions">
                <button class="iks-fbtn" @onclick="ClearFilter"><i class="ti ti-trash"></i>清除</button>
                <button class="iks-fbtn primary" @onclick="OnQuery"><i class="ti ti-search"></i>查詢</button>
            </div>
        </div>
    </TelerikPopup>

    @* ── 底部按鈕 ── *@
    <div style="display:flex; justify-content:flex-end; gap:8px; flex-shrink:0;
                border-top:1px solid #e5e7eb; padding-top:8px;">
        <button type="button" class="iks-fbtn primary" @onclick="OnConfirmClick" title="確定"><i class="ti ti-check"></i><span>確定</span></button>
        <button type="button" class="iks-fbtn" @onclick="Cancel" title="取消"><i class="ti ti-x"></i><span>取消</span></button>
    </div>
</div>

<MessageBox @ref="MsgBox" />

@code {
    // ── 對外 API（呼叫端接線見 details/wiring）──
    [Parameter] public EventCallback<List<PickRow>> OnConfirm { get; set; }   // 「確定」→ 回傳選取清單
    [Parameter] public EventCallback OnClose { get; set; }                    // 「取消」/關閉

    protected override string FomId => "TODO";   // TODO：功能代號（Table_Name/欄位設定用）

    private MessageBox MsgBox = default!;
    private string _url => iksService.ApiUrl;

    private string _keyword = "";                 // TODO：篩選條件依實體擴充
    private IksTextBox<string>? _keywordCtrl;     // 每個篩選控件一個 @ref，清除時 Reset()
    private TelerikPopup? FilterPopupRef;
    private bool _filterPopupVisible = false;
    private void ToggleFilterPopup() { _filterPopupVisible = !_filterPopupVisible; if (_filterPopupVisible) FilterPopupRef?.Show(); else FilterPopupRef?.Hide(); }
    private void ClearFilter() { _keyword = ""; _keywordCtrl?.Reset(); }   // 只清非必填；批次帶值欄不清（details/selection）

    private IksGrid_vnq<PickRow>? _grid;
    private List<PickRow> _data = new();
    private PickRow? _anchor;                     // Shift 區間錨點（details/selection）

    private List<IksGridHeaderButton> _headerButtons => new()
    {
        new() { Text = "全選",     Icon = "ti ti-checkbox", OnClick = SelectAll },
        new() { Text = "取消全選", Icon = "ti ti-x",        OnClick = ClearSelection },
    };

    // ── DTO（TODO：換成實際欄位；代碼欄顯示名稱見 details/display）──
    public class PickRow : IDisplayResolvable
    {
        public string KEY  { get; set; } = "";   // TODO：主鍵/代碼
        public string NAME { get; set; } = "";   // TODO：名稱
    }

    // ── 欄位（TODO：對齊實際欄位）──
    private Dictionary<string, GridColumnConfig> _columns => new()
    {
        { "KEY",  new GridColumnConfig { Field="KEY",  Title="代碼", Editable=false, Width="150px" } },
        { "NAME", new GridColumnConfig { Field="NAME", Title="名稱", Editable=false, Width="240px" } },
    };

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        await base.OnAfterRenderAsync(firstRender);
        if (firstRender) await LoadAsync();
    }

    private async Task OnQuery() { await LoadAsync(); _filterPopupVisible = false; FilterPopupRef?.Hide(); }

    // 查詢資料（TODO：接後端）→ 填 _data → 綁定
    private async Task LoadAsync()
    {
        SetPageLoading();
        try
        {
            // TODO：呼叫查詢 API 並反序列化到 List<PickRow>
            // var args = new Dictionary<string,string> { ["KEYWORD"] = _keyword.Trim() };
            // var result = await gQL.ApiCallAsync(_url, "query", "TODO_QueryWay", args);
            // if (result?.records != null)
            //     _data = JsonConvert.DeserializeObject<List<PickRow>>(JsonConvert.SerializeObject(result.records)) ?? new();
            _data = new();

            _anchor = null;
            if (_grid != null) await _grid.Rebind(_data);   // 欄寬異常改無參數 Rebind()，見 details/grid
            await InvokeAsync(StateHasChanged);
        }
        finally { SetPageLoaded(); }
    }

    // ── 點列選取 + Shift 區間（詳 details/selection）──
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
            foreach (var r in range) if (!set.Contains(r)) set.Add(r);   // union
        }
        else
        {
            if (!set.Remove(row)) set.Add(row);   // toggle
            _anchor = row;
        }
        _grid.SelectedItems = set;
        await InvokeAsync(StateHasChanged);
    }

    private async Task SelectAll()      { if (_grid != null) await _grid.SelectAll(); }
    private async Task ClearSelection() { if (_grid != null) await _grid.ClearSelection(); }

    private async Task OnConfirmClick()
    {
        var selected = _grid?.SelectedItems?.ToList() ?? new List<PickRow>();
        if (selected.Count == 0)
        {
            await MsgBox.Show("請至少選取一筆。", "選擇器", "warning");
            return;
        }
        await OnConfirm.InvokeAsync(selected);
    }

    private async Task Cancel() => await OnClose.InvokeAsync();
}
```
