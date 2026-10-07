# 範本 ③：Excel 批次匯入（excel-import）── 大骨架

> 適用：把外部 Excel 大量匯入。父頁工具列開 `TelerikWindow`，內含匯入元件 `{Form}A.razor`（選檔→工作表→預覽 Grid→驗證→匯入）。**先辨清兩種模式再選骨架：**
>   - **主檔批次匯入**（直接寫某主檔 DB）：後端 `{form}_M_CheckImport`（只驗）＋ `{form}_M_Import`（單一交易批次寫 DB）；成功回父頁 `OnImportSuccess` → 重整主 Grid。參考 `SAL041A`（B210a 開發客戶＋聯絡人）、`SAL021A`。
>   - **明細回填**（不直接寫 DB）：只做 `{form}_M_CheckImport` 驗證，通過後把列 `OnImportConfirmed` **回傳父頁灌進明細 grid**，隨主檔存檔才寫 DB。參考 `SAL025A`（B117 銷售明細）。
> Delphi 對照：主檔 `B210a.pas`/`B11402a.pas`；明細 `B117`。來源：舊 skill `excel-import`。
> ⚠️ **for_github 新 UI**：`iks-*` 語意 class、**CSS 一律進 app.css**（記憶 `shared_css_appcss`）；**元件頭列按鈕一律 `ToolbarButton`（圖示為主＋`Title` 提示，不放文字、不用 emoji）**，包一層 `<Toolbar OnAction="HandleToolbar">`，外層掛 `toolbar-field` class 取得 `.iks-toolbar` flex 版型（見 `details/toolbar.md`）。後端流程照舊。

---

## 怎麼用這份骨架（漸進式揭露）

只放**大骨架**（擺放位置 + `@code` 欄位 + lifecycle），每區帶指標。前後端六段：

| 段 | 位置 | 指標 |
|----|------|------|
| A | 父頁面接入（匯入鈕 + Window 常駐） | 本檔 |
| B | 匯入元件 UI（選檔/工作表/預覽/錯誤/匯入鈕） | 本檔 |
| C | 匯入元件 @code（讀檔/驗證/匯入流程） | 本檔 |
| D | Resolver 薄層 | `details/crud-handlers.md` |
| E | Service 驗證 + 匯入 | `details/backend-sql.md`、`details/delphi-reading.md` |
| F | Repository 批次交易 | `details/backend-sql.md`（**一律 `_iksDbFunc.*`**） |
| G | CSS（iks-import-* 進 app.css） | `details/css-layout.md` |

---

## A. 父頁面接入

```razor
@* 工具列：延伸功能組加匯入鈕（純圖示，details/toolbar.md）*@
<ToolbarButton Action="Import" Enabled="@_ImportEnabled" FontIcon="ti ti-file-import" Title="匯入" />

@* 匯入視窗：放頁面最底、@bind-Visible 讓元件常駐 DOM（不 unmount）*@
<TelerikWindow @bind-Visible="@_ImportWindowVisible" Modal="true" Width="1200px" Height="750px">
    <WindowTitle>Excel 批次匯入</WindowTitle>
    <WindowContent>
        <{{Form}}A OnClose="@CloseImportWindow" OnImportSuccess="@OnImportSuccess" />
    </WindowContent>
</TelerikWindow>
```
```csharp
private bool _ImportWindowVisible = false;
private void OpenImportWindow()  => _ImportWindowVisible = true;
private void CloseImportWindow() => _ImportWindowVisible = false;
private async Task OnImportSuccess() { CloseImportWindow(); {{Grid}}?.Rebind(); await InvokeAsync(StateHasChanged); }
// HandleToolbar 加 "Import" => OpenImportWindow()（同步分支包 Task.CompletedTask）
```
> Window 常駐 DOM → 重開不觸發 OnInitialized，元件內 `OnAfterRenderAsync` 要**無條件** Rebind（見 C）。

---

## B. 匯入元件 `{Form}A.razor` UI（for_github 風格）

