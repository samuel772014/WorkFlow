---
name: review-conventions
description: review-engine area.conventions 審查清單（跨區通用開發慣例）
disable-model-invocation: true
---

# review-conventions — 統一規則審查

> 規則來源：`CLAUDE.md` 鐵則與「通用慣例」、`page-migration/details/naming.md`、`dto-display.md`、`page-shell.md`、`shared-input-components.md`、`grid-incell.md`、`crud-handlers.md`、`backend-sql.md`。區代碼 **CNV**。
> **只審跨區通用的寫法**；某區專屬規範由該區審，不在此重報。
> CNV-03／05／07／08／10／13 已由 GATE1 `verify_static.py` C7–C12 機器檢查；本區對這幾項只覆核 GATE1 漏網與豁免理由。

## 1. 範圍
本頁 razor 與後端檔全部（規範面）。Delphi 幾乎不需讀。

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> list razor ; py … <SAL> list rows
py … <SAL> find "<TelerikTextBox[^>]*/>|string _url\s*=\s*\"|\"00001\"|status\s*(==\s*0|>\s*0)|OnBeforeEdit|LockDq|JsonConverter|class \w+Dto" --side cs
py … <SAL> list methods --grep "OnAfterRenderAsync|OnInitializedAsync"
```
comboBoxCode 是否登記、module 是否正確：對照 `IKSERPPRJ/IKSERPAPI/Modules/COMMON/ComboBoxService*.cs`（`_handlersCOMMON` vs 模組字典）。

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| CNV-01 | 分層（鐵則1）：業務邏輯在 API 層，UI 只放便利性邏輯 | rule-violation｜high |
| CNV-02 | DTO 宣告在本頁 `@code`、`partial class : EFModel, IDisplayResolvable`，只加 `_Int/_Bool/_Display/uState`；不建獨立 Dto.cs、不跨頁共用 | rule-violation｜low |
| CNV-03 | 自閉合文字輸入用 `IksTextBox`（帶 SuffixTemplate 者例外） | rule-violation｜low |
| CNV-04 | `comboBoxCode` 為 ComboBoxService 已登記 key，`module` 與登記字典一致（錯則下拉靜默無資料） | rule-violation｜high |
| CNV-05 | 身分：登入者用 `EmplyId`（OnInitializedAsync await base 之後），不寫死 `"00001"`、不在欄位初始化式引用 | rule-violation｜medium |
| CNV-14 | **登入者帶入要在動作當下取**（Delphi `gs_empno`／`gs_deptno`）：①`Add()` 新增預設（`*NewRecord` 的 `FEMPLYID/SALEREP/DEPID` 等）、存檔 payload、確認/作廢/取消確認送後端的 `EMPLYID`/`USERID`，須 `await iksService.GetEmplyIdAsync()` 當下取，用快取的 `EmplyId` 即報（先開頁後登入時恆空）；②由員工反查的值（部門 HR_EMPLYM.DEPID）須隨代號變動重查；③用到 `EmplyId` 的初值 API 放在 `OnAfterRenderAsync(firstRender)` 即報（早於 base 完成會送空值），應放 `OnInitializedAsync` 的 `await base` 之後（會 `await MsgBox` 的部分才留 firstRender）。查法：`find "EmplyId" --side cs` 逐一看是否進 `Add()`/送出 payload；`list methods --grep "OnAfterRenderAsync"` 看 firstRender 內呼叫的 API 是否帶 EmplyId。依據 `page-migration/details/page-shell.md`「登入者帶入」（2026-10-20，起因 SAL081） | rule-violation｜medium |
| CNV-06 | 生命週期：`OnAfterRenderAsync`、`OnInitializedAsync` 覆寫皆先 `await base` | rule-violation｜high |
| CNV-07 | status 判斷：成功一律 `status == 1`；`2` 需確認、`3` 部分成功另行處理；禁用 `== 0` 判失敗、`> 0` 判成功 | rule-violation｜medium |
| CNV-08 | `_url` 用 IksPageBase 提供值，不寫死 gqlway | rule-violation｜low |
| CNV-09 | 命名：gqlway `{form}_{動作}`；Repository `Query*`、Service `Get*`；IksLabel Key `Lb_/Lb_F_/Lb_E_` | rule-violation｜low |
| CNV-10 | 已淘汰寫法不再出現：`OnBeforeEdit`、整表鎖欄樣板、`OnCheckBoxChange`、`HighlightEditableCells`、`[JsonProperty]`＋Converter 的 `_Int` | rule-violation｜low |
| CNV-11 | 特殊字元參數用 `GraphQlArg.Encode`/`DecodeArg`（含 `"` `'` 換行的自由文字） | rule-violation｜medium |
| CNV-12 | 註解：保留功能性注解代碼與 Razor 中文說明；改程式時刪舊碼不留註解版本 | rule-violation｜info |
| CNV-13 | **遮罩內不得 await 訊息框**：`SetPageLoading()` 之後、`SetPageLoaded()` 之前（含 `try` 區塊內）出現 `await MsgBox.Show/Confirm`（或其他需使用者操作的對話框）→ 遮罩蓋住對話框、await 不返回、`finally` 不執行，畫面卡死。也檢查 `SetPageLoading()` 後沒有 `try/finally { SetPageLoaded(); }` 保護、`return` 前未解遮罩的路徑。查法：先跑 `py .claude/SelfFolder/review-engine/tools/lint_loading.py <該頁及子視窗 razor>`（機器掃描，`msgbox-under-loading`／`loading-not-released` 每筆都要轉 finding 或附理由豁免），再人工確認 `return` 路徑。依據 `page-migration/details/page-shell.md` IksPageBase 成員表（2026-10-13，起因 SAL078 新增存檔失敗卡死） | rule-violation｜high |

## 4. 邊界
各區專屬規範（grid 閘門、篩選 Popup 結構、版型 class…）由該區審；本區只收跨區共通項。

## 5. 輸出
同 `review-grid` §5（區代碼 CNV）；同一規則多處違反合成一條，claim 列出全部位置（行號），證據取第一處。
