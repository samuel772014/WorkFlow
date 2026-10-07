# Node 契約 — extract 三節點（Step 3）

> **這是什麼**：`extract.dfm-decode → extract.field-cross-check → extract.fact-resolve` 三個 node 的執行契約。
> **產物**：三者合出 `manifest`（事實層），寫進 `plans/<code>.md` front-matter；供 `plan` 與 `gen-*` 消費。
> **精神**：把「顯示與否、欄位順序、名稱、keycode、共用函式」全部**先查成事實**，杜絕生成階段推測（鐵則 4）。
> **規則來源**：一律 `.claude/skills/page-migration/details/delphi-reading.md`；本檔只定「輸入/輸出/怎麼跑/查無怎麼辦」。

---

## manifest 產出結構（三 node 合寫）

```yaml
manifest:
  fields:            # ← dfm-decode 寫
    main:   [ {field, title, width, top} ]      # 主 grid，欄序依 dfm Top
    detail: { dq1: [ ... ], dq2: [ ... ] }      # 各子 grid
  crosscheck:        # ← field-cross-check 寫
    - {field, in_dfm: true, in_sql: true, in_gettext: true, decision: show}   # 三方交叉逐欄
  facts:             # ← fact-resolve 寫（查 index.json 得到）
    program: {b_code, name, ui_type}            # 程式身分（權威名）
    keycode_maps: [ {key, table, field} ]       # 已註冊者
    name_maps:    [ {key, table, keyField, nmField} ]
    reuse_funcs:  [ {func, file} ]              # 可重用，勿重寫
```

---

## Node 1 — `extract.dfm-decode`（kind: pure，可快取）

| | |
|---|---|
| 讀 | `sources.dfm_path` |
| 工具 | `.claude/skills/page-migration/tools/dfm_decode.py` |
| 寫 | `manifest.fields`（主 grid + 每個子 grid 的 field/欄序/寬/中文標題） |
| 快取 | dfm 內容未變 → `cache_hit: true`，跳過重跑 |

指令：
```
PYTHONIOENCODING=utf-8 py .claude/skills/page-migration/tools/dfm_decode.py <dfm_path>
```
**權威**：欄位 Title＝dfm Caption/Selected.Strings；欄序＝控件 Top 座標（由上而下）。

---

## Node 2 — `extract.field-cross-check`（kind: pure／agent 覆核）

| | |
|---|---|
| 讀 | `manifest.fields` + `sources.pas_path` |
| 依據 | `details/delphi-reading.md` Step 2.0/2.1（三方交叉） |
| 寫 | `manifest.crosscheck`（逐欄：dfm × SQL select × gettext(`_Display`)） |

**做什麼**：每個 grid（主檔＋每個 Dq）逐欄比對三來源，決定「顯示/不顯示」：
- `in_dfm`：dfm 有此欄且 `Visible`
- `in_sql`：該 grid 的 SQL select 有取
- `in_gettext`：`FormCreate` 的 `AddFieldEvent(Self, DqN, 'F1;F2;…')` 有列
- `decision`：三者取交集原則（如 dfm∩SQL 才顯示，避免 null 欄——SAL084 cdD 的 OAPQTY/OUP/REMARK 即因此不顯示）

### ⚠️ 通則：grid↔Dq 歸屬「靠欄位判定，不照 dfm grid 名稱/順序」
> **2026-09-22 由 SAL046/SAL058 核對學到，必守。**
`dfm_decode` 給的 grid 識別（`DDBGrid1/2/4`、dfm 內 grid 先後順序）**不等於**目標的 Dq 編號，會錯位：
- **SAL046**：dfm `DDBGrid1→Dq2`(包裝)、`DDBGrid2→Dq3`(收款)、`DDBGrid4→Dq4`(備註)，且 `DDBGrid3` 跳號無對應。
- **SAL058**：dfm 第一個 grid＝目標表 `cd2`、第二個 grid＝來源表 `cd`（**先後與 UI 命名相反**）。

**做法**：以「**欄位集合 + `AddFieldEvent(Self, DqN, …)` 的 DqN**」比對來判定每個 dfm grid 對應哪個 Dq，**不可照 grid 序或 DDBGridN 編號硬配**。歸屬不確定 → 寫 `open_questions` 交人工，不假設（鐵則4）。此判定結果記入 `manifest.crosscheck`（每筆標所屬 grid 的**業務名**，非 DDBGridN）。

> agent 依 `delphi-reading.md` 執行並覆核；`.pas` 的 AddFieldEvent/picker/SQL 擷取可先跑輔助工具 **`tools/pas_extract.py <B代碼.pas>`**（回 UTF-8 JSON：`addfieldevent`＝in_gettext、`pickers`＝輔助控件選擇、`sql_selects`＝best-effort in_sql）。SQL 擷取模糊，`decision` 仍由 agent 三方交叉判定，不以工具輸出當權威（鐵則4）。

---

## Node 3 — `extract.fact-resolve`（kind: agent）

| | |
|---|---|
| 讀 | `code` + `manifest.crosscheck` |
| 工具 | `.claude/SelfFolder/graph-engine/tools/query_index.py` |
| 寫 | `manifest.facts`（命中者）、`open_questions`（查無者） |
| 規則 | `CLAUDE.md#鐵則4-禁止推測` |

**流程（查表，不猜）**：
1. 程式身分：`query_index.py resolve <code>` → 取 b_code/正式名/ui_type。查無 → `open_questions`。
2. 每個要顯示成名稱的代碼欄：
   - keycode 類：`query_index.py keycode SAL <KEY>`
   - name 類：`query_index.py name SAL <KEY>`（SAL 查無→**再查 `name COMMON <KEY>`**：DEPID/FACTID/CUR/TRDTERM/PAYTERM/A(F)EMPLYID 等跨模組碼註冊在 COMMON）
   - `found:true` → 記入 `manifest.facts`；`found:false` → 記入 `open_questions`（**不可輸出原碼當名稱**）。
   - ⚠️ **`_Display` 必與 field-change 依賴交叉**（2026-09-22 由 SAL046 CUSTMER 學到）：即使 index 回「純轉換」，若該欄在 pas 有**連動依賴**（`AddFieldEvent`/`Args` 帶上層欄、`XxxChange` 依他欄過濾，如 CUSTMER 依 OBJTP），要標記為 **API 版 `DisplayTransformApi`＋extraParams**，非一般 `DisplayTransform`（見 `details/dto-display.md` 通則2、`field-change.md`）。判不準 → `open_questions`，勿逕用一般版。
3. 要寫 SQL/計算前：`query_index.py func <關鍵字>` → 命中則記 `reuse_funcs`（勿重寫）。

**查詢範例**（皆回 UTF-8 JSON）：
```
py .claude/SelfFolder/graph-engine/tools/query_index.py resolve SAL097
py .claude/SelfFolder/graph-engine/tools/query_index.py keycode SAL CLAS
py .claude/SelfFolder/graph-engine/tools/query_index.py name    SAL SALETP
py .claude/SelfFolder/graph-engine/tools/query_index.py func    GetMRate
```

**路由**（見 graph-spec.md）：
- `open_questions.none` → 往 `plan`
- `open_questions.any` → 往 `human-review`（名稱/keycode/表名不明先問，**絕不推測**）

---

## 一個真實例子（SAL087 跳號）

`query_index.py resolve SAL087` → `program.found=false`、`page_exists=false` → 自動寫入 `open_questions`「不在對照表，勿推測」→ 路由轉 human。**這就是本輪『SAL087–094 是否要做』從人工翻查變成一行查表的機制。**
