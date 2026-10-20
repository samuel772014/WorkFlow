---
name: review-button
description: review-engine area.button 審查清單（工具列與列指令鈕/啟用條件/確認框/端點）
disable-model-invocation: true
---

# review-button — 按鈕功能審查（前端）

> 規則來源：`page-migration/details/toolbar.md`、`btn-control.md`、`crud-handlers.md`（前端流程段）、`attachment.md`。區代碼 **BTN**。
> **只審前端**：按下後的資料寫入、交易、鎖、SQL 一律歸 `review-backend`。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi | dfm 按鈕（`TRzBitBtn`/`TButton`/`TSpeedButton`/Action/選單）Caption、`Visible`、`OnClick`；導覽列內建功能（新增/修改/刪除/存檔/取消/查詢）；`ToggleControl`（各狀態按鈕啟用）；OnClick 內的前端互動（MessageDlg 確認、ShowMessage、開子視窗） |
| C# | `ToolbarButton`、`GridCommandButton`、`HandleToolbar`、`btnControl()` 旗標與條件、各 handler 的確認框與訊息、`gQL.*ApiCallAsync` 端點與 arg |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> list handlers --grep "Button|Click|Action"   # 含 dfm 事件綁定
py … <SAL> list comps --type TRzBitBtn ; py … <SAL> get proc ToggleControl
py … <SAL> list razor ; py … <SAL> get method btnControl ; py … <SAL> get method HandleToolbar
py … <SAL> get proc <XxxButtonClick> ; py … <SAL> get method <對應 handler>
py … <SAL> list gql
```
Delphi 按鈕的確認/訊息：`list procs` 的 `message_lines`（delphi 索引）或 `find "MessageDlg|ShowMessage" --side delphi`。

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| BTN-01 | Delphi 每個可見按鈕/功能在 C# 有對應；C# 無多出功能 | missing/extra｜medium |
| BTN-02 | 按鈕文字＝Delphi Caption（去 `&X`），Title/tooltip 一致 | mismatch｜low |
| BTN-03 | 工具列位置與順序：單檔工具列只放 新增→查詢；主檔明細主檔操作全在工具列，CRUD→查詢→特殊（grid 列指令鈕歸 grid 區 GRD-15） | rule-violation｜low |
| BTN-04 | 啟用條件＝Delphi `ToggleControl`/狀態判斷（如 STATUS='OP' 才可改/確認）；`btnControl()` 只設旗標、HandleToolbar 末尾呼叫 | mismatch｜medium |
| BTN-05 | 前端互動一致：確認框（刪除、確認、作廢、nzero 二次確認…）、提示訊息、取消後不送出 | missing/mismatch｜medium |
| BTN-06 | 呼叫的 gqlway 存在且 arg 帶齊（含 `EMPLYID`/`USR` 等身分值用 `EmplyId`，不寫死） | mismatch｜high |
| BTN-07 | 純圖示＋Title（Tabler `ti ti-*`），不放文字、不用 emoji | rule-violation｜low |
| BTN-08 | 附件：上傳/預覽/下載用 `FileFunc`，限 pdf、大小上限、上傳後即回寫（主檔已有單號時） | mismatch｜low |
| BTN-09 | 開子視窗類按鈕（匯入、選取…）開啟條件與回傳後處理一致 | mismatch｜medium |

## 4. 邊界
寫入/交易/鎖/SQL → backend；status 回傳值判斷寫法（`== 1`、禁 `== 0`/`> 0`）→ conventions；子視窗內部 → subwindow；匯出/列印 → export；權限 → permission（佔位）。
框架級通用功能（BaseForm/EditForm 的 grid 右鍵選單：依設定匯出Excel、欄排序、搜尋、篩選、固定欄位、連續新增；F11/翻頁/RecFirst 等快捷鍵）由 IksGrid 共用元件統一處理，**不逐頁審**（2026-10-08 裁決）。

## 5. 輸出
同 `review-grid` §5（區代碼 BTN）。
