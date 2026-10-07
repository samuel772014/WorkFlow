# 詳細規則：B. 工具列 Ribbon ＋ 按鈕配置

> 骨架指標來源：`templates/single-file.md` B 區。
> 本檔負責兩件事：①ToolbarGroup 寫法；②**按鈕該放哪裡的配置決策**（單檔 vs 明細兩模式）。

---

## 一、按鈕配置決策（最重要，跨區規則）

轉譯時**不要照搬 Delphi 導覽列一整排**。B101 這類 `TfmEditForm` 內建 新增/修改/刪除/存檔/取消/查詢/上下筆，要依模式拆到不同位置。

### 通則
- **按鈕順序固定**：`CRUD → 查詢查看 → 特殊功能`（「查看/詳細資料」歸「查詢查看」群，排在 CRUD 之後）。
- **上/下一筆**只出現在 **編輯畫面** 與 **詳細資料畫面**（Window 內右側導覽鈕），**不放工具列**。

### 單檔模式（single-file 範本）
| 動作 | 放哪 |
|------|------|
| 新增、查詢 | **工具列 Toolbar**（非單列操作） |
| 修改、刪除 | **GridView 指令欄** GridCommandColumn（針對單一資料列） |
| **詳細資料（查看）** | **GridView 指令欄，排在 CRUD（修改/刪除）之後**（查詢查看群） |
| 存檔、取消 | 編輯 **Window 內** |
| 上/下一筆 | 編輯 / 詳細資料 **Window 內右側** |

- 單檔模式：工具列＝`新增 → 查詢`；指令欄＝`修改 → 刪除 → 詳細資料(查看)`（CRUD → 查看）。
- **「詳細資料」鈕**：重用同一個編輯 Window，以**唯讀模式**開啟（所有輸入框 `Enabled="false"` / readonly），不另做檢視畫面。見記憶 `detail_readonly_reuse_edit`。

### 明細模式（master-detail 範本）
- **主檔（Mqy）所有操作**（新增/修改/刪除/存檔/取消…）**全部放工具列**，依 `CRUD → 查詢查看 → 特殊功能` 排序。
- 明細（Dq）的列操作走明細 grid 自己的 InCell/指令欄，不佔主檔工具列。

> 📌 模式怎麼選：來源檔若有 `AddDetail`（明細），**先問轉譯操作者**要單檔還是主檔明細，不自動判斷。明細已無使用→單檔模式（B101/SAL001 即此情形）。

---

## 二、ToolbarGroup 寫法

**大原則**：頁面最上方一條 `Toolbar`，`ToolbarGroup` 分組，純 Tabler 圖示 + tooltip，仿 Excel/Notion 扁平 ribbon。

**使用規則**
- 每顆 `ToolbarButton`：`Action`(字串) ＋ `FontIcon`(`ti ti-*`) ＋ `Title`(tooltip) ＋ `Enabled`(綁旗標)。
- 動作集中單一 `OnAction="HandleToolbar"` → 內部 switch 分派 → 尾端呼叫 `btnControl()`（見 `details/btn-control.md`）。
- 純圖示按鈕靠頁面層一個 `TelerikTooltip TargetSelector=".toolbar-field [title]"` 顯示用途。
- Enabled 旗標一律由 `btnControl()` 依 `pageStatus` 控制，勿寫死。

**【範例程式碼】** (SAL001，單檔模式：新增 + 查詢)
```razor
<div class="toolbar toolbar-field">
    <Toolbar OnAction="HandleToolbar">
        <ToolbarGroup>   @* CRUD：單檔僅新增（修改/刪除/詳細在 grid 指令欄）*@
            <ToolbarButton Action="Add"   Enabled="@_AddEnabled"   FontIcon="ti ti-plus"   Title="新增" />
        </ToolbarGroup>
        <ToolbarGroup>   @* 查詢 *@
            <ToolbarButton Action="Query" Enabled="@_QueryEnabled" FontIcon="ti ti-search" Title="查詢" />
        </ToolbarGroup>
    </Toolbar>
</div>
<TelerikTooltip TargetSelector=".toolbar-field [title]" Position="@TooltipPosition.Bottom" />
```

**【骨架程式碼】**
```razor
@* B. 工具列 —— 順序 CRUD→查詢→特殊；單檔只放非單列操作 *@
<div class="toolbar toolbar-field">
    <Toolbar OnAction="HandleToolbar">
        <ToolbarGroup>   @* CRUD *@
            <ToolbarButton Action="Add" Enabled="@_AddEnabled" FontIcon="ti ti-plus" Title="新增" />
            @* {{明細模式才在此續加 修改/刪除/存檔/取消}} *@
        </ToolbarGroup>
        <ToolbarGroup>   @* 查詢 *@
            <ToolbarButton Action="Query" Enabled="@_QueryEnabled" FontIcon="ti ti-search" Title="查詢" />
        </ToolbarGroup>
        @* {{個別特殊操作再開一組 ToolbarGroup}} *@
    </Toolbar>
</div>
<TelerikTooltip TargetSelector=".toolbar-field [title]" Position="@TooltipPosition.Bottom" />
```

> Grid 指令欄（修改/刪除/詳細）寫法見 `details/grid-virtual.md`；詳細資料唯讀開窗見 `details/edit-window.md`。
