---
name: iks-scroll-modes
description: IKSERP Blazor 頁面多層捲動版型 A/B/C（Contained/Page/Nested）的設定規範。當使用者要在 SAL301 等頁面套用/切換捲動模式、決定外層 overflow、pane 高度、Splitter 總高度、IksGrid Virtual 策略，或問「三種版型差別 / 捲動怎麼設 / 頁面出現雙卷軸」時觸發。搭配 page-migration 的 css-layout 使用。
---

# IKSERP 多層捲動版型 A / B / C 設定規範

> 技術棧：Blazor + `IksGrid_*`（TelerikGrid）。A/Contained 可用 `TelerikSplitter`（`Height="100%"`）；**C/Nested 改堆疊式，不用 Splitter**。
> **CSS 一律進 `wwwroot/app.css`**（勿散落頁面 `<style>`；IksPageBase 無法放 style，記憶 `shared_css_appcss`）。
> Mode class 掛在頁面自己的 **`#local-content`**，**不要**放到共用 `.app-main` / `#page-content`（會污染其他頁面與 Dialog）。
> 版面 class（`cd-body`/`cd-stack-top`/`cd-stack-bottom`）沿用 `page-migration` master-detail 既有命名。
>
> **範本分野（page-migration）**：**一般單檔（single-file）一律不套 Mode C** —— 外層就是純 `<div id="local-content">`，Grid 自己捲。**Mode C（Nested）只屬於主檔明細（master-detail）**。誤把 Mode C 套到單檔會讓外層被固定高度撐開（如 1200px 空白）。
> **Mode C 機制＝堆疊式（不用 `TelerikSplitter`）**：主檔 `.cd-stack-top` + 明細 `.cd-stack-bottom` 垂直堆疊，由 **`.cd-body` 捲動**（`flex-column + overflow-y:auto`，過高自動出捲軸）；主檔清單 `.iks-master-frame` 掛**確定高度**（inline `height:@_mqyHeight`）、grid 用 `Height="100%"`、明細 grid 各自固定 px。**不再用 `--iks-layout-total-height` CSS 變數**。
> ⚠ **舊 for_github 固定 px Splitter 機制（Height=980px）已淘汰**：固定高 Splitter 比 flex `.cd-body` 高→撐出捲軸→觸發 Telerik ResizeObserver `onResize→close` 在 SignalR 電路 **Connected 前**回呼 .NET→拋 `Cannot send data if the connection is not in the 'Connected' State`→互動 bootstrap 中斷→**卡在載入中**（Splitter 元件無罪，衝突點＝固定 px 高 vs. flex 版面）。

## 觸發時機

在 SAL301 等主檔明細頁套用/切換捲動模式、決定外層 overflow、區塊高度（A=pane / C=`.cd-stack-*` frame）、總高度來源、IksGrid Virtual 策略；或排查「頁面出現雙卷軸 / 內層被撐破 / Virtual Grid 空白列」。

## 核心判準（先問這兩題）

差別**不是**「有沒有寫 `overflow:auto`」，而是：
1. **誰擁有垂直捲動權** —— 外層 `#local-content` / pane / Grid 三者只該有明確的擁有者。
2. **Grid 是否維持 Virtual scrolling** —— Virtual Grid **必須有有限高度**，否則會空白列/計算錯誤。

選一個 Mode，底層要**同時**決定四件事：外層 overflow、區塊高度（A=pane / C=`.cd-stack-*` frame）、總高度來源、Grid 捲動模式。缺一就會雙卷軸或撐破。

## 快速對照

