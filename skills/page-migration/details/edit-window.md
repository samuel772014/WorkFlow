# 詳細規則：E. 編輯表單 Window（＋詳細 View 唯讀模式）

> 骨架指標來源：`templates/single-file.md` E 區。
> 資料來源：`.dfm` 主表單控件（Top 座標、DataField、ReadOnly、Visible）＋ `.pas` 欄位事件。

---

## 通則

### 1. 版面與欄位順序
- 表單本體用 `iks-edit-grid` / `iks-edit-row`（每列 `IksLabel` + 輸入控件）。
- **欄位順序＝DFM 各控件 `Top` 座標由上而下**（DFM 是權威；同 Title 來源）。B101：SALEREP(29)→SARPNM(56)→SARPENM(83)→DEPID(110)→SMANAGER(137)→STATUS(160,藏)。

### 2. 輸入控件
- 每欄用哪種控件 → `details/input-component-choice.md` 決策樹。
- 連動帶值 / change → `details/field-change.md`。
- DFM `ReadOnly=True` 或「由連動帶入」的欄位 → `Enabled="false"`（如 SARPNM）。

### 3. 必填（Required）
- **`Required` 由轉譯操作者設定**，不自動推導（Delphi `MqyValidate` 只驗外鍵存在、未明確編碼必填）。
- 標記方式：`<IksLabel Required="true" ... />`；存檔前於 `Save()` 對這些欄位做必填驗證（見 `details/crud-handlers.md`）。
- 哪些欄位必填 → **詢問轉譯操作者**。

### 4. 主鍵不可修改
- **主鍵（`sKeyFields`）修改時唯讀**：`Add` 用 Picker/輸入可設定；`Edit`/`View` 一律唯讀顯示。
- **不移植 Delphi 的 `cbEditKeyFields`（改主鍵勾選）** —— 一律禁止改主鍵。

### 5. 詳細 / View 唯讀模式（本 skill 新增的標準功能）
- **重用同一個編輯 Window**，以唯讀開啟（記憶 `detail_readonly_reuse_edit`），不另做檢視畫面。
- `pageStatus` 擴為 `"query" | "Add" | "Edit" | "View"`。
- `View` 時：**所有輸入框唯讀**、**隱藏存檔鈕**（只留關閉）、標題顯示「檢視」。
- **上/下一筆** 在 `Edit` **與** `View` 都可用（見 `details/row-navigate.md`）。
- 由 Grid 指令欄「詳細資料」鈕觸發（見 `details/toolbar.md`）。

---

## 【骨架程式碼】

```razor
<TelerikWindow Visible="@_editWindowVisible" VisibleChanged="@OnEditWindowClose" Modal="true" Width="480px">
    <WindowTitle>@(pageStatus switch { "Add" => "新增{{X}}", "View" => "檢視{{X}}", _ => "修改{{X}}" })</WindowTitle>
    <WindowContent>
      <div class="iks-edit-grid">
        @* 欄位順序依 DFM Top；控件依決策樹；唯讀看 _formReadonly *@
        <div class="iks-edit-row">
            <span class="iks-edit-label"><IksLabel Key="Lb_E_{{PK}}" defaulttext="{{主鍵標題}}" /></span>
            <span class="iks-edit-input">
                @if (pageStatus == "Add")
                {
                    <EditPick @bind-Value="current.{{PK}}" ... />   @* Add 可選 *@
                }
                else
                {
                    <IksTextBox @bind-Value="current.{{PK}}" Enabled="false" />  @* Edit/View 主鍵唯讀 *@
                }
            </span>
        </div>
        @* 其餘欄位：Enabled="@(!_formReadonly)"；Required 由操作者決定加 IksLabel Required="true" *@
        <div class="iks-edit-row">
            <span class="iks-edit-label"><IksLabel Required="true" Key="Lb_E_{{F}}" defaulttext="{{標題}}" /></span>
            <span class="iks-edit-input">
                <IksCodeComboBox @bind-Value="current.{{F}}" Enabled="@(!_formReadonly)"
                                 @bind-Value:after="On{{F}}Changed" ... />
            </span>
        </div>
      </div>
      <div class="iks-edit-actions">
          @if (pageStatus != "View")   @* View 隱藏存檔 *@
          { <TelerikButton ThemeColor="primary" Icon="@SvgIcon.Save" OnClick="Save">存檔</TelerikButton> }
          <TelerikButton Icon="@SvgIcon.Cancel" OnClick="Cancel">@(pageStatus == "View" ? "關閉" : "取消")</TelerikButton>
      </div>
      @* 右側上/下一筆：Edit 或 View 皆可 → details/row-navigate.md *@
    </WindowContent>
</TelerikWindow>
```
```csharp
private bool _formReadonly => pageStatus == "View";
```

---

## B101 → 編輯 Window 對應（DFM Top 序）

| DFM 控件 (Top) | 欄位 | 控件 | 唯讀? |
|----------------|------|------|-------|
| DBEdit1 (29) | SALEREP(主鍵) | Add→EditPick 3欄；Edit/View→唯讀 | 主鍵規則 |
| DBEdit2 (56) ReadOnly | SARPNM | IksTextBox | ✅(連動帶入) |
| RzDBEdit1 (79) | SARPENM | IksTextBox | 依模式 |
| DBEdit3 (110) | DEPID | IksCodeComboBox(2欄) `:after`→SMANAGER | 依模式 |
| DBEdit6 (137) | SMANAGER | EditPick(3欄) | 依模式 |
| DBEdit7 (160) Visible=False | STATUS | 不顯示，預設 "A" | 藏 |

> Required：本頁建議 SALEREP、DEPID 必填，但**最終由轉譯操作者確認**。

## 指路
- 控件選擇 → `details/input-component-choice.md`
- 連動 → `details/field-change.md`
- 上/下一筆 → `details/row-navigate.md`
- 存檔/驗證 → `details/crud-handlers.md`
- 詳細資料鈕位置 → `details/toolbar.md`
