# 範本 ②：單檔 清單+彈窗（single-file）── 大骨架

> 適用：**單一主表維護**。主查詢 Grid 點列開 `TelerikWindow` 單筆編輯（含上/下一筆）。
> 參考頁面：`SAL001`。排版標準：for_github 新 UI（ToolbarGroup ribbon、Grid frame-header、篩選 popup）。
> ⚠️ 單一主表維護**不用 InCell 批次編輯**（記憶 `deprecate_incell_single_master`）；InCell 只用於主檔明細範本的明細 grid。
> ⚠️ 因此**單檔無「明細 grid 欄位鎖定」需求**：編輯走 `TelerikWindow` 表單、主 Grid 唯讀。若某特例頁確有可編輯 grid（瀏覽唯讀／Add·Edit 才可編），一律用 `grid.SetColumnEditable(field, locked)` 鎖欄（寫 `LockDqGridColumns/UnlockDqGridColumns`，**每次 Rebind 後重套**）——做法見 `master-detail.md` 第 11 點與記憶 `reference_grid_onbeforeedit_colkey_lock`；勿用已淘汰的 `OnBeforeEdit`。
> ⚠️ **單檔一律不套 Mode C 巢狀捲動**：外層就是純 `<div id="local-content">`（不加 `iks-scroll--nested`、不包 `cd-body`、不設 `--iks-layout-total-height`），由 Grid 自己捲。Mode C 只屬於主檔明細範本（`master-detail.md`）。誤把 Mode C 套到單檔會讓外層被固定高度撐開（如 1200px）。

---

## 怎麼用這份骨架（漸進式揭露）

這裡只有**大骨架**：一眼看完整頁「所有程式的擺放位置」——畫面標籤、`@code` 欄位宣告、生命週期方法各自該放哪。**不含功能細節**。

每一區的橫幅註解都帶一個指標：

```
@* ── C. 主表 Grid frame ──  詳細規則 → details/grid-virtual.md *@
```

要動哪一區、才去讀那一區的 `details/*.md`。骨架負責「把區塊接起來」，細節（參數、眉角、變體、範例碼）在 details 檔。

| 區 | 位置 | 詳細規則檔 |
|----|------|-----------|
| A | 頁首宣告 + `@code` 狀態欄位 + 初始載入 | `details/page-shell.md` |
| B | 工具列 Ribbon | `details/toolbar.md` |
| C | 主表 Grid frame | `details/grid-virtual.md` |
| D | 進階篩選 Popup | `details/popup-filter.md` |
| E | 編輯表單 Window | `details/edit-window.md` |
| F | 上/下一筆導覽 | `details/row-navigate.md` |
| G | 按鈕控制 btnControl | `details/btn-control.md` |
| H | CRUD Handlers | `details/crud-handlers.md` |
| I | DTO 類別＋ColConfig | `details/dto-display.md` |
| J | CSS（進 app.css） | `details/css-layout.md` |

> 跨區共用：控件選擇一律先過 `details/input-component-choice.md`（用法 `details/shared-input-components.md`）；欄位連動/計算見 `details/field-change.md`；讀 Delphi 來源見 `details/delphi-reading.md`、命名 `details/naming.md`、後端 `details/backend-sql.md`。
> ⚠️ **遇到 Delphi 封裝函式**（ERPFunc/SALFunc/MPSFunc/StkFunc 等共用庫呼叫）：先查 `details/delphi-func-lookup.md` 確認 C# 對應方法名與狀態，再查 `details/shared-functions.md` 取得處理策略（已完成/待轉/作廢/佔位規則）。

---

## 大骨架（單一 .razor）

