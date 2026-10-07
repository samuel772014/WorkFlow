# 詳細規則：Delphi 共用函式庫 ↔ C# 完整對照表

> 來源：`共用函式列表.xlsx`（整理日：2026-08-13）
> 用途：轉譯時快速查詢 Delphi 封裝函式對應的 **C# 方法名稱 + 所在 .cs 檔**。
> 處理策略與佔位規則見 `details/shared-functions.md`。

---

## 函式庫總覽

| Delphi 函式庫 | C# 檔案 | 備註 |
|---|---|---|
| `ERPFunc`（Erpfunc） | `ERPFunc.cs` | 跨模組共用（金額/匯率/鎖定/價格等） |
| `SALFunc`（Salfunc） | `SALFunc.cs` | 銷售模組共用 |
| `MPSFunc`（Mpsfunc） | `MPSFunc.cs` | MRP 共用（BOM展開/供需計算） |
| `MPSFunc1`（Mpsfunc1） | `MPSFunc1.cs` | MRP 製令展開（T08-T53） |
| `MPSFunc2`（MpsFunc2） | `MPSFunc2.cs` | MRP 工單/用料/在製區 |
| `MPSFunc3`（Mpsfunc3） | `MPSFunc3.cs` | MRP 前置天數/產能預劃 |
| `MPSFuncP`（MpsfuncP） | `MPSFuncP.cs` | MRP 專案模式 |
| `MPS_Gfunc`（Mps_gfunc） | `MPS_Gfunc.cs` | MRP 通用工具（日期/工時/批量） |
| `StkFunc`（Stkfunc） | **`STFunc.cs`** ⚠️ 名稱不同 | 庫存共用（入出庫/儲區/批號） |
| `BseFunc` / `BuyFunc` / `CstFunc` / `Bsalem_uncf` | — | 全部作廢或併入個別程式 |

### 狀態圖示
| 圖示 | 說明 |
|---|---|
| ✅ | 已完成，C# 方法已存在 |
| 🚧 | 待轉，C# 方法名已規劃但尚未實作 |
| 🔄 | 改寫/重新設計，有對應但邏輯重新設計 |
| ➡️ | 併入其他函式或個別程式 |
| ❌ | 作廢，C# 不需要 |

---

## ERPFunc → `ERPFunc.cs`