> 版面用 `iks-import-*` 語意 class（CSS 進 app.css，見 G）；**頭列按鈕一律 `ToolbarButton`（圖示為主＋`Title`），不用 emoji/文字/滿版 inline style**。
> 需 `@using IKSERPUI.Components.Shared.Toolbar`；`ToolbarButton` 必須在 `<Toolbar OnAction>` 內，外層掛 `toolbar-field` 才吃到 `.iks-toolbar` flex 版型。

```razor
@inherits IksPageBase
@inject iksFoundationCore gQL
@using IKSERPUI.Components.Shared.Toolbar
@using IKSERPUI.iksUiFunc   @* GraphQlArg.Encode *@
<TelerikLoaderContainer Visible="@_isProcessing" Text="匯入中..." Size="@ThemeConstants.Loader.Size.Large" />

<div class="iks-import-frame">

  @* ── 頭列：選檔+工作表 ｜ (重新檢查)/匯入/取消。ToolbarButton 圖示為主＋Title；外層 toolbar-field 取得 flex ── *@
  <div class="toolbar-field">
    <InputFile id="{{form}}FileInput" OnChange="OnFileSelected" accept=".xlsx,.xls,.ods" style="display:none;" />
    <Toolbar OnAction="HandleToolbar">
      <ToolbarButton Action="SelectFile" FontIcon="ti ti-file-spreadsheet" Title="選擇檔案" />
      <IksTextBox Value="@(_fileName ?? \"尚未選擇\")" Enabled="false" Width="260px" />
      <span class="iks-import-sheet-lb">工作表</span>
      <TelerikDropDownList Data="@_sheetNames" Value="@_selectedSheet" ValueChanged="@((string v) => OnSheetChanged(v))" Width="220px" Enabled="@(_sheetNames.Count > 0)" />
      <span class="iks-fspacer"></span>
      @* 可選：開放編輯預覽時加「重新檢查」（見 C 眉角）*@
      <ToolbarButton Action="ReCheck" Enabled="@(!_isProcessing && _previewData.Count > 0)" FontIcon="ti ti-refresh" Title="重新檢查" />
      <ToolbarButton Action="Import" Enabled="@(_ImportEnabled && !_isProcessing)" FontIcon="ti ti-file-import" Title="匯入" />
      <ToolbarButton Action="Cancel" FontIcon="ti ti-circle-x" Title="取消" />
    </Toolbar>
  </div>
  @* HandleToolbar 分派：SelectFile(JS 觸發隱藏 InputFile)/ReCheck/Import/Cancel（見 C）*@

  @* ── 狀態訊息（成功綠 / 失敗紅，class 控色）── *@
  @if (!string.IsNullOrEmpty(_statusMsg)) { <div class="iks-import-status @(_isError ? \"is-error\" : \"is-ok\")">@_statusMsg</div> }

  @* ── 預覽 Grid（IksGrid_vnq）。可選：開放 InCell 編輯讓使用者就地修錯 → 綁 OnUpdate（見 C 眉角）── *@
  <div class="iks-import-preview">
    <IksGrid_vnq @ref="_grid" TItem="ImportRow" GridData="@_previewData" Table_Name="{{Form}}A_Grid"
                 ApiUrl="@_url" Columns="_columns" OnUpdate="PreviewUpdateHandler"
                 ShowAdd="false" ShowBuiltInToolbar="false" ShowFrameHeader="true" Height="100%" />
  </div>

  @* ── 錯誤清單：TelerikGrid **不可加 Scrollable**（會 NRE），用 iks-import-errbox（app.css: max-height+overflow）── *@
  @if (_errorList.Count > 0)
  {
    <div class="iks-import-errors">
      <div class="iks-import-errtitle"><i class="ti ti-alert-triangle"></i>驗證失敗明細（共 @_errorList.Count 筆）</div>
      <div class="iks-import-errbox">
        <TelerikGrid Data="@_errorList"><GridColumns>
          <GridColumn Field="@nameof(ErrorItem.Row)" Title="列號" Width="70px" />
          <GridColumn Field="@nameof(ErrorItem.Msg)" Title="錯誤原因" />
        </GridColumns></TelerikGrid>
      </div>
    </div>
  }
</div>
<TelerikTooltip TargetSelector=".toolbar-field [title]" Position="@TooltipPosition.Bottom" />
<MessageBox @ref="MsgBox" />
```

