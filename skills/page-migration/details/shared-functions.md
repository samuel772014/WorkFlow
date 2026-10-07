# 詳細規則：共用函式庫（FUNC）轉換查詢

> 給後端邏輯轉譯用。**Delphi 參考函式先查 `Modules/FUNC` 是否已有 C# 共用函式，勿重寫 SQL**（記憶 `reuse_func_modules`）。
> 來源：舊 `shared-functions`（共用function.xlsx，500+ 函式；完整表在 Desktop 備份，本檔只放方法與常用）。

---

## ⚠️ 封裝成函式的商業邏輯 → 寫進 log，不自行重寫

轉譯時若遇到「**封裝成函式的商業邏輯**」或**尚未實作的共用函式**（共用/FUNC 函式或 dm 方法裡包著業務規則，如資料權限 `SAL_DataCtrl`、自動序號 `GetNewItem`／`GetFMCODE`、金額/稅額/匯率計算、單號鎖定、`GetCUSTNSN` 客戶品號↔料號等；或 `Modules/FUNC` 已宣告卻 `NotImplementedException`／`TBD` 的方法），**不要自行重寫或臆測其內部規則**：

1. 在 C# 對應位置先留 `// TODO(封裝商業邏輯): {函式名} 待處理` 佔位，不猜規則。
2. **同步更新 `.claude/SelfFolder/TODO彙整.md`**（park／TODO 標記的單一彙整表）：把該項登記進對應分類段落（`二、UI 層` / `三、API 層 SAL Repository/Service` / `四、Resolvers` / `五、FUNC 共用模組` / `六、基礎`），每列格式 `檔名:行 說明`，並視情況更新「一、總覽」的分類/檔案數。若同類已有段落就併入，沒有才新增段落。
3. 由**使用者後續統一處理**（決定重用既有 C# 共用層 / 重新實作 / 併入 Service）。

> 純 UI/工具 helper（如 `EditPick`、`GetNoDESCPT` 顯示名）走下方「使用方法」對照即可，不需登記；**登記的是「含業務規則」的封裝函式或尚未實作的共用函式**。
> `TODO彙整.md` 是給人看的彙整表（依分類收斂、含總覽），逐筆流水帳仍寫 `translation-log.md`；兩者角色不同，遇到上述情況以更新 `TODO彙整.md` 為準。

---

## 使用方法
1. 掃 `.pas` 的 `uses` 段，確認引用哪些共用 Unit：
   `BseFunc / BuyFunc / ErpFunc / CstFunc / CstFunc1 / SalFunc / BSALEM_UNCF / MpsFunc / MpsFunc1 / MpsFunc2 / MpsFunc3 / MpsFuncP / Mps_GFunc / StkFunc`
2. 搜尋這些函式呼叫（`UnitName.FuncName(...)` 或直接 `FuncName(...)`）。
3. 查對照表取「用途／處理方式／負責人」。
4. 在 **C# 對應實作上方**加單行註解：`// 用途：{用途} 處理方式：{處理方式} 負責人：{負責人}`（空欄略去）。

## 處理方式 → C# 行動
| 處理方式 | 行動 |
|---------|------|
| `改寫` / `重新設計` | C# 重新實作（多半在 `Modules/FUNC` 的 `ERPFunc`/`SALFunc` 共用層） |
| `改C#本身功能` | 用 C# 原生 API 取代（如四捨五入 `Get_Round`→`Math.Round`） |
| `併入個別程式處理` | 邏輯寫入當前模組 Service |
| `作廢` | 不實作；舊呼叫加註說明已廢 |
| `TBD` | `// TODO:` 標記 |

## 常用（SAL 相關，轉 SAL301 類報價/訂單常見）
| 函式 | 用途 | 處理方式 |
|------|------|---------|
| `Calcu_MNYTAX` | 金額稅額計算（前端用版本） | 改寫（→ 後端 `{form}_CalcMNY`，計算一律後端） |
| `CalcNTMNY` | 依幣別取本幣小數位 | 改寫（Calcu_MNYTAX* 系列併入） |
| `Get_MRATE` | 取匯率 | ✅ 已改寫 `ERPFunc.GetMRateAsync`；各頁走共用 `SALService.GetSALCurMrateAsync` 轉發（見下方實例二） |
| `GetTaxRate` | 取稅率 | 改寫（SalFunc 版併入 ERPFUNC） |
| `Get_PAYTERM` | 依付款條件算預計付款日/票期 | 改寫 |
| `GetCUSTNSN` / `CUSTNSNGetNSN` | 客戶品號↔料號互查 | ✅ 已抽共用 `SALService.GetSALCustNsnInfoAsync`（見下方實例一） |
| `SALGetUp` / `SALGetYRQTY` | 取銷售價格 / 基本購量 | 改寫 |
| `Calc_CRMNY_INSMNY` | 計算運費保費 | 改寫 |
| `Calc_Master_MNY` | 彙算主檔總金額並調明細 | 改寫 |
| `ProcLCKFM` / `chkSTATUS1` | 單據鎖定 / 檢查最新單況 | 重新設計（見記憶 `doc_lock_pattern`） |
| `Get_Round/Round1/Round2` | 四捨五入/捨去/進位 | 改 C# 原生 |

