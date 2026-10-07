# 範本 ①：主檔明細 堆疊式 + 模式切換（master-detail）── 大骨架

> 適用：**主表 + 多組明細**。上下**垂直堆疊**（`.cd-stack-top` = 主表清單/編輯表單、`.cd-stack-bottom` = 明細；**不用 `TelerikSplitter`**，`.cd-body` 自動捲動），工具列 `iks-mode-switch` 切換 瀏覽/表單；明細以 `iks-mode-switch` 膠囊 + `@if` 面板切換（取代 TabStrip）。
> 版面標準：for_github `SAL301`（美工版）＋ Mode C 堆疊式（見 `iks-scroll-modes` skill）；邏輯來源：Delphi `B301`→**`B301Base`**（繼承鏈，見 SKILL 來源讀取原則）。
> 明細用 `IksGrid_vnq` InCell（`details/grid-incell.md`）。

---

## 怎麼用這份骨架（漸進式揭露）

只放**大骨架**（畫面標籤 + `@code` 欄位 + 生命週期擺放位置），每區橫幅帶 `詳細規則 → details/xxx.md`，要動哪區才讀。

| 區 | 位置 | 詳細規則檔 |
|----|------|-----------|
| A | 頁首宣告 + 狀態（多 `ActiveTabId`/`ActiveDetailTabId`/`_showDetail`） | `details/page-shell.md` |
| B | 工具列（模式膠囊 + **主檔全操作**，CRUD→查詢→延伸） | `details/toolbar.md` |
| C | 主檔區 `.cd-stack-top`：主檔清單（query）/ 主表單（edit） | `details/grid-virtual.md`、`details/edit-window.md` |
| D | 進階篩選 Popup（SQL WHERE 條件）；若有 checkbox 類**顯示/動作開關**（改前端不需重查）→ `details/detail-display-settings.md` | `details/popup-filter.md` |
| E | 明細區 `.cd-stack-bottom`：明細切換膠囊 + `@if` 面板（取代 TabStrip） | — |
| F | 各明細 InCell grid（含疊放式主檔欄位） | `details/grid-incell.md` ⭐ |
| G | 按鈕控制（pageStatus × ActiveTabId 雙態） | `details/btn-control.md` |
| H | CRUD（主+明細 transaction） | `details/crud-handlers.md` |
| I | DTO（主 Mqy + 各 Dqn，**含無 grid 的背景明細**） | `details/dto-display.md` |
| J | 連動 / 計算（一律後端） | `details/field-change.md` |
| K | 特殊 Window（規格明細/選配/拷貝/匯入…）；附件 PDF → `details/attachment.md` | Phase 6 |

> 控件選擇一律先過 `details/input-component-choice.md`。
> ⚠️ **遇到 Delphi 封裝函式**（ERPFunc/SALFunc/MPSFunc/StkFunc 等共用庫呼叫）：先查 `details/delphi-func-lookup.md` 確認 C# 對應方法名與狀態，再查 `details/shared-functions.md` 取得處理策略（已完成/待轉/作廢/佔位規則）。

---

## 大骨架（單一 .razor，結構同 for_github SAL301）

