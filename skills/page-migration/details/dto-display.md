# 詳細規則：I. DTO 類別 ＋ ColConfig

> 骨架指標來源：`templates/single-file.md` I 區。
> 資料來源：`.pas` 的 `GetText`（顯示轉換）＋ `.dfm` 的 Grid `Selected.Strings` / Label `Caption` / `ControlType`（欄位、Title、EditorTemplate）。

---

## 通則

### 1. DTO 繼承
- **畫面用的 DTO 一律 `partial class Xxx : {{EF Model}}, IDisplayResolvable`**。
- 繼承 EF Model 後只加：`_Int` / `_Bool` / `_Display` / `uState`（勿用 `[JsonProperty]` 改名，Virtual grid 反射會壞）。
- **特殊情況（無對應 EF Model、跨表組合…）→ 詢問轉譯操作者**。

### 1b. 宣告位置：頁面內、不跨頁共用
- DTO（`Mqy` / `Dq1` / `Dq2` …）**一律宣告在該頁 `.razor` 的 `@code` 內**（`#region` 分區，比照 SAL021），**不抽到 `Models/*.cs`、不跨頁共用型別**。
- **重用「元件」可以，但「DTO 型別」不共用**：明細 grid 用各頁自建 DTO；若該明細要開他頁的重用彈窗（如 SAL044 Dq2 開 SAL045A），只在**開窗邊界**把自建 DTO 轉成該彈窗的契約型別（例：`BuildDq2Record(Dq2) → SA_CASECRMDto`）。
- ⚠ 同名嵌套類別 vs `Models` 命名空間會衝突／混淆：若把 DTO 移進 razor，記得**刪掉舊 `Models/{{Form}}Dto.cs`**。

### 2. `_Display` 欄位（依 Delphi GetText 判斷）
Delphi `GetText` 用 `GetNoDESCPT` / `GetKeyCodeDESCPT` 的欄位才需要 `_Display`：

| Delphi GetText | 屬性寫法 |
|----------------|----------|
| 一般 代碼→名稱（`GetNoDESCPT`） | `[DisplayTransform("{{codeField}}", "{{module}}")]` |
| KeyCode 描述（`GetKeyCodeDESCPT`） | KeyCode 型 `DisplayTransform`（見本檔通則2 別名寫法） |
| 需**帶額外參數**（連動過濾） | `[DisplayTransformApi(gqlway: "{{form}}_{{Code}}_Display", codeField: "{{Code}}", extraParams: new[] { "OBJTP:OBJTP" })]` |

> ⚠️ **`_Display` 必與 field-change 依賴交叉判定，別只查一次共用轉換就定案**（2026-09-22 由 SAL046 CUSTMER 學到）：
> 某代碼欄雖在共用 `_map*`/`DisplayTransformService` 有「純代碼→名稱」註冊（查 index 會回一般 `DisplayTransform`），但若它在 Delphi 有**連動依賴**（`AddFieldEvent`/`Args` 帶上層欄位、`XxxChange` 依他欄過濾，如 SAL046 `CUSTMER` 依 `OBJTP` 內外銷），**必須改用 `DisplayTransformApi` + `extraParams`**（`"OBJTP:OBJTP"`），否則名稱解析會忽略連動、解錯。
> 做法：每個 `_Display` 欄先看 `details/field-change.md` 的連動盤點——**有依賴→API 版；無依賴→一般版**；判不準標【待確認】問操作者，勿逕用一般版。

- **例外不需 `_Display`**：
  - 顯示名稱**已是實欄**（如 SARPNM 本身存名稱）→ grid 直接綁實欄，不做 `_Display`。
  - 欄位在 DFM **`Visible=False`**（如 STATUS）→ 不顯示就不需 `_Display`。
- **KeyCode 名稱衝突用別名 + 後綴 map key**：`[DisplayTransformKeyCode("X","SAL")]` 的 displayCode 同時是 `_kcMapSAL` 的 key 與讀值來源屬性名；若 `X` 已被他表佔用，後端註冊後綴 key（如 `["INVCFG_TP"] = ("SA_INVCFG","TP")`），DTO 加別名屬性 `public string? INVCFG_TP { get => TP; set => TP = value; }` 再 `[DisplayTransformKeyCode("INVCFG_TP","SAL")] TP_Display`（SAL032）。
- **特殊情況 → 詢問轉譯操作者**。

### 3. ColConfig（Grid 欄位設定）
- **欄位/順序/寬度**：依 DFM Grid `Selected.Strings`（`欄名 寬度 標題 …`）。
- **Title**：來自 DFM ——Grid `Selected.Strings` 的中文標題，或該 Field 的 `DisplayLabel` / Label `Caption`。
- **可 pick / 可編輯欄位 → 加 `EditorTemplate`**：依 DFM `ControlType`（含 `CustomEdit;xxxPick`）或 `.pas` 的 `DblClick` 判斷該欄要開 Picker。
  - **EditorTemplate 寫法規則**：`details/editor-template.md`。
- 數值/日期欄位型別處理：整數 → 下方 3b；金額 `Format="#,##0.######"`；日期 `DisplayFormat="{0:yyyy/MM/dd}"`。

