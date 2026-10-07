# 詳細規則：A. 頁面殼（宣告 / 狀態 / 生命週期）

> 骨架指標來源：`templates/*` A 區。對應 Delphi：`TfmEditForm` 基底（→ `IksPageBase`）。
> 所有頁面 `@inherits IksPageBase`。

---

## 頁首宣告
```razor
@page "/{{MODULE}}/{{FORM}}"
@inherits IksPageBase
@inject iksFoundationCore gQL            @* GraphQL 呼叫 *@
@inject TokenStorage Token
@* 有附件才加：@inject IHttpClientFactory HttpClientFactory（details/attachment.md）*@
@using System.Data
@using Telerik.Blazor
@using Telerik.Blazor.Components
@using IKSERPUI.Components.Shared.Toolbar
@using IKSERPSHARE.Models
@using IKSERPUI.Components.Attributes
@using Newtonsoft.Json

<PageTitle>({{FORM}}){{頁面標題}}</PageTitle>
<TelerikLoaderContainer Visible="@IsPageLoading" Text="載入中..." Size="@ThemeConstants.Loader.Size.Large" />
```

## IksPageBase 提供的成員（免自己宣告）
| 成員 | 說明 |
|------|------|
| `_url` | API 端點（`=> iksService.ApiUrl`）——**勿寫死 `/gqlway`** |
| `EmplyId` | 登入者**員工代號**（EIP token 的 `EMPLYID` claim），OnInitializedAsync 由 **JWT 非同步**帶入。⚠ 與帳號 `USRID` 是不同 claim，詳見下方「取登入者身分」 |
| `JS` | `IJSRuntime`（附件/JS 互操作用，免再 inject） |
| `IsPageLoading` | 載入遮罩旗標；JS 初始化完成自動轉 false |
| `SetPageLoaded()` / `SetPageLoading()` | 手動解除/顯示遮罩 |
| `FomId`（virtual，覆寫） | 功能代碼，驅動多語系字典 `LoadDictionaryAsync(FomId)` |

## @code 狀態欄位（依範本）
```csharp
protected override string FomId => "{{FORM}}";        // 覆寫；多語系用
private string pageStatus = "query";                  // 單檔：query|Add|Edit|View；明細另加 Copy
// 明細範本再加：
// private string ActiveTabId = "query";              // 模式膠囊 query|edit
// private string ActiveDetailTabId = "d1";           // 明細頁籤
// private bool _showDetail = true;
private MessageBox MsgBox = default!;
```

---

## 生命週期規則（踩雷區）

### `OnAfterRenderAsync` — **必須先 `await base`**
```csharp
protected override async Task OnAfterRenderAsync(bool firstRender) {
    await base.OnAfterRenderAsync(firstRender);   // ← 必須！否則遮罩卡死＋鍵盤沒 init
    if (firstRender) {{Grid}}?.Rebind();          // firstRender 才首讀主檔
}
```
- `IksPageBase.OnAfterRenderAsync(firstRender=true)` 負責 `iksKeyboardInterop.init` 與（若未提前 `SetPageLoaded`）自動把 `IsPageLoading` 設 false。**漏 `await base` → 遮罩永遠不消、畫面卡死**。

### `OnInitializedAsync` — 覆寫要 `await base`，且 EmplyId 之後才有值
```csharp
protected override async Task OnInitializedAsync() {
    await base.OnInitializedAsync();   // 載多語系字典 + 由 JWT 取 EmplyId
    // 這裡才能用 EmplyId
}
```
- **`EmplyId` 是 base OnInitializedAsync 非同步（JWT）帶入** → **勿在欄位初始化式引用 `EmplyId`**（那時還是空字串）。要用登入者代號一律在 `OnInitializedAsync`（await base 之後）或更晚。（彙整記憶 `emplyid_ikspagebase`）
- 有額外非同步初始資料時，載完可在結尾 `SetPageLoaded()` 提前解遮罩。

## 取登入者身分（EmplyId / 帳號 / 名稱等）

> 登入身分**全部來自 EIP token 的 claim**（EIP 登入時就查好 `EIP_USR` + `EIP_USRMAPPING` 等寫進 token，經交接鏈原封抄進 ERP cookie）。**ERP 端不需要、也不要自己拿 USRID 去 SQL 反查這些值**。

