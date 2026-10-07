# 最後檢查：DFM × razor 三方比對（交付前必做）

> 頁面轉譯「完成後」的驗收檢查，把已寫好的 razor 逐項對回 Delphi `.dfm` / `.pas` 權威。
> 目的：抓出「預設文字錯、欄位順序錯、頁籤名稱/順序錯、顯示狀態(_Display)漏做、必填欄漏驗/漏寫」這類轉譯後才看得出來的偏差。
> 四個檢查缺一不可：**① 篩選區、② 明細切頁、③ 主/明細欄位 × 顯示狀態、④ 明細必填欄位(AddDetail) × 轉譯是否正確寫入**。

---

## 工具

- **grid 欄位**：`tools/dfm_decode.py`（解 wwDBGrid `Selected.Strings` → FIELD/欄序/寬/中文標題）。
- **篩選標籤 / 控件 / 頁籤 / 內嵌日期框**：`tools/dfm_audit.py`（indent-aware，支援 `object` 與 `inline` frame；印出 TLabel、篩選控件、TabSheet、日期/年月 frame，皆含 `top/left` 座標，可還原版面順序）。

```
PYTHONIOENCODING=utf-8 py .claude/skills/page-migration/tools/dfm_audit.py  <來源.dfm>
PYTHONIOENCODING=utf-8 py .claude/skills/page-migration/tools/dfm_decode.py <來源.dfm>
```

> ⚠ **繼承鏈**：子類 `.dfm`（如 `B432`/`B434`）常只覆寫 grid 欄位，**篩選與頁籤繼承自 base**（如 `B430Base`/`B404Base`）。篩選/頁籤一律對 **base 的 `.dfm`**；grid 欄位對「子類覆寫者 + base 未覆寫者」。先確認要對哪一支。
> ⚠ `dfm_audit.py` 只列 TLabel 的 `Caption`；**標籤↔控件的綁定以 TLabel 的 `FocusControl` 為權威**（位置推測會被中間的日期 frame 帶偏）。用下方 FocusControl 片段取得綁定。

### 取 TLabel↔控件綁定（FocusControl，權威）
```
PYTHONIOENCODING=utf-8 py - <<'PY'
import re
lines=open(r"<來源.dfm>",encoding='latin-1').readlines()
def dec(s):
    o=[]
    for q,n in re.findall(r"'([^']*)'|#(\d+)",s):
        o.append(chr(int(n)) if n else q.encode('latin-1').decode('cp950','replace'))
    return ''.join(o)
cur=cap=fc=None
for ln in lines:
    m=re.match(r'\s*object (\w+): TLabel',ln)
    if m: cur=m.group(1);cap=fc=None;continue
    if cur:
        mm=re.match(r'\s*Caption = (.+)',ln);  cap=dec(mm.group(1)) if (mm and cap is None) else cap
        mm=re.match(r'\s*FocusControl = (\w+)',ln); fc=mm.group(1) if mm else fc
        if re.match(r'\s*end',ln):
            if cap and fc: print(f"{cap:<16} Focus={fc}")
            cur=None
PY
```

---

## ① 篩選區（filter popup）

對 razor 的 `iks-filter-grid` 逐列檢查：

1. **預設文字（DefaultText）是否正確**
   - 權威＝base `.dfm` 的 **TLabel `Caption`**，配 **FocusControl** 對到正確的 RzButtonEdit/控件；`&X` 是快捷鍵標記，取字時去掉。
   - 常見錯誤：轉譯時自行簡化/臆測（「業務部門」寫成「部門」、「機型別」寫成「產品分類」、「參考單號」寫成「單號/出貨單」、「料品編號」寫成「料號」…）。**一律以 DFM 標籤字面為準**。
   - 日期區間框（`inline edtDate/edtDate1: TfrmP2Date`、`FmP2YRMN1: TfmP2YRMN`）的標題常是其 EditLabel；對不到時以「該日期綁的欄位」在 grid 的標題為輔證（例：edtDate→`m.PJDT`，grid PJDT 標題＝受訂日→標籤用「受訂日期」）。

