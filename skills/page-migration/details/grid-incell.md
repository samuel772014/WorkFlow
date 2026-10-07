# 詳細規則：F. 明細 InCell grid（master-detail 專用）

> 骨架指標來源：`templates/master-detail.md` F 區。
> 對應 Delphi：`AddDetail(Dqn, 明細鍵, 欄位, DDBGridn, ...)` + `DqnNewRecord` / `DqnChange` / `DqnValidate`。
> 明細用 `IksGrid_vnq` InCell 批次編輯（多組用 `iks-mode-switch` 膠囊 + `@if` 面板切換，**取代 `TelerikTabStrip`**；見 `templates/master-detail.md` E/F 區）。

---

## 通則

### 1. 編輯鎖定（跟隨主檔 pageStatus）
- **query / 瀏覽態：明細 grid 不可編輯**。點「修改」進 `Edit`（或 `Add`）態才解鎖。
- 做法：列指令鈕、「+」新增鈕的 `Enabled` 綁 `_dqEditEnabled`（`_dqEditEnabled = pageStatus is "Add" or "Edit"`）。
- **編輯鎖定只用「一層」＝全域閘門（唯一標準做法，2026-09-08 起，比照 STK / SAL056）**：
  - **這個 grid 現在整體能不能編**＝ `_dataEditing`，用 `grid.EnterEdit()` / `grid.ExitEdit()` 控制（**`_dataEditing` 預設 `true`**）。`ExitEdit()` 後整表任何格都不可編、與 ColKey 無關；`EnterEdit()` 後才依欄位設定可編。
  - **哪些欄「永遠」不可編**（per-column）＝ 在 `GridColumnConfig` 靜態設 `Editable=false`（如 PK、計算欄、顯示欄）。這是靜態宣告，`Rebind` 重建欄位時會一起重套，**不需**執行期補鎖。
  - 因此**整表鎖欄那一層是多餘的**：全域閘門 `ExitEdit` 已讓瀏覽態全表唯讀，可編欄的靜態 `Editable` 已處理 per-column → **不要再寫 `LockDqGridColumns`/`UnlockDqGridColumns`/`ApplyDqLock`/`SetDqColumnsLocked`（跑 `.Where(kv => kv.Value.Editable)` 迴圈逐欄 `SetColumnEditable` 開/關）這種樣板**，也不要 `_dqGridColumnsLocked` 一次性旗標。（此樣板已於 2026-09-08 從 SAL 模組全面移除。）
- ⚠️ **膠囊切換（`iks-mode-switch` + `@if`）會「重建」對應明細 grid**：重建的 `IksGrid_vnq` 全域閘門回預設 `_dataEditing=true`（＝可編）→ 瀏覽態切回該明細就誤開放編輯。
  - **標準修法（唯一做法，比照 STK001 / SAL056）**：在 `OnAfterRenderAsync`（**每次渲染、非 firstRender**）依 `_dqEditEnabled` 冪等同步每個明細 grid 的全域閘門——`EnterEdit()`/`ExitEdit()` 明文設計成「狀態未變即 no-op」，可安全每次渲染呼叫：
    ```csharp
    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        await base.OnAfterRenderAsync(firstRender);
        if (firstRender) { /* 主檔+各明細首次 Rebind */ }
        // InCell 編輯態閘門（每次渲染冪等同步；per-column 可編性由 GridColumnConfig.Editable 決定，不做整表鎖欄）
        if (Dq1 != null) { if (_dqEditEnabled) Dq1.EnterEdit(); else await Dq1.ExitEdit(); }
        // 其餘明細 grid 同樣一行
    }
    ```
  - ⚠️ 全域閘門放 `OnAfterRender` 每次渲染同步，不受 `Rebind` 時序影響——這正是**取代**舊「膠囊切換 handler 內 `SetColumnEditable`」的原因：後者若 `RebindAllDetail()` 是 `void`＋未 `await`，你設的 ColKey 鎖會被隨後才跑完的 `Rebind` 蓋掉（實際踩過：SAL044 產品/規格切換後誤可編輯）。閘門法無此問題。