| Delphi 函式名 | C# 方法名 | 狀態 | 用途 |
|---|---|---|---|
| `ProcLCKFM` | `ProcLckFm` | ✅ | 檢查/鎖定/解鎖單據（A=查/B=鎖/C=解） |
| `ChkLCKFM` / `SetLCKFM` | → `ProcLckFm` | ➡️ 合併 | 舊版鎖定函式，改用 ProcLckFm |
| `SALGetUp` | `SALGetUpAsync` | ✅ | 取銷售價格（依價格表/幣別/機種/日期） |
| `SALGetCRMNY` | `SALGetCRMNYAsync` | ✅ | 取運費保費 |
| `Calcu_MNYTAX` | `CalcuMnyTaxAsync` | ✅ | 計算金額/稅額（含MRATE版） |
| `Calcu_MNYTAX1` / `Calcu_MNYTAX2` / `Calcu_TAX` | → `CalcuMnyTaxAsync` | ➡️ 合併 | 舊版，併入 CalcuMnyTaxAsync |
| `Get_MRATE` | `GetMRateAsync` | ✅ | 取匯率 |
| `GetPKVOL` | `GetPKVolAsync` | ✅ | 計算包裝體積 |
| `SALGetYRQTY` | `SALGetYRQTYAsync` | 🚧 | 依價格表取年度購量/基本購量 |
| `update_ORDERD_CFOPQTY` | `UpdateOrderdCfopqtyAsync` | 🚧 | 更新出貨通知對應數量 |
| `update_LCKQTY` | `UpdateLCKQTYAsync` | 🚧 | 處理待出貨量/拋出貨待出貨量移轉 |
| `GetFactidOffDay` | `GetFactidOffDayAsync` | 🚧 | 依廠曆計算工作日 |
| `CheckUnitExists` | `CheckUnitExistsAsync` | 🚧 | 檢查單位是否存在料品主檔 |
| `GetCURID` | `GetCURIDAsync` | 🚧 | 取得本國幣別 |
| `CalcNTMNY` | `CalcNTMNYAsync` | 🚧 | 依傳入金額取本幣位數小數位 |
| `GetNTDot` | `GetNTDotAsync` | 🚧 | 取本國幣小數位數 |
| `Get_PAYTERM` | `GetPayTermAsync` | 🚧 | 依付款條件計算預計付款日及票期 |
| `Cal_PLNCSDT` | `CalPlncsdtAsync` | 🚧 | 計算應收票據的預計兌現日 |
| `Calc_MasterMNY` | `CalcMasterMnyAsync` | 🚧 | 彙算進銷貨單總金額並調整明細 |
| `GetAPUNIT` | `GetAPUnitAsync` | 🚧 | 取料品計價單位/換算率 |
| `GetNUp` | `GetNUpAsync` | 🚧 | 取採購商情單價 |
| `GetVUp` | `GetVUpAsync` | 🚧 | 取託工商情單價 |
| `GetTaxRate` | `GetTaxRateAsync` | 🚧 | 取稅率 |
| `GetPOREMARK` | `GetPOREMARK` | 🚧 | 備料基數換算處理 |
| `update_SA_ARPLN_OPMNY` | `UpdateSaArplnOpmnyAsync` | 🚧 | 更新應收帳款期款金額 |
| `CheckCredit` | `CheckCreditAsync` | 🚧 | 檢查客戶信用額度 |
| `updateCredit` | `UpdateCreditAsync` | 🚧 | 異動客戶信用額度 |
| `GetCUSTNSN` | `GetCustNsnAsync` | 🚧 | 依客戶編號+料號取客戶品號 |
| `CUSTNSNGetNSN` | `CustNsnGetNsnAsync` | 🚧 | 依客戶編號+客戶品號取料號 |
| `Ctrl_FI_DataCtrl` | `CtrlFiDataCtrlAsync` | 🚧 TBD | 配合 EIP 資料權限 |
| `SAL_DataCtrl` / `BUY_DataCtrl` / `MPS_DataCtrl` | → `CtrlFiDataCtrlAsync` | ➡️ 合併 | 各模組舊版資料權限函式，統一改用 CtrlFiDataCtrlAsync |
| `GetDays` | `GetDays` | 🚧 | — |
| `CheckOffDay` | `CheckOffDayAsync` | 🚧 | — |
| `GetCURNM` | `GetCURNMAsync` | 🚧 | — |
| `GetPOSTDT` | `GetPostDt` | 🚧 | — |
| `GetLastWORKDT` | `GetLastWorkDtAsync` | 🚧 | — |
| `VarToCurrency` / `DigitTransfer` 等 | — | 🔄 改C#本身功能 | 使用 C# 內建型別轉換/小數控制 |
| `update_TOORD` | — | ➡️ 併入個別程式 | 標記報價單轉訂單（B40101/B40103/B402Base） |
| `update_TOPJ` | — | ➡️ 併入個別程式 | 標記報價單轉草約 |
| `Calcu_PLNMNY` / `Calcu_PLNTAX` 等 | — | ❌ 作廢 | — |

---

## SALFunc → `SALFunc.cs`

| Delphi 函式名 | C# 方法名 | 狀態 | 用途 |
|---|---|---|---|
| `Calc_CRINSUMNY` | `CalcCrInSumMnyAsync` | 🚧 | 計算運費保費 |
| `update_BKDQTY` | `UpdateBkdQtyAsync` | ✅ | 更新銷退單待確認及確認轉訂單量 |
| `update_ORDQTY` | `UpdateOrdQtyAsync` | 🚧 | 更新訂單待出貨及出貨量 |
| `update_DODQTY` | `UpdateDodQtyAsync` | 🚧 | 更新出貨單待銷貨及銷貨量 |
| `update_SALDQTY` | `UpdateSaldQtyAsync` | 🚧 | 更新銷貨單待確認及已確認銷退量 |
| `CS_Proc` | `CsProcAsync` | 🔄 改寫 | 寄售銷貨帳務處理 |
| `Check_CARRIERTP` | `Check_CARRIERTPAsync` | 🔄 改寫 | 檢查電子發票載具類別條碼 |
| `Calc_SA_INVM` | `CalcSA_INVMAsync` | 🔄 改寫 | 彙算銷項發票金額 |
| `ProCheck` | `ProCheck`（→ iksUiFunc.cs） | 🚧 | 檢查固定結帳日設定規則 |
| `CheckNumber` | `CheckNumber`（→ iksUiFunc.cs） | 🚧 | 檢查固定結帳日必須為數字 |
| `Get_Round` / `Get_Round1` / `Get_Round2` | — | 🔄 改C#本身功能 | 四捨五入/無條件捨去/進位 |
| `English` / `Englishnew` 等 | — | ➡️ 併入Func | 數字轉英文 |
| `OBJ_SALNO` / ARPLN 等 SAL 特定邏輯 | — | ➡️ 併入個別程式 | 各頁自處理 |

