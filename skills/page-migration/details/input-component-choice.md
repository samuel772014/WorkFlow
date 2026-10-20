# 詳細規則：輸入元件選擇決策樹（跨區：篩選 D、編輯 E 共用）

> 篩選欄位（`details/popup-filter.md`）與編輯表單欄位（`details/edit-window.md`）都先來這裡決定「這個欄位該用哪種控件」。
> **判準：看 Delphi 來源該欄位實際怎麼取值、抓幾欄**，不是看畫面長相。

---

## 決策樹

```
該欄位在 Delphi 怎麼取值？
├─ KeyCodePick / KeyCodeValidate（KeyCode 類）      → KeyCodeComboBox
├─ EditPick →  pick SQL 實際 select 幾欄？
│               ├─ ≤ 2 欄（代碼 + 名稱）             → IksCodeComboBox
│               └─ ≥ 3 欄                            → EditPick（保留彈窗）
├─ EditMemo（DblClick 開多行長文字放大視窗）          → PopUpText（→ details/popuptext.md）
├─ 一般 DBEdit（純文字輸入）                          → IksTextBox
└─ 特殊情況（連動、唯讀帶入、非典型取值…）           → 詢問轉譯操作者
```

**規則說明**
- **KeyCode 類**：Delphi 用 `KeyCodePick`/`KeyCodeValidate`/`GetKeyCodeDESCPT` 的欄位（狀態、類別碼…）→ `KeyCodeComboBox`。
- **EditPick 看欄位數**：判斷依 pick 的 `select` 子句實際欄數（代碼+名稱＝2 欄）。
  - ≤ 2 欄 → `IksCodeComboBox`；優先用現成 `ComboBoxService` code，特殊過濾才另開 endpoint（見 details/shared-input-components.md）。
  - ≥ 3 欄 → 維持 `EditPick`。
- **EditMemo 類**：Delphi 在 grid/欄位的 `DblClick` 呼叫 `EditMemo(Sender,'標題',bgEdit)` 開多行長文字放大視窗（備註、說明、負責事項…）→ 轉 `PopUpText`（Grid 明細列以 `EditorTemplate` 內置 TextBox＋放大鈕開窗；用法與寫回見 `details/popuptext.md`）。標題沿用 Delphi 第二參數。
- **純文字**：一般 `DBEdit` → `IksTextBox`（見 details/shared-input-components.md IksTextBox）。
- **特殊情況一律詢問轉譯操作者**，不自行臆測。
- 選定控件後，**參考該控件的控件 skill 使用方式**（KeyCodeComboBox / IksCodeComboBox / EditPick / IksTextBox）。

### 總則：以 Delphi 原規則為準
- **忠實還原 Delphi**：Delphi 有的欄位就照原規則轉出來，**不隨意省略**（SAL001 當初藏起 STATUS 屬偏離，正解是照 Delphi 顯示）。
- 依原規則轉出的欄位，**在控件旁加繁體中文註解**說明用途/來源（見 `CLAUDE.md「通用慣例」`）。
- 真的要偏離 Delphi（省略欄位、改行為）才屬「特殊情況」→ 詢問轉譯操作者。

---

## 指路

- 篩選欄位怎麼擺 → `details/popup-filter.md`
- 編輯欄位怎麼擺、連動帶值 → `details/edit-window.md`
- 各控件參數細節 → 對應控件 skill（KeyCodeComboBox / IksCodeComboBox / EditPick / IksTextBox）