### 2. 按鈕分位
- **針對「該列」的功能 → 寫在列指令欄 `GridCommandColumn`**（拷貝/修改/刪除/取消/選配…）。
- **非針對單列（整批）的功能 → 寫在 grid 工具列 / `HeaderButtons`**（如全表匯入、批次設定、「+」新增列）。
- **列指令鈕一律純圖示 + `Title`**（同工具列 ribbon，與 master 列一致）：`Icon` 傳 Tabler class 字串（`Icon="@("ti ti-pencil")"`）、`Title` 當提示、**不放文字**（勿用 `>拷貝</GridCommandButton>` 內文、勿用 `@FontIcon.X`）。`Command`（Edit/Delete/Cancel）/ `OnClick` 事件維持原樣——明細 InCell 用 `Command="Edit"` 走列內編輯，與 master 開窗的 `OnClick="@OnRowEdit"` 不同是正常的。常用對應：copy=`ti ti-copy`、pencil=`ti ti-pencil`、trash=`ti ti-trash`、cancel=`ti ti-circle-x`、tool=`ti ti-tool`。

### 3. 新增列（InCell）
- 用 `ShowAddButton="true"` + `OnAdd`；**「+」AddNewRow 只觸發 `OnAdd`、不觸發 `OnCreate`** → `uState = UState.Insert` 必須寫在 `OnAdd`（記憶 `incell_ustate_onadd`）。
- 新增列帶主檔鍵、項次用 `GetNewItem` 對應邏輯（`ITM`/`QUOTITM` 遞增）。

### 4. 拷貝列
- 用 `AddNewRow()` + `OnAdd` 帶入來源資料，grid 才會捲到新列（記憶 `incell_copy_pattern`）。

### 5. 刪除列
- **直接呼叫 API、與存檔分開**；存檔只管新增/修改（記憶 `incell_delete_direct`）。

### 6. 存檔
- **Save() 送所有 Insert，再送所有 Update**（勿只取第一筆 Insert 就 return，記憶 `incell_save_insert_update`）。
- **明細主鍵重複雙重檢查**：前端先檢查（如 `QUOTITM`/`ITEM` 不重複），後端 mutation 內再檢查一次。
- 主檔+各明細**同一 transaction 全成才 commit**（見 `details/crud-handlers.md`）。

### 7. 眉角
- **各動作 handler 開頭先 `ExitEditModeAsync`**（提交當前儲存格，勿放 render 生命週期，記憶 `exit_edit_before_action`）。
  - ⚠️ **例外：`OnUpdate` handler 內「絕對不可」呼叫 `ExitEditModeAsync`**。`ExitEditModeAsync` 內部會反過來 `InvokeAsync(OnUpdate)`，在 OnUpdate 裡再呼叫等於無窮遞迴 → **StackOverflow**（EditPick_Button 選料號帶回時最容易觸發，因為 `Apply` 會呼叫 `ExitEditModeAsync`→OnUpdate→…）。
  - 會呼叫 `ExitEditModeAsync` 的是**「使用者動作」handler**（拷貝/刪除/存檔的 `OnClick`、EditPick_Button 的 `Apply` callback…），提交當前格再做事；**`OnUpdate` 本身即是提交**，直接更新 GD 即可，不需也不能再 Exit（比照 SAL024 update handler）。
- **`IksGrid_vnq` 不傳 `OnCheckBoxChange`**（會透傳崩潰）；bool 走 `OnBoolChanged→OnUpdate`（記憶 `vnq_no_oncheckboxchange`）；bool cell 鎖定用 `Editable=false`（記憶 `bool_column_lock`）。
- **新增/存檔/取消換 pageStatus 時，明細 grid 要顯式 `Rebind`**，否則殘留上一筆（記憶 `detail_rebind_add_save`）。編輯態的開/關由 `OnAfterRender` 的 `EnterEdit/ExitEdit` 閘門依 `_dqEditEnabled` 自動同步，換態 handler 內**不需**再呼叫任何鎖/解欄方法。
- 可編輯明細的 combobox 用單欄 `Field="X_Display"` + `EditorTemplate`（記憶 `dto_inherit_model`；EditorTemplate 寫法 → `details/editor-template.md`）。
- **grid 內欄位要 pick（選代碼帶回）→ 一律用 `EditPick_Button` + 頁面層級 `@ref`（唯一做法）**：**禁止**在 `EditorTemplate` 內塞 `EditPick`（有狀態子元件在虛擬捲動/InCell 會 render diff 崩潰），也**禁止自創繞法**（純文字直輸／自寫外部彈窗等）。五步驟見 `details/editor-template.md`。`EditPick` 只用於 grid 外（篩選區/一般欄）。遇到不確定先查 skill/範例，不猜。
- 金額等**計算一律走後端**（見 `details/field-change.md`）；Delphi `Calcu_MNYTAX` → 後端 `{form}_CalcMNY`。