---

## MPSFunc → `MPSFunc.cs`

| Delphi 函式名 | C# 方法名 | 狀態 | 用途 |
|---|---|---|---|
| `GetPSDUSTK` | `GetPsDuStkAsync` | 🚧 | MRP 展開 BOM 虛階庫存判斷 |
| `Update_PP_MPS_From_PP_MSPLOG` | `UpdatePpMpsFromPpMpslogAsync` | 🚧 | 更新PP_MPS及計算預計存量 |
| `CalRECQTYN` | `CalRECQTYNAsync` | 🚧 | 計算備料明細建議量 |
| `GetLeadTime` | `GetLeadTimeAsync` | 🚧 | 計算前置天數 |
| `INS_MPSLOG` | `InsMpsLogAsync` | 🚧 | 供需異動資料寫入PP_MPSLOG |
| `ExpMRP` | `ExpMrpAsync` | 🚧 | MRP 展開 |
| `Exp_SIMULBOM` | `ExpSimulBomAsync` | 🚧 | — |
| `Exp_BOM` | `ExpBomAsync` | 🚧 | — |
| `Exp_BOMD` | `ExpBomDAsync` | 🚧 | — |
| `Exp_MBOM_T05` | `ExpMBomT05Async` | 🚧 | — |
| `Exp_PLNDDMRP` | `ExpPlnddMrpAsync` | 🚧 | — |
| `Exp_MBOM_T07` | `ExpMBomT07Async` | 🚧 | — |
| `Exp_MINFDDMRP` | `ExpMinfddMrpAsync` | 🚧 | — |
| `Exp_ORDERDD` | `ExpOrderDdAsync` | 🚧 | — |
| `T01`~`T07` | `T01Async`~`T07Async` | 🚧 | MRP 計算步驟 T01-T07 |
| `Charge_T05` | `ChargeT05Async` | 🚧 | — |
| `Charge_T07` | `ChargeT07Async` | 🚧 | — |
| `SwitchMRP` | `SwitchMrpAsync` | 🚧 | — |

---

## MPSFunc1 → `MPSFunc1.cs`

| Delphi 函式名 | C# 方法名 | 狀態 |
|---|---|---|
| `Exp_MOBOM` | `ExpMoBomAsync` | 🚧 |
| `T08`~`T16` | `T08Async`~`T16Async` | 🚧 |
| `T20`~`T32_06` | `T20Async`~`T32_06Async` | 🚧 |
| `T33`~`T38` | `T33Async`~`T38Async` | 🚧 |
| `T40`~`T53` | `T40Async`~`T53Async` | 🚧 |

> 命名規則：`T{NN}Async` 對應 Delphi `T{NN}`，全部為 MRP 計算步驟。

---

## MPSFunc2 → `MPSFunc2.cs`

| Delphi 函式名 | C# 方法名 | 狀態 | 用途 |
|---|---|---|---|
| `AppendPP_MOD3D` | `AppendPP_MOD3DAsync` | 🚧 | 依PP_MOD3新增PP_MOD3D |
| `AppendPP_MOD2` | `AppendPP_MOD2Async` | 🚧 | 新增/更新(託)工單用料 |
| `BKFINV` | `BkfInvAsync` | 🚧 | 倒扣料處理 |
| `UnPPWMWM` | `UnPPWMWMAsync` | 🚧 | 取消領料出庫 |
| `UnPPWMRM` | `UnPPWMRMAsync` | 🚧 | 取消生產入庫 |
| `UnPPVMRM` | `UnPPVMRMAsync` | 🚧 | 取消託工不良入庫 |
| `UnPPACPTM` | `UnPPACPTMAsync` | 🚧 | 取消託工驗收入庫 |
| `WIPM_Proc` | `WipMProcAsync` | 🚧 | 在製區材料處理程序（多筆） |
| `WIPS_Proc` | `WipsProcAsync` | 🚧 | 在製區材料處理程序（單筆） |
| `UpdateUSEDQTY` | `UpdateUSEDQTYAsync` | 🚧 | 計算更新製令/工單/託工單生產耗用量 |
| `CheckISSQTY` | `CheckIssQtyAsync` | 🚧 | — |
| `REALOCQTY` | `ReAlocQtyAsync` | 🚧 | — |
| `WOINSTK` | `WoInStkAsync` | 🚧 | — |
| `VOINSTK` | `VoInStkAsync` | 🚧 | — |
| `ConfirmAction_MO` | `ConfirmActionMOAsync` | 🚧 | — |
| `CancelAction_MO` | `CancelActionMOAsync` | 🚧 | — |

