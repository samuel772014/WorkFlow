# 詳細規則：Delphi 來源逐層讀法 ＋ 後端產出順序

> Phase 0 讀來源用。搭配 SKILL「來源檔讀取原則」（繼承鏈先問、DFM 權威）。
> 來源：舊 `delphi-to-csharp` SKILL 的非衝突部分彙整（前端規則以本專案 for_github 新 UI 為準，見末段衝突註記）。

---

## Step 1 — 開始前必問操作者
1. C# 功能代碼？（如 SAL302）→ 影響所有檔名
2. Razor 路由？（如 /SAL/SAL302）
3. 子表命名：沿用 Dq1/Dq2… 還是語意命名？
（＋ 有繼承鏈 / 有明細去向不明 / 特殊情況，一律先問——見 SKILL 來源讀取原則）

## Step 2 — 先讀 `.dfm`，再讀 `.pas`
**`.dfm` 必確認**（DFM 是版面權威）：
- `inherited Mqy:`/`Dq1:` → `DataSet.CommandText`＝查哪張表；底下 `object Xxx:` `FieldName`＝欄位清單
- `MDBGrid.Selected.Strings`＝主表瀏覽欄位/標題；`DDBGrid.Selected.Strings`＝子表欄位（`ControlType` 有 pick 但未必顯示）
- `tbEdit→MScrollBox→object DBEditX:`＝編輯表單欄位（注意 **`Visible=False`** 不顯示、`Color=淺綠=PK`）；欄位順序依 `Top` 座標

### Step 2.0 — 用 `dfm_decode.py` 解出 grid 欄位（**強制，勿手抄亂碼**）
DFM 的 `Selected.Strings` 中文標題以 **Big5(cp950) 原始位元組或 `#NNNN` 十進位字碼**儲存，直接 Read 會是亂碼/難核對。**每頁轉譯前必跑本工具**把每個 grid 解成「序號. FIELD  w=寬  中文標題」：
```bash
PYTHONIOENCODING=utf-8 py .claude/skills/page-migration/tools/dfm_decode.py <來源.dfm>
```
（`PYTHONIOENCODING=utf-8` 不可省，否則 Windows 管道把中文轉亂碼。Windows 上 `python` 常指向 Store 空殼，用 `py`。）
- 產出即**主 grid 與各子 grid 的權威欄位清單**：欄位代碼(FIELD)、**欄序**、寬度、**中文標題**。razor 的 `Columns`/`GridColumnConfig`（Field/Title/順序）**一律以此為準**，勿憑 SQL 或臆測補欄。
- B430Base 這類「一主檔＋多子明細頁籤」會列出全部 `DDBGridN`（每個頁籤一個 grid）；逐一對頁籤。

### Step 2.1 — grid 欄位三方交叉核對（**強制；主 grid 與「每一個」Dq 子 grid 都要做**）
**逐一 grid**（主檔 cd／`Dq1`／`Dq2`／… 每個頁籤都算一個 grid），把三個來源對齊，任一不一致即回頭查 Delphi、勿自行裁決：
1. **`dfm_decode` 欄位清單**（要顯示哪些欄、欄序、標題）——見 Step 2.0（每個 dfm grid 對一個 Dq，但**編號/順序未必一致**，見下方 ⚠️）。
2. **該 grid 的資料來源 SQL select 欄位**：主 grid＝`DisplayButtonClick`/`OpenPick`；子 grid＝`cdAfterScroll`（或各 `DqN` 的 `SQLOpen`/`CommandText`）。grid 顯示欄必為 SQL 子集，隱藏欄留給驗證/交易用、勿刪。
   - ⚠️ **明細表名的權威來源是 `.dfm` 的 `DataSet.CommandText`**（2026-09-22 由 SAL069/B511 學到）：`.pas` 的 `SQLOpen` 常不含明細表（dataset 預設 SQL 在 `.dfm` 物件），故 `.dfm` 找不到就別從 `.pas` 猜表名。做法：`grep "DataSet.CommandText.*from" <B碼>.dfm` 取各 dataset 的表，再用**該 dataset 的欄位物件前綴**（如 `object Dq3PLTNO`→dataset Dq3）對回 Dq。搭配上方 grid↔Dq 通則（靠欄位/AddDetail 不照 grid 名序）。
3. **該 grid 的 gettext 顯示對應**——決定哪些欄要 `_Display`（代碼→名稱）：
   - **不是只有主檔 `MqyGetText`**：每個子表可能有自己的 `Dq1GetText`/`DqNGetText`，或共用一個 GetText 但**以 `FormCreate` 裡的 `AddFieldEvent(Self, DqN, 'F1;F2;…', nil, nil, XxxGetText)` 宣告該 grid 要做名稱解析的欄位集**（分號分隔）。**逐一 grid 抓它自己那組 `AddFieldEvent` 欄位清單**，這才是該 grid 的 `_Display` 權威來源。
   - 例：`AddFieldEvent(Self, Dq2, 'FACTID;STATUS', …)` → Dq2 grid 的 FACTID/STATUS 要 `_Display`；`AddFieldEvent(Self, Dq3, 'FACTID;VNDERID;STATUS', …)` → Dq3 另一組。見 `details/dto-display.md`。