### 9. 鍵盤控制（`IksGrid_vnq` 內建，master/明細通用）
- **快捷鍵綁在元件本身**（`window.iksGridRegisterKey`，`wwwroot/js/pageJs.js`），**頁面不用寫任何 JS**；掛在 grid 容器元素的 `keydown`，回呼元件的 `[JSInvokable]` 方法：

  | 按鍵 | 回呼 | 行為 |
  |------|------|------|
  | `↑` / `↓`（無 Ctrl）| `UpData()` / `DownData()` | 目前列（`CurrentItem`）依 index 上/下移一列，並 `OnRowClick.InvokeAsync(...)`。**不 `preventDefault`** → Telerik 內建 NavigateUp/Down 仍把焦點列捲進可視範圍，兩者同步上/下移一列 |
  | `Ctrl+I` | `OnCtrlI()` | 新增列（唯讀 `_dataEditing=false` 時封鎖）|
  | `Ctrl+C` | `OnCtrlC()` | 觸發 `OnCopy` |
  | `Ctrl+D` | `OnCtrlD()` | 保留（目前 no-op）|

- ⚠️ **`↑`/`↓` 觸發的 `UpData`/`DownData` 呼叫 `OnRowClick` 時 `EventArgs` 為 `null`**（非 `MouseEventArgs`）。若頁面「選取只靠滑鼠」，`OnRowClick` handler 開頭要擋：`if (args.EventArgs is not MouseEventArgs mouse) return;`，否則鍵盤移動會誤選（記憶 `vnq_keyboard_nav_null_eventargs`）。
- **綁定時序（元件已處理好，頁面免管，排查用）**：① `DotNetObjectReference` 必須以「欄位」持有（`_keyRef`）——只 `Create(this)` 傳 JS 而不保存會被 GC 回收 → 之後 `invokeMethodAsync` 靜默失敗。② 綁定**不能只在 `firstRender` 綁一次**（首次 render 時 DOM/interop 可能未就緒）；元件用 `_keyBound` 旗標，每次 render 未綁就重試（`iksGridRegisterKey` 回 `false` 代表元素還沒進 DOM、下次再試），成功才停。③ 以「字串 id」(`_gridElId`) 而非 `ElementReference` 傳 JS，避免 marshaling 卡住。
- **master-detail「移動即切換明細」用 `OnRowClick`（目前標準做法）**：`IksGrid_vnq` 的 `OnRowClick` **滑鼠點列與鍵盤 `↑`/`↓`（`UpData`/`DownData`，見上表）都會觸發**，因此單一 `OnRowClick` 即可同時支援點擊與鍵盤切換明細，**不需 `RowKeyField`、不需 `OnRowFocus`**。
  - 寫法（SAL025 Dq1 明細）：grid 設 `OnRowClick="SwitchDq1Detail"`；handler 收 `GridRowClickEventArgs`、以 `args.Item is not Dqn row` 取列並防 null／型別不符：
    ```csharp
    private async Task SwitchDq1Detail(GridRowClickEventArgs args)
    {
        if (args.Item is not Dq1 row) return;
        if (_currentDq1 != null && row.ITM_Int == _currentDq1.ITM_Int) return;   // 同列略過，不重查、不打斷編輯
        _currentDq1 = row;
        // 只重繪子明細 View、不動本 grid（避免打斷 InCell 編輯；切格會自動提交前一格）
    }
    ```
  - ⚠️ **此處「不要」加通則 9 上面那條 `if (args.EventArgs is not MouseEventArgs) return;` 的 null 防呆**：那條是給「選取只靠滑鼠」的頁面擋鍵盤誤選用；master-detail 切換**正需要**鍵盤 `↑`/`↓`（EventArgs=null）也切換明細，加了反而讓鍵盤導覽失效。
- **列 focus 追蹤（`OnRowFocus` + `RowKeyField`）是另一套舊機制**（`IksRowFocusTracker` + `iksRowFocusInterop`）：focus（鍵盤或滑鼠）落到某列即回呼該列，不需點擊或進編輯（記憶 `grid_focus_masterdetail`）。**明細切換已改用上面的 `OnRowClick`**（更單純、不需 RowKeyField、與鍵盤導覽同源）；`OnRowFocus` 保留給「純 focus、不靠點擊」的特殊需求。⚠ `Rebind` 會重用 `<tr>`，元件在 `Rebind` 內已 `Focus.ResetAsync()` 清 lastTr（避免點回同位置被去重吃掉），頁面不用管。

