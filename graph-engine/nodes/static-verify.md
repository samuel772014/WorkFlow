# Node 契約 — static-verify（GATE 1，Step 4）

> **這是什麼**：生成/assemble 後的整體檢察 node，把 `acceptance-criteria.md` 的 S1–S9 儘量機器化，產出結構化 `findings`（供條件邊路由）。
> **這是缺口 #1 的解**：以前文件說有 verifier、實際沒有；本 node 補上。
> **規則來源**：`.claude/SelfFolder/checklist/acceptance-criteria.md`（判準以其為準）＋ page-migration details。

---

## findings 結構（first-class state）

```yaml
findings:
  - category: title-name          # 問題類別（route/title/title-name/xform-unregistered/display-wired/…）
    verdict:  CONFIRMED           # CONFIRMED(機器可確定) | PLAUSIBLE(需人覆核)
    area:     grid                # toolbar/grid/detail/editwindow/tabview/subwindow/backend → 供路由回對應 gen node
    file:     SAL095.razor
    line:     12
    summary:  標題 ≠ 對照表正式名
```
`area` 就是 `graph-spec.md` 條件邊 `findings.any(area~grid)` 路由回該片段 node 的依據。

---

## S1–S9 分層：誰來判

| S | 檢查項 | 由誰判 | 機制 |
|---|---|---|---|
| S1 | @page 路由 + 標題含代號 | **機器** | `verify_static.py` C1 |
| S9 | 標題＝對照表正式名 | **機器** | `verify_static.py` C2（PLAUSIBLE） |
| （bug類）| DisplayTransform 屬性 KEY 已註冊 | **機器** | `verify_static.py` C3 |
| （bug類）| grid *_Display 有接上屬性 | **機器** | `verify_static.py` C4 |
| （bug類）| razor 的 `iks-*` class 在 css 有定義（禁自創 class） | **機器** | `verify_static.py` C5 |
| （bug類）| `IksCodeComboBox` 的 comboBoxCode 登記在所傳 module | **機器** | `verify_static.py` C6 |
| （慣例類）| 自閉合文字輸入用 IksTextBox、不寫死 `"00001"`／`_url`、status 以 `== 1` 判成功、無已淘汰寫法 | **機器** | `verify_static.py` C7–C11（C9 PLAUSIBLE；對應 review-conventions CNV-03/05/07/08/10） |
| （慣例類）| 遮罩內不 await 訊息框、遮罩必解除 | **機器** | `verify_static.py` C12（呼叫 `review-engine/tools/lint_loading.py`；CNV-13） |
| S2 | 欄位/欄序對 dfm（Top 座標） | **agent** | 對 `manifest.fields` 覆核 |
| S3/S5/S7/S8 | 工具列/grid 指令/按鈕順序 | **agent** | 依 toolbar/grid-incell details |
| S4 | 新增/編輯/刪除 handler 存在＋位置 | **agent** | 依 crud-handlers |
| S6 | NSN 用 editpick | **agent** | 依 input-component-choice |
| 執行期/人眼 | 篩選正常、畫面一致… | **human** | 標【需人工判斷】 |

> 機器層先跑（快、可確定）；agent 層覆核需判斷者；剩人眼留 `human-review`。

---

## 執行流程

1. **機器層**：`py .claude/SelfFolder/graph-engine/tools/verify_static.py <code>`
   → 得 C1–C12 findings（route/title/title-name/xform/display-wired/css-class-undefined/combobox-module/textbox/hardcoded-emply/status-check/hardcoded-url/deprecated/msgbox-under-loading/loading-not-released）。
2. **agent 層**：讀 `manifest`＋`acceptance_claims`，對 S2–S8 逐項判，追加 findings（附 area）。
3. 合併寫入 `state.findings`。

## 路由（見 graph-spec.md）
- `findings.none` → `compile-gate`
- `findings.any(area~backend)` → `gen-backend`（attempts<max）
- `findings.any(area~toolbar/grid/detail/editwindow/tabview/subwindow)` → 對應 `gen-ui.*`（attempts<max）
- `attempts>=max` → `human-review`
- `PLAUSIBLE` findings：不自動退回，彙整到 `human-review` 由人裁決（避免誤判反覆重跑）

---

## verify_static.py 現況

已實作 C1–C6（C5/C6 於 2026-10-06 補：SAL074–076 自創 class `iks-single-frame`、SAL073 下拉 module 傳錯，皆為 C1–C4 漏網）。實測（SAL083–100）**立即抓到 SAL095/096/099/100 四支標題非對照表正式名**——人工複查漏掉、機器一次揪出，即本 node 的價值證明。

2026-10-20 補 C7–C12：把 review-conventions 可機械判的 CNV 項前移到實作階段。對 140 支 SAL razor 試跑：C7 13 處／8 頁、C9 5 處／4 頁、C11 1 處（SAL046 OnBeforeEdit）、C12 3 處（SAL055 等），C8/C10 0 處。既有頁面於下次轉譯／修正跑 GATE1 時才會浮出。`class XxxDto` 需看上下文（API payload 輔助類別不算違規），不機械判，留 review CNV-02。
