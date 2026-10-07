---
name: popuptext
description: IKSERP Blazor 共用元件 PopUpText 的使用規則。當使用者要在頁面（尤其是 Grid 明細列）新增「彈出大字文字編輯視窗」來編輯長文字欄位（如備註 REMARK、說明），或說「加 PopUpText」「用彈窗編輯備註」「文字視窗」時觸發。以 STK012 的備註欄用法為藍本。
---

# PopUpText 彈出文字編輯視窗 Skill（IKSERP Blazor）

## 觸發時機

使用者要在頁面新增「彈出視窗編輯長文字」的功能，典型情境：

- Grid 明細列的備註／說明欄位太窄，需要點按鈕開大字視窗編輯後寫回。
- 編輯區某個多行文字欄位想用獨立視窗放大編輯。
- 使用者說「加 PopUpText」「文字視窗」「用彈窗編輯備註」「參考 STK012 的備註視窗」。

---

## 元件說明

`Components/Shared/PopUpText.razor` 是一個 Modal `TelerikWindow`，內含一個放大字體（20px）、16 行的 `TelerikTextArea`，底部有「確定 / 取消」兩顆按鈕。

設計重點：**開窗、初始文字、回寫邏輯全部由呼叫端透過 `@ref` 指令式（imperative）設定，不走 `[Parameter]` 綁定。**
原因是這個元件常被放在 **Grid EditorTemplate** 內觸發，此時父層不一定會重繪本元件，因此 `Visible` 的 setter 自己驅動 `StateHasChanged`，不依賴父層重繪。

> 與 [[feedback_editpick_button_pattern]] 同一原則：Grid 內開視窗的元件，一律在**頁面層級**用 `@ref` 宣告，不可 inline 寫在 grid template 裡。

---

## 屬性一覽

指令式成員（透過 `@ref` 在 handler 中設定，**非** `[Parameter]`）：

| 成員 | 型別 | 說明 |
|------|------|------|
| `Value` | `string?` | 視窗開啟時顯示的初始文字 / 當前編輯內容 |
| `OnApply` | `Func<string, Task>?` | 按「確定」時執行的回寫邏輯，參數為使用者編輯後的文字 |
| `Visible` | `bool` | 設 `true` 開窗、`false` 關窗；setter 自行重繪 |

`[Parameter]`（開窗前一次設定，通常用預設值即可）：

| 屬性 | 型別 | 預設 | 說明 |
|------|------|------|------|
| `WindowTitleText` | `string` | `"文字視窗"` | 視窗標題 |
| `WindowWidth` | `string` | `"1230px"` | 視窗寬度 |
| `WindowHeight` | `string` | `"600px"` | 視窗高度 |
| `Enabled` | `bool` | `true` | TextArea 是否可輸入 |
| `ReadOnly` | `bool` | `false` | TextArea 是否唯讀（查看模式用 `true`） |

> 行為：按「確定」→ 呼叫 `OnApply(Value)` 後關窗；按「取消」→ 直接關窗，不觸發 `OnApply`。

---

## 使用三步驟（以 STK012 備註欄為藍本）

### 1. 頁面層級宣告 @ref（放在 `@code` 外的 markup 尾端）

```razor
<PopUpText @ref="PText"></PopUpText>

@code {
    private PopUpText PText = default!;
}
```

### 2. 觸發按鈕放在 Grid 欄位的 EditorTemplate（TextBoxSuffixTemplate）

```razor
private RenderFragment<Dq1> RemarkTemplate => (item) =>
    @<div style="display:inline-block; min-width:0;">
        <div style="width:150px;">
            <TelerikTextBox @bind-Value="item.REMARK" Width="150px" Enabled="@EditStatus">
                <TextBoxSuffixTemplate>
                    <TelerikButton OnClick="@(() => Dq1_REMARK_Click(item))"
                                   Enabled="@EditStatus"
                                   Icon="@("ti ti-dots-vertical")">
                    </TelerikButton>
                </TextBoxSuffixTemplate>
            </TelerikTextBox>
        </div>
    </div>;
```