### 9. 鍵盤控制（`IksGrid_vnq` 內建，master/明細通用）
- **快捷鍵綁在元件本身**（`window.iksGridRegisterKey`，`wwwroot/js/pageJs.js`），**頁面不用寫任何 JS**；掛在 grid 容器元素的 `keydown`，回呼元件的 `[JSInvokable]` 方法：

  | 按鍵 | 回呼 | 行為 |
  |------|------|------|
  | `↑` / `↓`（無 Ctrl）| `UpData()` / `DownData()` | 目前列（`CurrentItem`）依 index 上/下移一列，並 `OnRowClick.InvokeAsync(...)`。**不 `preventDefault`** → Telerik 內建 NavigateUp/Down 仍把焦點列捲進可視範圍，兩者同步上/下移一列 |
  | `Ctrl+I` | `OnCtrlI()` | 新增列（唯讀 `_dataEditing=false` 時封鎖）|
  | `Ctrl+C` | `OnCtrlC()` | 觸發 `OnCopy` |
  | `Ctrl+D` | `OnCtrlD()` | 保留（目前 no-op）|

- ⚠️ **`↑`/`↓` 觸發的 `UpData`/`DownData` 呼叫 `OnRowClick` 時 `EventArgs` 為 `null`**（非 `MouseEventArgs`）。若頁面「選取只靠滑鼠」，`OnRowClick` handler 開頭要擋：`if (args.EventArgs is not MouseEventArgs mouse) return;`，否則鍵盤移動會誤選（記憶 `vnq_keyboard_nav_null_eventargs`）。
- **綁定時序（元件已處理好，頁面免管，排查用）**：① `DotNetObjectReference` 必須以「欄位」持有（`_keyRef`）——只 `Create(this)` 傳 JS 而不保存會被 GC 回收 → 之後 `invokeMethodAsync` 靜默失敗。② 綁定**不能只在 `firstRender` 綁一次**（首次 render 時 DOM/interop 可能未就緒）；元件用 `_keyBound` 旗標，每次 render 未綁就重試（`iksGridRegisterKey` 回 `false` 代表元素還沒進 DOM、下次再試），成功才停。③ 以「字串 id」(`_gridElId`) 而非 `ElementReference` 傳 JS，避免 marshaling 卡住。
- **master-detail「移動即切換明細」用 `OnRowClick`（目前標準做法）**：`IksGrid_vnq` 的 `OnRowClick` **滑鼠點列與鍵盤 `↑`/`↓`（`UpData`/`DownData`，見上表）都會觸發**，因此單一 `OnRowClick` 即可同時支援點擊與鍵盤切換明細，**不需 `RowKeyField`、不需 `OnRowFocus`**。
  - 寫法（SAL025 Dq1 明細）：grid 設 `OnRowClick="SwitchDq1Detail"`；handler 收 `GridRowClickEventArgs`、以 `args.Item is not Dqn row` 取列並防 null／型別不符：
    ```csharp
    private async Task SwitchDq1Detail(GridRowClickEventArgs args)
    {
        if (args.Item is not Dq1 row) return;
        if (_currentDq1 != null && row.ITM_Int == _currentDq1.ITM_Int) return;   // 同列略過，不重查、不打斷編輯
        _currentDq1 = row;
        // 只重繪子明細 View、不動本 grid（避免打斷 InCell 編輯；切格會自動提交前一格）
    }
    ```
  - ⚠️ **此處「不要」加通則 9 上面那條 `if (args.EventArgs is not MouseEventArgs) return;` 的 null 防呆**：那條是給「選取只靠滑鼠」的頁面擋鍵盤誤選用；master-detail 切換**正需要**鍵盤 `↑`/`↓`（EventArgs=null）也切換明細，加了反而讓鍵盤導覽失效。
- **列 focus 追蹤（`OnRowFocus` + `RowKeyField`）是另一套舊機制**（`IksRowFocusTracker` + `iksRowFocusInterop`）：focus（鍵盤或滑鼠）落到某列即回呼該列，不需點擊或進編輯（記憶 `grid_focus_masterdetail`）。**明細切換已改用上面的 `OnRowClick`**（更單純、不需 RowKeyField、與鍵盤導覽同源）；`OnRowFocus` 保留給「純 focus、不靠點擊」的特殊需求。⚠ `Rebind` 會重用 `<tr>`，元件在 `Rebind` 內已 `Focus.ResetAsync()` 清 lastTr（避免點回同位置被去重吃掉），頁面不用管。

---

## 【範例程式碼】(SAL301 Dq1 明細)