### G. CSS（進 app.css，勿頁面 <style>）
```css
.iks-import-frame   { display:flex; flex-direction:column; height:100%; gap:6px; padding:8px; box-sizing:border-box; }
.iks-import-head    { display:flex; align-items:center; gap:8px; }
.iks-import-file    { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.iks-import-sheet-lb{ font-weight:600; white-space:nowrap; margin-left:8px; }
.iks-import-actions { display:flex; gap:6px; }
.iks-import-status  { font-weight:600; padding:2px 0; }
.iks-import-status.is-ok    { color:#16a34a; }
.iks-import-status.is-error { color:#dc2626; }
.iks-import-preview { flex:1 1 auto; min-height:0; }
.iks-import-errtitle{ font-weight:600; color:#dc2626; font-size:13px; margin-bottom:4px; display:flex; align-items:center; gap:4px; }
.iks-import-errbox  { max-height:140px; overflow-y:auto; }   /* 取代 TelerikGrid Scrollable，避免 NRE */
```

---

## C. 匯入元件 @code（骨架）

```csharp
[Parameter] public EventCallback OnClose { get; set; }
[Parameter] public EventCallback OnImportSuccess { get; set; }
protected override string FomId => "{{FORM}}";
private string _url => iksService.ApiUrl;
private MessageBox MsgBox = default!;

// 狀態
private bool _isProcessing, _ImportEnabled, _isError;
private string? _fileName, _statusMsg;
// 檔案/工作表
private IksExcelWorkbook? _workbook; private List<string> _sheetNames = new(); private string _selectedSheet = "";
// 預覽 + 錯誤
private IksGrid_vnq<ImportRow>? _grid; private List<ImportRow> _previewData = new(); private List<ErrorItem> _errorList = new();
private class ErrorItem { public int Row { get; init; } public string Msg { get; init; } = ""; }

// 必要欄位（對應 Excel 標題列，依 Delphi 必填/欄位清單）
private static readonly string[] RequiredCols = { "{{COL1}}", "{{COL2}}" /* … */ };
// 每個 Excel 欄位一個屬性（+ ImportStatus/ErrorMsg）
private class ImportRow { public string ImportStatus = ""; public string {{COL1}} = ""; /* … */ public string ErrorMsg = ""; }
private Dictionary<string, GridColumnConfig> _columns => new() {
    { "ImportStatus", new(){ Field="ImportStatus", Title="Status", Editable=false, Width="60px" } },
    { "{{COL1}}",     new(){ Field="{{COL1}}", Title="{{標題}}", Editable=false, Width="100px" } },
    { "ErrorMsg",     new(){ Field="ErrorMsg", Title="Error", Editable=false, Width="200px" } },
};

// 選檔 → 讀 workbook → 預設第一工作表 → LoadSheetData
private async Task OnFileSelected(InputFileChangeEventArgs e) {
    var file = e.File; if (file == null) return;
    _fileName = file.Name; /* 重置 sheet/preview/error/ImportEnabled */ _statusMsg = "讀取中...";
    using var stream = file.OpenReadStream(maxAllowedSize: 52_428_800);
    _workbook = await iksExpOffice.LoadExcelWorkbookAsync(stream, file.Name);
    _sheetNames = _workbook.SheetNames.ToList();
    if (_sheetNames.Count > 0) { _selectedSheet = _sheetNames[0]; await LoadSheetData(_selectedSheet); }
}
private async Task OnSheetChanged(string s) { _selectedSheet = s; /* 重置 preview/error */ await LoadSheetData(s); }

// 讀工作表 → 檢查必要欄位 → 映射 ImportRow → 自動驗證
private async Task LoadSheetData(string sheetName) {
    var sheet = _workbook!.GetSheet(sheetName); if (sheet == null) return;
    var missing = RequiredCols.Where(c => !sheet.GetHeaderRow().Contains(c)).ToList();
    if (missing.Any()) { _statusMsg = $"缺少必要欄位：{string.Join(\", \", missing)}"; _isError = true; return; }
    _previewData = sheet.GetDataRows().Select(row => new ImportRow { {{COL1}} = row.GetValueOrDefault("{{COL1}}", "") /* … */ }).ToList();
    _grid?.Rebind(_previewData); await CheckImportData();
}

// 驗證：呼叫後端 CheckImport；錯誤格式 "行號:訊息|行號:訊息"
private async Task CheckImportData() {
    if (_previewData.Count == 0) return;
    var result = await gQL.ApiCallAsync(_url, "mutation", "{{form}}_M_CheckImport",
        new() { ["rows"] = GraphQlArg.Encode(BuildPayload()) });   // Base64 傳列，含 " ' 換行的資料避免 HC0011（記憶 graphql_arg_base64）
    _errorList = new();
    if (result?.status == -1 && !string.IsNullOrEmpty(result.message)) {
        _isError = true;
        foreach (var e in result.message.Split('|', StringSplitOptions.RemoveEmptyEntries)) {
            var p = e.Split(':', 2);
            if (p.Length == 2 && int.TryParse(p[0], out int i)) { _errorList.Add(new(){ Row=i, Msg=p[1] }); if (i>0 && i<=_previewData.Count) _previewData[i-1].ImportStatus = "✗"; }
        }
        _statusMsg = $"驗證失敗（{_errorList.Count} 筆），請修正後重新匯入";
    } else { foreach (var r in _previewData) r.ImportStatus = "✓"; _statusMsg = $"驗證通過（共 {_previewData.Count} 筆）"; }
    _ImportEnabled = !_isError; _grid?.Rebind(_previewData);
}

// 匯入：呼叫後端 Import；成功 → OnImportSuccess
private async Task Import() {
    _isProcessing = true; _ImportEnabled = false;
    try {
        var result = await gQL.ApiCallAsync(_url, "mutation", "{{form}}_M_Import",
            new() { ["rows"] = GraphQlArg.Encode(BuildPayload()) });
        if (result?.status == 1) { await MsgBox.Show(result.message ?? "匯入完成", "匯入", "success"); await OnImportSuccess.InvokeAsync(); }
        else { /* 解析 result.message 成 _errorList；_statusMsg="匯入失敗"；_isError=true */ }
    } finally { _isProcessing = false; }
}
private async Task Cancel() => await OnClose.InvokeAsync();

// 頭列 ToolbarButton.Action 分派；SelectFile 以 JS 觸發隱藏 InputFile
private async Task HandleToolbar(string action) {
    switch (action) {
        case "SelectFile": await JS.InvokeVoidAsync("eval", "document.getElementById('{{form}}FileInput').click()"); break;
        case "ReCheck": await ReCheck(); break;   // 僅開放編輯預覽時需要（見 C-2）
        case "Import":  await Import();  break;
        case "Cancel":  await Cancel();  break;
    }
}
private List<Dictionary<string, string>> BuildPayload() => _previewData.Select(r => new Dictionary<string, string> { ["{{COL1}}"] = r.{{COL1}} /* … */ }).ToList();

// Window 常駐 DOM → 每次 render 無條件 Rebind（不加 firstRender 判斷）
protected override async Task OnAfterRenderAsync(bool firstRender) { await base.OnAfterRenderAsync(firstRender); _grid?.Rebind(_previewData); }
```

