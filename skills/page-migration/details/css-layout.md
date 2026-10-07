# 詳細規則：J. 畫面控件排版（CSS Grid，取代 TelerikGridLayout）

> 骨架指標來源：`templates/*` J 區。
> **CSS 一律進 `wwwroot/app.css`**，勿散落頁面 `<style>`（記憶 `shared_css_appcss`；IksPageBase 無法放 style）。
> 來源：舊 skill `css-grid-layout` 彙整。

---

## 命名規則

| 用途 | Grid 容器 | Row | 子元件放法 |
|------|-----------|-----|-----------|
| 篩選欄位（Popup） | `iks-filter-grid` | `iks-filter-row` | **整包**直接放子元件（row 本身兩欄 Grid，不需 label/input span） |
| 編輯表單（edit-field） | `iks-edit-grid` | `iks-edit-row` | `iks-edit-label` span + `iks-edit-input` span（row 用 flex） |

## 核心原理：auto-fill 自動換行
- 每組 label+input 包一個 `row` div，外層 Grid 用 `auto-fill + minmax` 依**容器寬度**自動決定每行放幾組、不足換行（偵測容器寬度、非螢幕寬度）。
- **不用明確 `grid-row/grid-column` 定位**（auto-fill 動態改欄數會跑位）；改流排。
- `auto-fill` 需**容器有明確寬度**：`container-fluid`(100%)、`TelerikPopup Width` 皆可；無寬度 inline 容器會退化單欄。

## CSS（進 app.css）
```css
/* 篩選：每組 minmax = label(150)+input(250)=400 */
.iks-filter-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); row-gap: 3px; }
.iks-filter-row  { display: grid; grid-template-columns: 150px 1fr; align-items: center; }
/* 編輯：每組 minmax = label(110)+input(270)=380 */
.iks-edit-grid  { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); row-gap: 3px; column-gap: 0; }
.iks-edit-row   { display: flex; align-items: center; }
.iks-edit-label { min-width: 110px; }
.iks-edit-input { min-width: 270px; }
```

## 跨欄欄位（原 TelerikGridLayout ColumnSpan → CSS Grid）

| 原 ColumnSpan（含 label） | CSS Grid |
|---|---|
| 2 | `<div class="iks-edit-row" style="grid-column: span 2;">` |
| 3 | `style="grid-column: span 2;"` + input `flex:1` |
| 5+ | `style="grid-column: span 3;"` + input `flex:1` |
| 全寬（TextArea） | `style="grid-column: 1 / -1;"` + input `flex:1` |
| `RowSpan` | 移除，改全寬 `grid-column: 1 / -1` |

> pair 數換算：原 ColumnSpan 欄數 ÷ 2（label+input 各 1 欄）。

## 眉角
- **`<span>` 內不可放 `<div>`**（span 是 inline）。多元件並排時直接在 span 加 `style="display:flex; gap:4px; align-items:center;"`：
```razor
<span class="iks-edit-input" style="display:flex; flex-wrap:nowrap; gap:4px; align-items:center;">
    <IksTextBox @bind-Value="current.F1" /><IksTextBox @bind-Value="current.F2" Width="50px" />
</span>
```

## 【骨架程式碼】
```razor
@* 編輯表單 *@
<div class="iks-edit-grid">
  <div class="iks-edit-row">
    <span class="iks-edit-label"><IksLabel Key="Lb_E_{{F}}" DefaultText="{{中文}}" /></span>
    <span class="iks-edit-input"><{{控件}} @bind-Value="current.{{F}}" ... /></span>
  </div>
  @* 跨欄：style="grid-column: span 2;" / 全寬：grid-column: 1 / -1; *@
</div>
@* 篩選（整包，無 span）*@
<div class="iks-filter-grid">
  <div class="iks-filter-row"><IksLabel Key="Lb_F_{{F}}" DefaultText="{{中文}}" /><{{控件}} @bind-Value="@Filter.{{F}}" ... /></div>
</div>
```

## 指路
- 編輯欄位順序（DFM Top）→ `details/edit-window.md`
- 篩選 Popup 外框（iks-filter-popup head/body/actions）→ `details/popup-filter.md`
- 控件用法 → `details/shared-input-components.md`
- master-detail 版面 class（cd-body[flex-column+overflow-y:auto]/cd-stack-top/cd-stack-bottom/iks-mode-switch[含 iks-detail-switch]/iks-detail-body/iks-detail-panel/iks-frame-head/iks-detail-stacked）→ 同進 app.css。⚠ 已淘汰 cd-splitter/cd-pane-*（改堆疊式，見 iks-scroll-modes skill）