---

## MPSFunc3 → `MPSFunc3.cs`

| Delphi 函式名 | C# 方法名 | 狀態 | 用途 |
|---|---|---|---|
| `GET_LEADTM` | `GetLeadTmAsync` | 🚧 | 依需求量調整前置天數 |
| `GET_LEADTM_PRDTM` | `GetLeadTmPrdTmAsync` | 🚧 | 調整前置天數及計算需求日 |
| `CRP_CHK` | `CrpChkAsync` | 🚧 | 產能預劃-查 |
| `CRP_PREP` | `CrpPrepAsync` | 🚧 | 產能預劃-備 |
| `CRP_PROC` | `CrpProcAsync` | 🚧 | 產能預劃-執行 |
| `CRP_POST` | `CrpPostAsync` | 🚧 | 產能預劃-過帳 |

---

## MPSFuncP → `MPSFuncP.cs`

| Delphi 函式名 | C# 方法名 | 狀態 |
|---|---|---|
| `Exp_MBOM_PRJ` | `ExpMBomPrjAsync` | 🚧 |
| `Exp_PRJDD2MRP` | `ExpPrjdd2MrpAsync` | 🚧 |
| `Charge_T07PJ` | `ChargeT07PjAsync` | 🚧 |
| `T12PJ`~`T14PJ` | `T12PjAsync`~`T14PjAsync` | 🚧 |
| `T31PJ` | `T31PjAsync`（改傳入FMNO） | 🚧 |
| `T32PJ` | `T32PjAsync`（改傳入FMNO） | 🚧 |

---

## MPS_Gfunc → `MPS_Gfunc.cs`

| Delphi 函式名 | C# 方法名 | 狀態 | 用途 |
|---|---|---|---|
| `LastDay` / `FirstDay` / `YMtoSDate` 等 | — | 🔄 重新設計 | 日期工具（傳回月首/月末/格式轉換） |
| `MinDATE` / `MaxDATE` / `SumQty` / `GetYM` 等 | — | 🔄 重新設計 | 資料集聚合工具 |
| `GetNSNLTM` | `GetNSNLTMAsync` | 🚧 | — |
| `CalWorkTimeN` | `CalWorkTimeNAsync` | 🚧 | 計算正班及加班工時 |
| `MarthWorkTime` | `MarthWorkTime` | 🚧 | — |
| `Calc_VWOM_MNY`（直接更新DB版） | `Calc_VWOM_MNYAsync` | 🚧 | 計算託工金額（直接更新資料表） |
| `GetPIDT` | `GetPIDTAsync` | 🚧 | 推算開工日 |
| `GetNDDT` | `GetNDDTAsync` | 🚧 | 推算完工日 |
| `GetPQTY` | `GetPQTYAsync` | 🚧 | 取批量或撥料基數 |
| `GetMOPRI` | `GetMOPRIAsync` | 🚧 | 賦予製令優先度 |

---

## StkFunc → `STFunc.cs` ⚠️ Delphi 名稱 Stkfunc，C# 檔名 STFunc.cs

