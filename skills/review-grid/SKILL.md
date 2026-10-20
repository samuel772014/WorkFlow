---
name: review-grid
description: review-engine area.grid 審查清單（grid 欄位/欄序/標題/顯示轉換/可編輯/InCell）
disable-model-invocation: true
---

# review-grid — grid 表格審查

> 規則來源：`page-migration` details（本檔只列「查什麼、怎麼對」，不另立規則）。finding 格式：`.claude/SelfFolder/review-engine/finding-schema.md`。
> 區代碼 **GRD**；finding id＝`<SAL>-GRD-<流水號>`。

## 1. 範圍

| 側 | 審查對象 |
|---|---|
| Delphi | 主檔＋繼承鏈合併後的 dfm grid（`TwwDBGrid` 等）`Selected.Strings`、`ControlType.Strings`、grid 所屬 TabSheet；`.pas` 的 `AddFieldEvent`/`*GetText`、`*DblClick`（pick）、`*NewRecord`、`AddDetail`（明細鍵、`sNotNullFields`）、各 grid 資料來源 SQL |
| C# | razor 的 `IksGrid_*` 元件參數、`GridColumnConfig` 字典、DTO 的 `_Display/_Int/_Bool`、`LeftColumnsTool` 指令鈕、grid 相關 handler（OnAdd/OnUpdate/OnDelete/Rebind/閘門）、`NavigateRow` |

## 2. 取基準（一律經 query.py，不整檔讀）

```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> compare grids   # ★先跑：依欄位重疊配對＋漏欄／多欄／欄序／標題／F 旗標 vs Editable（含子 form）
py … <SAL> list grids [--unit main|<子form>]   # Delphi grid＋欄位
py … <SAL> list razor                                  # C# grid 元件、ColConfig、DTO 清單
py … <SAL> get grid <dfm grid 名>                      # 單一 Delphi grid 屬性＋欄位（含 F/T 旗標）
py … <SAL> get colconfig <字典名>                      # 單一 C# ColConfig 逐欄
py … <SAL> list procs --grep "GetText|DblClick|NewRecord|FormCreate"
py … <SAL> get proc FormCreate                         # AddFieldEvent / AddDetail / sNotNullFields
py … <SAL> find "AddFieldEvent|AddDetail" --side delphi
py … <SAL> get method <handler> --file <SAL>.razor
py … <SAL> find "Required=true|Required = true" --side cs       # GRD-21：C# 明細必填標記
py … <SAL> list procs --grep "NewRecord"                         # GRD-21：不可編必填欄的預設值來源
```

**grid 配對（先做）**：`compare grids` 已依欄位重疊自動配對（不照 grid 名稱或順序，符合 `page-migration/details/delphi-reading.md` grid↔Dq 通則）；再以 `find "AddDetail|AddFieldEvent"` 的 DqN 複核。重疊 < 30% 或複核不一致 → open_question，不猜。
`compare` 只給差異線索：「F 旗標但 C# 唯讀」需再查 `.pas` 是否真可編（`get proc <Dq>DblClick`、`find "<欄>.ReadOnly"`），確認後才寫 finding。

## 3. 檢查清單

