# 詳細規則：共用輸入元件用法（IksCodeComboBox / KeyCodeComboBox / IksTextBox / EditPick / IksLabel / bool checkbox）

> 所有 details 的「→ 參考控件 skill」都落到這裡。**選哪個控件**先過 `details/input-component-choice.md` 決策樹；本檔講**各控件怎麼用**。
> 來源：舊 skill `shared-input-components` / `editpick-mapping` / `ikslabel` / `grid-checkbox`（Desktop 備份彙整）。

---

## 通用：module 參數
三個 Service 型控件（ComboBox/TextBox）都要**明確傳 `module`**，後端以 `module`+`code` 路由，不自動偵測。
- `"COMMON"`：跨模組共用基礎表（HR_DEP/HR_EMPLYM/PP_PLANT/SS_CUR/AC_INVITP/SA_PAYTERM…）。
- `"SAL"` 等：模組專屬（客戶/業務人員/報價單號…）。**不可跨模組呼叫**。

---

## IksCodeComboBox（EditPick ≤2 欄 → 用它）
**comboBoxCode 命名**：`欄位名大駝峰 + ComoBox`（固定後綴）。例 `CUR→CurComoBox`、`SALEREP→SalerepComoBox`、`INVITPNO→InvitpnoComoBox`。

```razor
@* 範例 *@
<IksCodeComboBox @bind-Value="@model.CUR" _url="@_url" module="COMMON" comboBoxCode="CurComoBox" />
@* 帶連動過濾（Args 動態帶上層值）*@
<IksCodeComboBox @bind-Value="@model.CUSTMER" _url="@_url" module="SAL" comboBoxCode="CustmerComoBox"
                 Args="@(new Dictionary<string,string>{ ["OBJTP"]=model.OBJTP ?? "" })"
                 @bind-Value:after="OnCustmerChanged" />
```
```razor
@* 骨架 *@
<IksCodeComboBox @bind-Value="@model.{{FIELD}}" _url="@_url" module="{{COMMON|模組}}" comboBoxCode="{{Field}}ComoBox"
                 Args="@(...)" @bind-Value:after="On{{FIELD}}Changed" />
```
> 常用 code：COMMON=`DepidComoBox`(STATUS)/`EmplyidComoBox`/`FactidComoBox`/`UnitComboBox`/`CurComoBox`/`InvitpnoComoBox`/`PaytermComoBox`(ARTERM)；SAL=`SalerepComoBox`(STATUS)/`CustmerComoBox`(OBJTP)/`SprcidComoBox`(CUR,FLDT)/`PortidComboBox`/`QuotnoComboBox`。連動見 `details/field-change.md`。

---

## KeyCodeComboBox（Delphi KeyCodePick → 用它）
查 KEYCODE 表，`TBL_NAME`=主表名、`ComboBoxKey`=欄位名；`module` 幾乎恆 COMMON、免傳。

```razor
<KeyCodeComboBox @bind-Value="@model.CTAXTP" TBL_NAME="SA_QUOTM" ComboBoxKey="CTAXTP" _url="@_url" />
```
```razor
<KeyCodeComboBox @bind-Value="@model.{{FIELD}}" TBL_NAME="{{主表}}" ComboBoxKey="{{FIELD}}" _url="@_url" @bind-Value:after="On{{FIELD}}Changed" />
```
> Validate 由元件保證，免另寫。

---

## IksTextBox（一般文字 / 需後端驗證）
`OnBlur` 以 `textBoxCode` 路由後端驗證；`Args` 帶條件（如 `STATUS`=pageStatus 判 Add/Edit）。

```razor
<IksTextBox @bind-Value="@model.QUOTNO" textBoxCode="QUOTNO" module="SAL" _url="@_url"
            Args="@(new Dictionary<string,string>{ ["STATUS"]=pageStatus })"
            AutoFormat="IksTextBox<string>.IksFormatType.Uppercase" />
@* 純輸入不需驗證：直接 @bind-Value 即可 *@
<IksTextBox @bind-Value="@model.CUSTORD" />
```
> 屬性：`Enabled` / `Width`(預設220px) / `Placeholder` / `MaxLength`(對應 Delphi MaxLength) / `AutoFormat`(None/Uppercase/Trim/Lowercase) / `ValidationRegex`。自閉合文字框一律用 IksTextBox（記憶 `prefer_ikstextbox`）。

