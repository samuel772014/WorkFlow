# 詳細規則：H. CRUD Handlers（存檔 / 刪除 / 查詢）

> 骨架指標來源：`templates/single-file.md` H 區。
> 對應 Delphi：`TfmEditForm` 框架內建存檔/刪除 + `MqyValidate`(NoValidate/CheckNo)。

---

## 通則

### endpoint 命名
- 主檔：`{form}_M_Add` / `{form}_M_Update` / `{form}_M_Delete`（`_M_` = master）。
- 查詢：`{form}_M_Query`。
- 明細：`{form}_{Dq}_Add/Update/Delete`。
- 連動查詢：`{form}_Get{來源}_{目標}`（見 `details/field-change.md`）。

### 存檔（Save）
1. **前端先驗必填**：缺必填欄位 → `MsgBox` 警告、`return`，不送後端。
2. **重複鍵雙重檢查**（新增時）：
   - **第一道（前端）**：存檔前先呼叫後端 pre-check（`KeyExists`）確認主鍵不存在。
   - **第二道（後端）**：mutation 內 `Add/Update` 時再 `KeyExistsAsync` 確認一次（防競態、防直接呼叫繞過前端）。
   - **不依賴 DB 錯誤碼/例外型別**判重（要導 Oracle，記憶 `db_agnostic_no_errorcode`）。
3. **主檔明細一起存 → 用 transaction**：主表 + 各明細在**同一交易**內，全部成功才 `commit`，任一失敗整筆 rollback（原子性）。
4. 依 `pageStatus` 決定走 `Add` 或 `Update` endpoint。
5. 成功 → 關窗、`pageStatus="query"`、`btnControl()`、Grid `Rebind()`。失敗 → `MsgBox` 顯示 `result.message`。

### 刪除（Delete）
- 先 `MsgBox.Confirm`（有明細要提示「同時刪除所有明細」）。
- 刪除與存檔**分開**：刪除直接呼叫 API，不走 Save（記憶 `incell_delete_direct`）。
- 成功 → 清 `MqySelect`、Grid `Rebind()`。

### 查詢（Query）
- 組 `WhereParameters` 字典（只放有值的條件）→ Grid `Rebind()`。
- SQL 端維持 `SELECT *`，只精簡前端欄位（記憶 `keep_select_star`）。

---

## 指令欄列動作 handlers（拷貝 / 修改 / 詳細資料）

> 對應 `templates/single-file.md` C 區 `GridCommandColumn` 的 `OnClick`。
> 按鈕順序＝**CRUD → 查詢**：`拷貝 → 修改 → 刪除 → 詳細資料`（刪除見上節 `Delete()`）。
> 每顆 `GridCommandButton` 的 `OnClick` 收 `GridCommandEventArgs`，`args.Item` 即該列 DTO。

| 鈕 | pageStatus | 鎖定 | 開窗 | 說明 |
|----|-----------|------|------|------|
| 拷貝 | `Add` | 不鎖（存檔才建） | ✅ 唯讀=false | clone 該列、**清主鍵**、當新增預填 |
| 修改 | `Edit` | `StartEdit` 上鎖 | ✅ 唯讀=false | clone 該列進表單、主鍵唯讀 |
| 詳細資料 | `View` | 不鎖 | ✅ 唯讀=true | 重用編輯 Window 唯讀開（記憶 `detail_readonly_reuse_edit`）|

**眉角**
- **clone 一份**再進表單，勿直接綁 grid 列物件（否則取消時 grid 顯示已被改動）。
- **鎖定**走業務 API（`StartEdit`/`CancelEdit`），存檔/狀態變更由 Service 端嵌入解鎖（記憶 `doc_lock_pattern`）。只有「修改」需要在開窗前上鎖；拷貝/詳細不鎖。

```csharp
private async Task OnRowCopy(GridCommandEventArgs args) {
    current = Clone((Mqy)args.Item);      // clone 一份
    current.{{PK}} = "";                   // 清主鍵 → 當新增
    pageStatus = "Add";
    _editWindowVisible = true;
}

private async Task OnRowEdit(GridCommandEventArgs args) {
    var row = (Mqy)args.Item;
    var lockRs = await gQL.ApiCallAsync(_url, "mutation", "{{form}}_StartEdit",
        new Dictionary<string,string> { ["{{PK}}"] = row.{{PK}} ?? "" });
    if (lockRs?.status != 1) { await MsgBox.Show(lockRs?.message ?? "單據已被鎖定", "修改", "warning"); return; }
    current = Clone(row);
    pageStatus = "Edit";
    _editWindowVisible = true;
}

private async Task OnRowDetail(GridCommandEventArgs args) {
    current = Clone((Mqy)args.Item);
    pageStatus = "View";                   // 唯讀重用編輯 Window（_formReadonly 由此判斷）
    _editWindowVisible = true;
}
```