### C-2. 可編輯預覽 + 重新檢查（選用；讓使用者就地修錯再驗，不必重存 Excel）

欄位多時 `ImportRow` 改用 **`Data` 字典 + get/set 顯示屬性**（比幾十個欄位屬性乾淨），並加 `_rowId` 供 InCell 寫回：

```csharp
public class ImportRow {
    public Guid _rowId { get; set; } = Guid.NewGuid();
    public string ImportStatus { get; set; } = "";  public string ErrorMsg { get; set; } = "";
    public Dictionary<string,string> Data { get; set; } = new();
    // 只為「要顯示/可編輯」的欄位開 get/set（讀寫回 Data；InCell 編輯即改 Data）；未顯示欄仍在 Data、原值照送
    public string {{COL1}} { get => Data.GetValueOrDefault("{{COL1}}", ""); set => Data["{{COL1}}"] = value ?? ""; }
}
// _columns：可編輯欄 Editable=true（狀態/錯誤欄 Editable=false）；grid 綁 OnUpdate="PreviewUpdateHandler"
// BuildPayload 直接送 Data：_previewData.Select(r => r.Data).ToList()

// InCell 提交：依 _rowId 寫回。⚠ 勿在此呼叫 ExitEditModeAsync（會反觸發 OnUpdate → 無窮遞迴 StackOverflow，見 details/grid-incell.md）
private async Task PreviewUpdateHandler(GridCommandEventArgs args) {
    var row = (ImportRow)args.Item; int i = _previewData.FindIndex(r => r._rowId == row._rowId);
    if (i < 0) return; _previewData[i] = row; if (_grid != null) await _grid.RebindKeepState(_previewData);
}
// 「重新檢查/匯入」等動作鈕才先提交儲存格再做事（動作 handler 可安全呼叫 ExitEditModeAsync）
private async Task ReCheck() { if (_grid != null) await _grid.ExitEditModeAsync(); await CheckImportData(); }
// Import() 開頭亦加：if (_grid != null) await _grid.ExitEditModeAsync();
```
> 顯示欄應涵蓋**所有會被後端驗證的欄位**，使用者才能在 grid 內修正全部錯誤；未顯示欄以 Excel 原值匯入。

