---
name: review-export
description: review-engine area.export 審查清單（匯出 Excel/列印報表）
disable-model-invocation: true
---

# review-export — 匯出／列印審查

> ⚠ **page-migration 尚無匯出/列印規則**（`details/export-print.md` 待補，已列提醒）。本區暫以「與 Delphi 一致」為唯一基準，`rule-violation` 類暫不適用；規則補齊後再加規範檢查。區代碼 **EXP**。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi | 匯出/列印按鈕與 handler（`ExportButton`、`PrintButton`、`Excel`、`QuickRep`、`frxReport`、呼叫 R 報表程式）；報表 SQL 與欄位 |
| C# | 匯出/列印按鈕、端點、產出檔欄位與格式 |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> find "Export|Excel|Print|Report|frx|QuickRep|R\d{3}" --side delphi
py … <SAL> list handlers --grep "Print|Export|Excel" ; py … <SAL> get proc <handler>
py … <SAL> find "Export|Excel|Print|Report" --side cs
```

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| EXP-01 | Delphi 每個匯出/列印功能在 C# 有對應 | missing｜medium |
| EXP-02 | 匯出欄位集合、順序、標題與 Delphi 相同 | mismatch｜low |
| EXP-03 | 資料範圍（依目前篩選／選取列／整單）與 Delphi 相同 | mismatch｜medium |
| EXP-04 | 數值/日期格式、合計列與 Delphi 相同 | mismatch｜low |
| EXP-05 | 列印報表：版面欄位與報表 SQL 與 Delphi 報表程式一致 | mismatch｜medium |

## 4. 邊界
按鈕位置/啟用 → button；報表 SQL 若在共用後端 → backend 協同（本區記功能差異，backend 記 SQL 差異）。

## 5. 輸出
同 `review-grid` §5（區代碼 EXP）。