```razor
@* ══ A. 頁首宣告 ══  → details/page-shell.md *@
@page "/{{MODULE}}/{{FORM}}"
@inherits IksPageBase
@inject iksFoundationCore gQL
@inject TokenStorage Token
<PageTitle>({{FORM}}){{頁面標題}}</PageTitle>
<TelerikLoaderContainer Visible="@IsPageLoading" Text="載入中..." Size="@ThemeConstants.Loader.Size.Large" />

@* ══ Mode C Nested（堆疊式，主檔明細專用）══  詳細規則 → iks-scroll-modes skill
   ⚠ 不用 TelerikSplitter（固定 px Splitter 會撐捲軸→Telerik resize 在電路連上前回呼→卡載入）。
   主檔 .cd-stack-top + 明細 .cd-stack-bottom 垂直堆疊；.cd-body 為捲動擁有者
   （flex-column + overflow-y:auto，內容過高自動出捲軸）；
   主檔 .iks-master-frame 掛確定高度（inline height:@_mqyHeight）、grid 用 Height="100%"（原始 flex 鏈）；
   明細 grid 各自固定 px。
   ⚠ 單檔範本不套此 class（見 single-file.md）。 *@
<div id="local-content" class="iks-scroll-layout iks-scroll--nested">

    @* ══ B. 工具列 ══  → details/toolbar.md（明細模式：主檔全操作，順序 模式→CRUD→查詢→延伸）*@
    <div class="toolbar toolbar-field">
        <Toolbar OnAction="HandleToolbar">
            @* 模式切換膠囊：瀏覽(query)/表單(edit) *@
            <ToolbarGroup>
                <div class="iks-mode-switch" role="tablist" aria-label="檢視模式">
                    <button type="button" class="iks-mode-option @(ActiveTabId == "query" ? "is-active" : "")"
                            disabled="@(!_ReadEnabled)" role="tab" aria-selected="@(ActiveTabId == "query")"
                            @onclick='() => HandleToolbar("Read")'><i class="ti ti-eye"></i><span>瀏覽</span></button>
                    <button type="button" class="iks-mode-option @(ActiveTabId == "edit" ? "is-active" : "")"
                            disabled="@(!_DetailReadEnabled)" role="tab" aria-selected="@(ActiveTabId == "edit")"
                            @onclick='() => HandleToolbar("DetailRead")'><i class="ti ti-edit"></i><span>詳細資料</span></button>
                </div>
            </ToolbarGroup>
            @* 資料維護 CRUD *@
            <ToolbarGroup>
                <ToolbarButton Action="Add"    Enabled="@_AddEnabled"    FontIcon="ti ti-plus"          Title="新增" />
                <ToolbarButton Action="Copy"   Enabled="@_CopyEnabled"   FontIcon="ti ti-copy"          Title="拷貝" />
                <ToolbarButton Action="Edit"   Enabled="@_EditEnabled"   FontIcon="ti ti-pencil"        Title="修改" />
                <ToolbarButton Action="Save"   Enabled="@_SaveEnabled"   FontIcon="ti ti-device-floppy" Title="存檔" />
                <ToolbarButton Action="Cancel" Enabled="@_CancelEnabled" FontIcon="ti ti-circle-x"      Title="取消" />
                @* {{作廢等狀態操作}} *@
            </ToolbarGroup>
            @* 查詢 *@
            <ToolbarGroup>
                <ToolbarButton Action="Query"  Enabled="@_QueryEnabled"  FontIcon="ti ti-search"        Title="查詢" />
                @* {{搜尋/明細等}} *@
            </ToolbarGroup>
            @* 延伸功能（個別特殊操作，依 DFM/pas 特殊按鈕）*@
            <ToolbarGroup>
                @* {{<ToolbarButton Action="Import"…>匯入</ToolbarButton> / 規格明細 / 電子郵件…}} *@
            </ToolbarGroup>
        </Toolbar>
    </div>
    <TelerikTooltip TargetSelector=".toolbar-field [title]" Position="@TooltipPosition.Bottom" />

    @* ══ 主體：主檔/明細垂直堆疊（不用 Splitter）══
       .cd-body = 捲動擁有者（flex-column + overflow-y:auto）；兩區各自然高度堆疊。 *@
    <div class="cd-body">

          @* ── 主檔區：C 主要視窗 ── *@
          <div class="cd-stack-top">

              @* ══ C-query. 主檔清單 ══  → details/grid-virtual.md ＋ D 篩選 → details/popup-filter.md *@
              @if (ActiveTabId == "query")
              {
                @* ⚠ 堆疊模式：frame 掛確定高度（inline height:@_mqyHeight），grid 用 Height="100%" 走原始 flex 鏈。
                   勿把 _mqyHeight 直接給 grid Height —— Virtual 需祖先鏈有確定高度，否則列渲染成空白（DOM 在、可點、但看不到）。 *@
                <div class="iks-master-frame" style="height:@_mqyHeight">
                  <div class="iks-master-grid">
                    <IksGrid_Virtual @ref="{{Grid}}" TItem="Mqy" ApiName="{{form}}_M_Query" ApiUrl="@_url"
                                     Table_Name="{{Grid}}" Columns="{{ColConfig}}" WhereParameters="{{parameter}}"
                                     sortKey="{{KEY}}" RowKeyField="{{KEY}}" Height="100%" ShowAdd="false"
                                     ShowFrameHeader="true" ShowFilterButton="true" ShowBuiltInToolbar="false"
                                     FilterAnchorClass="mqy-filter-popup-target" OnFilterClick="ToggleFilterPanel"
                                     OnHeightChanged="OnMqyHeightChanged"
                                     OnRowClick="OnMqyRowClick">
                        <LeftColumnsTool></LeftColumnsTool>
                    </IksGrid_Virtual>
                  </div>
                  <TelerikPopup @ref="@FilterPopupRef" AnchorSelector=".mqy-filter-popup-target">
                    @* {{iks-filter-popup：head / iks-filter-grid 篩選欄位 / 清除·查詢}} *@
                  </TelerikPopup>
                </div>
              }

              @* ══ C-edit. 主表單 ══  → details/edit-window.md（欄位順序 DFM Top／控件決策樹／連動）*@
              @if (ActiveTabId == "edit")
              {
                <div class="container-fluid edit-field">
                  <div class="iks-edit-grid">
                    @* {{主檔欄位：iks-edit-row 多列；Enabled 依 pageStatus；主鍵唯讀；Required 由操作者}} *@
                  </div>
                </div>
              }
          </div>

          @* ── 明細區：D 明細（_showDetail 控制顯示）── *@
          @if (_showDetail)
          {
            <div class="cd-stack-bottom">

                @* ══ E. 明細切換膠囊（同上方瀏覽/表單，取代 TabStrip）══
                   切某頁需載入資料時（如群組信用）在 SetDetailTab 內分派。 *@
                <div class="iks-mode-switch iks-detail-switch" role="tablist" aria-label="明細切換">
                    <button type="button" class="iks-mode-option @(ActiveDetailTabId == "d1" ? "is-active" : "")"
                            role="tab" aria-selected="@(ActiveDetailTabId == "d1")" @onclick='() => SetDetailTab("d1")'>{{明細1}}</button>
                    @* {{更多膠囊；可 @if 控制 Visible}} *@
                </div>

                @* ══ F. 明細面板（@if 依 ActiveDetailTabId 顯示，取代 TabStripTab）══  → details/grid-incell.md
                   明細 grid 用固定 px Height（堆疊模式無 pane 高度可填 100%）。 *@
                <div class="iks-detail-body">
                  @if (ActiveDetailTabId == "d1")
                  {
                    <div class="iks-detail-panel">
                      @* HighlightEditableCells 只在「可編輯欄 ≤ 全欄 1/3」時才加 → details/grid-incell.md 通則 7 *@
                      <IksGrid_vnq @ref="{{Dq1}}" GridData="{{Dq1_GD}}" TItem="Dq1" ApiUrl="@_url"
                                   Columns="{{dq1Cols}}" Table_Name="{{Dq1}}" Height="250px"
                                   ShowFrameHeader="true" ShowBuiltInToolbar="false"
                                   ShowAddButton="true" AddButtonEnabled="@_dqEditEnabled" HeaderButtons="@Dq1HeaderButtons"
                                   HighlightEditableCells="true"
                                   OnAdd="Dq1_OnAdd" OnUpdate="Dq1_Update" OnDelete="Dq1_Delete">
                          <LeftColumnsTool>
                              @* 針對列：拷貝/Edit/Delete/Cancel/特殊；Enabled 綁 _dqEditEnabled *@
                          </LeftColumnsTool>
                      </IksGrid_vnq>
                      @* 有明細加總才放（Delphi 唯讀 ButtonEdit 合計）：值後端算、純顯示 → details/css-layout.md
                      <div class="iks-total-bar">
                        <span class="iks-total-cell"><span class="iks-total-label">{{合計名}}</span><span class="iks-total-value">@{{_sumX}}.ToString("#,##0.######")</span></span>
                      </div> *@
                    </div>
                  }

                  @* 疊放式明細面板（主檔欄位 + grid）：iks-detail-stacked
                  @if (ActiveDetailTabId == "d2")
                  {
                    <div class="iks-detail-panel">
                      <div class="container-fluid edit-field iks-detail-stacked">
                        <div class="iks-edit-grid"> {{主檔級欄位，綁 current 主檔}} </div>
                        <IksGrid_vnq @ref="{{Dq2}}" ... Height="250px" />
                      </div>
                    </div>
                  } *@
                </div>
            </div>
          }
    </div>
</div>

@* ══ K. 特殊 Window（規格明細/選配/拷貝帶明細/匯入…）＋ 附件 PDF ══ Phase 6 *@
<MessageBox @ref="MsgBox" />

@code {
    @* ── A. 狀態 ──  details/page-shell.md ── *@
    protected override string FomId => "{{FORM}}";
    private string ActiveTabId = "query";            // "query" | "edit"（模式膠囊）
    private string ActiveDetailTabId = "d1";          // 明細頁籤
    private bool _showDetail = true;                   // 明細區顯示
    private string _mqyHeight = "250px";               // 主檔 frame 高度（由「設定高度」combo 控制）
    private string pageStatus = "query";              // query|Add|Edit|View|Copy
    private MessageBox MsgBox = default!;

    @* ── B/G. 工具列旗標 ──  details/btn-control.md ── *@
    private bool _ReadEnabled, _DetailReadEnabled, _AddEnabled, _CopyEnabled,
                 _EditEnabled, _SaveEnabled, _CancelEnabled, _QueryEnabled;
    private bool _dqEditEnabled => pageStatus is "Add" or "Edit";   // 明細編輯鎖定

    @* ── C. 主檔清單 ──  details/grid-virtual.md ── *@
    private IksGrid_Virtual<Mqy>? {{Grid}};
    private Mqy? MqySelect;
    private Dictionary<string, object> {{parameter}} = new();

    @* ── D. 篩選 ──  details/popup-filter.md ── *@
    private TelerikPopup? FilterPopupRef;
    private Mqy {{Filter}} = new();

    @* ── C-edit. 主表單 ──  details/edit-window.md ── *@
    private Mqy current{{Master}} = new();

    @* ── F. 明細（每組 ref + GridData；含無 grid 背景明細仍建 DTO）──  details/grid-incell.md ── *@
    private IksGrid_vnq<Dq1>? {{Dq1}};
    private List<Dq1> {{Dq1_GD}} = new();
    // {{Dq2/Dq3/Dq4… 各一份；nil-grid 背景明細只留 List}}

    @* ── 初始載入 ── firstRender 首讀主檔 ＋ 每次渲染同步明細編輯鎖 ── *@
    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        await base.OnAfterRenderAsync(firstRender);
        if (firstRender) {{Grid}}?.Rebind();
        @* ⚠ 膠囊切換用 @if 重建明細 grid，重建的 IksGrid_vnq `_dataEditing` 預設 true → 瀏覽態誤可編輯。
           每次渲染依 _dqEditEnabled 冪等同步各明細 grid 全域編輯閘門（EnterEdit/ExitEdit 狀態未變即 no-op，比照 STK001）。
           ⚠ 別只在 SetDetailTab handler 內 SetColumnEditable：會被未 await 的 Rebind 重置 ColKey 蓋掉（SAL044 踩過）。*@
        if ({{Dq1}} != null) { if (_dqEditEnabled) {{Dq1}}.EnterEdit(); else await {{Dq1}}.ExitEdit(); }
        @* {{其餘明細 grid 同樣一行}} *@
    }

    @* ── B. 工具列分派 ──  details/toolbar.md ──（Read/DetailRead 切模式；Add/Copy/Edit/Save/Cancel/Query…）*@
    private async Task HandleToolbar(string action) { /* switch … ; 尾端 btnControl() */ }
    private void SetDetailTab(string id) => ActiveDetailTabId = id;
    // 明細只顯示/隱藏，不動高度（堆疊模式 cd-body 自動捲動）；高度改由 combo 單一控制
    private void ToggleDetail() => _showDetail = !_showDetail;
    // 「設定高度」combo 選值 → 更新主檔 frame/堆疊高度（grid Height="100%" 跟著長）
    private void OnMqyHeightChanged(string newHeight) => _mqyHeight = newHeight;

    @* ── G. 按鈕控制（pageStatus × ActiveTabId 雙態）──  details/btn-control.md ── *@
    private async Task btnControl() { }

    @* ── H. CRUD（主+明細同 transaction；換 Tab/Add/Save/Cancel 明細顯式 Rebind）──  details/crud-handlers.md ── *@
    private async Task Save() { }   private async Task Delete() { }  private Task Query() { }
    private async Task Add() { }    private async Task Edit() { }    private async Task Cancel() { }

    @* ── F. 明細 InCell handlers（每組一套）──  details/grid-incell.md ──
       OnAdd 設 uState=Insert；刪除直接呼叫 API；存檔 Insert 全送再 Update 全送；主鍵前+後端雙重檢查 *@
    private Task Dq1_OnAdd(Dq1 item) { item.uState = UState.Insert; return Task.CompletedTask; }
    private async Task Dq1_Update(GridCommandEventArgs a) { }
    private async Task Dq1_Delete(GridCommandEventArgs a) { }

    @* ── F. 明細鎖定有「兩層」（統一用 grid API；比照 SAL025/MPS021）──
       ① 哪些欄可編（per-column）＝ ColKey，用 SetColumnEditable（LockDqGridColumns/UnlockDqGridColumns，下方）。
       ② 這個 grid 整體能不能編（全域閘門）＝ _dataEditing，用 grid.EnterEdit()/ExitEdit()；_dataEditing 預設 true。
       明細平常唯讀、Add/Edit 才可編輯。①掛點：明細載入/Rebind 後 + Cancel → Lock；Add/Copy/Edit → Unlock。
       ⚠ IksGrid.Rebind() 會「重置」ColKey（回到 !Editable＝預設可編輯，GridColumnConfig.Editable 預設 true）
         → 每次載入/重綁後都要重新套用（多明細/延遲載入頁把重綁點統一改 async，尾端 await ApplyDqLock）。
       ⚠ SetColumnEditable(field, locked)：locked=true→鎖定唯讀、false→可編輯（參數即 ColKey）。
       ⚠ 膠囊切換 @if 重建 grid → 兩層都預設可編；②的全域閘門在 OnAfterRenderAsync 每次渲染冪等同步最穩（見上方 OnAfterRenderAsync），
         別只靠切換 handler 內 SetColumnEditable（會被未 await 的 Rebind 蓋掉，SAL044 踩過）。
       淘汰 OnBeforeEdit 回呼設 ColKey（只在進儲存格瞬間才改、平常渲染仍可編輯）。*@
    private async Task ApplyDqLock()  // 依 pageStatus 自動鎖/解（多明細/延遲載入頁掛在每個載入點最省事）
        { if (pageStatus is "Add" or "Edit") await UnlockDqGridColumns(); else await LockDqGridColumns(); }
    private async Task LockDqGridColumns()   => await SetDqColumnsLocked(true);
    private async Task UnlockDqGridColumns() => await SetDqColumnsLocked(false);
    private async Task SetDqColumnsLocked(bool locked)
    {   // 每組明細 grid × 其可編輯欄逐一套用（唯讀對照 grid 欄位 Editable=false 會被 .Where 濾掉，不受影響）
        foreach (var c in {{dq1Cols}}.Where(kv => kv.Value.Editable).Select(kv => kv.Key)) if ({{Dq1}} != null) await {{Dq1}}.SetColumnEditable(c, locked);
        // {{其餘明細 grid 同樣一行}}
    }

    @* ── J. 連動/計算（一律後端）──  details/field-change.md ── *@
    @* ── I. DTO ──  details/dto-display.md ──
       主：partial Mqy : {{EFModel}}, IDisplayResolvable
       每組明細：partial Dqn : {{EFModelD}}, IDisplayResolvable（含 uState；背景明細也要建）*@
}
```