### C-3. 預覽列直接刪除（選用；不必重新上傳檔案就移除錯誤/不要的列）

預覽 grid 加「指令」`GridCommandColumn` + 刪除鈕（純圖示＋Title，記憶 `gridcommandbutton_style`）；直接從 `_previewData` 移除（記憶 `incell_delete_direct`），刪後重新驗證更新狀態/錯誤明細/匯入鈕。

```razor
<IksGrid_vnq @ref="_grid" TItem="ImportRow" GridData="@_previewData" ... Height="100%">
    <LeftColumnsTool>
        <GridCommandButton Icon="@("ti ti-trash")" OnClick="@(args => DeletePreviewRow((ImportRow)args.Item))" ShowInEdit="false" Title="刪除" />
    </LeftColumnsTool>
</IksGrid_vnq>
```
```csharp
private async Task DeletePreviewRow(ImportRow row) {
    _previewData.Remove(row);
    _grid?.Rebind(_previewData);
    if (_previewData.Any()) await CheckImportData();   // 重新驗證，更新每列 ImportStatus/錯誤明細/匯入鈕
    else { _errorList = new(); _ImportEnabled = false; _isError = false; _statusMsg = "已無資料列"; }
    await InvokeAsync(StateHasChanged);
}
```
> 實例：`SAL050Import`。錯誤格式的行號對應 `_previewData` 索引，刪後 `CheckImportData` 會重驗，行號自然對齊新清單。

---

## D~F. 後端（薄層 → 驗證 → 批次交易）

```csharp
// D. Resolver（{Form}Mutation.cs 薄層）→ details/crud-handlers.md
public async Task<mutationResult?> {{form}}_M_CheckImport(string arg, [Service] DapperContext context) => await _{{mod}}Service.CheckImport{{Form}}Async(arg, context);
public async Task<mutationResult?> {{form}}_M_Import(string arg, [Service] DapperContext context)      => await _{{mod}}Service.Import{{Form}}Async(arg, context);

// E. Service：CheckImport 只驗不寫；Import 先驗再寫。共用 ValidateImportRowsAsync
//    驗證順序（對齊 Delphi）：①主鍵空白→continue ②必填空白 ③長度上限 ④套預設值 ⑤代碼合法性 DB 檢查
//    錯誤累積成 "行號:訊息|…"（string.Join("|", errors)）

// F. Repository 批次交易 —— 寫入一律 _iksDbFunc.* 的 conn/tx 多載（禁止直呼 conn.ExecuteAsync；details/backend-sql.md）
//    「已存在→略過 or 更新」依 Delphi：B210a 為**略過不更新**；其他頁可能是 update。
public async Task<(int inserted, int skipped)> BatchImport{{Form}}Async(List<Dictionary<string,string>> rows) {
    using var conn = _context.CreateConnection(); conn.Open(); using var tx = conn.BeginTransaction();
    int ins = 0, skip = 0;
    var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);   // 攔同批重複主鍵（本交易未 commit，跨連線讀不到，不能只靠 DB 查）
    try {
        foreach (var r in rows) {
            string pk = r["{{PK}}"];
            // 存在性檢查是讀取，走非交易多載即可（查已 commit 資料；避免某些 repo 未提供 SQLValue 的 conn/tx 多載）
            int exists = await _iksDbFunc.SQLValue<int>("SELECT COUNT(*) FROM {{TABLE}} WHERE {{PK}}=@PK", new { PK = pk });
            if (exists > 0 || !seen.Add(pk)) { skip++; continue; }
            await _iksDbFunc.SQLExec("INSERT INTO {{TABLE}} (…) VALUES (…)", conn, tx, r); ins++;   // +子表（如 SA_NRPNM 聯絡人 ITM 1/2/3）
        }
        tx.Commit(); return (ins, skip);
    } catch { tx.Rollback(); throw; }
}
```
> ⚠ **FK 代碼驗證用「現行 schema」的表**，勿照抄 Delphi 舊表名（可能已換表，如 B210a `SA_SALER` → 現行 `HR_EMPLYM`；比對該頁 `_Display`/ComboBox 走哪張表）。

