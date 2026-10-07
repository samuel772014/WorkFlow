# 詳細規則：明細 grid EditorTemplate ＋ EditPick_Button（控件）

> 給 `details/grid-incell.md`／`details/dto-display.md`／`details/shared-input-components.md` 指來：明細 grid 內可 pick/編輯欄位的 EditorTemplate 寫法。
> 對應 Delphi：DFM `ControlType 'X;CustomEdit;xxxPick'` 或 `.pas` `DqnDblClick`。來源：舊 `editpick-mapping` 彙整。

---

## 何時用 EditPick_Button（而非 EditPick / ComboBox）
- 欄位在 `IksGrid_vnq` 明細的 `EditorTemplate` 內（**不論欄數**）→ `EditPick_Button` + 頁面層級 `@ref`。
- 或選取後需**回寫 3 個以上欄位**。
- **禁止在 EditorTemplate 內 inline 宣告 Picker**（每列各建實例會壞，記憶 `editpick_button_pattern`）。
- 主表 ≤2 欄→`IksCodeComboBox`、KeyCode→`KeyCodeComboBox`、日期→`TelerikDatePicker`（決策 → `details/input-component-choice.md`）。
- **`DqnDblClick` 是 `EditMemo(...)`（多行長文字放大視窗）不是 pick** → 改用 **`PopUpText`**（EditorTemplate 內 TextBox＋放大鈕開窗），不是 `EditPick_Button`；用法與泛型多欄共用寫法見 `details/popuptext.md`。

## 五步驟

**1. 頁面層級宣告（所有 grid 之外，靜態屬性）**
```razor
<EditPick_Button @ref="EditPickNSN" TItem="Dq1" Url="@_url" Width="130px" OnApply="dq1Change_NSN" />
```
**2. @code 變數**
```csharp
private EditPick_Button<Dq1> EditPickNSN = null!;
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
    EditPickNSN.curritem = data; EditPickNSN.Visible = true;
}
```
> ⚠️ **`FixedPost` / `Value` 是 `[Parameter]`，不可在 handler 直接設 `EditPickX.FixedPost = ...`** —— 觸發 BL0005，且參數/render 遞迴 → **`StackOverflowException`**（實際踩過：SAL044 NSN/CUSTNSN、SAL045A QUOTNO）。正確做法（比照 SAL024）：
> - **markup 綁欄位**：`<EditPick_Button @ref="EditPickX" ... FixedPost="@_xFixedPost" OnApply="..." />`
> - **handler 只設欄位**：`_xFixedPost = new Dictionary<string,string>{ {"CUSTMER", cur.CUSTMER ?? ""} };`（連動過濾靠動態 FixedPost，記憶 `feedback_dependent_editpick_rebind`；勿用 `@key`）
> - 反之 `QueryWay / QueryGet / Columns / curritem / Visible / Keyword / Display` 是**普通公開欄位**，在 handler 直接設 OK（如上例）。

> ⚠️ **EditorTemplate 內「邊打邊查/回填」勿用即時 `ValueChanged` + `Rebind`** —— `Value="@item.X" ValueChanged="@(v => Handler(item,v))"` 內呼叫 API/`Rebind`，會「Rebind→重繪→`ValueChanged` 再觸發→…」**遞迴 `StackOverflowException`**（SAL044 CUSTNSN 手動反查踩過）。改法：
> - 純顯示/選取 → **`@bind-Value`**（雙向即可，勿手動 ValueChanged）。
> - 需失焦查一次（手動輸入代碼→反查名稱）→ `@bind-Value` + **`OnBlur`**（OnBlur 不會在 re-render 重複觸發，安全）。

**5. OnApply 回寫多欄 + `RebindKeepState()`（保捲動位置）**
```csharp
private async Task dq1Change_NSN(Dq1 item, IDictionary<string, object> row) {
    item.NSN    = row.TryGetValue("NSN",    out var n)  ? n?.ToString()  ?? "" : "";
    item.ITMCNM = row.TryGetValue("ITMCNM", out var ic) ? ic?.ToString() ?? "" : "";
    item.SPECNM = row.TryGetValue("SPECNM", out var sp) ? sp?.ToString() ?? "" : "";
    await {{Dq1}}.RebindKeepState();
}
```
> 數值欄改 `TelerikNumericTextBox T="decimal?"`，OnApply 用 `decimal.TryParse` 轉型。

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