grid 欄位設定用 `EditorTemplate` 指向這個 RenderFragment：

```csharp
{"REMARK", new GridColumnConfig {Field="REMARK", Title="備註", Width="200px",
    Editable=true, EditorTemplate = (context) => RemarkTemplate((Dq1)context)} },
```

### 3. Click handler：設 Value → 設 OnApply → 開窗

```csharp
public void Dq1_REMARK_Click(Dq1 data)
{
    PText.Value = data.REMARK ?? "";

    // 按「確定」才寫回：更新列值 → 標記待存檔 → 併入 Update 清單
    PText.OnApply = async text =>
    {
        Dq1? dq1 = Dq1_GD.FirstOrDefault(x => x.ADJITM == data.ADJITM);
        if (dq1 == null) return;

        dq1.REMARK = text ?? "";
        if (dq1.uState != UState.Insert)
            dq1.uState = UState.Update;

        int index = Update_Dq1.FindIndex(x => x.ADJITM == dq1.ADJITM);
        if (index == -1)
            Update_Dq1.Add(dq1);
        else
            Update_Dq1[index] = dq1;

        await InvokeAsync(StateHasChanged);
    };

    PText.Visible = true;
}
```

---

## 關鍵要點

- **`OnApply` 內回寫套用既有存檔流程**：更新列值 → 依 `uState`（非 Insert 就設 Update）標記 → 併入該明細的 `Update_XXX` 清單，與同頁 NSN／SLocation 等 Apply 寫回一致（參 [[feedback_incell_save_insert_update]]、[[feedback_detail_rebind_add_save]]）。
- **每次開窗都重設 `OnApply`**：因為 handler 內用閉包綁定當前 `data`，不同列要指向不同的回寫目標，不可共用一份 OnApply。
- **不可 inline 宣告**：`<PopUpText @ref="PText">` 只放頁面層級一份，多列共用同一實例，靠 handler 每次重設 `Value`/`OnApply`。
- **查看（唯讀）模式**：開窗前設 `PText.ReadOnly = true`（或用 `Enabled=false`）即可只顯示不可改，配合 [[feedback_detail_readonly_reuse_edit]] 的唯讀重用原則。
- **`Value` 是 public 屬性非 nullable 綁定**：TextArea 直接 `@bind-Value="Value"`，開窗前務必先給值（`?? ""`）避免殘留上一列內容。

---

## Delphi `EditMemo` → PopUpText（轉譯對應）

Delphi 在 grid 的 `DqnDblClick` 用 `EditMemo(Sender,'標題',bgEdit)` 開多行長文字放大視窗（備註、說明、負責事項、營業項目…）。轉譯時**該欄一律改用 PopUpText**（決策樹見 `details/input-component-choice.md`）；視窗標題沿用 `EditMemo` 第二參數。註解掉的 `EditMemo`（如 `//EditMemo(...,'通訊地址',...)`）**不轉**。

### 同頁多個 memo 欄 → 用一支泛型 helper（免每欄各寫一份）

一頁常有多個明細 grid、多個 memo 欄（SAL041 B210Base 有 12 個）。用泛型 `MemoEditor<T>` 統一，`getter/setter/gd/grid/標題` 當參數傳：

