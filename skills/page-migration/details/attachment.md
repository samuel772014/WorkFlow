# 詳細規則：K. 附件 PDF 上傳 / 下載 / 預覽（iksUiFunc.FileFunc）

> 骨架指標來源：`templates/master-detail.md` K 區（如備註 Tab 附件）；單檔若有附件亦適用。
> 對應 Delphi：`UPLoadATTACH(...)`。來源：舊 skill `iksUiFunc` 彙整。

---

## 架構（已全域可用）
```
IKSERPUI/iksUiFunc/FileFunc.cs             靜態方法庫（UI 呼叫）
IKSERPAPI/Modules/COMMON/FileController.cs REST：POST /api/file/upload、GET /api/file/download
IKSERPUI/wwwroot/js/pageJs.js              JS（Blob 下載/預覽）
```
- `_Imports.razor` 已全域 `@using IKSERPUI.iksUiFunc`，免個別宣告。
- 頁面只需 `@inject IHttpClientFactory HttpClientFactory`；`IJSRuntime JS` 由 `IksPageBase` 提供。
- HttpClient 一律 `HttpClientFactory.CreateClient("ApiAuth")`。

## 三個方法
```csharp
FileFunc.UploadPdfAsync(client, stream, fileName, moduleGroup, moduleName) → (Success, FileName, FilePath, Error)
FileFunc.PreviewPdfAsync(JS, client, filePath, fileName)                    → (Success, Error)   // blob 新視窗
FileFunc.DownloadPdfAsync(JS, client, filePath, fileName)                   → (Success, Error)   // showSaveFilePicker，Firefox 降級直下
```
- `moduleGroup`=模組群（如 `"SAL"`）、`moduleName`=模組碼（如 `"SAL301"`）→ 存到 `Modules/{群}/{碼}_DATA/`。
- 目前限 `.pdf`；上傳大小上限 `52_428_800`。

## DB 慣例欄位
| 欄位 | 型別 | 說明 |
|------|------|------|
| `ATTACHFILE` | nvarchar(60) | 檔名（`test.pdf`） |
| `ATTACHPATH` | nvarchar(200) | 相對路徑（`Modules/SAL/SAL301_DATA/test.pdf`） |
> **路徑一律正斜線 `/`**（`Path.Combine` 的反斜線會破壞存 DB 的 JSON，勿用）。

## 上傳後立即回寫（不等整單存檔）
上傳成功即打薄層 mutation `{form}_UpdateAttach` 回寫 ATTACHFILE/ATTACHPATH（前提：主檔單號已存在）。

---

## 【範例程式碼】(SAL301 備註 Tab)
```razor
@inject IHttpClientFactory HttpClientFactory
<div style="display:flex; gap:4px; align-items:center;">
    <TelerikTextBox Value="@(current.ATTACHFILE ?? "")" Enabled="false" Width="180px" />
    <InputFile id="sal301AttachInput" OnChange="UploadAttachFileAsync" accept=".pdf" style="display:none;" />
    <TelerikButton OnClick="@(async () => await JS.InvokeVoidAsync(\"eval\", \"document.getElementById('sal301AttachInput').click()\"))" Enabled="@_UploadEnabled">上傳PDF</TelerikButton>
    @if (!string.IsNullOrEmpty(current.ATTACHFILE))
    {
        <TelerikButton OnClick="PreviewAttachFileAsync" Enabled="@_PreviewEnabled">預覽PDF</TelerikButton>
        <TelerikButton OnClick="DownloadAttachFileAsync" Enabled="@_DownloadEnabled">下載PDF</TelerikButton>
    }
</div>
```
```csharp
private async Task UploadAttachFileAsync(InputFileChangeEventArgs e) {
    var file = e.File; if (file == null) return;
    using var stream = file.OpenReadStream(maxAllowedSize: 52_428_800);
    var client = HttpClientFactory.CreateClient("ApiAuth");
    var (ok, attachFile, attachPath, err) = await FileFunc.UploadPdfAsync(client, stream, file.Name, "SAL", "SAL301");
    if (!ok) { await MsgBox.Show(err!, "業務系統", "error"); return; }
    if (!string.IsNullOrEmpty(current.QUOTNO))    // 已有單號 → 立即回寫
        await gQL.MultipleDataApiCallAsync(_url, "mutation", "sal301_UpdateAttach",
            new() { ["arg"] = JsonConvert.SerializeObject(new { current.QUOTNO, ATTACHFILE = attachFile, ATTACHPATH = attachPath }) });
    current.ATTACHFILE = attachFile; current.ATTACHPATH = attachPath;
    await InvokeAsync(StateHasChanged);
}
private async Task PreviewAttachFileAsync() {
    if (string.IsNullOrEmpty(current.ATTACHPATH)) return;
    var (ok, err) = await FileFunc.PreviewPdfAsync(JS, HttpClientFactory.CreateClient("ApiAuth"), current.ATTACHPATH, current.ATTACHFILE ?? "");
    if (!ok) await MsgBox.Show(err!, "業務系統", "error");
}
private async Task DownloadAttachFileAsync() {
    if (string.IsNullOrEmpty(current.ATTACHPATH)) return;
    var (ok, err) = await FileFunc.DownloadPdfAsync(JS, HttpClientFactory.CreateClient("ApiAuth"), current.ATTACHPATH, current.ATTACHFILE ?? "");
    if (!ok) await MsgBox.Show(err!, "業務系統", "error");
}
```

## 【骨架程式碼】
```razor
@inject IHttpClientFactory HttpClientFactory
<InputFile id="{{form}}AttachInput" OnChange="UploadAttachFileAsync" accept=".pdf" style="display:none;" />
<TelerikButton OnClick="@(async () => await JS.InvokeVoidAsync(\"eval\", \"document.getElementById('{{form}}AttachInput').click()\"))">上傳PDF</TelerikButton>
@* 有檔才顯示 預覽/下載 *@
```
```csharp
private async Task UploadAttachFileAsync(InputFileChangeEventArgs e) {
    var file = e.File; if (file == null) return;
    using var stream = file.OpenReadStream(maxAllowedSize: 52_428_800);
    var (ok, af, ap, err) = await FileFunc.UploadPdfAsync(HttpClientFactory.CreateClient("ApiAuth"), stream, file.Name, "{{MODULE_GROUP}}", "{{FORM}}");
    if (!ok) { await MsgBox.Show(err!, "業務系統", "error"); return; }
    if (!string.IsNullOrEmpty(current.{{PK}}))
        await gQL.MultipleDataApiCallAsync(_url, "mutation", "{{form}}_UpdateAttach",
            new() { ["arg"] = JsonConvert.SerializeObject(new { current.{{PK}}, ATTACHFILE = af, ATTACHPATH = ap }) });
    current.ATTACHFILE = af; current.ATTACHPATH = ap; await InvokeAsync(StateHasChanged);
}
// Preview/Download 同上，呼叫 FileFunc.PreviewPdfAsync / DownloadPdfAsync
```

## 後端薄層（回寫）
```csharp
// {{Form}}Mutation.cs
public async Task<mutationResult?> {{form}}_UpdateAttach(string arg, [Service] DapperContext context)
    => await _{{mod}}Service.Update{{Form}}AttachAsync(arg, context);
// Repository: UPDATE {{TABLE}} SET ATTACHFILE=@ATTACHFILE, ATTACHPATH=@ATTACHPATH WHERE {{PK}}=@{{PK}}
```

## 指路
- 按鈕啟用（_UploadEnabled 等）→ `details/btn-control.md`
- 上傳回寫走 mutation → `details/crud-handlers.md`（記憶 `mutation_pattern`）
