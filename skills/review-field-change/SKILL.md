---
name: review-field-change
description: review-engine area.field-change 審查清單（欄位連動/驗證/帶值/新增預設值）
disable-model-invocation: true
---

# review-field-change — 欄位連動／驗證審查

> 規則來源：`page-migration/details/field-change.md`、`business-logic.md`（計算落點）、`grid-incell.md`（OnUpdate）、`editor-template.md`。區代碼 **FCH**。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi | `MqyChange`/`Dq*Change`（依 `Field.FieldName` 分支）、`*Validate`（CheckNo/CheckKeyCode/自訂檢查與訊息）、`*NewRecord`、`BeforePost*`、`AddFieldEvent` 註冊的欄位與事件 |
| C# | `@bind-Value:after` handler、InCell `OnUpdate` 的 `args.Field` 分派、連動查詢 endpoint、`Add()`/`OnAdd` 預設、存檔前驗證、後端連動/計算 endpoint |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> find "AddFieldEvent" --side delphi   # 哪些欄掛了 Change/Validate
py … <SAL> get proc MqyChange ; py … <SAL> get proc Dq1Change ; py … <SAL> get proc Dq1Validate
py … <SAL> get proc MqyNewRecord ; py … <SAL> get proc Dq1NewRecord
py … <SAL> list methods --file <SAL>.razor --grep "Changed|Update|OnAdd|Add$|Save"
py … <SAL> get method <handler>
```
大 handler（如 1000 行的 `Dq1Change`）：先 `find "FieldName\s*=\s*'<欄>'"` 定位分支，再 `src` 取該段。

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| FCH-01 | Delphi 每個 Change 分支（觸發欄）在 C# 有對應 handler | missing｜medium |
| FCH-02 | 帶值目標欄與來源一致（帶哪些欄、從哪張表、條件） | mismatch｜medium |
| FCH-03 | 需查 DB 的計算（取換算率、匯率、稅率等）在後端；**純計算（不查 DB，如 QTY×TRFRT1/TRFBS1 換算、明細加總回寫父列）可留前端，但須抽成 `IKSERPUI/iksUiFunc/iksUiFunc.cs`（`IksUiFunc`）共用函式**，不得散寫在頁面 razor，不必搬後端（2026-10-19 裁決，起因 SAL071-FCH-003）；計算公式/小數位與 Delphi 一致。前端純計算散寫在頁面 → rule-violation｜medium；需查 DB 的計算放前端或公式/小數位不一致 → high | rule-violation/mismatch｜high/medium |
| FCH-04 | 驗證規則與訊息：Delphi `*Validate`/BeforePost 的檢查條件、擋下時機、訊息文字，C# 相同 | missing/mismatch｜medium |
| FCH-05 | 新增預設值（`*NewRecord`）→ `Add()`/`OnAdd` 相同欄與值（含 uState=Insert、項次遞增） | missing/mismatch｜medium |
| FCH-06 | 相依欄：上層改→清空下層；相依 ComboBox 用 `Args` 帶上層值過濾 | missing｜low |
| FCH-07 | InCell 連動走 `OnUpdate` 依 `args.Field` 分派、鍵值撈 GD 實際列；EditorTemplate `ValueChanged` 不打 API、不 Rebind；OnUpdate 內不呼叫 `ExitEditModeAsync` | rule-violation｜medium |
| FCH-08 | 連鎖連動（一個改值觸發多個重算）順序與 Delphi 相同 | mismatch｜medium |
| FCH-09 | Delphi 中被註解掉的連動，C# 不應實作（反之 C# 漏實作現行連動） | extra/missing｜low |

## 4. 邊界
存檔寫入哪些欄/交易 → backend；grid 欄位定義與可編性 → grid；編輯表單欄位有無/唯讀 → editform；跨功能狀態規則 → special-logic。

## 5. 輸出
同 `review-grid` §5（區代碼 FCH）。Delphi 分支條件不明（依執行期資料）→ open_question。