2. **順序是否正確（由上到下、由左到右）**
   - 權威＝`dfm_audit.py` 的控件 `top,left` 排序（含日期/年月 frame 一起排序）。razor 篩選列**逐一照這個順序排**，不用「自訂邏輯分組」。

3. **搭配 FilterDblClick / FilterValidate 檢查規則**
   - 讀 `.pas` 的 `FilterDblClick`（決定各控件的 EditPick/KeyCodePick 來源表與欄位）與 `FilterValidate`（CheckNo/CheckKeyCode）。
   - 核對 razor：兩欄(代碼+名稱) pick → ComboBox；三欄以上 → EditPick；KeyCode → `KeyCodeComboBox`；純文字 like → TextBox。來源表/條件（如 `MM_ITMTP where GOOD='Y'`）要對得上。

4. **`Visible = False` 的篩選要不要顯示**
   - DFM 標 `Visible=False` 的 CheckBox/控件（如 chkMO「只列有製令」、Chk1「只顯示已銷貨訂單」）→ **忠於原程式不顯示**；razor 移除該列並留一行註解說明來源與 Visible=False。

---

## ② 明細切頁（頁籤名稱 + 順序）

- 權威＝base `.dfm` 的 **TTabSheet `Caption`**（`dfm_audit.py` 的「TabSheet 頁籤」區，**檔案順序＝PageControl 顯示順序**）。
- 核對 razor 的 `iks-mode-switch` 膠囊：
  1. **名稱**逐字對 TabSheet Caption（例：「生產計劃」應為「排產記錄」）。
  2. **順序**照 DFM 檔案順序排**膠囊按鈕**（下方 `@if ActiveDetailTabId==...` 的 grid 區塊靠 id 判斷，原始碼順序不影響顯示，**只要重排按鈕列**即可）。
- Tab1 標題若隨旗標變動（如 `gbHASSER`→「規格及選配」/「配料」）照 `.pas` FormCreate 邏輯保留。

---

## ③ 主檔與明細欄位（欄位名/欄序）× MqyGetText 顯示狀態

1. **欄位名 + 欄序**：`dfm_decode.py` 對每個 grid（主 + 每個 Dq）出「FIELD/欄序/中文標題」，逐欄對 razor 的 `GridColumnConfig`（Field 名、順序、Title 全對）。
2. **顯示狀態（_Display）**：讀 `.pas` 各 grid 的 `AddFieldEvent(Self, <DataSet>, 'F1;F2;…', … , <XxxGetText>)` 取得「有註冊顯示轉換」的欄位集（主檔 `MqyGetText`、**子表各自的 GetText**），再看該 handler 用哪種：
   - `GetNoDESCPT(...,'表','名稱欄',…)` → 名稱查表 → razor 用 `[DisplayTransform("<key>","<模組>")]` + `_Display`；缺 key 就到 `DisplayTransformService.SAL.cs` 的 `_mapSAL` 補一筆 `(表, 鍵欄, 名稱欄)`。
   - `GetKeyCodeDESCPT(...,'欄',…,'表')` → KeyCode 文字 → 補 `_kcMapSAL` 一筆 `(表, 欄)`，razor 用 `[DisplayTransform]`／`[DisplayTransformKeyCode]` + `_Display`。
   - **常見錯誤**：把 MqyGetText 有做名稱/KeyCode 轉換的欄，razor 卻直接顯示原碼，或誤用勾選框（Bool）。例：`ZCLOSE` 走 `GetKeyCodeDESCPT` 應顯示 KeyCode 文字，不是 checkbox；`PROD` 走 `GetNoDESCPT(SA_PROD)` 應顯示名稱。
   - **不在 AddFieldEvent 名單** 的 Y/N 欄才維持原碼/勾選框（依 DFM ControlType）。
   - DFM 中 `Visible=False`（或 razor 未列）的欄不需 `_Display`。
3. 交叉核對＝**「dfm 欄位 × SQL select × 該 grid 的 gettext」** 三方一致（與讀源時 Step 2.0/2.1 同一把尺，收尾再驗一次）。