### 3b. `_Int` 整數顯示欄
numeric(n,0) 欄位 EF 映射成 `decimal`，直接綁會顯示小數；要整數顯示時加 `_Int`：

**一律 get/set 包裝 base**（含非編輯的項次/序號欄、Virtual 與 vnq 皆同）：
`public int QTY_Int { get => (int)(QTY ?? 0); set => QTY = value; }`（非 nullable base 則 `get => (int)ITEM;`）。
- 理由：編輯改的是 base，wrapper 讓顯示與 base 自動同步；Virtual grid 走反射不吃 `[JsonProperty]`。
- ⚠ **不用 `[JsonProperty]`＋`NewtonsoftDecimalToIntConverter` 獨立屬性**：本地編輯後 `_Int` 不更新→殘留舊值；與 base 映射同一 JSON key，序列化存檔衝突。既有 9 支舊寫法列入待改。
- ColConfig 的 **key 與 Field 都要改成 `X_Int`**（vnq 的欄位鎖定 / `SetColumnEditable` 以 key 對應）。
- **日期欄不用 `_Int`**：ColConfig 加 `DisplayFormat="{0:yyyy/MM/dd}"`，DTO 仍綁 `DateTime?`。
- 實例：SAL046（B301）QTY/UP/TUP/MNY/TMNY/PKVOL/NW/GW/CRR/INSUR/ARATE 全用 get/set 包裝 base。

### 3c. 明細可編輯 ComboBox EditorTemplate 寬度慣例
明細 grid 內以 ComboBox 當 EditorTemplate 的欄位（`IksCodeComboBox` / `KeyCodeComboBox`），寬度設定兩鐵則：

| 參數 | 值 | 理由 |
|------|-----|------|
| `Width` | **該欄 ColConfig 的 `Width` − 10px** | ComboBox 塞進儲存格不撐破欄寬、留邊界 |
| `PopupWidth` | **`"230px"`** | 下拉展開比欄位寬，代碼＋名稱（`KEY:DESCPT`）不被截斷、便於閱讀 |

- 兩元件皆支援 `Width` 與 `PopupWidth`（`KeyCodeComboBox` 的 `PopupWidth` 於 2026-08 補齊，比照 `IksCodeComboBox` 用 `ComboBoxPopupSettings.Width`）。
- 範例（SAL050 Dq1，欄寬 100px → Width 90px）：
  ```razor
  private RenderFragment<Dq1> PrdtpEditorTemplate => (item) =>
      @<IksCodeComboBox @bind-Value="item.PRDTP" _url="@_url" module="COMMON" comboBoxCode="PrdtpComboBox" Width="90px" PopupWidth="230px" />;
  ```

---

## 【範例程式碼】(SAL001)

```csharp
public partial class Mqy : SA_SALER, IDisplayResolvable
{
    [DisplayTransform("DEPID", "COMMON")]    public string? DEPID_Display { get; set; }
    [DisplayTransform("SMANAGER", "COMMON")] public string? SMANAGER_Display { get; set; }
    // 註：SARPNM 是實欄（已存名稱）→ 不做 SALEREP_Display；STATUS DFM Visible=False → 不做
}

private Dictionary<string, GridColumnConfig> SAL001Mqy_ColConfig => new()
{   // 欄位/順序/寬度/Title 全對 DFM MDBGrid Selected.Strings
    { "SALEREP",          new(){ Field="SALEREP",          Title="業務代表",     Width="100px", Order=1 } },
    { "SARPNM",           new(){ Field="SARPNM",           Title="業務代表姓名", Width="200px", Order=2 } },
    { "SARPENM",          new(){ Field="SARPENM",           Title="英文姓名",     Width="200px", Order=3 } },
    { "DEPID_Display",    new(){ Field="DEPID_Display",    Title="業務部門",     Width="180px", Order=4 } },
    { "SMANAGER_Display", new(){ Field="SMANAGER_Display", Title="業務主管",     Width="200px", Order=5 } },
};
```

## 【骨架程式碼】

```csharp
public partial class Mqy : {{EFModel}}, IDisplayResolvable
{
    // 依 .pas GetText 有 GetNoDESCPT/GetKeyCodeDESCPT 的欄位才加；顯示已是實欄或 DFM 隱藏者不加
    [DisplayTransform("{{code}}", "{{module}}")] public string? {{Code}}_Display { get; set; }
    // 需帶參數：[DisplayTransformApi(gqlway:"{{form}}_{{Code}}_Display", codeField:"{{Code}}", extraParams:new[]{"{{P}}:{{P}}"})]
}

private Dictionary<string, GridColumnConfig> {{ColConfig}} => new()
{   // Field/Title/Width/Order 依 DFM Grid Selected.Strings；可 pick 欄加 EditorTemplate（→ details/editor-template.md）
    { "{{欄}}", new(){ Field="{{欄}}", Title="{{DFM Caption}}", Width="{{}}px", Order={{n}} } },
};
```

---

## 指路
- 控件選擇 → `details/input-component-choice.md`
- EditorTemplate 寫法 → `details/editor-template.md`
- 存檔欄位 → `details/crud-handlers.md`
