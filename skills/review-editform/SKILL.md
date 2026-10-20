---
name: review-editform
description: review-engine area.editform 審查清單（編輯 Window 欄位/標籤/順序/控件/唯讀/必填）
disable-model-invocation: true
---

# review-editform — 單筆編輯表單審查

> 規則來源：`page-migration/details/edit-window.md`、`input-component-choice.md`、`shared-input-components.md`、`final-dfm-check.md` ④、`popuptext.md`。區代碼 **EDT**。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi | dfm 編輯區（`tbEdit`/`MScrollBox*`，含其他 TabSheet 的編輯區）標籤＋控件（DataField、Top/Left、`Visible`、`ReadOnly`、`MaxLength`）；`.pas` `MqyDblClick`（pick／EditMemo）、`FormCreate` 的 `sKeyFields`／`sNotNullFields`、`MqyNewRecord` 預設值 |
| C# | 編輯 Window／主表單的 `iks-edit-row`、控件與綁定、`Enabled`/`ReadOnly`、`IksLabel Required`、View 模式、主鍵欄處理、`Add()` 預設 |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> compare editform   # ★先跑：欄位/標籤/順序/隱藏/唯讀/開窗 vs C# 編輯列
py … <SAL> compare editform --tab <TabSheet 名或 Caption>                   # 單頁籤重現比對（不列 C# 多出列，多出欄對照該頁籤 razor 區塊人工核）
py … <SAL> get proc MqyDblClick ; py … <SAL> get proc FormCreate ; py … <SAL> get proc MqyNewRecord
py … <SAL> list rows --kind edit
py … <SAL> get comp <控件名>                                                # 單一控件屬性（Visible/ReadOnly/MaxLength）
```

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| EDT-01 | 欄位集合一致（漏／多）；`Visible=False` 欄不顯示但預設值/存檔值仍處理 | missing/extra｜medium |
| EDT-02 | 標籤文字逐字＝dfm Caption（去 `&X`）；標籤與控件綁定（FocusControl）一致 | mismatch｜low |
| EDT-03 | 欄位順序依 dfm Top→Left（同 TabSheet 內） | mismatch｜low |
| EDT-04 | 控件依決策樹（KeyCode／EditPick 欄數／EditMemo→PopUpText／純文字 IksTextBox）；`MqyDblClick` 有 pick 分支的欄 C# 須有對應開窗（signal `edit-pick-missing`）；代碼欄顯示的名稱欄＝`MqyGetText` `GetNoDESCPT` 的名稱欄（ComboBox 的 Map 名稱欄、EditPick `NameField`） | rule-violation｜medium |
| EDT-05 | Delphi `ReadOnly=True` 或連動帶入欄 → C# 唯讀（優先 `ReadOnly`，不支援才 `Enabled=false`） | mismatch｜low |
| EDT-06 | 必填＝`sNotNullFields` 中的可編輯欄：`IksLabel Required` ＋ 存檔前驗證；非必填不標 | mismatch｜medium |
| EDT-07 | 主鍵（`sKeyFields`）Add 可設、Edit/View 唯讀；不提供改主鍵 | rule-violation｜medium |
| EDT-08 | 檢視模式重用編輯 UI、全部唯讀（ReadOnly 優先）、隱藏存檔、標題「檢視」 | rule-violation｜low |
| EDT-09 | `MqyNewRecord` 預設值 → `Add()` 相同欄、相同值 | missing/mismatch｜medium |
| EDT-10 | `MaxLength`、大小寫轉換等輸入限制一致 | mismatch｜low |
| EDT-11 | Delphi 依狀態/條件切換可編性的欄（`MqyBeforeEdit`、`ToggleControl` 內欄位 ReadOnly），C# 同條件 | mismatch｜medium |

## 4. 邊界
欄位改值後連動／帶值／驗證訊息 → field-change；存檔寫入欄位 → backend；comboBoxCode 登記 → conventions；編輯窗內上/下一筆 → grid（GRD-19）。

## 5. 輸出
同 `review-grid` §5（區代碼 EDT）。「[座標配對]」「[標籤未綁控件]」者引用前需 `get comp` 複核；Delphi 標籤明顯指錯控件（如標籤文字與 DataField 意義不符）記 `delphi-defect`。
漏欄／多欄／順序（EDT-01、EDT-03）依 TabSheet（或 MScrollBox 區塊）各立一條 finding，claim 開頭標區塊名，讓每個區塊可各自裁決。

## 6. 重現判定（使用者問「是否完全重現」或做單頁籤比對時）
1. 第一句給判定：**完全重現**，或 **未重現 N 項**。N＝與 Delphi 的全部落差數。
2. 全部落差列在同一張表：控件／落差／既有 review ID＋裁決。已記錄待修、park、accept 的落差照樣列入表內，accept 者註明「先前 accept，是否維持？」。
3. 一致項只用一行帶過（如「其餘 N 欄一致」），放在表後。
4. 修完部分項目回報時，再給一次判定（完全重現／仍未重現 N 項）。