---

## ④ 明細必填欄位（AddDetail `sNotNullFields`）× 轉譯是否正確寫入

> 目的：抓「Delphi 宣告為必填的欄位，轉譯後漏驗證或漏寫入」。**逐欄先判狀態、再決定要不要查必填**——不要把唯讀欄誤當必填輸入。

### 判斷順序（逐欄；主 grid + 每個 Dq）

1. **先判該欄是否「可編輯」——以 `.pas` 為權威，DFM 旗標只是輔助**。
   - DFM 輔助：`dfm_decode.py` 每欄印 `[可直輸]/[非直輸]`（wwDBGrid 第 4 碼 F=格內可直接輸入 / T=不可直接輸入）。
   - ⚠⚠ **`非直輸(T)` 不等於唯讀**：該欄仍可能靠 `.pas` 的 **`CdDblClick`/`MqyDblClick`/`DqnDblClick` pick** 或 InCell 編輯（實例：B512 主 grid `FACTID` 旗標=T，但 `CdDblClick` 有 FACTID pick → 其實可編輯）。
   - **真正可編輯 ＝ 旗標 F（可打字）｜或 `.pas` 有對該欄的 pick／InCell**。逐欄查 `.pas`：`Mqy/Dq DblClick`（含 wwDBComboDlg 的 `DataField=` 分支）決定哪些欄開 pick、哪些是純數量 InCell。
   - **判定為不可編輯（無旗標F、也無 pick/InCell）** → razor `GridColumnConfig.Editable=false`；此欄不列入必填輸入驗證（唯讀/計算/交易帶入欄走顯示或寫入，不做 Checknull）。
   - **判定為可編輯**（打字或 pick）→ 進入第 2 步查必填。

2. **可編輯者才看是不是「必填」**（權威＝`.pas` `FormCreate` 的 `sNotNullFields`；主檔與每個 `AddDetail(Dqn,…,sNotNullFields,…)` 各取自己那組，分號分隔。見 `details/delphi-reading.md`「Required 來源」）。
   - 只有**「可編輯（打字或 pick）+ 必填」**的欄才是本檢查要核對的對象。

### 對每個「可編輯 + 必填」欄三方核對（缺一即【待確認】）

1. **DTO 有欄位**：存在於明細 DTO（`partial : EFModel`）或其 base，未於轉譯時被精簡掉。
2. **存檔前有驗證**：新增/存檔（前端 Save 或 Service）對該欄做 Checknull（空→擋下、不送/不寫），對應 Delphi `BeforePost`/`Checknull(sNotNullFields)`。
3. **insert SQL 有寫入**：該明細 INSERT 欄位清單確含此欄（不可只驗不寫，或只寫不驗）。

### 常見錯誤

- 把**判定為不可編輯**的欄誤加必填驗證（使用者無從輸入 → 永遠被擋）；勿只憑 DFM `[非直輸]` 就當唯讀，要先確認 `.pas` 無 pick。
- 可編輯必填欄：DTO 未帶（前端 round-trip 丟欄）→ insert 寫入 NULL/空。
- 只做前端 Checknull 但 insert 漏欄；或 insert 有欄卻無必填驗證（Delphi 有 Checknull）。
- 多明細（多個 `AddDetail`）只驗主明細，漏其他 Dq 的 `sNotNullFields`。

> **SelectForm/拋轉類**（無 CRUD 明細、以交易寫 DO/單據系列）：把「必填」對映到**交易寫入目標表的業務必填欄**——一樣先確認來源 grid 該欄唯讀與否，再確認拋轉 insert 有帶、且對必填欄有 Checknull（例：SA_DOD 的 STKNO/UNIT/ORDERNO）。

---

## 收尾

- 每支頁面把上面 ①②③④ 的偏差改完後，做 `SKILL.md`「交付前檢查」的 UI 編譯掃描與存檔欄位對照。
- 若 `_Display` 需新增 `DisplayTransformService.SAL.cs` 的 map，記得該註冊是共用檔，用別名避開既有 key 衝突（見檔內既有註解慣例）。
