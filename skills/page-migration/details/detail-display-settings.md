# 詳細規則：明細顯示設定 Popup

> 適用頁型：**批次作業頁**（查詢候選清單→勾選→批次動作），非一般 CRUD 主檔維護頁。
> 參考來源：MPS023（Deploy_testing_project 分支）、MPS031。

---

## 定義與用途

「明細顯示設定」是一組**畫面顯示 / 批次動作開關**，與「進階篩選」（查詢條件）是不同概念：

| 差異點 | 進階篩選 | 明細顯示設定 |
|--------|----------|--------------|
| 作用範圍 | 改變後端 WHERE 條件，需重新查詢 | 控制 UI 顯示或傳遞動作參數 |
| 是否需重新查詢 | 是（有「查詢」動作按鈕） | **不需要**（無動作按鈕，勾選即時生效） |
| Popup 寬度 | 依欄位組數 × 430px | 固定較窄（360px 左右） |
| AnchorSelector class | `.popup-target` | `.popup-target-detail`（避免衝突） |

---

## 開關類型與生效時機

| 開關類型 | 範例 | 生效時機 |
|----------|------|----------|
| **立即切換 UI 可見性** | 顯示/隱藏備料明細 grid | `@bind-Value` 直接改 `bool`，下次 render 即反映 |
| **立即觸發明細重查** | 顯示虛階或零需求、顯示取消需求 | `@bind-Value:after="OnDq1FilterChanged"` 呼叫明細 Rebind |
| **下次主查詢時生效** | 顯示已展開料表項目 | 存入 `bool`，下次 `QueryAsync()` 才帶入 WHERE |
| **下次批次動作時生效** | 更新待確認製令用料 | 存入 `bool`，執行展開/更新時當參數傳後端 |

---

## 按鈕放置

**必須用 `iks-fbtn` 純 button**，不可用 `ToolbarButton` 元件（後者不支援 `Class` 屬性，無法帶 popup 錨點 class）：

```razor
<ToolbarGroup>
    @* 其他 ToolbarButton ... *@
    <button class="iks-fbtn popup-target-detail" title="明細顯示設定"
            @onclick="@ToggleDetailPopup">
        <i class="ti ti-adjustments-horizontal"></i>明細顯示設定
    </button>
</ToolbarGroup>
```

---

## Popup 宣告

```razor
@* ===== 明細顯示設定：純顯示/動作開關，不含查詢條件，勾選即時生效，無動作按鈕 ===== *@
<TelerikPopup @ref="@DetailPopupRef"
              AnchorSelector=".popup-target-detail"
              AnimationType="@AnimationType.SlideDown"
              AnimationDuration="200"
              Width="360px">
    <div class="iks-filter-popup" aria-label="明細顯示設定">
        <div class="iks-filter-popup-head">
            <span class="iks-filter-popup-title">明細顯示設定</span>
            <button class="iks-fbtn ghost iks-filter-close" @onclick="ToggleDetailPopup" title="關閉">
                <i class="ti ti-circle-x"></i>
            </button>
        </div>
        <div class="iks-filter-popup-body">
            <div class="iks-filter-grid">
                @* 立即切換 UI 可見性 *@
                <div style="display:flex; align-items:center; gap:4px;">
                    <TelerikCheckBox Id="chkShowDetail" @bind-Value="@_showDetail" />
                    <label for="chkShowDetail" style="cursor:pointer;">顯示備料明細</label>
                </div>
                @* 立即觸發明細重查（用 :after 接 handler） *@
                <div style="display:flex; align-items:center; gap:4px;">
                    <TelerikCheckBox Id="chkZero" @bind-Value="@_showZero" @bind-Value:after="OnDq1FilterChanged" />
                    <label for="chkZero" style="cursor:pointer;">顯示虛階或零需求料品</label>
                </div>
                <div style="display:flex; align-items:center; gap:4px;">
                    <TelerikCheckBox Id="chkShowCancelled" @bind-Value="@_showCancelled" @bind-Value:after="OnDq1FilterChanged" />
                    <label for="chkShowCancelled" style="cursor:pointer;">顯示取消需求料品</label>
                </div>
                @* 下次主查詢時生效 *@
                <div style="display:flex; align-items:center; gap:4px;">
                    <TelerikCheckBox Id="chkShowExpanded" @bind-Value="@_showExpanded" />
                    <label for="chkShowExpanded" style="cursor:pointer;">顯示已展開料表項目</label>
                </div>
                @* 下次批次動作時生效 *@
                <div style="display:flex; align-items:center; gap:4px;">
                    <TelerikCheckBox Id="chkMod2" @bind-Value="@_mod2" />
                    <label for="chkMod2" style="cursor:pointer;">更新待確認製令用料</label>
                </div>
            </div>
        </div>
        @* 無 actions 區：不需清除/查詢按鈕 *@
    </div>
</TelerikPopup>
```

---

## @code 對應

```csharp
// ── 明細顯示設定開關（依生效時機分類） ──
private bool _showDetail    = true;    // 立即切換 UI 可見性
private bool _showZero      = false;   // 立即觸發明細重查
private bool _showCancelled = false;   // 立即觸發明細重查
private bool _showExpanded  = false;   // 下次主查詢才生效
private bool _mod2          = true;    // 下次批次動作才生效

// Popup 開合（同進階篩選的 Show/Hide 寫法，不用 @bind-Visible）
private TelerikPopup? DetailPopupRef;
private bool _detailPopupVisible = false;
private void ToggleDetailPopup()
{
    _detailPopupVisible = !_detailPopupVisible;
    if (_detailPopupVisible) DetailPopupRef?.Show();
    else DetailPopupRef?.Hide();
}

// 立即觸發明細重查（綁在 @bind-Value:after）
private async Task OnDq1FilterChanged()
{
    if (_focusedCandidate != null) await LoadDq1Async();
}
```

---

## 後端 SQL 對應

**主查詢（候選清單）**— `_showExpanded` 控制：
```csharp
// showExpanded=false（預設）：只列尚未展開者
sql += showExpanded ? " AND d.ZCLOSE='N'" : " AND d.RUNMRP<>'Y' AND d.ZCLOSE='N'";
```

**明細查詢（Dq1/PP_PLNDD）**— `_showZero`、`_showCancelled` 控制：
```csharp
if (!showZero)      sql += " AND dd.PSDU<>'Y' AND dd.PLNQTY>0";
if (!showCancelled) sql += " AND dd.ZCLOSE<>'Y'";
```

**批次動作 Payload**— `_mod2` 作為參數傳後端：
```csharp
var payload = new { ..., MOD2 = _mod2 ? "1" : "0", ITEMS = ... };
```

---

## 與進階篩選並存的注意事項

當頁面同時有「進階篩選」與「明細顯示設定」兩個 Popup 時：

- 進階篩選用 `.popup-target`，明細顯示設定用 `.popup-target-detail`，兩個 class 不重疊
- 若進階篩選已被搬進 Grid 的 `HeaderButtons`（`Class = "popup-target"`），則 Toolbar 上只需放明細顯示設定按鈕
- `ToggleFilterPopupAsync()` 需包成 `Task` 版本才能傳給 `HeaderButton.OnClick`（`Func<Task>` 型別）

---

## 指路

- 進階篩選 Popup 寫法 → `details/popup-filter.md`
- Toolbar / ToolbarGroup / iks-fbtn 按鈕 → `details/toolbar.md`
- Grid HeaderButtons 用法 → `details/grid-virtual.md` 或 `details/grid-incell.md`
