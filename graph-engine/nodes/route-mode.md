# Node 契約 — route-mode（進入點：判範本模式）

> **這是什麼**：整張圖的 `entrypoint`。讀來源判斷本頁該用哪個**範本模式**，產出候選＋理由，最終由 `human-review` 確認（鐵則2「遷移以參考程式為單位」、鐵則5「嚴格照範本」）。
> **runner**：主 session（讀 dfm/pas 提案）→ 交 human 確認。
> **精神**：**不自動拍板**。有 `AddDetail`（明細）或繼承鏈時，一律**先問轉譯操作者**，不自行判單檔/明細（見 `details/toolbar.md` 模式選擇註）。
> **規則來源**：`skills/page-migration/SKILL.md#步驟1-選擇使用範本`。

---

## 讀 / 寫

| | |
|---|---|
| 讀 | `code`、`sources.dfm_path`／`sources.pas_path`（＋ `sources.base_pas` 繼承鏈） |
| 寫 | `mode`、`mode_confirmed`、（繼承鏈/模式不明時）`open_questions` |
| runner | 主 session |
| rules_ref | `skills/page-migration/SKILL.md#步驟1-選擇使用範本` |

---

## mode 值域（範本）

| mode | 何時 | 範本 |
|---|---|---|
| `single-file` | 單一主表維護（明細已無使用，如 B101/SAL001） | `templates/single-file.md` |
| `master-detail` | 主檔＋明細（來源有 `AddDetail`，且確認明細仍在用） | `templates/master-detail.md` |
| `excel-import` | Excel 匯入型 | `templates/excel-import.md` |
| `selectform` | 選擇/穿梭清單型 | `templates/selectform.md` |
| `dropform` | 雙表穿梭撥轉作業頁（查候選→挑→批量設定→撥轉；**非 CRUD**） | `templates/dropform.md`（藍本 SAL058/B407） |
| `特例` | 不屬上列 → 標記後跳過，**不自行設計解法**（鐵則2） | — |

> **view_mode（呈現模式：incell/telerik-window/tab-browse-detail）不在此決定**——那是 `plan` 的「分頁」三問之一（見 `nodes/plan.md`）。route-mode 只定**範本 layout**。
> **dropform 例外**：無編輯 Window、無 view_mode；其 fragment 形狀自成一格（工具列動作／來源 grid／目標 grid InCell／篩選 popup／批量 popup），gen 階段照 `templates/dropform.md` 走，不套 gen-ui.editwindow/tabview。

---

## 判斷流程（提案，不拍板）

1. 讀 dfm/pas，看是否有 `AddDetail`（明細）、是否 Excel 匯入、是否選擇型清單。
2. **有明細 or 有繼承鏈（`base_pas` 非空）** → 產候選＋理由，寫 `open_questions`（「單檔或主檔明細？」「繼承鏈 base 是誰？」），**轉 human 先問**。
3. 明確單一情形（無明細、無繼承）→ 提 `mode` 候選，仍交 human 確認（`mode_confirmed=false` → true）。
4. 不屬任何範本 → `mode: 特例`，標記跳過。

---

## 路由（見 graph-spec.md）
- `mode_confirmed`（human 已確認）→ `extract.dfm-decode`
- `mode_ambiguous`（含 open_questions：明細/繼承/特例未定）→ `human-review`

> route-mode 是 fan-out 之前、整圖之始；模式未經 human 確認，不得進 extract（避免用錯範本骨架整串白做）。
