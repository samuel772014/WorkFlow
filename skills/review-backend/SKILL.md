---
name: review-backend
description: review-engine area.backend 審查清單（存檔/交易/鎖/SQL/分層）
disable-model-invocation: true
---

# review-backend — 存檔／交易／鎖＋後端審查

> 規則來源：`page-migration/details/crud-handlers.md`（含「單據鎖定」「後端分層」）、`backend-sql.md`（含 status 語意）、`shared-functions.md`、`.claude/SelfFolder/共用函式對照表.md`。區代碼 **BKD**。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi | 存檔（`PostAction`、`BeforePostTransaction`、框架存檔）、刪除、狀態變更（CF/CC/CR 等按鈕的寫入段）、查詢 SQL（`OpenPick`/`DisplayButtonClick`/明細 SQL）、`StartTransaction/Commit/Rollback`、`ProcLCKFM`、共用函式呼叫 |
| C# | Repository/Service/Resolver（本頁＋locate 追到的共用方法）、SQL、`BeginTransaction`、`ProcLckFm`、回傳 `queryResult`/`mutationResult` |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> list txn                     # 兩側交易/鎖位置
py … <SAL> list sql --side delphi --grep "<表名>" ; py … <SAL> list sql --side cs --grep "<表名>"
py … <SAL> get proc PostAction ; py … <SAL> get proc <XxxButtonClick>                  # 大流程用 src 分段
py … <SAL> get method <Service/Repository 方法>
py … <SAL> list commented                                                              # Delphi 已註解區塊（C# 不應實作）
```
共用函式：Delphi 呼叫名查 `共用函式對照表.md` 得 C# 方法，確認 C# 有呼叫而非自寫 SQL。

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| BKD-01 | 存檔寫入欄位＝Delphi 實際存的欄（不是畫面全欄或 UPDATE 全欄）；唯讀/自動維護欄不被覆為 null | missing/mismatch｜high |
| BKD-02 | 交易邊界：主檔＋各明細同一交易；狀態變更流程的交易範圍與 Delphi 相同 | mismatch｜high |
| BKD-03 | 單據鎖 SS_LCKFM：修改上鎖/取消解鎖/存檔解鎖/狀態變更交易外上鎖＋finally 解鎖；FMID 正確；USR＝登入者 EmplyId | missing/mismatch｜high |
| BKD-04 | 狀態變更（確認/作廢/取消確認…）步驟順序與影響的表逐段對齊 Delphi（含庫存、銷貨單、MPS、信用額度等副作用） | missing/mismatch｜high |
| BKD-05 | 查詢 SQL 語意：JOIN、WHERE（非篩選部分）、ORDER BY、欄位來源與 Delphi 相同 | mismatch｜medium |
| BKD-06 | 共用函式：Delphi 呼叫的共用函式 → C# 呼叫對照表中的對應方法，不重寫 SQL；未移植者留 TODO 並登記 `TODO彙整.md` | rule-violation/missing｜medium |
| BKD-07 | 單號產生（GetFMCODE 等）規則一致 | mismatch｜high |
| BKD-08 | SQL 參數化（不字串串接使用者輸入）；一律 `_iksDbFunc.*` | rule-violation｜high |
| BKD-09 | 刪除連動（主檔刪除連同明細）與 Delphi 一致；重複鍵前後端雙重檢查（DB-agnostic） | mismatch｜medium |
| BKD-10 | 回傳 status 語意：1 成功、0/-1 失敗、2 需前端確認、3 部分成功 | rule-violation｜medium |
| BKD-11 | 分層：Resolver 只轉發、商業邏輯在 Service/Repository；Mutation 與 Query 共用同一 partial | rule-violation｜low |
| BKD-12 | Delphi 已註解掉的流程（`list commented`），C# 未擅自實作；Delphi 現行流程 C# 未遺漏 | extra/missing｜medium |
| BKD-14 | **文字欄空字串寫入**：INSERT/UPDATE 的字串參數若可能為 `""`（`GetValueOrDefault(k,"")`、`v ?? ""`、`ODS`/`A78Str`/`HS` 類 helper 直接當參數、`TryGetValue` 存在即寫）→ 須轉 NULL；新增列有 Delphi `NewRecord` 預設的欄，空字串須套預設而非寫 `''`（CHECK 約束欄不收 `''` → 存檔失敗，如 SAL078 `CK__SA_SALEM__TOTAR`、`CK__SA_SALED__BKPBK`）。涵蓋主檔、各明細、子視窗匯入、狀態變更 update。查法：`find "DbType.String|\\?\\? \"\"|GetValueOrDefault\\(\\w+, \"\"\\)" --side cs` 逐一看是否進 INSERT/UPDATE。依據 `page-migration/details/crud-handlers.md` 存檔第 6 點（2026-10-13） | mismatch｜high |
| BKD-13 | Delphi 疑似缺陷（殘留游標、條件寫錯、欄位筆誤）：記 `delphi-defect`，並註明 C# 照搬或已修正 | delphi-defect｜medium |

## 4. 邊界
前端按鈕流程/確認框 → button；欄位連動計算 → field-change；查詢 WHERE 的篩選條件語意 → filter；跨功能狀態規則與資料權限 → special-logic。

## 5. 輸出
同 `review-grid` §5（區代碼 BKD）。大流程逐段比對時，每段一條 finding，Delphi/C# 各取該段代表性 quote。
