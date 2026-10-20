# 詳細規則：明細 grid EditorTemplate ＋ EditPick_Button（控件）

> 給 `details/grid-incell.md`／`details/dto-display.md`／`details/shared-input-components.md` 指來：明細 grid 內可 pick/編輯欄位的 EditorTemplate 寫法。
> 對應 Delphi：DFM `ControlType 'X;CustomEdit;xxxPick'` 或 `.pas` `DqnDblClick`。來源：舊 `editpick-mapping` 彙整。

---

## 何時用 EditPick_Button（而非 EditPick / ComboBox）
- 欄位在 `IksGrid_vnq` 明細的 `EditorTemplate` 內（**不論欄數**）→ `EditPick_Button` + 頁面層級 `@ref`。
- 或選取後需**回寫 3 個以上欄位**。
- **禁止在 EditorTemplate 內 inline 宣告 Picker**（每列各建實例會壞）。
- 主表 ≤2 欄→`IksCodeComboBox`、KeyCode→`KeyCodeComboBox`、日期→`TelerikDatePicker`（決策 → `details/input-component-choice.md`）。
- **`DqnDblClick` 是 `EditMemo(...)`（多行長文字放大視窗）不是 pick** → 改用 **`PopUpText`**（EditorTemplate 內 TextBox＋放大鈕開窗），不是 `EditPick_Button`；用法與泛型多欄共用寫法見 `details/popuptext.md`。

## 五步驟

**1. 頁面層級宣告（所有 grid 之外，靜態屬性）**
```razor
<EditPick_Button @ref="EditPickNSN" TItem="Dq1" Url="@_url" Width="130px" FixedPost="@_nsnFixedPost" />  @* FixedPost 每次點擊換新參考才會開窗 *@
```
**2. @code 變數**
```csharp
private EditPick_Button<Dq1> EditPickNSN = null!;
private Dictionary<string, string>? _nsnFixedPost;   // 每次點擊換新參考，觸發子元件重繪開窗
```
**3. EditorTemplate（TextBox/NumericTextBox + SuffixTemplate 鈕）**
```csharp
private RenderFragment<Dq1> NSNTemplate => item =>
@<div style="display:inline-block; min-width:0;">
    <TelerikTextBox @bind-Value="item.NSN" Width="150px">
        <TextBoxSuffixTemplate>
            <TelerikButton OnClick="@(() => Dq1_NSN_Click(item))" Icon="@Telerik.SvgIcons.SvgIcon.MoreVertical" />
        </TextBoxSuffixTemplate>
    </TelerikTextBox>
</div>;
// ColConfig: { "NSN", new GridColumnConfig{ Field="NSN", ..., EditorTemplate=(c)=>NSNTemplate((Dq1)c) } }
```

> ⚠️ **回傳型別眉角**：
> - **屬性 + `item =>` 形式**（上例）用 `RenderFragment<T>`（`RenderFragment<Dq1> Xxx => item => @<...>`）。
> - **方法帶額外參數**（如多欄共用一個 memo template，帶 `get/set`）時，方法本體 `@<...>` 產生的是**非泛型 `RenderFragment`**，方法**回傳型別必須是 `RenderFragment`（不是 `RenderFragment<T>`）**，否則 Razor 產生器會把它當 templated 元件、報 `Txxx 未包含 OpenComponent`（CS1061/CS0029/CS1643）。
>   ```csharp
>   // 對：帶 get/set 的共用 memo template
>   private RenderFragment MemoTemplate(Dq3 item, Func<Dq3,string?> get, Action<Dq3,string?> set) =>
>   @<TelerikTextArea Value="@get(item)" ValueChanged="@((string v)=>set(item,v))" Width="100%" Rows="2" />;
>   // ColConfig: EditorTemplate=(c)=>MemoTemplate((Dq3)c, r=>r.SWOT, (r,v)=>r.SWOT=v)
>   ```
**4. Click handler（命令式設查詢條件並開窗；每次重設確保多 Picker 各自獨立）**
```csharp
private void Dq1_NSN_Click(Dq1 data) {
    EditPickNSN.QueryWay = "{{form}}_GetDQ1_MM_ITMMASTR";
    EditPickNSN.QueryGet = "NSN ITMCNM SPECNM";
    EditPickNSN.Columns  = new List<EditPick_Button<Dq1>.PickColumn> {
        new(){ Title="料品編號", Field="NSN", Width="110px" },
        new(){ Title="料品名稱", Field="ITMCNM", Width="130px" },
        new(){ Title="料品規格", Field="SPECNM", Width="130px" },
    };
    EditPickNSN.curritem = data;
    _nsnFixedPost = new() { { "_sortBy", "NSN" } };   // 換新參考（有連動條件就放條件）
    // EditPickNSN.Apply = …（第 5 步）
    EditPickNSN.Visible = true;
}
```
> ⚠️ **點擊後視窗打不開（SAL028 踩過）**：EditPick_Button 靠 `OnParametersSetAsync` 偵測 `Visible` 由 false→true 開窗；若 handler 只命令式設 `Visible=true`、而 markup 參數全沒變，Blazor 會略過該子元件不重跑生命週期 → 不開窗。**一律在 markup 綁一個 handler 內每次換新參考的 `FixedPost`**（無連動需求就放 `new(){{"_sortBy","NSN"}}`）。

