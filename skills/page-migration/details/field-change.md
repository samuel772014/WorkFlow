# 詳細規則：欄位連動 / change 事件（跨區：編輯 E、明細 grid 共用）

> 來源：Delphi `MqyChange` / `Dq1Change` / `FilterValidate` 等欄位變動事件。
> 參考頁面：`SAL046`（連動最完整）。編輯欄位與 grid 儲存格 change 都用本通則。

---

## 連動處理通則

1. **前端觸發用 `@bind-Value:after="XxxChanged"`** 指派方法（ComboBox/KeyCodeComboBox/數值框皆是）。
2. **凡「計算」一律打後端 API 計算**（金額、小計、稅額、匯率換算…都送後端算，前端不做算術）。
3. **帶值連動分兩種來源**：
   - **EditPick 多欄** → pick 已回傳所需欄位，直接用 **`Apply` 回呼的 row 在前端指派**，**免再打 API**。
   - **ComboBox（只回代碼+名稱）** → 要帶其他欄位就 `@bind-Value:after` **打後端查**。
4. **純畫面異動走前端**：清空相依欄位（上層改→下層 `=null`）、控制 Tab/欄位顯示、`StateHasChanged`。
5. **handler 開頭防呆**：`if (string.IsNullOrEmpty(來源值)) return;`。
6. **後端連動 endpoint 命名**：`{form}_Get{來源}_{目標}`（如 `sal001_GetDEPID_SMANAGER`、`sal046_GetCUSTMER_Info`）。
7. **相依 ComboBox 用 `Args` 動態帶條件**做連動過濾（記憶 `dependent_editpick_rebind`；SAL046 CUSTMER 帶 OBJTP、SPRCID 帶 FLDT）。
8. **連鎖連動抽共用方法**：一個 change 可再觸發其他，抽 `RefreshXxx()` 重用（SAL046 `RefreshMRATE`/`RefreshTaxRate`）。
9. **GridView 儲存格 change 同通則**：`ValueChanged="@(v => _ = OnXxxChanged(item, v))"` 傳 item+value；指派後**計算送後端**。
10. **任何不確定 → 詢問轉譯操作者**。

> ⚠️ 註：`SAL046` 明細金額目前是**前端算術**（`Dq1_CalcMNYAsync`），屬舊例外。**新規則以「計算一律後端」為準**，勿再照抄前端算術。

---

## 【範例程式碼】(SAL046)

```razor
@* 前端觸發 → :after 指派方法 *@
<IksCodeComboBox @bind-Value="currentSA_QUOTM.SALEREP" _url="@_url" module="SAL"
                 comboBoxCode="SalerepComoBox" @bind-Value:after="OnSALEREPChanged" />
@* 相依 ComboBox：Args 動態帶上層值做連動過濾 *@
<IksCodeComboBox @bind-Value="@currentSA_QUOTM.CUSTMER" _url="@_url" module="SAL" comboBoxCode="CustmerComoBox"
                 Args="@(new Dictionary<string,string>{ {"OBJTP", currentSA_QUOTM.OBJTP ?? ""} })"
                 @bind-Value:after="OnCUSTMERChanged" />
```
```csharp
// 純畫面異動 → 前端（清相依欄）
private async Task OBJTP_E_Changed() { currentSA_QUOTM.CUSTMER = null; await InvokeAsync(StateHasChanged); }

// 帶值連動 → 後端查（防呆 + endpoint 命名 + 指派）
private async Task OnSALEREPChanged() {
    if (string.IsNullOrEmpty(currentSA_QUOTM.SALEREP)) return;
    var r = await gQL.ApiCallAsync(_url, "query", "sal046_GetSALEREP_DEPID",
        new Dictionary<string,string> { ["SALEREP"] = currentSA_QUOTM.SALEREP ?? "" });
    if (r?.records?.Rows.Count > 0)
        currentSA_QUOTM.DEPID = r.records.Rows[0]["DEPID"]?.ToString();
    await InvokeAsync(StateHasChanged);
}
```

## 【骨架程式碼】

```razor
@* ComboBox 連動：:after 打後端 *@
<IksCodeComboBox @bind-Value="current.{{SRC}}" _url="@_url" module="{{MOD}}" comboBoxCode="{{Code}}"
                 @bind-Value:after="On{{SRC}}Changed" />
@* EditPick 多欄連動：用 Apply 前端帶，免打 API *@
<EditPick @bind-Value="current.{{SRC}}" Apply="On{{SRC}}_Apply" QueryGet="{{欄位清單}}" ... />
```
```csharp
// ComboBox → 後端帶值
private async Task On{{SRC}}Changed() {
    if (string.IsNullOrEmpty(current.{{SRC}})) return;
    var r = await gQL.ApiCallAsync(_url, "query", "{{form}}_Get{{SRC}}_{{TGT}}",
        new Dictionary<string,string> { ["{{SRC}}"] = current.{{SRC}} ?? "" });
    if (r?.records?.Rows.Count > 0) current.{{TGT}} = r.records.Rows[0]["{{TGT}}"]?.ToString();
    await InvokeAsync(StateHasChanged);
}
// EditPick → 前端用 Apply row 帶（免 API）
private async Task On{{SRC}}_Apply(IDictionary<string, object?> row) {
    current.{{TGT}} = row.TryGetValue("{{PICK_COL}}", out var v) ? v?.ToString() : null;
    await InvokeAsync(StateHasChanged);
}
// 計算一律後端
private async Task Recalc() { /* gQL.ApiCallAsync(..., "{{form}}_CalcXxx", ...) → 回填欄位 */ }
```

---

## B101 兩條連動的對應

| Delphi (MqyChange) | 來源控件 | 走法 | endpoint |
|--------------------|---------|------|----------|
| SALEREP → SARPNM + DEPID | EditPick 3 欄（回 EMPLYNM/DEPID） | **前端** Apply row 帶（EMPLYNM→SARPNM、DEPID→DEPID） | 免 |
| DEPID → SMANAGER | ComboBox 2 欄（只回 DEPID/DEPNM） | **後端** `@bind-Value:after` 查 | `sal001_GetDEPID_SMANAGER` |

> DEPID→SMANAGER 是 SAL001 註解掉、依「以 Delphi 為準」要補回的連動。

---

## 指路
- 編輯欄位擺放 → `details/edit-window.md`
- 明細 grid 儲存格 → `details/grid-incell.md`（主檔明細範本）
- 控件選擇 → `details/input-component-choice.md`
