---
name: review-filter
description: review-engine area.filter 審查清單（進階篩選欄位/標籤/條件語意/預設值）
disable-model-invocation: true
---

# review-filter — 篩選欄位審查

> 規則來源：`page-migration/details/popup-filter.md`、`input-component-choice.md`、`detail-display-settings.md`、`final-dfm-check.md` ①。區代碼 **FLT**。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi | dfm FilterPanel 內標籤／控件（含基底、`Visible`、Top/Left）；`.pas` `FilterDblClick`（pick 來源）、`FilterValidate`、`DisplayButtonClick`/`OpenPick` 組 WHERE 的邏輯、`FormCreate` 的篩選預設值 |
| C# | `TelerikPopup` 篩選區的 `iks-filter-row`、控件與綁定、`ClearFilter`/`ApplyFilter`/`Query`、條件字典的初始化時機（`OnInitializedAsync`／`OnAfterRenderAsync(firstRender)`）、後端查詢方法的 WHERE 組法 |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> compare filter     # ★先跑：標籤/順序/隱藏 vs C# 篩選列（含子 form）
py … <SAL> get proc FilterDblClick ; py … <SAL> get proc FilterValidate
py … <SAL> get proc OpenPick ; py … <SAL> get proc DisplayButtonClick
py … <SAL> list rows --kind filter
py … <SAL> get method Query --file <SAL>.razor ; py … <SAL> list sql --side cs --grep "<查詢方法名>"
```

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| FLT-01 | 篩選欄位集合一致（漏／多）；Delphi `Visible=False` 者不出現 | missing/extra｜medium |
| FLT-01a | Delphi `FilterPanel` 為 `Locked=True`／高度收起，或 `DisplayButton` 設 `Visible=False`（無篩選）→ C# **不得有**進階篩選 popup／篩選鈕（`ShowFilterButton`）／關鍵字欄，後端查詢也不得收對應參數；有的話報 extra（例：SAL072A 自行加了關鍵字篩選）。依 `area-review.md`「擅加功能盤點」 | extra｜medium |
| FLT-02 | 標籤文字逐字＝dfm TLabel Caption（去 `&X`，不簡化） | mismatch｜low |
| FLT-03 | 順序依 dfm Top→Left | mismatch｜low |
| FLT-04 | 控件依決策樹：KeyCode→KeyCodeComboBox；EditPick ≤2 欄→IksCodeComboBox；≥3 欄→EditPick；純文字→IksTextBox；日期→DatePicker | rule-violation｜low |
| FLT-05 | pick 來源表與條件（如 `MM_ITMTP where GOOD='Y'`）一致 | mismatch｜medium |
| FLT-06 | 查詢條件語意一致：等於／LIKE（前綴／包含）／區間起迄／空值略過，與 Delphi 組 WHERE 相同 | mismatch｜medium |
| FLT-07 | 預設值（如單況預設 OP、日期區間預設）與 Delphi FormCreate 相同 | mismatch｜low |
| FLT-07a | **必填篩選欄位**：Delphi 查詢條件一律帶入、沒有「空值略過」（如 `OpenPick` 寫 `where STATUS='+AA(cb1.Text)` 而非 `iif(cb1.Text='','',…)`），或 `FilterValidate`／`DisplayButtonClick` 擋空值 → 視為必填。C# 必須同時做到三件事：① 標籤 `IksLabel Required="true"`；② `Query` 開頭擋空值並 `MsgBox` 提示（參考 SAL057「請先選擇單況後再查詢」），不得用「空白＝全部」繞過；③ `ClearFilter` 不清必填欄位（不寫 `Filter = new()`、不對必填控件呼叫 `Reset()`），見 FLT-08。任一項缺漏就報（例：SAL073 單況） | mismatch/rule-violation｜medium |
| FLT-07b | **預設篩選須帶入首次查詢**：篩選有預設值（單況 `OP`、日期區間、年度…）時，開頁第一次主檔查詢必須已帶這些條件。檢查三點：① grid 綁的條件字典在首次 render 前（欄位宣告或 `OnInitializedAsync` 第一個 `await` 前）已含預設條件；② 預設值本身不是在 `OnAfterRenderAsync(firstRender)` 才設定；③ `Query` 原地更新同一個字典（`Clear()`＋逐鍵寫入）後 `Rebind()`，不是 `{{parameter}} = BuildFilter()` 換新字典。典型錯法：字典宣告為空 `new()`、`firstRender` 內才 `{{parameter}} = BuildFilter(); grid.Rebind()` → 開頁先查出全部資料（例：SAL079 首查未帶單況 OP）。規則見 `page-migration/details/popup-filter.md`「有預設篩選值」 | mismatch｜medium |
| FLT-08 | Popup 結構：Grid 外部、錨點 `{grid}-filter-popup-target`、各控件 `@ref`＋`Reset()`、清除只清非必填（不用 `Filter = new()` 洗掉必填） | rule-violation｜low |
| FLT-09 | 只改顯示/動作參數的 checkbox 應放「明細顯示設定」Popup，不放進階篩選（反之亦然） | rule-violation｜low |
| FLT-10 | 篩選一律 Popup，不用 inline 篩選區（含子視窗） | rule-violation｜low |

## 4. 邊界
子 form 的篩選（`compare filter` 的 [子form] 段）→ subwindow；comboBoxCode 是否登記／module 是否正確 → conventions；查詢 SQL 的 JOIN/欄位（非 WHERE 條件）→ backend；grid 欄位 → grid。

## 5. 輸出
同 `review-grid` §5（區代碼 FLT）。`compare filter` 標「[座標配對]」者為座標推定，引用前需 `get comp` 複核。
