---
name: review-subwindow
description: review-engine area.subwindow 審查清單（子 form/picker/PopUpText 存在/版型/回傳接線）
disable-model-invocation: true
---

# review-subwindow — 子視窗／彈窗審查

> 規則來源：skill `popup-window`、`multiselect-picker`、`page-migration/details/popuptext.md`、`templates/excel-import.md`。區代碼 **SUB**。
> 子 form 自己的 grid／篩選欄位用 `compare grids`／`compare filter`（已含子 form）審，記在本區（不重複記到 grid/filter 區）。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi | `sources.delphi.subforms`（B###a…）整個 form（含其基底鏈）；主檔中開子 form 的呼叫點（`ShowModal`、`Create`）；`EditMemo(…)` 呼叫 |
| C# | 子元件 razor（SAL###A/B/D）、呼叫端 `TelerikWindow` 接線、`PopUpText`、`EditPick_Button` 以外的彈窗 |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> compare grids ; py … <SAL> compare filter      # 看 [子form] 段
py … <SAL> list handlers --unit <子form B 碼> --used ; py … <SAL> get proc KButtonClick --unit <子form>
py … <SAL> list razor --file <SAL>A ; py … <SAL> list gql --file <SAL>A
py … <SAL> find "EditMemo\(|ShowModal" --side delphi
```

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| SUB-01 | Delphi 每個子 form／彈窗在 C# 有對應子元件；C# 無多出彈窗 | missing/extra｜medium |
| SUB-02 | 子 form grid 欄位／欄序／標題（`compare grids` 子 form 段）；**含 GRD-05**：子 form `AddFieldEvent` 掛 GetText 的代碼欄須保留代碼＋`_Display`/DisplayTransform，不得換成後端組的名稱欄（如 `_NM`） | missing/mismatch/rule-violation｜medium |
| SUB-03 | 子 form 篩選（`compare filter` 子 form 段）；篩選一律 Popup | mismatch/rule-violation｜low |
| SUB-04 | 多選勾選來源＝元件 `SelectedItems`（全選用 `SelectAll()`/`ClearSelection()`），不用 DTO `_Selected` | rule-violation｜medium |
| SUB-05 | 子 form 確認動作（如 `KButtonClick`）帶回的資料與處理與 Delphi 相同（寫入部分交 backend） | mismatch｜high |
| SUB-06 | 接線：呼叫端 `TelerikWindow @bind-Visible`＋`WindowAction Close`；子元件 `OnConfirm`/`OnClose`/`OnCancel`；開啟時帶入的條件參數一致 | rule-violation/mismatch｜low |
| SUB-07 | Delphi `EditMemo` 欄 → C# `PopUpText`，標題＝EditMemo 第二參數；註解掉的 EditMemo 不轉 | missing/mismatch｜low |
| SUB-08 | 版型：A 純編輯型／B 查詢型（篩選 Popup）；動作鈕在底部 `iks-edit-actions`，不與查詢同列 | rule-violation｜low |

## 4. 邊界
子 form 確認後的資料寫入、交易 → backend；Excel 匯入窗的寫入 → backend；子視窗標題 → title。

## 5. 輸出
同 `review-grid` §5（區代碼 SUB）；quote 檔案指向子 form／子元件自己的檔。

## 6. 工具警示必須結案（2026-10-08，防誤判）
- 本區一律先跑 `py .claude/SelfFolder/review-engine/tools/query.py <SAL> compare <grids|filter|editform> --save`，每個警示寫成 `state.signals`。
- **每個 signal 必須結案**，二擇一：
  - 立成 finding：`review_state.py resolve <SAL> <signal-id> finding=<finding-id>`
  - 豁免：`review_state.py resolve <SAL> <signal-id> "waive=<理由>@@<規範出處>"`，理由與規範出處（檔名＋章節／行號）**都必填**。
- **禁止**以「顯示差異」「應為刻意設計」「影響不大」等沒有規範依據的說法略過；找不到規範條文支持豁免就立 finding，交 triage／human-review 判斷。
- 未結案的 signal 會讓 evidence-check 閘門把本區退回重跑。
