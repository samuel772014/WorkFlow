---
name: review-special-logic
description: review-engine area.special-logic 審查清單（全域旗標/系統參數/資料權限/共用函式/Delphi 疑似缺陷）
disable-model-invocation: true
---

# review-special-logic — 特殊邏輯審查

> 規則來源：`page-migration/details/business-logic.md`、`shared-functions.md`、`.claude/SelfFolder/共用函式對照表.md`、`TODO彙整.md`。區代碼 **SPL**。
> **只收不屬於其他區的規則**；屬 button/backend/field-change/grid/editform 的不在此重報。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi | `FormCreate`/`FormShow` 的全域旗標與系統參數（`GetPRVAL`、`gb*`）、依旗標改變行為的分支、資料權限（`SAL_DataCtrl` 等）、跨功能狀態判斷、共用函式呼叫點、未使用變數/死碼 |
| C# | 對應的旗標讀取（後端 `GetPRVAL`）、條件分支、TODO 佔位、共用方法呼叫 |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> get proc FormCreate ; py … <SAL> get proc FormShow
py … <SAL> find "GetPRVAL|gb[A-Z]\w+|DataCtrl" --side delphi ; py … <SAL> find "GetPRVAL|TODO" --side cs
py … <SAL> list procs     # 看 shared_calls（delphi 索引）
```

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| SPL-01 | 系統參數／全域旗標（如 `SALPROC`、`gPSDU`、`gbHASSER`）在 C# 讀取並套用到同樣的分支 | missing/mismatch｜high |
| SPL-02 | 資料權限（`SAL_DataCtrl` 等）有實作，或已留 TODO 並登記 `TODO彙整.md` | missing｜high |
| SPL-03 | 共用函式：已移植者 C# 有呼叫（不重寫）；未移植者留 `// TODO(封裝商業邏輯)` 並登記 | rule-violation/missing｜medium |
| SPL-04 | 需查 DB 的計算（取換算率、匯率、稅率等）在後端；**純計算（不查 DB）可留前端，但須抽成 `IKSERPUI/iksUiFunc/iksUiFunc.cs`（`IksUiFunc`）共用函式**，不得散寫在頁面 razor，不必搬後端（2026-10-19 裁決，同 review-field-change FCH-03）；已有對應共用函式者須呼叫、不重寫 | rule-violation｜medium |
| SPL-05 | 跨功能狀態規則（如單況流轉條件、與其他單據的關聯檢查）一致 | mismatch｜medium |
| SPL-06 | Delphi 死碼（賦值未使用、永不成立分支）C# 不必實作；C# 若實作記 info | extra｜info |
| SPL-07 | Delphi 疑似缺陷（不屬 backend 者）記 `delphi-defect`，註明 C# 照搬或已修 | delphi-defect｜medium |

## 4. 邊界
寫入/交易/鎖 → backend；欄位連動 → field-change；按鈕啟用條件 → button；通用寫法慣例 → conventions。

## 5. 輸出
同 `review-grid` §5（區代碼 SPL）。