| 面向 | A｜Contained（預設） | B｜Page | C｜Nested（堆疊式） |
|------|------|------|------|
| 外層 `#local-content` | `overflow:hidden` 不捲 | `overflow-y:auto` 唯一捲動者 | `overflow:hidden`；改由 **`.cd-body` 捲**（`flex-column + overflow-y:auto`） |
| 版面容器 | `TelerikSplitter`（可拖拉）pane `height:100%` | 自然 `height:auto` stack | **不用 Splitter**；`.cd-stack-top/-bottom` 垂直堆疊（自然高度） |
| Grid | 各自捲、維持 Virtual `Height="100%"` | 不捲、**取消 Virtual** | 主檔 frame 掛確定高、grid `Height="100%"`；明細 grid 固定 px |
| 總高度 | = 視窗可用高度 | 隨內容增高 | 兩區堆疊自然高度，超過 `.cd-body` 才出捲軸 |
| 落地 | 純 CSS（Splitter Height=100%；SAL013/024/025/041） | 需改 IksGrid 元件 | 堆疊 + `.cd-body` overflow-y:auto（SAL021 落地） |
| 適用 | 主檔/明細常態頁 | 表單、報表、資料量少 | 主檔明細、內容高度可能超出視窗 |

## 決策路徑

1. 大量資料 / 必須 Virtual？ 是 → A 或 C；否 → 可選 B
2. pane 必須一直保有操作高度？ 是 → A 或 C；否 → B
3. pane 總高度可能超過螢幕？ 是 → C；否 → A
4. 可能到三層？ 用 Region list + `TotalHeight`，**不新增特例 class**

---

## A — Contained（外層固定，pane 各自捲）※預設

外層鎖在視窗可用高度並 `overflow:hidden`；Splitter 分配上下區；每個 IksGrid 自己擁有卷軸（Virtual + `Height="100%"`）。視窗縮小外層不冒卷軸。SAL301 現況最接近此模式。

```css
/* → wwwroot/app.css */
.iks-scroll-layout { display:flex; flex-direction:column; height:100%; min-height:0; }
.iks-scroll--contained { overflow:hidden; }
.iks-scroll--contained .cd-body { flex:1 1 auto; min-height:0; overflow:hidden; }
/* region 必須是 flex column，內層 .iks-master-frame(flex:1 1 auto) 才撐得起來 */
.iks-scroll--contained .iks-scroll-region { display:flex; flex-direction:column; width:100%; height:100%; min-height:0; overflow:hidden; }
```

驗收：視窗縮小外層不出現卷軸；上下 Grid 各自捲、resize 後仍填滿；所有 flex 父層保留 `min-height:0`。

## B — Page（只由整頁外層捲）

所有內容依自身高度排開，只有 `#local-content` 捲；pane/Grid 都不捲。

> ⚠️ **關鍵限制**：`IksGrid_Virtual` / `IksGrid_vnq` 目前硬編碼 Virtual，Virtual 需有限高度 →
> **真正的 B 不能只關 CSS overflow**，必須讓 IksGrid 的 `ScrollMode`/`Height` 由參數/Context 決定。

```razor
@* 以 vertical stack 取代 Splitter，勿用 CSS 硬壓 Splitter 高度 *@
<div id="local-content" class="iks-scroll-layout iks-scroll--page">
  <div class="cd-body iks-scroll-stack">
    <section class="iks-scroll-region">@TopContent</section>
    <section class="iks-scroll-region">@BottomContent</section>
  </div>
</div>
```

```razor
@* IksGrid 元件：Virtual 與 Height 改由 Context 決定 *@
<TelerikGrid ScrollMode="@EffectiveScrollMode" Height="@EffectiveHeight" RowHeight="@GridRowHeight">...</TelerikGrid>
@code {
  [Parameter] public GridScrollMode? ScrollMode { get; set; }
  [Parameter] public string? Height { get; set; } = "500px";
  [CascadingParameter] public IksScrollContext? ScrollContext { get; set; }
  private GridScrollMode EffectiveScrollMode =>
      ScrollMode ?? ScrollContext?.GridMode ?? GridScrollMode.Virtual;
  private string? EffectiveHeight =>
      EffectiveScrollMode == GridScrollMode.Virtual ? Height : null;
}
```

效能規則：只給資料量有限或已有 Server paging 的頁面，勿一次渲染數萬筆 DOM。
驗收：上下區無卷軸、滾輪只移動 `#local-content`；Grid 無空白列/截斷；大量資料頁已分頁。

## C — Nested（堆疊式：cd-body 捲動 + 主/明細垂直堆疊，不用 Splitter）