> `刪除` 鈕 → 直接呼叫上節 `Delete()`（記憶 `incell_delete_direct`，與存檔分開）。
> `Clone()` 用淺拷貝即可（`current = new Mqy { ... }` 或 `MemberwiseClone` 包裝），DTO 欄位以繼承 EF Model 為準（記憶 `dto_inherit_model`）。

---

## 【範例程式碼】(SAL001)

> ⚠️ **存檔參數依 Delphi 設定**：`BuildXxxArgs`／存檔 `args` 的欄位以 **Delphi 該表單實際存的欄位為準**，不是「後端 UPDATE 全欄」、也不是「畫面全欄」。唯讀/自動維護欄（如「最近接洽日」由子表回寫）依 Delphi 決定是否回送——**若後端 UPDATE 有該欄但主表單不寫，須回送現值以免被覆為 null**（或後端 UPDATE 不納該欄）。

```csharp
private async Task Save() {
    if (string.IsNullOrWhiteSpace(currentMqy.SALEREP)) { await MsgBox.Show("業務代表為必填", "必填", "warning"); return; }
    if (string.IsNullOrWhiteSpace(currentMqy.DEPID))   { await MsgBox.Show("業務部門為必填", "必填", "warning"); return; }

    var args = new Dictionary<string,string> { ["SALEREP"]=currentMqy.SALEREP??"", /* … */ };
    string endpoint = pageStatus == "Add" ? "sal001_M_Add" : "sal001_M_Update";
    var result = await gQL.ApiCallAsync(_url, "mutation", endpoint, args);
    if (result?.status == 1) {
        pageStatus = "query"; _editWindowVisible = false;
        await btnControl(); SAL001Mqy?.Rebind(); await InvokeAsync(StateHasChanged);
    } else await MsgBox.Show(result?.message ?? "存檔失敗", "存檔", "error");
}

private async Task Delete() {
    if (MqySelect == null) { await MsgBox.Show("請先選取一筆資料", "刪除", "warning"); return; }
    if (!await MsgBox.Confirm($"確定刪除【{MqySelect.SALEREP}】？同時刪除所有明細。", "刪除確認")) return;
    var result = await gQL.ApiCallAsync(_url, "mutation", "sal001_M_Delete",
        new Dictionary<string,string> { ["SALEREP"] = MqySelect.SALEREP ?? "" });
    if (result?.status == 1) { MqySelect = null; SAL001Mqy?.Rebind(); }
    else await MsgBox.Show(result?.message ?? "刪除失敗", "刪除", "error");
}
```

## 【骨架程式碼】

```csharp
private async Task Save() {
    // 1. 前端必填驗證
    if (string.IsNullOrWhiteSpace(current.{{必填}})) { await MsgBox.Show("...必填", "必填", "warning"); return; }
    // 2. 新增時前端重複鍵 pre-check（第一道）
    if (pageStatus == "Add") { /* await gQL...{{form}}_M_KeyExists → 存在則警告 return */ }
    // 3. 送後端（後端 mutation 內再 KeyExistsAsync；主檔+明細用 transaction 全成才 commit）
    string endpoint = pageStatus == "Add" ? "{{form}}_M_Add" : "{{form}}_M_Update";
    var result = await gQL.ApiCallAsync(_url, "mutation", endpoint, args);
    if (result?.status == 1) { /* 關窗 → query → btnControl → Grid.Rebind */ }
    else await MsgBox.Show(result?.message ?? "存檔失敗", "存檔", "error");
}

private async Task Delete() {
    if (MqySelect == null) { /* 提示選取 */ return; }
    if (!await MsgBox.Confirm("確定刪除…（同時刪除明細）", "刪除確認")) return;
    var result = await gQL.ApiCallAsync(_url, "mutation", "{{form}}_M_Delete", key);
    if (result?.status == 1) { MqySelect = null; Grid?.Rebind(); }
    else await MsgBox.Show(result?.message ?? "刪除失敗", "刪除", "error");
}
```

---

## B101 對應
- `MqyValidate`(NoValidate 外鍵存在) → 存檔前必填/外鍵驗證。
- `TfmEditForm` 內建存檔 → `_M_Add/_M_Update`；主鍵 SALEREP 重複走雙重 KeyExists。
- 刪除主檔連帶 Dq1 明細 → Confirm 提示 + 後端 transaction 一起刪。
- `MqyNewRecord` 設 `STATUS='A'` → `Add()` 時預設。

## 指路
- 連動/計算 → `details/field-change.md`
- DTO/存檔欄位 → `details/dto-display.md`
- 後端 mutation 建法 → 記憶 `mutation_pattern`（Query/Mutation 共用 Service，薄 Resolver）
