# Node 契約 — human-review（GATE 3 + interrupt + 閉環，Step 7）

> **這是什麼**：圖的最終人工關卡，也是 interrupt（可暫停/續跑）與**規則閉環**的入口。
> **這是缺口 #6 的解**：以前「建議→人工裁決→人工改 skill」是開迴路、無驗證；本 node 把它收成
> 「候選 skill diff → 使用者核可 → golden set 回歸 → 套用」的閉環。
> **kind: human**。

---

## 消費 / 產出（state）

| 讀 | 意義 |
|---|---|
| `findings`（PLAUSIBLE） | static-verify 需人判者 |
| `compile_errors` | 反覆修不好升上來的 |
| `open_questions` | 事實不明（名稱/keycode/表名，如 SAL087 跳號） |
| `open_decisions` | 需拍板（如 SAL083 REOP、SAL100 DB 方言） |

| 寫 | 意義 |
|---|---|
| `decisions` | 使用者裁決：`[{id, choice, date}]` |
| `skill_diff_candidates` | 從本次學到、可回饋 page-migration/index 的候選精進，待核可 |

---

## 流程

1. **呈報**：主 session 停下，把上述四類彙整給使用者（一次看完、集中裁決）。
2. **裁決**：寫入 `decisions`；依 human-review 出邊續跑
   - `decisions.reopen_facts` → 回 `extract.fact-resolve`（例：補了 keycode 註冊，重萃取）
   - `decisions.accepted` → `DONE`（收尾寫 `translation-log/<code>.md`）
3. **收斂閉環（若本次揭示了通則）**：
   - 產 `skill_diff_candidates`：具體到「改 page-migration 哪支 details / 加哪筆 index 註冊 / 調哪條 verify 規則」。
   - 記入既有 `.claude/SelfFolder/translation-log/_skill-feedback.md`（本專案原有的精進入口）。
   - **套用前必跑回歸**：`py tools/golden_check.py`
     - 全 PASS → 安全，套用該 skill/index 變更。
     - 有回歸 → 擋下，先修（避免新規則改壞舊頁）。

---

## 為什麼要 golden set 把關

規則是共用的：改一條 detail/verify 規則會影響**所有**頁。沒有回歸樣本，就是「改了規則、祈禱沒弄壞別頁」。
`golden_check.py` 對已定案頁重跑 `verify_static`，把「祈禱」變成「可驗證」——這就是閉環的最後一哩。

## 現況
`golden/goldenset.md`（10 頁：SAL083–100，皆 verify PASS）＋ `tools/golden_check.py` 已建並實測全綠。
候選 skill diff 沿用 `_skill-feedback.md` 為帳本，不另造。