```razor
<IksGrid_vnq @ref="SAL301Dq1" GridData="SAL301Dq1_GD" TItem="Dq1"
             ApiUrl="@_url" Columns="dq1EditerColumns" Table_Name="SAL301Dq1" Height="100%"
             ShowFrameHeader="true" ShowBuiltInToolbar="false"
             ShowAddButton="true" AddButtonEnabled="@_dqEditEnabled" HeaderButtons="@Dq1HeaderButtons"
             OnAdd="Dq1_OnAdd" OnUpdate="Dq1_UpdateHandler" OnDelete="Dq1_DeleteHandler"
             OnSelect="Dq1_OnSelect" OnBeforeEdit="Dq1_OnBeforeEdit" OnCheckBoxChange="Dq1_OnCheckBoxChange">
    <LeftColumnsTool>
        @* 針對該列的功能都放這 *@
            <GridCommandButton Icon="@("ti ti-copy")"   OnClick="@(a => Dq1Copy((Dq1)a.Item))" ShowInEdit="false" Enabled="@_dqEditEnabled" Title="拷貝" />
            <GridCommandButton Command="Edit"   Icon="@("ti ti-pencil")"  Enabled="@_dqEditEnabled" Title="修改" />
            <GridCommandButton Command="Delete" Icon="@("ti ti-trash")"   Enabled="@_dqEditEnabled" Title="刪除" />
            <GridCommandButton Command="Cancel" Icon="@("ti ti-circle-x")" ShowInEdit="true" Title="取消" />
            <GridCommandButton Icon="@("ti ti-tool")" OnClick="@(async a => await Bom((Dq1)a.Item))" ShowInEdit="false" Title="選配" />
    </LeftColumnsTool>
</IksGrid_vnq>
```
```csharp
private bool _dqEditEnabled => pageStatus is "Add" or "Edit";   // query/瀏覽態鎖定
private Task Dq1_OnAdd(Dq1 item) {                              // 「+」只觸發 OnAdd
    item.QUOTNO = current.QUOTNO; item.QUOTITM = NextItm(); item.uState = UState.Insert;   // uState 在此設
    return Task.CompletedTask;
}
```

## 【骨架程式碼】

```razor
<IksGrid_vnq @ref="{{Dqn}}" GridData="{{Dqn_GD}}" TItem="Dqn" ApiUrl="@_url"
             Columns="{{dqnCols}}" Table_Name="{{Dqn}}" Height="100%"
             ShowFrameHeader="true" ShowBuiltInToolbar="false"
             ShowAddButton="true" AddButtonEnabled="@_dqEditEnabled"
             OnAdd="Dqn_OnAdd" OnUpdate="Dqn_Update" OnDelete="Dqn_Delete">
    <LeftColumnsTool>
        @* 針對列：拷貝/Edit/Delete/Cancel/特殊(選配…)；Enabled 綁 _dqEditEnabled *@
    </LeftColumnsTool>
</IksGrid_vnq>
```
```csharp
private bool _dqEditEnabled => pageStatus is "Add" or "Edit";
private Task Dqn_OnAdd(Dqn item) { item.{{FK}} = current.{{PK}}; item.{{ITM}} = NextItm(); item.uState = UState.Insert; return Task.CompletedTask; }
private async Task Dqn_Update(GridCommandEventArgs a) { /* ⚠ 勿呼叫 ExitEditModeAsync（會遞迴回 OnUpdate → StackOverflow）；直接更新 GD + 計算送後端 */ }
private async Task Dqn_Delete(GridCommandEventArgs a) { /* 直接呼叫 API 刪除，與存檔分開 */ }
// Save 主流程：所有 Insert 全送 → 所有 Update 全送；主鍵前端+後端雙重檢查；主+明細同 transaction
```

---

## B301Base → 明細對應

`FormCreate` 5 個 `AddDetail`（先看 DFM 有無 grid，nil 者問操作者，但**物件一律建立**）：

| Delphi | 明細鍵 | grid | 去向 |
|--------|--------|------|------|
| Dq1 | QUOTITM | DDBGrid | Tab「明細」InCell |
| Dq2 | ITEM | DDBGrid2 | Tab「外銷資料」grid |
| DqSPEC | SITM | nil | 規格明細 **Window** |
| Dq3 | QUOTITM;SITM | nil | 背景關聯（DTO 仍建立） |
| Dq4 | QUOTNO;ITM | DDBGrid4 | Tab「備註資料」grid |

## 指路
- 連動/計算 → `details/field-change.md`
- 存檔/transaction → `details/crud-handlers.md`
- DTO（明細 partial : EFModel）→ `details/dto-display.md`
- EditorTemplate → `details/editor-template.md`