```text
L. CSS —— → details/css-layout.md：cd-body（flex-column + overflow-y:auto）/ cd-stack-top /
   cd-stack-bottom / iks-mode-switch（含 iks-detail-switch）/ iks-detail-body / iks-detail-panel /
   iks-detail-stacked …進 app.css（記憶 shared_css_appcss）。
   ⚠ 堆疊模式下主檔 `.iks-master-frame` 掛 inline `height:@_mqyHeight`（確定高度）+ grid `Height="100%"`；
   勿把 frame/grid 改成 auto 高度（Virtual 會算不出視窗、列渲染成空白但可點）。見 iks-scroll-modes skill。
```

---

## 與單檔範本的關鍵差異

1. **模式膠囊 `iks-mode-switch`**（瀏覽 query / 表單 edit）在工具列 ToolbarGroup。
2. **主檔/明細垂直堆疊（不用 `TelerikSplitter`）**：`.cd-stack-top` = 主檔清單/主表單（隨 `ActiveTabId`）、`.cd-stack-bottom` = 明細（`_showDetail` 控制）；`.cd-body` 為捲動擁有者，過高自動出捲軸。
3. **工具列擺全部主檔操作**（含存檔/取消），順序 模式→CRUD→查詢→延伸（`details/toolbar.md`）。
4. **明細 = `IksGrid_vnq` InCell**，多組用切換膠囊（`iks-mode-switch`）+ `@if` 面板切換（**取代 `TabStrip`**，`details/grid-incell.md`）；明細 grid 用固定 px Height；**只有少數欄可編輯時加 `HighlightEditableCells="true"`**（門檻見 `details/grid-incell.md` 通則 7）。⚠ `_dqEditEnabled` 只鎖「列指令鈕/新增鈕」，**欄位本身的可編輯要另用 `SetColumnEditable` 鎖**（見第 11 點）。
5. **疊放式明細 Tab**（`iks-detail-stacked`）：上半主檔欄位（綁 current 主檔）+ 下半明細 grid。
6. **金額加總（Delphi 唯讀 ButtonEdit）不做成表單欄位**：明細合計→明細 grid 下方 `.iks-total-bar`；主檔清單合計→`IksGrid_Virtual` 的 `FrameHeaderExtra`（`details/grid-virtual.md`）。值一律後端算、前端純顯示。
7. **btnControl 是 pageStatus × ActiveTabId 雙態**；換態時明細顯式 `Rebind`（記憶 `detail_rebind_add_save`）。
8. **存檔＝主表 + 各明細同一 transaction，全成才 commit**；主鍵前+後端雙重檢查。
9. **明細對應非 1:1**：`AddDetail` 先看 DFM 有無 grid，無者問操作者，但**背景明細 DTO 仍要建立**。
10. **Mode C 巢狀捲動（堆疊式）**：`#local-content` 加 `iks-scroll-layout iks-scroll--nested`；**不用 Splitter**，`.cd-body`（flex-column + overflow-y:auto）為捲動擁有者、`.cd-stack-top/-bottom` 垂直堆疊；主檔 `.iks-master-frame` 掛確定高度 `style="height:@_mqyHeight"`、grid 用 `Height="100%"`（Virtual 需祖先鏈確定高度，直接給 grid `@_mqyHeight` 會列空白）、明細 grid 固定 px。⚠ 舊 for_github 固定 px Splitter 機制已淘汰（撐捲軸→Telerik resize 在電路連上前回呼→卡載入）。**單檔範本不套**。細節見 `iks-scroll-modes` skill。
11. **明細欄位鎖定（瀏覽唯讀 / Add·Edit 才可編輯）＝統一用 `grid.SetColumnEditable(field, locked)`**（`locked=true` 鎖定、`false` 可編輯；即設 `iksBaseClass.ColSetting.ColKey`）。寫一對 `LockDqGridColumns()/UnlockDqGridColumns()`（迴圈各明細 ColConfig 的 `Editable` 欄逐一套用），多明細/延遲載入頁用 `ApplyDqLock()` 依 `pageStatus` 自動選。**掛點**：明細載入/Rebind 後 + Cancel → Lock；Add/Copy/Edit → Unlock。⚠ **`IksGrid.Rebind()` 會重置欄位可編輯性**（回到 `!Editable`，而 `GridColumnConfig.Editable` 預設 `true`）→ **每次載入/重綁後都要重新套用**（把重綁點改 async、尾端 `await ApplyDqLock()`）。已淘汰 `OnBeforeEdit` 設 ColKey 的舊法。⚠ `ColSetting` 型別須限定 `iksBaseClass`（與 `IKSERPSHARE.Models.ColSetting` 同名，兩者都 import 會 CS0104）。細節見記憶 `reference_grid_onbeforeedit_colkey_lock`。

> Delphi 邏輯在 base（`B301Base`），繼承鏈先問操作者（SKILL 來源讀取原則）。