### 可直接取用的身分 claim（EIP token 帶進來）
| claim | 內容 | 常用取法 |
|-------|------|---------|
| `EMPLYID` | 員工代號 | 頁面直接用 `EmplyId`（base 已帶入） |
| `USRID` | 登入**帳號** | `authState.User.FindFirst("USRID")?.Value` |
| `USRNM` | 使用者**名稱** | `authState.User.FindFirst("USRNM")?.Value` |
| `ENTID`/`ENTNM` | 企業代號/名稱 | 同上，換 claim 名 |
| `UNITID`/`UNITNM` | 單位代號/名稱 | 同上 |
| `LANGID` | 語系 | 同上（一般走 `iksService.LangId`） |

> ⚠ `EMPLYID` 有值的前提：該帳號 `EIP_USR.ENTID` 非空且 `EIP_USRMAPPING(USRID,ENTID)` 有對應列，否則 claim 為空字串。帶進來是空的先查那兩張表。

### 頁面內取員工代號 → 直接用 `EmplyId`
```csharp
protected override async Task OnInitializedAsync() {
    await base.OnInitializedAsync();     // ← EmplyId 在此之後才有值
    _usr = EmplyId;                      // 之後任意處都可用 EmplyId
}
// 傳給 API：post["USERID"] = EmplyId;（arg 名沿用後端既有慣例，值放 EmplyId）
```
- ✅ 正例：`SAL050` 存檔 `FEMPLYID = EmplyId`、`["USERID"] = EmplyId`。
- ❌ 反例：`private string _usr = "00001";` 寫死假值，或欄位初始化式 `= EmplyId`（那時恆空）。

### 頁面外（元件/服務）取 → 注入 `iksService`
```csharp
[Inject] iksService iksService { get; set; } = default!;
var emplyid = await iksService.GetEmplyIdAsync();   // 讀 EMPLYID claim
```
其餘 claim 注入 `AuthenticationStateProvider`、`(await GetAuthenticationStateAsync()).User.FindFirst("<CLAIM>")`。

### 分界：claim vs. 進 API 查 SQL
- **只要 claim 現成的值（emplyid / 帳號 / 名稱…）** → UI 層讀 claim，屬便利性邏輯，**不進後端**。
- **要用 USRID/EMPLYID 去 ERP 資料庫查衍生資料**（如查 `SA_SALER` 判斷是否業務員、帶部門）→ 屬業務邏輯，**一律放 API 層**（`details/business-logic.md`、`backend-sql.md`；範例 `SALRepository.SAL046` 的 `QuerySAL046NewMqyDefaultsAsync`）。

---

### 底部固定元件
```razor
<MessageBox @ref="MsgBox" />
```

---

## 【骨架程式碼】
```razor
@page "/{{MODULE}}/{{FORM}}"
@inherits IksPageBase
@inject iksFoundationCore gQL
@inject TokenStorage Token
<PageTitle>({{FORM}}){{標題}}</PageTitle>
<TelerikLoaderContainer Visible="@IsPageLoading" Text="載入中..." Size="@ThemeConstants.Loader.Size.Large" />
@* … 版面（templates/*）… *@
<MessageBox @ref="MsgBox" />
@code {
    protected override string FomId => "{{FORM}}";
    private string pageStatus = "query";
    private MessageBox MsgBox = default!;
    // grid/filter/current/明細 欄位宣告 → 各 details

    protected override async Task OnAfterRenderAsync(bool firstRender) {
        await base.OnAfterRenderAsync(firstRender);
        if (firstRender) {{Grid}}?.Rebind();
    }
    // 需登入者代號/額外初始 → 覆寫 OnInitializedAsync 並 await base（EmplyId 才有值）
}
```

## 指路
- 版面/區塊 → `templates/single-file.md`｜`master-detail.md`｜`excel-import.md`
- 主檔清單 grid（含首讀 Rebind、鍵盤）→ `details/grid-virtual.md`
- 按鈕狀態 → `details/btn-control.md`
- 命名（FomId/路由）→ `details/naming.md`