```razor
@* ══ A. 頁首宣告 ══  詳細規則 → details/page-shell.md *@
@page "/{{MODULE}}/{{FORM}}"
@inherits IksPageBase
@inject iksFoundationCore gQL
@inject TokenStorage Token
@* {{其餘 @using：Telerik、IKSERPUI.Components.Shared.Toolbar、Models、Newtonsoft…}} *@

<PageTitle>({{FORM}}){{頁面標題}}</PageTitle>
<TelerikLoaderContainer Visible="@IsPageLoading" Text="載入中..." Size="@ThemeConstants.Loader.Size.Large" />

<div id="local-content">

    @* ══ B. 工具列 Ribbon ══  詳細規則 → details/toolbar.md *@
    <div class="toolbar toolbar-field">
        <Toolbar OnAction="HandleToolbar">
            @* {{ToolbarGroup 分組；每顆 ToolbarButton = Action+FontIcon+Title+Enabled}} *@
        </Toolbar>
    </div>
    <TelerikTooltip TargetSelector=".toolbar-field [title]" Position="@TooltipPosition.Bottom" />

    @* ══ C. 主表 Grid frame ══  詳細規則 → details/grid-virtual.md *@
    @* frame 掛 inline height:@_mqyHeight（確定高度）、grid 維持 Height="100%"：虛擬捲動才算得出視窗高度、
       正確畫列（否則列空白但可點）。高度由 frame-header「高度」combo 經 OnMqyHeightChanged 回寫（見 app.css:846）。
       @code 需宣告： private string _mqyHeight = "550px";
                      private void OnMqyHeightChanged(string h) => _mqyHeight = h; *@
    <div class="iks-master-frame" style="height:@_mqyHeight">
        <div class="iks-master-grid">
            <IksGrid_Virtual @ref="{{Grid}}" TItem="Mqy"
                             ApiName="{{查詢endpoint}}" ApiUrl="@_url" Table_Name="{{Grid}}"
                             Columns="{{ColConfig}}" WhereParameters="{{parameter}}"
                             Height="100%" ShowAdd="false"
                             ShowFrameHeader="true" ShowFilterButton="true" ShowBuiltInToolbar="false"
                             FilterAnchorClass="{{grid}}-filter-popup-target" OnFilterClick="ToggleFilterPopup"
                             OnHeightChanged="OnMqyHeightChanged"
                             OnSelect="OnMqySelect" RowKeyField="{{KEY}}" OnRowFocus="OnMqyRowFocus">
                <LeftColumnsTool>
                    @* 指令欄按鈕順序：CRUD(拷貝/修改/刪除) → 查詢(詳細資料)；純圖示+Title，不放文字 → details/grid-virtual.md *@
                    <GridCommandButton Icon="@("ti ti-copy")"   OnClick="@OnRowCopy"   Title="拷貝" />
                    <GridCommandButton Icon="@("ti ti-pencil")" OnClick="@OnRowEdit"   Title="修改" />
                    <GridCommandButton Icon="@("ti ti-trash")"  OnClick="@OnRowDelete" Title="刪除" />
                    <GridCommandButton Icon="@("ti ti-eye")"    OnClick="@OnRowDetail" Title="詳細資料" />
                </LeftColumnsTool>
            </IksGrid_Virtual>
        </div>

        @* ══ D. 進階篩選 Popup ══  詳細規則 → details/popup-filter.md *@
        <TelerikPopup @ref="@FilterPopupRef" AnchorSelector=".{{grid}}-filter-popup-target">
            @* {{iks-filter-popup：head / body(iks-filter-grid 篩選欄位) / actions(清除/查詢)}} *@
        </TelerikPopup>
    </div>
</div>

@* ══ E. 編輯表單 Window ══  詳細規則 → details/edit-window.md
   （表單本體 = iks-edit-grid 輸入欄位；含存檔/取消；右側 F. 上/下一筆） *@
<TelerikWindow Visible="@_editWindowVisible" VisibleChanged="@OnEditWindowClose" Modal="true">
    <WindowTitle>@(pageStatus == "Add" ? "新增{{X}}" : "修改{{X}}")</WindowTitle>
    <WindowContent>
        @* {{iks-edit-grid + iks-edit-row 欄位；存檔 Save()/取消 Cancel()}} *@
        @* F. 上/下一筆 → details/row-navigate.md：NavigateRow("prev"/"next") *@
    </WindowContent>
</TelerikWindow>

<MessageBox @ref="MsgBox" />

@code {
    @* ── A. 狀態/宣告 ──  details/page-shell.md ── *@
    protected override string FomId => "{{FORM}}";
    private string pageStatus = "query";              // "query" | "Add" | "Edit"
    private MessageBox MsgBox = default!;

    @* ── B/G. 工具列旗標 ──  details/btn-control.md ── *@
    private bool _AddEnabled = true;
    private bool _QueryEnabled = true;

    @* ── C. 主表欄位 ──  details/grid-virtual.md ── *@
    private IksGrid_Virtual<Mqy>? {{Grid}};
    private Mqy? MqySelect;
    private Dictionary<string, object> {{parameter}} = new();

    @* ── D. 篩選欄位 ──  details/popup-filter.md ── *@
    private TelerikPopup? FilterPopupRef;
    private bool _filterPopupVisible = false;
    private Mqy {{Filter}} = new();
    // private IksCodeComboBox? _{{field}}Combo;   // {{每個篩選控件一個 @ref，供 Reset()}}

    @* ── E. 編輯表單欄位 ──  details/edit-window.md ── *@
    private bool _editWindowVisible = false;
    private Mqy currentMqy = new();
    // private string? {{Field}}_E_Key;            // {{EditPick 的 keyword}}

    @* ── 初始載入（畫面基本方法）── firstRender 才首讀 Grid ── *@
    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        await base.OnAfterRenderAsync(firstRender);
        if (firstRender) {{Grid}}?.Rebind();
        @* 註：單檔範本走彈窗編輯（欄位 Enabled 以 pageStatus 宣告式控制），主清單是 IksGrid_Virtual、無 InCell 明細，
           故「不需」主檔明細範本那套「每次渲染 EnterEdit/ExitEdit 同步 IksGrid_vnq 編輯鎖」。
           若本頁破例嵌了 IksGrid_vnq InCell（且用 @if 顯示/隱藏），才比照 details/grid-incell.md 通則 1 補同步。*@
    }

    @* ── 工具列分派 ──  details/toolbar.md ── *@
    private async Task HandleToolbar(string action) { /* switch → Add()/Query()… ; 尾端 btnControl() */ }

    @* ── G. 按鈕控制 ──  details/btn-control.md ──（pageStatus 驅動旗標）*@
    private async Task btnControl() { /* ... */ }

    @* ── D. 篩選動作 ──  details/popup-filter.md ── *@
    private void ToggleFilterPopup() { }
    private void ClearFilter() { }         // 不關窗、只清空；各控件自呼 Reset()
    private async Task ApplyFilter() { }   // Query() 後關窗

    @* ── H. CRUD Handlers ──  details/crud-handlers.md ── *@
    private Task Query() { }               // 組 parameter → Grid.Rebind()
    private Task Add() { }                 // currentMqy=new；開 Window
    private async Task OnRowEdit(GridCommandEventArgs args) { }
    private async Task OnRowDelete(GridCommandEventArgs args) { }
    private Task Edit() { }                // 複製 MqySelect→currentMqy；開 Window
    private async Task Delete() { }        // Confirm → mutation → Rebind
    private async Task Save() { }          // 驗證必填 → Add/Update endpoint → Rebind
    private async Task Cancel() { }        // 關窗、回 query

    @* ── C. 列選取/focus ──  details/grid-virtual.md ── *@
    private void OnMqySelect(Mqy item) => MqySelect = item;
    private async Task OnMqyRowFocus(Mqy row) { }   // focus=選取

    @* ── F. 上/下一筆 ──  details/row-navigate.md ── *@
    private async Task NavigateRow(string direction) { }

    @* ── I. DTO 類別 ──  details/dto-display.md ──
       partial class Mqy : {{EFModel}}, IDisplayResolvable（加 _Display / DisplayTransform）
       ＋ {{ColConfig}}（GridColumnConfig 字典） *@
}
```

```text
J. CSS —— 詳細規則 → details/css-layout.md
   版面 class（.toolbar-field / .iks-master-frame / .iks-filter-popup / .iks-edit-grid …）
   一律進 wwwroot/app.css，勿散落頁面 <style>（記憶 shared_css_appcss）。
```

---

> 📌 **下一步**：本骨架的 `details/*.md` 逐支補齊（各含：大原則/使用規則 + 範例碼 + 眉角 + 參考控件 skill）。
> 需要做哪一區才寫哪一支，維持漸進式揭露、不一次灌爆。