> 完整 500+ 函式表在 `C:\Users\samuel\Desktop\.claude\skills\delphi-to-csharp\references\shared-functions.md`（共用function.xlsx）。

---

## 後端共用函式抽取規則（某頁查詢/邏輯要給另一頁重用）

> 情境：某頁已有的後端查詢/邏輯（如 SAL046 的 `sal046_GetCUSTNSN_Info`）另一頁也要用（SAL044 客戶品號↔料號）。
> 裁決：**把共用實作移到共用 service/repository，各頁 resolver 薄層轉發到同一份，不各頁複製 SQL。**

### 何時抽共用
- **同一查詢/邏輯被 ≥2 頁使用**才抽（如 CUSTNSN↔NSN 互查供 SAL044/SAL046）。單頁專用不必抽。

### 落點
- 共用實作放**共用 partial**：`SALRepository.Common.cs` / `SALService.Common.cs`（與各頁 `SALService.SALxxx.cs` 同 class 的 partial）；或既有共用層 `SALFunc`（如 `GetCUSTNSN` 系列，見上表「改寫，移到 SALFunc」）。
- 方法改成**頁面無關命名**：`GetSALCustNsnInfoAsync`（勿沿用 `sal046_` 前綴）。

### 分層：resolver 各頁獨立 → 共用抽在 service 層 → service 呼叫共用 FUNC
- **resolver 各頁獨立、不共用**：每頁保留自己的 GraphQL resolver（`sal046_GetCUSTNSN_Info` / `sal044_GetCUSTNSN_Info`；`sal045_/sal046_/sal025_GetCUR_MRATE`），**只做薄層轉發**，不含 SQL/邏輯。
- **共用抽在 service 層**：多頁重用的實作放共用 `SALService`（必要時 `SALRepository`）方法，各頁 resolver 都轉發同一份。
- **service 呼叫共用 FUNC**：service 方法內再呼叫 `Modules/FUNC`（`ERPFunc`/`SALFunc`）的共用函式（如 `ERPFunc.GetMRateAsync`）。
- 即：**各頁獨立 resolver → 模組共用 service → 共用 FUNC**（呼應記憶 `mutation_pattern`：只加薄 Resolver 層）。

  ```
  sal046_GetCUSTNSN_Info ─┐
                          ├─► SALService.GetSALCustNsnInfoAsync ─► SALRepository（共用實作，單一份 SQL）
  sal044_GetCUSTNSN_Info ─┘
  ```

### 具體實例一：CUSTNSN ↔ NSN 互查（抽「某頁查詢」到共用）
- 資料來源：`SA_PRDCNSN`（客戶品號）＋ `MM_ITMMASTR`（料號主檔），客戶品號 ↔ 料號互查。
- 供 **SAL044 / SAL046** 共用：兩頁 resolver（`sal044_GetCUSTNSN_Info` / `sal046_GetCUSTNSN_Info`）轉發同一份 `GetSALCustNsnInfoAsync`。
- 與常用表「`GetCUSTNSN` / `CUSTNSNGetNSN`」一致：此為該裁決的後端實作範式。

### 具體實例二：幣別匯率（包「已存在的 Modules/FUNC 函式」成共用，並用 arg 帶參數差異）
- 對應 business-logic.md **第 1a 類**：共用 FUNC `Get_MRATE` 已有 C# 版 `ERPFunc.GetMRateAsync`，**不留 TODO**，包一支共用 `SALService.GetSALCurMrateAsync` 呼叫它，各頁 resolver 轉發。
- **參數差異用 arg 帶入 + 預設值**（各頁需求不同時的通則）：`GetSALCurMrateAsync` 讀 `CUR`＋`MTP`(預設 A 海關)＋`IOTP`(預設 I 進口)＋`FLDT`(預設今日)。
  - SAL045：前端只帶 CUR（A/I/今日預設）。SAL046：帶 CUR+FLDT。SAL025：帶 CUR + `MTP=B`/`IOTP=O`（銀行匯率·出口）。
- 收斂效果：淘汰 SAL046 原本自查 `SS_MRATE` 的重複實作；SAL045/SAL025 原本各自 `new ERPFunc(...).GetMRateAsync` 也收斂到單一共用入口。
  ```
  sal045_GetCUR_MRATE ─┐
  sal046_GetCUR_MRATE ─┼─► SALService.GetSALCurMrateAsync ─► ERPFunc.GetMRateAsync（單一入口）
  sal025_GetCUR_MRATE ─┘        （MTP/IOTP/FLDT 由 arg 帶入給預設）
  ```
- **通則**：若各頁呼叫同一 FUNC 但參數不同，共用方法用 arg + 預設值吸收差異；各頁前端只帶「與預設不同」的參數。

---

## 指路
- **Delphi 函式名 → C# 方法名完整查找表** → `details/delphi-func-lookup.md`（ERPFunc/SALFunc/MPSFunc/StkFunc 全庫對照，含狀態/用途）
- 商業邏輯四類決策樹（含第 1 類入 log 佔位） → `details/business-logic.md`
- 後端 SQL/交易 → `details/backend-sql.md`
- 金額計算一律後端 → `details/field-change.md`
- 單號鎖定 → 記憶 `doc_lock_pattern`（ERPFunc.ChkLckFm/ProcLckFm）
