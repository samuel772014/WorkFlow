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

### GraphQL 呼叫參數
- `ApiCallAsync`：直接傳真實欄位，不包 `["arg"]=JSON`。
- 多列／巢狀存檔：`MultipleDataApiCallAsync` + `["arg"]=JSON`（例見 `details/attachment.md`）。
- 特殊字元（`"` `'` 換行）：前端 `iksUiFunc.GraphQlArg.Encode`、後端 `Modules.FUNC.GraphQlArg.DecodeArg`。

### 存檔（Save）
1. **前端先驗必填**：缺必填欄位 → `MsgBox` 警告、`return`，不送後端。
2. **重複鍵雙重檢查**（新增時）：
   - **第一道（前端）**：存檔前先呼叫後端 pre-check（`KeyExists`）確認主鍵不存在。
   - **第二道（後端）**：mutation 內 `Add/Update` 時再 `KeyExistsAsync` 確認一次（防競態、防直接呼叫繞過前端）。
   - **不依賴 DB 錯誤碼/例外型別**判重（要導 Oracle）。
3. **主檔明細一起存 → 用 transaction**：主表 + 各明細在**同一交易**內，全部成功才 `commit`，任一失敗整筆 rollback（原子性）。
4. 依 `pageStatus` 決定走 `Add` 或 `Update` endpoint。
5. 成功 → 關窗、`pageStatus="query"`、`btnControl()`、Grid `Rebind()`。失敗 → `MsgBox` 顯示 `result.message`。
6. **文字欄空字串一律寫 NULL（後端 INSERT/UPDATE 參數）**：前端 `S(x)=x??""`、`ODS`/`A78Str` 類 helper 會把 null 變 `""`；ERP 多個 Y/N 或代碼欄有 CHECK 約束（如 `SA_SALEM.TOTAR`、`SA_SALED.BKPBK`）不收 `''` → 存檔失敗。規則：
   - 寫入參數：`string.IsNullOrEmpty(v) ? null : v`（Delphi 未指定欄位＝NULL；來源 NULL 照搬仍為 NULL）。
   - 新增列有 Delphi `NewRecord` 預設值的欄（如 BKPBK/ISSTK='N'、CONSIGNMENT='N'）：**空字串視同未帶 → 套預設**，不可因「鍵存在」就略過預設。
   - 查詢 WHERE 參數不在此限（`=@X` 以 `''` 或 NULL 結果不同時依原語意）。
   - 範例：SAL078 `sal078_SaveDoc`（表頭 ISd/S、Dq1SaveStr、Yn 預設）、ImportOrd `ODN`、SAL078A `A78Nul`；SAL079 test-fix-null。

### 刪除（Delete）
- 先 `MsgBox.Confirm`（有明細要提示「同時刪除所有明細」）。
- 刪除與存檔**分開**：刪除直接呼叫 API，不走 Save（見 details/grid-incell.md 通則5）。
- 成功 → 清 `MqySelect`、Grid `Rebind()`。

### 查詢（Query）
- 組 `WhereParameters` 字典（只放有值的條件）→ Grid `Rebind()`。
- SQL 端維持 `SELECT *`，只精簡前端欄位。

---

## 指令欄列動作 handlers（拷貝 / 修改 / 詳細資料）

> 對應 `templates/single-file.md` C 區 `GridCommandColumn` 的 `OnClick`。
> 按鈕順序＝**CRUD → 查詢**：`拷貝 → 修改 → 刪除 → 詳細資料`（刪除見上節 `Delete()`）。
> 每顆 `GridCommandButton` 的 `OnClick` 收 `GridCommandEventArgs`，`args.Item` 即該列 DTO。

| 鈕 | pageStatus | 鎖定 | 開窗 | 說明 |
|----|-----------|------|------|------|
| 拷貝 | `Add` | 不鎖（存檔才建） | ✅ 唯讀=false | clone 該列、**清主鍵**、當新增預填 |
| 修改 | `Edit` | `StartEdit` 上鎖 | ✅ 唯讀=false | clone 該列進表單、主鍵唯讀 |
| 詳細資料 | `View` | 不鎖 | ✅ 唯讀=true | 重用編輯 Window 唯讀開（見 details/edit-window.md 通則5）|

**眉角**
- **clone 一份**再進表單，勿直接綁 grid 列物件（否則取消時 grid 顯示已被改動）。
- **鎖定**走業務 API（`StartEdit`/`CancelEdit`），存檔/狀態變更由 Service 端嵌入解鎖（見下方「單據鎖定」）。只有「修改」需要在開窗前上鎖；拷貝/詳細不鎖。

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

> `刪除` 鈕 → 直接呼叫上節 `Delete()`（見 details/grid-incell.md 通則5，與存檔分開）。
> `Clone()` 用淺拷貝即可（`current = new Mqy { ... }` 或 `MemberwiseClone` 包裝），DTO 欄位以繼承 EF Model 為準（見 details/dto-display.md 通則1）。

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

## 單據鎖定（SS_LCKFM；對應 Delphi B301Base.MqyBeforeEdit / MqyAfterPost / CCButtonClick）

**前端不感知鎖定，只呼叫業務語意 API**：
| 動作 | API | Service 內 |
|---|---|---|
| 修改鈕 | `{form}_StartEdit` | `ChkLckFm`（A 查 + B 鎖） |
| 取消鈕 | `{form}_CancelEdit` | `ProcLckFm` C 解鎖 |
| 存檔成功 | `{form}_Save` | Save 內嵌 `ProcLckFm` C |
| 狀態變更（確認/作廢/取消確認…） | 各自 mutation | DB 交易外 `ProcLckFm` A→B 上鎖、`finally` C 解鎖（實例 SAL067 CF/CC/CR） |

- 一律用 `IKSERPAPI/Modules/FUNC/ERPFunc.cs`：`ERPFunc.SetLckFm(fmId, fmNo, usr)`（static，回 `LckFmRecord`）；`ChkLckFm`/`ProcLckFm` 為 instance 方法 → `new ERPFunc(_iksDbFunc)`。勿用舊 `IksDbFunc` 版。
- `FMID`：查 `SS_FMCODE.FMID`（報價單 SA_QUOTM＝`B1`、出貨單＝`B7`…）。
- `USR`：前端帶登入者 `EmplyId`（`details/page-shell.md`），勿寫死 `"00001"`；B 鎖與 C 解須同一 USR。

## 後端分層（Query / Mutation 共用 Service、Repository）
- 新 Mutation 只加薄 `Resolvers/{MOD}/{FORM}Mutation.cs`（只委派），方法追加在**既有** `{MOD}Service.{FORM}.cs` / `{MOD}Repository.{FORM}.cs` partial，不另建 Service/Repository 檔。

## 指路
- 連動/計算 → `details/field-change.md`
- DTO/存檔欄位 → `details/dto-display.md`
- 後端 mutation 建法 → 本檔「後端分層」
