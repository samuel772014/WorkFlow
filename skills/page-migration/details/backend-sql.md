# 詳細規則：後端 SQL 執行（IksDbFunc / Transaction / 回傳封裝）

> 給 H 區 CRUD 與連動查詢的後端實作用（`details/crud-handlers.md`、`details/field-change.md` 指來這）。
> 對應 Delphi：`SQLOpen`/`SQLValue`/`SQLExec` 等。來源：舊 `db-operation-mapping` 彙整。
> **先找共用函式**：Delphi 參考函式先查 `Modules/FUNC` 是否已有 C# 版，勿重寫（記憶 `reuse_func_modules`）。

---

## Delphi → C# 對照
| Delphi | C# |
|--------|----|
| `SQLOpen(ds, sql)` | `_iksDbFunc.SQLCreate(sql, param)` |
| `SQLValue('select…')` | `_iksDbFunc.SQLValue(sql)` / `SQLValue<T>(sql)` |
| `GetNewItem(Dq,'COL')` | `_iksDbFunc.SQLFirst<T>("SELECT MAX(COL)+1 FROM …")` |
| `DataSet['COL']` / `Field.AsString` | `args["COL"]`（Dictionary） |
| `AA(str)` 包引號拼接 | **禁止** → 用 `DynamicParameters` |

## 一律走 `_iksDbFunc.*`，禁止直呼 conn.QueryAsync/ExecuteAsync
| 方法 | 用途 |
|------|------|
| `SQLValue(sql,p?)` / `SQLValue<T>` | 第一列第一欄（無資料回空字串／default） |
| `SQLFirst(sql,p?)` / `SQLFirst<T>` | 第一列（無資料 null／default） |
| `SQLCreate(sql,p?)` / `SQLCreate<T>` | 結果集（= Delphi SQLOpen） |
| `SQLExec(sql,p?)` | INSERT/UPDATE/DELETE（回影響列數） |
| `SQLExec/SQLCreate/SQLFirst(sql, conn, tx, p?)` | Transaction 內共用 conn/tx |

## AA() → DynamicParameters（參數化，防注入）
```csharp
// Delphi: iif(sVal='','',' AND COL='+AA(sVal))
if (!string.IsNullOrWhiteSpace(val)) { sql += " AND COL=@COL"; parameters.Add("COL", val); }
// LIKE：Delphi ' AND NSN LIKE '+AA(sNSN+'%')  →
sql += " AND NSN LIKE @NSN"; parameters.Add("NSN", nsn + "%");
```

## Transaction（主+明細一起存，全成才 commit）
```csharp
using var conn = _context.CreateConnection(); conn.Open();
using var tx = conn.BeginTransaction();
try {
    // 重複鍵後端二次檢查（KeyExistsAsync）→ 主表 → 各明細 全走 conn/tx 多載
    await _iksDbFunc.SQLExec(sqlMaster, conn, tx, pMaster);
    foreach (var d in details) await _iksDbFunc.SQLExec(sqlDetail, conn, tx, pDetail);
    tx.Commit();
} catch { tx.Rollback(); throw; }
```
> 對應 `details/crud-handlers.md`（主+明細 transaction、重複鍵雙重檢查）。

## 回傳封裝
| 類型 | 類別 | 簽章 |
|------|------|------|
| 查詢 | `queryResult` | `(int status, string msg, int totalCount, string? jsonData)` |
| 異動 | `mutationResult` | `(int status, string msg, string? jsonData)` |
> `status`：`1`=成功、`-1`=失敗。Resolver 只轉發、商業邏輯在 Service（記憶 `mutation_pattern`）。設計 DB-agnostic、勿依 DB 錯誤碼（記憶 `db_agnostic_no_errorcode`）。

## 指路
- 存檔/刪除流程 → `details/crud-handlers.md`
- 連動查詢 endpoint → `details/field-change.md`
- 命名（Repository Query/Service Get/Mutation）→ `details/naming.md`
