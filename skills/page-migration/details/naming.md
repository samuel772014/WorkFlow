# 詳細規則：命名對照（Delphi → C# / Blazor）

> 轉譯通用命名，任一區都可能參考。來源：舊 `naming-mapping` 彙整。搭配記憶 [[reference_naming_rules]]（各層大小駝峰規則）。

---

## 變數前綴（Delphi → C#）
| Delphi | 意義 | C# |
|--------|------|----|
| `g` 全域 / `l` bool / `s` string / `a` int | 匈牙利前綴 | **一律去前綴**，用型別本身 |
| `TFmXxx` 表單類別 | | 移除 `TFm`，用功能代碼（`SAL301.razor`） |
| `frm` / `dm` 前綴 | 表單 / DataModule | 移除；`dm` → Repository 查詢方法 |

## DataSet
| Delphi | C# |
|--------|----|
| `Mqy`（主查詢+主表） | `MqyFilter`（篩選）/ `current{Master}`（編輯單筆）/ `{Grid}`（清單 ref） |
| `Dq1/Dq2…` 子表 | 保留序號：`{Dqn}` ref、`{Dqn}_GD` 資料、方法 `GetSAL301Dq1Async` |
| `DqXxx` 語意子表（DqSPEC） | 語意命名 `GetSAL301SpecAsync` |

## UI 元件（本專案現用）
| Delphi | Blazor（現用） |
|--------|---------------|
| `TfmEditForm` 基底 | `IksPageBase` |
| `TwwDBGrid` 主表瀏覽 | **`IksGrid_Virtual`** |
| `TwwDBGrid` 子表（可編輯） | **`IksGrid_vnq`**（InCell） |
| `TRzDBEdit` 唯讀/一般 | `IksTextBox` |
| `TRzDBButtonEdit`/`TRzButtonEdit` | `IksTextBox`+Picker → `details/editor-template.md`（≤2欄改 `IksCodeComboBox`）|
| `TRzDBComboBox` | `KeyCodeComboBox` 或 `IksCodeComboBox` |
| `TfrmP2Date` | `TelerikDatePicker` |
| `TRzTabSheet` | 一般分頁 `TelerikTabStrip` + `TabStripTab`；**master-detail 明細改 `iks-mode-switch` 膠囊 + `@if` 面板** |
| `TSplitter` | master-detail 上下改 **CSS Flexbox 堆疊**（`.cd-stack-top/-bottom`，不用 `TelerikSplitter`；見 iks-scroll-modes） |
| `TRzBitBtn` 工具列 | `<ToolbarButton Action="…">` |
| `RzDBNav` 巡覽列 | `<Toolbar>`（拆三處，見 `details/toolbar.md`） |
| `TLabel`+元件 | `<IksLabel Key="Lb_欄位名" DefaultText="中文" />`+元件 |

## 方法命名 `[動詞][功能碼][語意][Async]`
動詞：Get / Add / Update / Delete / Change / Copy
```
Repository： Query{FORM}MqyAsync      （Query 開頭）
Service：    Get{FORM}MqyAsync        （Get 開頭）
Mutation：   Add{FORM}Dq1Async / Change{FORM}StatusCCAsync / Copy{FORM}QuoteAsync
連動查詢：   {form}_Get{來源}_{目標}   （resolver endpoint）
```

## comboBoxCode
```
欄位名（去底線、各段首字大寫）+ ComoBox
CUR→CurComoBox、SALEREP→SalerepComoBox、INVITPNO→InvitpnoComoBox、TRDTERM→TrdtermComoBox
```

## IksLabel Key
```
一般：Lb_欄位名    （Lb_CUSTMER）
篩選：Lb_F_欄位名  （Lb_F_Salerep）
編輯：Lb_E_欄位名  （Lb_E_Salerep）
```

## 指路
- 各層大小駝峰（Razor/C#/API gqlway）→ 記憶 [[reference_naming_rules]]
- 控件用法 → `details/shared-input-components.md`；後端 → `details/backend-sql.md`