| 編號 | 檢查 | Delphi 依據 | C# 依據 | type／預設 severity | 規則 |
|---|---|---|---|---|---|
| GRD-01 | 每個 Delphi grid 都有對應 C# grid；C# 無多出的 grid | dfm grid、`AddDetail` | `IksGrid_*` | missing/extra｜medium | delphi-reading Step 2.1 |
| GRD-02 | 欄位集合一致（漏欄／多欄）。顯示欄＝dfm `Selected.Strings` ∩ 未 `Visible=False`；SQL 有取但 dfm 無者不顯示 | `Selected.Strings`、SQL select | ColConfig key/Field | missing/extra｜medium | final-dfm-check ③ |
| GRD-03 | 欄序一致 | `Selected.Strings` 順序 | ColConfig 順序／`Order` | mismatch｜low | dto-display 3 |
| GRD-04 | 標題逐字一致（不簡化、不改字） | `Selected.Strings` 第 3 段 | `Title` | mismatch｜low | final-dfm-check ③ |
| GRD-05 | 代碼→名稱：`AddFieldEvent`/`GetText` 用 `GetNoDESCPT`/`GetKeyCodeDESCPT` 的欄，C# 以 `_Display` 顯示；有連動依賴者用 `DisplayTransformApi` | `*GetText`、`AddFieldEvent` | DTO `_Display` 屬性、ColConfig Field | missing/mismatch｜medium | dto-display 2 |
| GRD-06 | 可編輯性：旗標 `F` 或 `.pas` 有 pick/InCell → 可編；否則 `Editable=false`（注意 `T` 不等於唯讀） | 旗標 F/T、`*DblClick` | ColConfig `Editable`、EditorTemplate | mismatch｜medium | final-dfm-check ④ |
| GRD-07 | 明細編輯閘門：`OnAfterRenderAsync` 每次渲染依 `_dqEditEnabled` 呼叫 `EnterEdit()/ExitEdit()`；無整表鎖欄樣板、無 `OnBeforeEdit` | — | razor | rule-violation｜medium | grid-incell 通則1 |
| GRD-08 | `SetColumnEditable` 只用於依業務條件切單欄；`Rebind` 後與條件變動時重套；傳 `true`＝鎖 | Delphi 該條件判斷 | 呼叫處 | rule-violation／mismatch｜medium | grid-incell 通則1 |
| GRD-09 | grid 內 pick：`EditPick_Button` 頁面層級 `@ref`；回寫用 `Apply`＋鍵值撈 GD 實際列＋`StateHasChanged`；markup 綁每次換新參考的 `FixedPost`；不 inline `EditPick` | `*DblClick` pick | EditPick_Button 宣告與 handler | rule-violation｜medium | editor-template |
| GRD-10 | bool 欄：`X_Bool` 且 ColConfig key＝Field；變更走 `OnUpdate`；不傳 `OnCheckBoxChange` | ControlType CheckBox | DTO、ColConfig、grid 參數 | rule-violation｜low | shared-input-components bool、grid-incell 7 |
| GRD-11 | `_Int` 一律 get/set 包裝 base；不用 `[JsonProperty]`＋Converter | numeric(n,0) 欄 | DTO | rule-violation｜low | dto-display 3b |
| GRD-12 | 金額 `#,##0.######`、日期 `DisplayFormat="{0:yyyy/MM/dd}"` | dfm DisplayFormat | ColConfig/控件 Format | rule-violation｜low | grid-virtual 其他眉角 |
| GRD-13 | InCell 新增：`OnAdd` 設 `uState=Insert`＋明細鍵＋項次；拷貝用 `AddNewRow()`；刪除直接呼叫 API；Save 送全部 Insert 再全部 Update | `*NewRecord`、`AddDetail` 鍵 | handler | missing/mismatch｜high（寫錯資料）/medium | grid-incell 3–6 |
| GRD-14 | 明細刪除鈕非編輯態才可按（`_dqDeleteEnabled`） | — | GridCommandButton Delete Enabled | rule-violation｜medium | grid-incell 5 |
| GRD-15 | 列指令鈕純圖示＋`Title`；順序 拷貝→修改→刪除→詳細（Delphi 有拷貝才放） | Delphi 是否有拷貝 | LeftColumnsTool | rule-violation｜low | toolbar、grid-incell 2 |
| GRD-16 | 列切換：主檔 `IksGrid_Virtual` 用 `RowKeyField`＋`OnRowFocus`（focus＝選取→載明細）；vnq 明細切子明細用 `OnRowClick` | `*AfterScroll` | grid 參數、handler | mismatch｜medium | grid-virtual、grid-incell 8 |
| GRD-17 | frame-header：`ShowFrameHeader="true"` 且 `ShowBuiltInToolbar="false"` | — | grid 參數 | rule-violation｜low | grid-virtual |
| GRD-18 | Rebind：master 無參數 `Rebind()`；明細 `Rebind(list)` 每格單次；換 pageStatus 後明細顯式 Rebind | — | handler | rule-violation｜low | grid-virtual 生命週期 |
| GRD-19 | 上/下一筆：編輯/檢視 Window 內 `NavigateRow`，Edit 與 View 皆可；master-detail 換筆後重載明細 | RzDBNav | 導覽鈕與 handler | missing/mismatch｜low | row-navigate |
| GRD-20 | 唯讀合計（Delphi 唯讀 ButtonEdit 加總）：主檔→`FrameHeaderExtra`、明細→`.iks-total-bar`；值由後端算 | 唯讀 ButtonEdit | 合計顯示位置與來源 | missing/mismatch｜low | grid-virtual 合計、css-layout |
| GRD-21 | **明細必填**：逐個 `AddDetail(DqN,鍵,sNotNullFields,…)` 取第 3 參數（分號分隔），扣掉系統鍵（主檔鍵、項次鍵＝`AddDetail` 第 2 參數）後逐欄判：① **可編輯欄**（GRD-06 判定）→ ColConfig `Required=true`（標題紅字）**且**存檔前（`Save*` 送後端前）對 Insert/Update 列驗空並 `MsgBox` 指出「明細名＋項次＋欄名」，兩者缺一即報；② **不可編輯欄** → 不得標 `Required`／不得前端驗（使用者無從輸入），改查值來源：`*NewRecord` 預設（如 `OFFDT:=cNow` → C# `OnAdd` 須帶）或後端計算，皆無即報（insert 會寫 NULL）；③ 依條件擇一可輸的欄（如 CTAXTP 決定 ARMNY/ARTMNY 哪欄可編、另一欄後端互算）→ 只驗當下可輸那欄，兩欄都驗會擋正常存檔，算錯報。例：SAL078 Dq1 `QTY;APQTY;NSN`、Dq2 `SITM;ARTERM;ARMNY;ARTMNY;PDT`、Dq3 `SRCNO;MNY;TAX;TMNY;OFFDT` | `FormCreate` `AddDetail` 第 3 參數、`*NewRecord` | ColConfig `Required`、存檔驗證方法、`OnAdd` | missing/mismatch｜medium（不可編必填欄無值來源→high） | edit-window 3、final-dfm-check ④ |