> 核對結論寫進計畫檔（或 translation-log）：**每個 grid 各一張表**，列「FIELD｜標題(dfm_decode)｜SQL 有無｜是否 `_Display`(來自該 grid 的 AddFieldEvent/GetText)」，缺漏/衝突標【待確認】。

> ⚠️ **grid↔Dq 歸屬「靠欄位判定，不照 dfm grid 名稱/順序」**（2026-09-22 由 SAL046/SAL058 學到）：`dfm_decode` 的 grid 識別（`DDBGrid1/2/4`、dfm 內先後）**不等於** Dq 編號，實測會錯位——
> - SAL046：dfm `DDBGrid1→Dq2`(包裝)、`DDBGrid2→Dq3`(收款)、`DDBGrid4→Dq4`(備註)，`DDBGrid3` **跳號無對應**。
> - SAL058：dfm **第一個 grid＝目標 cd2、第二個＝來源 cd**（先後與 UI 命名相反）。
>
> 正解：以「**欄位集合 ＋ `AddFieldEvent(Self, DqN, …)` 的 DqN**」比對判定各 dfm grid 對應哪個 Dq，**禁照 grid 序或 DDBGridN 編號硬配**；不確定 → 標【待確認】問操作者，不假設。

**`.pas` 依序掃描**：
1. `FormCreate` — PK(`sKeyFields`)、**必填(`sNotNullFields`)**、子表連結(`AddDetail`)
2. `MqyDblClick`/`Dq1DblClick` — 逐欄判 UI 元件 → `details/input-component-choice.md`；欄位判 `EditPick`(選單)還是 `EditMemo(Sender,'標題',bgEdit)`(多行長文字放大視窗 → `PopUpText`，見 `details/popuptext.md`)
3. `MqyGetText`/`Dq1GetText` — 決定哪些欄位要 `_Display` → `details/dto-display.md`
4. `MqyChange`/`Dq1Change` — 連動 → `details/field-change.md`（計算一律後端）
5. `MqyNewRecord`/`Dq1NewRecord` — 新增預設值 → 明細寫在 `OnAdd`（`details/grid-incell.md`）
6. `BeforePostTransaction`/`PostAction` — 存檔前驗證 → Service 商業邏輯
7. 其他按鈕 OnClick — 對應 `ToolbarButton` 或獨立 API
8. `uses` 段 — 共用 Unit → Step 2.5

> **Required 來源**：優先取 Delphi `sNotNullFields`；沒有才問操作者（補充 `details/edit-window.md`）。

## Step 2.5 — 共用函式檢查
`uses` 出現 FUNC 系列 Unit → 查 `details/shared-functions.md`，在 C# 實作上方加 `// 用途/處理方式/負責人` 註解。

## Step 3 — 後端產出順序
```
① {MOD}Repository.{FORM}.cs   SQL 查詢/CRUD/商業查詢（一律 _iksDbFunc.*，參數化）
② {MOD}Service.{FORM}.cs      參數解析 + 呼叫 Repository（try-catch 包覆）
③ Resolvers/{FORM}Query.cs    GraphQL Query 薄層
④ Resolvers/{FORM}Mutation.cs GraphQL Mutation 薄層
⑤ Models/{FORM}Dto.cs         DTO + _Display（partial : EFModel, IDisplayResolvable）
⑥ {FORM}.razor                UI 頁面（骨架 → templates/*）
```

## Service 層範本（try-catch 必包）
```csharp
public async Task<queryResult> Get{Form}MqyAsync(string arg, DapperContext context, string? fs = null) {
    var args = JsonConvert.DeserializeObject<Dictionary<string,string>>(arg);
    if (args == null) return new queryResult(0, "參數錯誤", 0, null);
    try {
        var repo = new {Mod}Repository(context, _iksDbFunc);
        var (data, total) = await repo.Query{Form}MqyAsync(args);
        return new queryResult(1, string.Empty, total, JsonConvert.SerializeObject(data));
    } catch (Exception ex) { return new queryResult(0, ex.Message, 0, null); }
}
```
> 後端方法/交易細節 → `details/backend-sql.md`；命名 → `details/naming.md`。

---

## 前端一律以 for_github 新 UI 為準
舊 delphi-to-csharp SKILL 的**後端流程照用**；**前端一律用 for_github 新 UI，舊寫法已淘汰、不採用**：
- master-detail 明細切換與 query/edit 切換都用 `iks-mode-switch` 膠囊 + `@if` 面板（**已淘汰 `TelerikTabStrip`**；`templates/master-detail.md`）。
- grid 新行初始化直接用 `OnAdd`/`OnUpdate`/`OnDelete` 參數，uState=Insert 寫在 `OnAdd`（`details/grid-incell.md`）。
- 工具列純 Tabler 圖示+tooltip；單檔修改/刪除在 grid 指令欄（`details/toolbar.md`）。