| Delphi 函式名 | C# 方法名 | 狀態 | 用途 |
|---|---|---|---|
| `IncYM` | `IncYM` | 🚧 | 增加或減少的年月 |
| `DiffMM` | `DiffMM` | 🚧 | 取得差異月數 |
| `ChkNSTKYM` | `ChkNSTKYMAsync` | 🔄 改寫 | 檢查重開帳年月 |
| `ChkStkMn` | `ChkStkMnAsync` | 🔄 改寫 | 檢查儲區年月 |
| `ChkAll` | `ChkAllAsync` | 🔄 改寫 | 綜合庫存有效性檢查 |
| `GetDefaultSTKNO` | `GetDefaultSTKNOAsync` | 🔄 改寫 | 取預設儲區 |
| `GetNVNDERID` | `GetNVNDERIDAsync` | 🔄 改寫 | 取母件第一個委外工序廠商 |
| `GetMaxRECITM` | `GetMaxRECITMAsync` | 🔄 改寫 | — |
| `GetSLOC` | `GetSLOCAsync` | 🔄 改寫 | 取預設儲位 |
| `InsertMM_STK` | `InsertMM_STKAsync` | 🚧 | 更新儲區存量及新增庫存交易紀錄 |
| `UpdateMM_ITMSTK` | `UpdateMM_ITMSTKAsync` | 🚧 | 更新儲位批號存量及新增交易紀錄 |
| `FIFO_Proc` | `FIFOProcAsync` | 🔄 改寫 | 先進先出沖銷處理 |
| `SM_ProcN` | `SmProcNAsync` | 🚧 | 整單處理寄外存貨帳務 |
| `GetDefInACNTID` | `GetDefInACNTIDAsync` | 🔄 改寫 | 取其他入庫料品預設會計科目 |
| `GetDefOutACNTID` | `GetDefOutACNTIDAsync` | 🔄 改寫 | 取其他出庫料品預設會計科目 |
| `GetDefautFACTID` | `GetDefautFACTIDAsync` | 🔄 改寫 | 取登入者預設廠別 |
| `GetSTK_FACTID` | `GetSTKFACTIDAsync` | 🔄 改寫 | 取儲區所屬廠別 |
| `GetTFMNO_Field` | `GetTFMNOFieldAsync` | 🔄 改寫 | 取儲區交易紀錄的來源單欄位 |
| `GetTFMNO_STNM` | `GetTFMNOSTNMAsync` | 🔄 改寫 | 取儲區交易紀錄的廠商/客戶/部門名稱 |
| `ITMLOTQTY` | — | ➡️ 各程式直接處理 | 批號明細量彙總至明細 |
| `R01_Chk`~`R20_Chk` | `R01_ChkAsync`~`R20_ChkAsync` | 🚧 | 入庫類型 R01-R20 事前檢查 |
| `R01_In`~`R20_In` | `R01_InAsync`~`R20_InAsync` | 🚧 | 入庫類型 R01-R20 執行 |
| `R12_Chk` / `R12_In` | — | ❌ 作廢 | 成本調整（M203直接依RECTP處理） |
| `W01_Chk`~`W11_Chk` | `W01_ChkAsync`~`W11_ChkAsync` | 🚧 | 出庫類型 W01-W11 事前檢查 |
| `W01_Out`~`W11_Out` | `W01_OutAsync`~`W11_OutAsync` | 🚧 | 出庫類型 W01-W11 執行 |
| `W12_Chk` / `W12_Out` | — | ❌ 作廢 | 成本調整（同R12） |
| `W13_Chk`~`W20_Chk` | `W13_ChkAsync`~`W20_ChkAsync` | 🚧 | 出庫類型 W13-W20 事前檢查 |
| `W13_Out`~`W20_Out` | `W13_OutAsync`~`W20_OutAsync` | 🚧 | 出庫類型 W13-W20 執行 |
| `R0C_In` | `R0C_InAsync` | 🚧 | 成本調整入庫 |
| `W0C_Out` | `W0C_OutAsync` | 🚧 | 成本調整出庫 |
| `T03_Confirm` | `T03_ConfirmAsync` | 🚧 | — |
| `T04_CloseChk` | `T04_CloseChkAsync` | 🚧 | — |
| `T04_Close` | `T04_CloseAsync` | 🚧 | — |

---

## 不轉為共用函式庫（全部或大部分併入個別程式）

| Delphi 函式庫 | 處理方式 |
|---|---|
| `BseFunc` | 全部作廢或併入個別程式（C# 不另建共用函式） |
| `BuyFunc` | 全部作廢或併入個別程式 |
| `CstFunc` | 全部併入個別程式或在個別模組改寫 |
| `CstFunc1` | 改寫後功能併入 CstFunc 相關模組 |
| `Bsalem_uncf` | 全部併入個別程式（B702Base） |

---

## 指路
- 處理策略與佔位規則（何時入 log / 留 TODO / 作廢） → `details/shared-functions.md`
- 後端 SQL/交易規則 → `details/backend-sql.md`
- 商業邏輯四類決策樹 → `details/business-logic.md`