```csharp
// 方法本體 @<...> 產生「非泛型 RenderFragment」→ 回傳型別必須是 RenderFragment（非 RenderFragment<T>）
private RenderFragment MemoEditor<T>(T item, string title,
    Func<T, string?> getter, Action<T, string?> setter,
    List<T> gd, IksGrid_vnq<T>? grid) where T : class, IDetailRow, new()
    => @<div style="display:inline-block; min-width:0; width:100%;">
        <TelerikTextBox Value="@getter(item)" ValueChanged="@((string v) => setter(item, v))"
                        ValueExpression="@(() => _memoValueExpr)"
                        Width="100%" Enabled="@_dqEditEnabled">
            <TextBoxSuffixTemplate>
                <TelerikButton OnClick="@(() => OpenMemo(item, title, getter, setter, gd, grid))"
                               Enabled="@_dqEditEnabled" Icon="@("ti ti-dots-vertical")" />
            </TextBoxSuffixTemplate>
        </TelerikTextBox>
    </div>;

private void OpenMemo<T>(T item, string title, Func<T, string?> getter, Action<T, string?> setter,
    List<T> gd, IksGrid_vnq<T>? grid) where T : class, IDetailRow, new()
{
    PText.WindowTitleText = title;          // 標題依欄位動態設（markup 的 <PopUpText> 勿寫死 WindowTitleText）
    PText.Value = getter(item) ?? "";
    PText.OnApply = async text => {
        if (grid != null) await grid.ExitEditModeAsync();   // ★ 先收掉仍開著的 InCell 編輯器
        // ★ 用鍵值到 gd 找回真正那一列再寫回（不可直接改 closure 的 item，見下方陷阱）
        T target = gd.FirstOrDefault(x => x.CUSTNO == item.CUSTNO && x.ITM == item.ITM) ?? item;
        setter(target, text ?? "");
        if (target.uState != UState.Insert) target.uState = UState.Update;
        if (grid != null) await grid.RebindKeepState(gd);
        await InvokeAsync(StateHasChanged);
    };
    PText.Visible = true;
}
// ColConfig: { "ZJOB", new GridColumnConfig{ Field="ZJOB", Title="負責事項",
//     EditorTemplate = ctx => MemoEditor((Dq1)ctx, "負責事項", x=>x.ZJOB, (x,v)=>x.ZJOB=v, SAL041Dq1_GD, SAL041Dq1) } }
```

### 兩個編譯陷阱（實際踩過）

- ⚠️ **泛型 helper 的約束要含 `new()`**：`IksGrid_vnq<TItem>` 本身限定 `TItem : new()`，helper 若只寫 `where T : class, IDetailRow` → 報「'T' 必須是具有公用無參數建構函式的非抽象類型」。正解 `where T : class, IDetailRow, new()`。
- ⚠️ **含 `EditorTemplate` 的 `ColConfig` 必用「運算式屬性 `=>`」而非「欄位初始式 `=`」**：`EditorTemplate` 參考實例方法（`MemoEditor`）時，欄位初始式 `= new(){...}` 會報「欄位初始設定式無法參考非靜態欄位、方法或屬性」。把 `= new()` 改成 `=> new()` 即解（比照 STK012 `dq1EditerColumns`；同 `EditPick_Button` 的 EditorTemplate 情況）。
- ⚠️ **`OnApply` 寫回後 grid 沒回寫/不顯示 → 別改 closure 的 `item`，要用鍵值到 `gd` 找回實際列**：EditorTemplate 在 InCell 編輯態才出現，開 modal `PopUpText` 會讓那格編輯器**失焦**，Telerik 隨即把「編輯複本 commit 後丟棄」，於是 handler closure 捕捉到的 `item` 變成**孤兒複本**，直接 `setter(item,…)` 改的是複本、**不會反映到 `gd`**。正解：`OnApply` 內先 `await grid.ExitEditModeAsync()` 收掉編輯器，再 `gd.FirstOrDefault(鍵值)` 取回真正那列去 `setter` + 標 `uState`，最後 `await grid.RebindKeepState(gd)` 刷新（同 `EditPick_Button` Apply 先 Exit 再 Rebind 的精神）。只改 `item` 或只 `Rebind` 都會「看起來沒回寫」。
- ⚠️ **用 `Value`＋`ValueChanged`（非 `@bind-Value`）的 `TelerikTextBox` 必補 `ValueExpression`**：泛型 helper 靠 `getter/setter` 綁值不能用 `@bind-Value`，Telerik 少了 `ValueExpression` 會在 render 時丟 `InvalidOperationException: requires a value for the 'ValueExpression'` → **整個 circuit 崩潰**。給一個佔位成員存取式即可（`ValueExpression="@(() => _memoValueExpr)"`，`_memoValueExpr` 為頁面一個 `string?` 欄位）——無 EditForm 驗證，只是拿來產 FieldIdentifier，佔位成員足夠。