外層 `#local-content` 不捲，改由 **`.cd-body` 捲動**（`flex-column + overflow-y:auto`）；主檔 `.cd-stack-top` + 明細 `.cd-stack-bottom` 依內容**自然高度垂直堆疊**，兩區高度總和超過 `.cd-body` 可用高度時，就由 cd-body 自動出捲軸巡覽。主檔清單的 **`.iks-master-frame` 掛確定高度**（inline `style="height:@_mqyHeight"`），內部 Virtual grid 用 **`Height="100%"`** 走原始 flex 鏈；明細 grid 各自固定 px。明細分頁用切換膠囊 + `@if` 面板（**取代 `TelerikTabStrip`**）。**只用於主檔明細**；單檔不套。

> ⚠ **不要把 `_mqyHeight` 直接給 grid `Height`**：Virtual 捲動需**祖先鏈有確定高度**才算得出視窗；若 frame/grid 是 auto 高度，列會**渲染成空白（DOM 在、可點、但看不到）**。正解＝frame 掛確定高度 + grid `Height="100%"`。

> ⚠ **不要用 `TelerikSplitter` 掛固定像素 Height**：固定高 Splitter 比 flex `.cd-body` 高→撐出捲軸→Telerik `onResize→close` 在電路 Connected 前回呼 .NET→拋 `Cannot send data...`→卡載入。若要 Splitter 外觀，只能用 `Height="100%"`（＝ Mode A/Contained，pane 固定填滿、不溢出）。

```razor
@* 只在 #local-content 掛 class；主/明細垂直堆疊，cd-body 捲動 *@
<div id="local-content" class="iks-scroll-layout iks-scroll--nested">
  <div class="toolbar toolbar-field">...</div>
  <div class="cd-body">
    <div class="cd-stack-top">
      @* 主檔清單：frame 掛確定高度，grid 用 Height="100%"（原始 flex 鏈，Virtual 才畫得出列）*@
      <div class="iks-master-frame" style="height:@_mqyHeight">
        <div class="iks-master-grid">
          <IksGrid_Virtual ... Height="100%" />
        </div>
      </div>
    </div>
    @if (_showDetail)
    {
      <div class="cd-stack-bottom">
        @* 明細切換膠囊（取代 TabStrip）*@
        <div class="iks-mode-switch iks-detail-switch" role="tablist">
          <button class="iks-mode-option @(ActiveDetailTabId == "d1" ? "is-active" : "")" @onclick='() => SetDetailTab("d1")'>...</button>
        </div>
        <div class="iks-detail-body">
          @if (ActiveDetailTabId == "d1") { <div class="iks-detail-panel"><IksGrid_vnq ... Height="250px" /></div> }
        </div>
      </div>
    }
  </div>
</div>
```

```css
/* → wwwroot/app.css：外層不捲，改由 cd-body 捲動；主/明細堆疊 */
#local-content.iks-scroll--nested { overflow: hidden; }
#local-content.iks-scroll--nested .cd-body {
    flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;
    overflow-y: auto; overflow-x: hidden; gap: 8px;
}
#local-content.iks-scroll--nested .cd-stack-top    { flex: 0 0 auto; min-height: 0; }
#local-content.iks-scroll--nested .cd-stack-bottom { flex: 0 0 auto; min-height: 0; border-top: 1px solid #e5e7eb; }
/* ⚠ 主檔 grid 高度：不靠 CSS override，改由頁面在 .iks-master-frame 掛 inline height:@_mqyHeight
   （確定高度）＋ grid Height="100%"，沿用既有 .iks-master-frame/.iks-master-grid flex 鏈即可。 */
```

要調整主檔高度：由 grid frame-header 的「設定高度」combo 驅動——`IksGrid_Virtual` 的 `OnHeightChanged` 回拋新高度，頁面 handler 寫進 `_mqyHeight`（frame 掛 `style="height:@_mqyHeight"`，grid `Height="100%"` 跟著長；`.cd-body` 過高自動捲動）。明細切換只顯示/隱藏、**不動高度**（避免與 combo 打架）。明細高度改各 grid 的固定 px `Height`。
驗收：`.cd-body` 卷軸能巡覽主/明細、主檔 grid 顯示且維持 Virtual、明細膠囊可切換；在 1366×768、1920×1080 與 125% 縮放測 wheel/鍵盤/resize。**參考頁：SAL021（master-detail 的 Mode C 堆疊式）**。

