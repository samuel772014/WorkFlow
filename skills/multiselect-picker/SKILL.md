---
name: multiselect-picker
description: 建立 IKSERP Blazor「多選選擇器」(picker) 的流程與規則。當使用者說「建立/做一個選擇器」「多選 picker」「參考 SAL027A 做選擇器」，或要「篩選 → 清單勾選多筆 → 確定帶回」的彈窗時觸發。以 SAL027A 穿梭頁左側結構為藍本（IksGrid_vnq 多選、OnRowClick+Shift 選取、載入遮罩、iks-fbtn、OnConfirm/OnClose）。
---

# IKSERP 多選選擇器（MultiSelect Picker）

> 「選擇器」＝以 `TelerikWindow` 嵌入的**篩選 + 單一清單多選 + 確定回傳多筆**對話框。
> 非 CRUD 維護頁（那走 `page-migration`）、非單筆小彈窗（那用 `EditPick`）。以 SAL027A 左側結構為藍本。

## 觸發時機

使用者說「建立/做一個選擇器」「多選 picker」「參考 SAL027A 做選擇器」，或要一個「篩選 → 清單勾選多筆 → 確定帶回」的彈窗。

## 何時用 / 何時不用

- ✅ **用**：呼叫端要讓使用者從一份清單挑「**多筆**」帶回（批次挑料品／客戶／單號…）。
- ❌ **不用**：
  - 單筆挑選且欄位少 → 用 `EditPick`（小彈窗）。
  - 有新增/修改/刪除的維護頁 → 走 `page-migration`。

## 骨架（放大版）

> 完整可貼範本見 `templates/picker.md`。核心結構（由上而下）：

1. `@inherits IksPageBase` + `<TelerikLoaderContainer Visible="@IsPageLoading">` 載入遮罩。
2. **篩選區**（grid 版型 filter；控件依實體：`IksCodeComboBox` / `EditPick` / `IksTextBox`）+ `iks-fbtn` 查詢鈕。
3. **`IksGrid_vnq<TItem>`**：`ShowCheckbox="true"` `ShowSelectAll="false"`、`HeaderButtons`=全選/取消、`OnRowClick`=選取。
4. **底部 `iks-fbtn`**：確定(`primary`)→ `OnConfirm` 回傳選取清單；取消 → `OnClose`。

`@code` 宣告位置：對外 `OnConfirm`/`OnClose`；`_grid`(@ref)、`_data`、`_anchor`(Shift 錨點)；`FomId`；DTO + `_columns`。
Lifecycle：`OnAfterRenderAsync(firstRender)` 首查一次 → `LoadAsync()`（`SetPageLoading`/`SetPageLoaded` 包）。

## 流程

1. **問使用者**：選什麼實體、篩選欄位、清單欄位、回傳型別（多用 `List<TItem>`）。
2. **複製** `templates/picker.md` 骨架 → 改元件名、`FomId`、`Table_Name`、DTO、`_columns`、篩選控件、`LoadAsync` 查詢 API。
3. **選取行為**（`details/selection.md`）：⚠ InCell 下點列**不觸發 OnSelect**，一律用 `OnRowClick`；Shift 區間用 `MouseEventArgs.ShiftKey`+本地 index `GetRange`；欄位 checkbox 不支援 Shift。
4. **代碼欄顯示名稱**（`details/display.md`）：`[DisplayTransform]` + `X_Display` + 欄位 `Field="X_Display"`。
5. **欄寬異常**（`details/grid.md`）：用**無參數 `Rebind()`** 重載欄寬設定（`Rebind(list)` 不重載）。
6. **呼叫端接線**（`details/wiring.md`）：`TelerikWindow` 包住 + 綁 `OnConfirm`/`OnClose`。

## details 索引（要做哪區才讀哪支）

| 區 | 檔 |
|----|----|
| 完整骨架範本 | `templates/picker.md` |
| 選取（OnRowClick / Shift / checkbox 限制；整批設定/清除篩選 的選取保留） | `details/selection.md` |
| 代碼 → 名稱顯示（_Display） | `details/display.md` |
| Grid 欄寬 / Rebind 眉角 | `details/grid.md` |
| 呼叫端接線（Window / OnConfirm / OnClose） | `details/wiring.md` |