> 欄寬：Delphi 寬度單位為字元、C# 為 px，**不比對**。

## 4. 邊界（不歸本區，交給該區）

| 情況 | 交給 |
|---|---|
| 儲存格改值後的連動、計算、驗證訊息 | field-change |
| 存檔寫入哪些欄、交易、SQL 欄位 | backend |
| 篩選 Popup 的欄位 | filter |
| 單筆編輯 Window／表單欄位 | editform |
| 工具列按鈕（非 grid 列指令） | button |
| grid 版型高度、捲動模式、CSS class | style |
| 跨區通用慣例（命名、DTO 宣告位置、IksTextBox…） | conventions |
| 子 form（SAL###A…）的 grid（`compare grids` 的 [子form] 段） | subwindow |

## 5. 輸出

- 每項問題一條 finding，`check` 填 GRD-xx，`rule_ref` 填上表規則檔路徑（`.claude/skills/page-migration/details/…`）。
- quote：從 `query.py` 輸出**逐字複製**最短可辨識片段（dfm 欄位列可整行，如 `'DONO'#9'15'#9#20986…`）。
- 同一 grid 多欄同類問題（如 5 欄標題不同）→ 合成一條，claim 列出全部欄位，證據取其中一欄。
- 查不到 Delphi 意圖 → `open_questions`（`area: grid`），不推測成 finding。
- 寫入：`review_state.py upsert <SAL> findings @<檔>`，完成後 `review_state.py area <SAL> grid done <數量>`。

## 6. 工具警示必須結案（2026-10-08，防誤判）
- 本區一律先跑 `py .claude/SelfFolder/review-engine/tools/query.py <SAL> compare <grids|filter|editform> --save`，每個警示寫成 `state.signals`。
- **每個 signal 必須結案**，二擇一：
  - 立成 finding：`review_state.py resolve <SAL> <signal-id> finding=<finding-id>`
  - 豁免：`review_state.py resolve <SAL> <signal-id> "waive=<理由>@@<規範出處>"`，理由與規範出處（檔名＋章節／行號）**都必填**。
- **每個豁免都要有規範條文支持**；找不到條文就立 finding，交 triage／human-review 判斷（「顯示差異」「應為刻意設計」「影響不大」不算依據）。
- 未結案的 signal 會讓 evidence-check 閘門把本區退回重跑。
