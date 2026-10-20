---
name: iks-scroll-modes
description: IKSERP Blazor 主檔明細頁的捲動版型（Mode C Nested 堆疊式）設定規範。當使用者要設定主檔明細頁的捲動、外層 overflow、主檔/明細高度、IksGrid Virtual 高度，或問「捲動怎麼設 / 頁面出現雙卷軸 / Virtual Grid 列空白 / 一開頁卡載入中」時觸發。搭配 page-migration 的 css-layout 使用。
---

# IKSERP 捲動版型規範（Mode C Nested 堆疊式）

> 技術棧：Blazor + `IksGrid_*`（TelerikGrid）。**專案現行只用 Mode C**（`iks-scroll--nested`，35 頁）；原 A/Contained、B/Page 程式 0 處使用，已自本 skill 移除（2026-10-08）。
> **CSS 一律進 `wwwroot/app.css`**（勿散落頁面 `<style>`；IksPageBase 無法放 style，見 page-migration/details/css-layout.md）。
> Mode class 只掛在頁面自己的 **`#local-content`**（掛到共用 `.app-main` / `#page-content` 會污染其他頁面與 Dialog）。
> 版面 class（`cd-body`/`cd-stack-top`/`cd-stack-bottom`）沿用 `page-migration` master-detail 既有命名。
>
> **範本分野（page-migration）**：**一般單檔（single-file）一律不套 Mode C** —— 外層就是純 `<div id="local-content">`，Grid 自己捲。**Mode C 只屬於主檔明細（master-detail）**。誤把 Mode C 套到單檔會讓外層被固定高度撐開（如 1200px 空白）。

## 核心判準

1. **誰擁有垂直捲動權** —— 外層 `#local-content` / `.cd-body` / Grid 只該有明確的擁有者；Mode C 由 `.cd-body` 捲。
2. **Virtual Grid 必須有有限高度** —— 否則列空白/計算錯誤。

## Mode C — Nested（堆疊式：cd-body 捲動 + 主/明細垂直堆疊，不用 Splitter）

外層 `#local-content` 不捲，改由 **`.cd-body` 捲動**（`flex-column + overflow-y:auto`）；主檔 `.cd-stack-top` + 明細 `.cd-stack-bottom` 依內容**自然高度垂直堆疊**，兩區高度總和超過 `.cd-body` 可用高度時，由 cd-body 自動出捲軸。主檔清單的 **`.iks-master-frame` 掛確定高度**（inline `style="height:@_mqyHeight"`），內部 Virtual grid 用 **`Height="100%"`** 走原始 flex 鏈；明細 grid 各自固定 px。明細分頁用切換膠囊 + `@if` 面板（`TelerikTabStrip` 已淘汰）。

> ⚠ **`_mqyHeight` 掛在 frame（確定高度），grid 用 `Height="100%"`**：Virtual 捲動需**祖先鏈有確定高度**才算得出視窗；把 `_mqyHeight` 直接給 grid `Height`、或 frame/grid 是 auto 高度，列會**渲染成空白（DOM 在、可點、但看不到）**。

> ⚠ **不要用 `TelerikSplitter`**：固定 px 高 Splitter 比 flex `.cd-body` 高→撐出捲軸→觸發 Telerik ResizeObserver `onResize→close` 在 SignalR 電路 **Connected 前**回呼 .NET→拋 `Cannot send data if the connection is not in the 'Connected' State`→互動 bootstrap 中斷→**卡在載入中**。舊 for_github 固定 px Splitter 機制（Height=980px）已淘汰。**不再用 `--iks-layout-total-height` CSS 變數**。

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
驗收：`.cd-body` 卷軸能巡覽主/明細、主檔 grid 顯示且維持 Virtual、明細膠囊可切換；在 1366×768、1920×1080 與 125% 縮放測 wheel/鍵盤/resize。**參考頁：SAL021**。

## 常見排錯

| 症狀 | 原因 | 處理 |
|------|------|------|
| 出現雙卷軸 | 外層與 cd-body 同時可捲 | 外層 `#local-content` 必須 `overflow:hidden`（掛 `iks-scroll--nested`） |
| 區塊被 Grid 撐破 | flex 父層缺 `min-height:0` | 每層 flex 父層補 `min-height:0` |
| cd-body 不出現卷軸 | 主/明細堆疊總高未超過 cd-body 可用高度 | 屬正常；要更高改 `_mqyHeight` / 明細 grid 固定 px |
| 主檔 grid 消失（高度 0）/ 列渲染成空白（可點卻看不到） | 堆疊下父層 auto，frame 塌 0；或 frame/grid 改 auto 高度 → Virtual 算不出視窗 | `.iks-master-frame` 掛 inline `height:@_mqyHeight` + grid `Height="100%"`（勿用 auto 高度 override） |
| 一開頁卡「載入中」+ console `Cannot send data...` | 誤用固定 px Splitter，撐捲軸觸發 resize 在電路連上前回呼 | 拿掉 Splitter，改堆疊式 |
| 單檔外層被撐 1200px 空白 | 單檔套了 Mode C | 單檔移除 `iks-scroll--nested`＋`cd-body` 包裝，回純 `#local-content` |

## 指路

- 排版 CSS 通則、`cd-*` 版面 class → `page-migration/details/css-layout.md`
- master-detail 堆疊式骨架（主/明細 `.cd-stack-*` + 明細膠囊切換）→ `page-migration/templates/master-detail.md`
- 主檔清單 Grid / Virtual → `page-migration/details/grid-virtual.md`
