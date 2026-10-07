# 呼叫端接線（wiring）

選擇器是**內容元件**，由呼叫端放進 `TelerikWindow` 開關，並綁 `OnConfirm`（收選取）/ `OnClose`（關閉）。

## 選擇器對外

```csharp
[Parameter] public EventCallback<List<PickRow>> OnConfirm { get; set; }
[Parameter] public EventCallback OnClose { get; set; }

private async Task OnConfirmClick()
{
    var selected = _grid?.SelectedItems?.ToList() ?? new List<PickRow>();
    if (selected.Count == 0)
    {
        await MsgBox.Show("請至少選取一筆。", "選擇器", "warning");
        return;
    }
    await OnConfirm.InvokeAsync(selected);   // 回傳；是否關窗由呼叫端決定
}

private async Task Cancel() => await OnClose.InvokeAsync();
```

- 「確定」**只回傳、不自己關窗**——關窗（`Visible=false`）由呼叫端在 `OnConfirm` 內做，保持職責單一。
- 需要預帶篩選條件時，加 `[Parameter]` 傳入（如 `[Parameter] public string? FixedType { get; set; }`），`OnAfterRenderAsync` 首查時套用。

## 呼叫端

```razor
<TelerikWindow @bind-Visible="@_pickerVisible" Modal="true" Width="720px" Height="600px">
    <WindowTitle>選擇料品</WindowTitle>
    <WindowContent>
        @if (_pickerVisible)   @* 每次開重建，確保 firstRender 首查 *@
        {
            <XxxPicker OnConfirm="OnPicked" OnClose="@(() => _pickerVisible = false)" />
        }
    </WindowContent>
</TelerikWindow>

@code {
    bool _pickerVisible;
    void OpenPicker() => _pickerVisible = true;

    void OnPicked(List<XxxPicker.PickRow> rows)
    {
        // 處理選取結果（帶回主檔/明細…）
        _pickerVisible = false;   // 關窗
    }
}
```

- `@if (_pickerVisible)` 包住內容元件：每次開窗重建，`OnAfterRenderAsync(firstRender)` 才會重跑首查（否則第二次開沿用舊資料/舊選取）。
- 選取型別對外是 `List<TPickerRow>`；DTO 是 picker 的 `public` 巢狀類別（`XxxPicker.PickRow`），或抽成獨立類別供雙方共用。