---

## EditPick / EditPick_Button（≥3 欄 或 grid 內）
- **主表 ≥3 欄**：頁面內用 `<EditPick @bind-Keyword @bind-Value Apply QueryWay QueryGet Columns .../>`（`ReturnMode="id:name"`、`FixedPost` 帶固定條件、連動用動態 FixedPost；記憶 `dependent_editpick_rebind`）。
- **grid（IksGrid_vnq）內**：**必用 `EditPick_Button` + 頁面層級 `@ref`**，不可 inline 宣告（每列會建獨立實例壞掉，記憶 `editpick_button_pattern`）。EditorTemplate 放 TextBox/NumericTextBox + SuffixTemplate 鈕，Click handler 命令式設 `QueryWay/QueryGet/Columns/curritem/Visible`，OnApply 回寫多欄後 `RebindKeepState()`。

```razor
@* 主表 EditPick（3 欄）*@
<EditPick @bind-Keyword="Trdterm_E_Key" @bind-Value="model.TRDTERM" Apply="OnTrdtermApply"
          QueryWay="{{form}}_GetSS_TRDTRM" QueryGet="TRDTERM STNM TRDNM" Url="@_url"
          IdField="TRDTERM" NameField="TRDNM" ReturnMode="id:name"
          Columns="@(new List<EditPick.PickColumn>{ new(){Title=\"價格條件\",Field=\"TRDTERM\",Width=\"160px\"}, /*…*/ })" />
```
> 詳細 grid EditPick_Button 五步驟（@ref 宣告→變數→EditorTemplate→Click handler→OnApply）見 `details/editor-template.md`。

---

## IksLabel
`Key`（多語系）+ `DefaultText`（查不到時後備，**一律填欄位中文名，取自旁邊 `@* 中文 *@` 注解**）；`Required="true"` 顯示紅星。固定提示文字用 `Text`（免 Key/DefaultText）。

```razor
<div class="iks-edit-row">
    <span class="iks-edit-label"><IksLabel Required="true" Key="Lb_E_SALEREP" DefaultText="業務代表" /></span> @* 業務代表 *@
    <span class="iks-edit-input"><IksCodeComboBox @bind-Value="model.SALEREP" _url="@_url" module="SAL" comboBoxCode="SalerepComoBox" /></span>
</div>
```

---

## bool（Y/N）欄位 checkbox
DTO 加 `欄位_Bool` 包裝屬性（`get => X=="Y"; set => X = value?"Y":"N"`）；**GridColumnConfig 的 key = Field = `X_Bool`**（key≠Field 會 KeyNotFoundException），不設 Template/EditorTemplate。
- Grid bool 自動 render `TelerikCheckBox`；鎖定：`IksGrid_vnq` 用 `SetColumnEditable`／`Editable=false`（記憶 `bool_column_lock`），`IksGrid_Virtual` bool 無法真鎖（限制）。
- 可編輯明細標 dirty：`OnCheckBoxChange`→uState=Update，**只有 `IksGrid_vnq` 有此參數**（記憶 `vnq_no_oncheckboxchange`）。
- `Add()` 要給 Y/N 預設值；存檔一律傳字串 `"Y"/"N"`，不傳 bool。

```csharp
public bool ISMPS_Bool { get => ISMPS == "Y"; set => ISMPS = value ? "Y" : "N"; }
// { "ISMPS_Bool", new GridColumnConfig{ Field="ISMPS_Bool", Title="是否排產", Width="80px" } }
```

---

## 指路
- 選哪個控件 → `details/input-component-choice.md`
- 連動帶值/計算 → `details/field-change.md`
- grid 內 EditPick / EditorTemplate → `details/editor-template.md`
- 後端新增 handler：ComboBoxService（COMMON→`ComboBoxService.cs`，模組→`ComboBoxService.{MOD}.cs`）、TextBoxService 同理；同名 key 衝突用「表名_欄位名」。
