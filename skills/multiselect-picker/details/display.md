# 代碼欄顯示名稱（_Display）

清單有「代碼欄」（如 PACKID、UNIT、CUSTMER…）時，檢視要顯示**名稱**而非代碼，用專案的 `DisplayResolver` 機制。

## 三步

1. **DTO 實作 `IDisplayResolvable`**，並為代碼欄加 `_Display` 屬性 + `[DisplayTransform]`：
   ```csharp
   public class PickRow : IDisplayResolvable
   {
       public string PACKID { get; set; } = "";
       [DisplayTransform("PACKID", "COMMON")]   // (DisplayCode, Module)
       public string? PACKID_Display { get; set; }
   }
   ```
   - `DisplayCode` 同時是**來源屬性名**；`_Display` 屬性名慣例 = `DisplayCode + "_Display"`。
   - `Module` 對應後端 DisplayTransform 路由 key（`"COMMON"`/`"SAL"`/`"MM"`…），省略後端自動偵測。
   - 需 `@using IKSERPUI.Components.Attributes`。

2. **欄位 `Field` 指向 `_Display`**（顯示名稱）：
   ```csharp
   { "PACKID_Display", new GridColumnConfig { Field="PACKID_Display", Title="包裝方式", Editable=false } },
   ```

3. **解析自動發生**：`IksGrid_vnq` 的 `Rebind` / `RebindKeepState` 會呼叫 `DisplayResolver.ResolveIfResolvableAsync`，把 `_Display` 填成 `"代碼:名稱"`（如 `P01:紙箱`）；查不到則回代碼（graceful）。

## 眉角

- 若欄位「可編輯 combobox」，用 `Field="X_Display"` + `EditorTemplate` 綁 `item.X`（代碼）——view 顯名稱、edit 選代碼。此時 InCell 更新的 `args.Field` 會是 `X_Display`（非 `X`），連動判斷要用它當 key。
- 編輯完代碼後 `_Display` 會過期 → 用 `RebindKeepState(_data)` 重新解析（它內部會 re-resolve）。
- 純選擇器（唯讀）通常不含編輯，只要 DTO 有 `_Display` + 欄位 `Field` 指過去即可。

> 對應記憶：`feedback_dto_inherit_model`、`reference_displaytransform_keycode_alias`。參考頁：SAL027A（PACKID_Display）、SAL025/046。
