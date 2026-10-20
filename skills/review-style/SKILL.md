---
name: review-style
description: review-engine area.style 審查清單（範本選用/Mode C 捲動/CSS 落點/ribbon/膠囊）
disable-model-invocation: true
---

# review-style — 畫面風格審查

> 規則來源：`page-migration/templates/*`、`details/css-layout.md`、`details/page-shell.md`、skill `iks-scroll-modes`。區代碼 **STY**。
> Delphi 只用來判斷「該用哪個範本」；其餘檢查以規範為準（type 多為 rule-violation）。

## 1. 範圍
C# razor 版面結構、`#local-content` class、版面 `iks-*` class、`<style>` 區塊、Toolbar 結構、膠囊切換、grid frame 與高度；Delphi form 型別（`TfmEditForm*`/`TfmSelectForm`/`AddDetail` 有無）。

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> list razor
py … <SAL> find "class=\"[^\"]*iks-|<style|TelerikSplitter|TelerikTabStrip|iks-scroll--|iks-master-frame" --side cs
py … <SAL> get comp <form 名>       # Delphi form 型別
```
`iks-*` class 是否定義：`grep` `IKSERPPRJ/IKSERPUI/wwwroot/*.css`（app.css 以外另有 `iks-edit-layout.css` 等）或元件 `.razor.css`。

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| STY-01 | 範本選用符合 Delphi 型別：單一主表→single-file；主檔＋明細→master-detail；穿梭轉單→dropform；Excel 匯入→excel-import | rule-violation｜medium |
| STY-02 | 捲動版型：主檔明細 `#local-content` 掛 `iks-scroll-layout iks-scroll--nested`＋`.cd-body`；單檔不套 Mode C | rule-violation｜medium |
| STY-03 | 主檔 grid frame：單檔＝`.iks-master-frame`（不設 inline 高度，flex 撐滿）＋`.iks-master-grid`＋grid `Height="100%"`；主檔明細 Mode C＝frame 掛 `height:@_mqyHeight`＋`OnHeightChanged`；明細 grid 固定 px | rule-violation｜medium |
| STY-04 | 不用 `TelerikSplitter`、`TelerikTabStrip`；明細切換用 `iks-mode-switch` 膠囊＋`@if` | rule-violation｜medium |
| STY-05 | 頁面用到的 `iks-*` class 皆已在 app.css／元件 css 定義（未定義會靜默失效） | rule-violation｜medium |
| STY-06 | 共用樣式不寫在頁面 `<style>`；inline style 僅限骨架允許處 | rule-violation｜low |
| STY-07 | 工具列：`toolbar toolbar-field` ＋ `Toolbar OnAction` ＋ `ToolbarGroup` 分組 ＋ `TelerikTooltip TargetSelector=".toolbar-field [title]"` | rule-violation｜low |
| STY-08 | 版面排版用 `iks-filter-grid`/`iks-edit-grid` 系列，不用 `TelerikGridLayout` | rule-violation｜low |

## 4. 邊界
grid 欄位/參數 → grid；按鈕有無與順序 → button；命名與通用寫法 → conventions。

## 5. 輸出
同 `review-grid` §5（區代碼 STY）；`delphi` 證據多為 null（rule-violation 只需 csharp＋rule_ref）。