---

## 建議 RD 入口（Mode 為唯一公開參數）

RD 不該記多組 height/overflow 組合。由 `IksScrollLayout` 產 root class、CSS 變數與 Cascading Context；IksGrid 再依 Context 選有效模式。

```csharp
public enum IksLayoutScrollMode { Contained, Page, Nested }
```

| 模式 | 頁面用法 |
|------|----------|
| A | `<IksScrollLayout Mode="Contained">`，region 用 `Size="58%"` |
| B | `<IksScrollLayout Mode="Page">`，region 用 `MinHeight="320px"` |
| C | `<IksScrollLayout Mode="Nested">`，主/明細用 `.cd-stack-top/-bottom` 堆疊（落地＝cd-body `flex-column + overflow-y:auto`，主檔 grid 固定高、明細 grid 固定 px，**不用 Splitter**）|

**責任切分**：`IksScrollLayout` 管 Mode class/外層 overflow/總高度/Context；`IksScrollRegion` 管每層 Size/MinHeight；`IksGrid` 依 Context 選 Virtual/Scrollable。三者不得跨界（Layout 不管資料查詢與 PageSize，Grid 不改外層 overflow）。

## 落地順序

先把 SAL301 現況收斂命名為 **A/Contained**（行為不改）→ 擴充 IksGrid（ScrollMode/EffectiveHeight/Context）→ 加入 **B**（自然高度 stack + 分頁）→ 最後 **C**（堆疊式：cd-body `flex-column + overflow-y:auto` + `.cd-stack-top/-bottom` + 主檔 grid 固定高，**不用 Splitter**，已於 SAL021 落地驗證）。

## 常見排錯

| 症狀 | 原因 | 處理 |
|------|------|------|
| 出現雙卷軸 | 外層與 pane 同時可捲 | 依 Mode 表確定唯一 owner；A 讓外層 `overflow:hidden` |
| pane 被 Grid 撐破 | flex 父層缺 `min-height:0` | 每層 flex 父層補 `min-height:0` |
| Virtual Grid 空白列/截斷 | Virtual 無有限高度（誤用在 B） | B 取消 Virtual 或改 Server paging |
| `.iks-master-frame` 高度為 0 | region 非 flex，frame 的 `flex:1 1 auto` 失效 | region 補 `display:flex; flex-direction:column`（對齊 `.cd-pane-inner`） |
| C cd-body 不出現卷軸 | 主/明細堆疊總高未超過 cd-body 可用高度 | 屬正常（內容放得下就不需捲）；要更高改 `_mqyHeight` / 明細 grid 固定 px |
| C 主檔 grid 消失（高度 0）/ 列渲染成空白（可點卻看不到） | 堆疊下父層 auto，`.iks-master-frame` flex:1 塌 0 → grid 消失；若把 frame/grid 改 auto 高度 → Virtual 算不出視窗、列空白 | 在 `.iks-master-frame` 掛 inline `height:@_mqyHeight`（確定高度）+ grid `Height="100%"`，走原始 flex 鏈（勿用 auto 高度 override）|
| C 一開頁卡「載入中」+ console `Cannot send data...` | 誤用固定 px Splitter，撐捲軸觸發 resize 在電路連上前回呼 | 改堆疊式（拿掉 Splitter）；或 Splitter 改 `Height="100%"`（Mode A） |
| C 單檔誤用（外層被撐 1200px 空白） | 單檔套了 Mode C | 單檔移除 `iks-scroll--nested`＋`cd-body` 包裝，回純 `#local-content` |

## 指路

- 排版 CSS 通則、`cd-*` 版面 class → `page-migration/details/css-layout.md`
- master-detail 堆疊式骨架（主/明細 `.cd-stack-*` + 明細膠囊切換）→ `page-migration/templates/master-detail.md`
- 主檔清單 Grid / Virtual → `page-migration/details/grid-virtual.md`

> 本文為設計/實作規格；SAL301 的 A/B/C demo 目前為隔離驗證版，尚非共用架構落地。