> ⚠️ **`FixedPost` / `Value` 是 `[Parameter]`，不可在 handler 直接設 `EditPickX.FixedPost = ...`** —— 觸發 BL0005，且參數/render 遞迴 → **`StackOverflowException`**（實際踩過：SAL044 NSN/CUSTNSN、SAL045A QUOTNO）。正確做法（比照 SAL024）：
> - **markup 綁欄位**：`<EditPick_Button @ref="EditPickX" ... FixedPost="@_xFixedPost" />`
> - **handler 只設欄位**：`_xFixedPost = new Dictionary<string,string>{ {"CUSTMER", cur.CUSTMER ?? ""} };`（連動過濾靠動態 FixedPost，見 details/shared-input-components.md EditPick；勿用 `@key`）
> - 反之 `QueryWay / QueryGet / Columns / curritem / Visible / Keyword / Display` 是**普通公開欄位**，在 handler 直接設 OK（如上例）。

> ⚠️ **EditorTemplate 內「邊打邊查/回填」勿用即時 `ValueChanged` + `Rebind`** —— `Value="@item.X" ValueChanged="@(v => Handler(item,v))"` 內呼叫 API/`Rebind`，會「Rebind→重繪→`ValueChanged` 再觸發→…」**遞迴 `StackOverflowException`**（SAL044 CUSTNSN 手動反查踩過）。改法：
> - 純顯示/選取 → **`@bind-Value`**（雙向即可，勿手動 ValueChanged）。
> - 需失焦查一次（手動輸入代碼→反查名稱）→ `@bind-Value` + **`OnBlur`**（OnBlur 不會在 re-render 重複觸發，安全）。

**5. 選取回寫：`Apply` EventCallback + 用鍵值到 GD 撈實際列 + `StateHasChanged`（STK012 標準）**
InCell 編輯時 handler 拿到的 `item` 是**編輯複本**，直接改它＋`RebindKeepState` 會被「還原編輯狀態」蓋回去。正解：在 click handler（第 4 步）設 `Apply`，callback 內用主鍵從 GD 清單撈「真正那一列」來改，最後主動重繪；**不用 `RebindKeepState`**。
```csharp
// 第 4 步 click handler 內、Visible=true 之前加：
EditPickNSN.Apply = EventCallback.Factory.Create<IDictionary<string, object?>>(this, async row =>
{
    var gd = {{Dq1_GD}}.FirstOrDefault(x => x.{{KEY}} == data.{{KEY}});   // ← GD 實體列（非 edit 複本）
    if (gd == null) return;
    gd.NSN    = row.TryGetValue("NSN",    out var n)  ? n?.ToString()  ?? "" : "";
    gd.ITMCNM = row.TryGetValue("ITMCNM", out var ic) ? ic?.ToString() ?? "" : "";
    gd.SPECNM = row.TryGetValue("SPECNM", out var sp) ? sp?.ToString() ?? "" : "";
    if (gd.uState != UState.Insert) gd.uState = UState.Update;
    await InvokeAsync(StateHasChanged);                                 // ← 主動重繪
});
```
> 第 1 步 markup 不再需要 `OnApply="..."`（`OnApply` 與 `Apply` 擇一，採 `Apply`）。實例：STK012、SAL024/028/044/066/082。
> 數值欄改 `TelerikNumericTextBox T="decimal?"`，Apply callback 內用 `decimal.TryParse` 轉型。

## 對照
| 位置 | Delphi 欄數 | 回寫欄數 | 元件 |
|------|-----------|---------|------|
| 主表 | 2 / 3+ | 1 | `IksCodeComboBox` |
| 明細 grid | 任意 | ≥1 | **`EditPick_Button` + @ref** |
| 任意 | 任意 | ≥3 | **`EditPick_Button` + @ref** |

## DTO `_Display`（GetText → 屬性）
```csharp
[DisplayTransform("CurComoBox")]           public string? CUR_Display { get; set; }      // EditPick 非 KEYCODE
[DisplayTransformKeyCode("SA_QUOTM","CTAXTP")] public string? CTAXTP_Display { get; set; } // KeyCodePick
```
> 帶額外參數用 `[DisplayTransformApi(gqlway, codeField, extraParams)]`（見 `details/dto-display.md`）。

## 指路
- 控件選擇 → `details/input-component-choice.md`；用法 → `details/shared-input-components.md`
- 明細 grid → `details/grid-incell.md`；DTO → `details/dto-display.md`
