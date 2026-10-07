# Golden Set — 回歸樣本清單

> **用途**：規則精進（改 page-migration skill / index / verify 規則）後，重跑這批**已定案**頁的 `verify_static`，
> 確認新規則**沒把舊頁改壞**（缺口 #6 閉環的守門）。
> **期望**：清單內每頁 `verify_static` 皆 **PASS**；任一 FAIL ＝ 回歸，擋下該次規則變更。
> **維護**：使用者定案一頁就加進來；發現某頁其實不該當基準就移除。`golden_check.py` 讀 `- SALxxx` 行。

## 樣本（本 session 已複查/修正並 verify PASS）

- SAL083
- SAL084
- SAL085
- SAL086
- SAL095
- SAL096
- SAL097
- SAL098
- SAL099
- SAL100

> 註：這批為 2026-09-21 經 static-verify 全綠的查詢/發票頁。後續可再納入更早定案的樣板頁
> （如 SAL021 主檔明細、SAL046 報價單）擴大覆蓋——但納入前該頁需先 verify PASS。

## 待補（新 fragment 結構／view_mode 迴歸，尚無定案樣本）

> gen-ui 於 2026-09-21 重構為 toolbar/grid/detail + 呈現模式擇一（editwindow/tabview）。
> 下列**每種呈現模式至少各要一支已定案頁**當迴歸基準，涵蓋 fragment 五分類。
> **未列入上方清單＝尚未 verify PASS，不得當基準**（不捏造 PASS，鐵則4）。定案一支即上移。

| view_mode | 涵蓋 fragment | 候選樣本 | 狀態 |
|---|---|---|---|
| `incell` | toolbar/grid/detail（編輯在 grid） | 主檔明細 InCell 頁（如 SAL021/SAL044 系） | 待該頁走新流程 verify PASS |
| `telerik-window` | toolbar/grid/editwindow | 單一主表彈窗編輯頁（如 SAL001） | 待 verify PASS |
| `tab-browse-detail` | toolbar/grid/tabview | 瀏覽↔明細資料分頁頁（待指定） | 待指定＋verify PASS |