---

## 關鍵規則
1. **TelerikWindow 常駐 DOM**：`@bind-Visible` 不 unmount → 元件 `OnAfterRenderAsync` **無條件** `_grid?.Rebind(_previewData)`（不加 firstRender）。
2. **錯誤清單 TelerikGrid 不可加 `Scrollable`**（`GridScrollMode.Scrollable` 會 `RemoteJSRuntime` NRE）→ 用外層 div `max-height + overflow-y:auto`。
3. **驗證順序**（對齊 Delphi）：主鍵空白 continue → 必填空白 → 長度上限 → 套預設值 → 代碼合法性 DB 檢查。
4. **匯入鈕開關**：`errors.Count == 0` → `_ImportEnabled=true`；失敗/無資料 → false。
5. **批次交易一律 `_iksDbFunc.*` 的 conn/tx 多載**，全成才 commit（`details/backend-sql.md`）。
6. 匯入成功回父頁 `OnImportSuccess` → 父頁 Rebind 主 Grid（主檔模式）；明細模式改回 `OnImportConfirmed(rows)` 灌明細。
7. Excel 讀取用 `iksExpOffice.LoadExcelWorkbookAsync` → `IksExcelWorkbook`（`SheetNames`/`GetSheet`/`GetHeaderRow`/`GetDataRows`）。
8. **頭列按鈕一律 `ToolbarButton`（圖示為主＋`Title` 提示）**，包 `<Toolbar OnAction="HandleToolbar">`＋外層 `toolbar-field`；不放文字、不用 emoji、不用滿版 inline style（見 `details/toolbar.md`）。
9. **rows 用 Base64**：`iksUiFunc.GraphQlArg.Encode`（前端）＋ `Modules.FUNC.GraphQlArg.DecodeArg`（後端）——客戶名稱/地址含 `" ' 換行` 直送會 HC0011 解析失敗（記憶 `graphql_arg_base64`）。
10. **可編輯預覽（選用）**：`ImportRow` 用 `Data` 字典＋get/set＋`_rowId`；grid 綁 `OnUpdate` 依 `_rowId` 寫回，**⚠ OnUpdate 內勿呼叫 `ExitEditModeAsync`**（會遞迴 StackOverflow）；「重新檢查/匯入」等動作鈕才先 `ExitEditModeAsync` 提交（見 C-2 與 `details/grid-incell.md`）。
11. **FK 代碼驗證用現行 schema 的表**，非 Delphi 舊表名（見 F 段警語）。
12. **預覽列直接刪除（選用）**：「指令」`GridCommandColumn` + 刪除鈕直接從 `_previewData` 移除、重新驗證，不必重傳檔案（見 C-3；實例 `SAL050Import`）。

> 完整實作參考：主檔批次匯入 `SAL041A`（B210a，可編輯預覽＋重新檢查）、`SAL021A`；明細回填 `SAL025A`（B117）。Delphi 對照 `D:\ikserp\MT\SAL\{B210a,B11402a}.pas`。
