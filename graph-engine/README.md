# Graph Engine — Delphi→C# 遷移的圖式 AI 工作流

> 全新獨立架構，與 `.claude/skills/page-migration` **並列**（不取代它）。
> page-migration 仍是**轉譯規則的唯一真實來源**；本 graph engine 只負責**編排**（把「一次做完＋人工複查」改成「宣告式圖＋狀態＋品質閘門」）。
> 載體：**宣告式 spec（本資料夾）＋ Claude Code agents（各 node 一支）**，主 session 依 spec 編排。零新 runtime。
> 位置：`.claude/SelfFolder/`（個人空間，gitignore，不影響 repo／團隊）。

---

## 為什麼要這層

現況是一張「沒被宣告出來的隱式圖」：編排在主 session 的人腦裡、狀態散在 markdown、沒有 verify/compile 守門、429 中斷即失、規則回饋是開迴路。本 engine 把它變成可宣告、可續跑、可自動檢察的圖。

對應解掉的缺口（見架構圖 #1–#6）：
1. verifier 只在文件無實體 → 補 `static-verify` node
2. S1–S9 靠主觀自我宣告 → verifier 機器判 ＋ 知識圖譜交叉
3. 禁 shell build（鐵則 6）致型別錯漏網 → `compile-gate` 用隔離 worktree build
4. 批次不能續跑 → `state.schema.yaml` 的 `stage`/`nodes.status` ＋ checkpoint
5. 重複性錯誤（研判名／_Display／keycode／方言）無守門 → `extract.fact-resolve` 查知識圖譜
6. 規則回饋開迴路 → `human-review` 產候選 skill diff ＋ golden set 回歸

---

## 三份地基檔（Step 1 產出）

| 檔案 | 角色（graph engineering 術語） |
|---|---|
| `graph-spec.md` | **Spec** — nodes / edges / entrypoint / 條件路由 / 終止條件（md 說明＋內嵌 ```yaml 圖定義） |
| `state-schema.md` | **State** — per-program run state 的 schema、reducer、checkpoint 約定（md 說明＋內嵌 ```yaml 範本） |
| `README.md` | 本檔 — 定位、如何編排、與現有 skill/docs 的接點 |

> 檔案格式採**混合**：說明文件與段落解說用 md，spec/state 的結構用 md 內嵌 ```yaml 區塊（對 agent 機器可讀、對人可讀可註解）。

---

## Node 粒度原則（切到這裡為止，不再往下）

一個步驟**至少一條成立**才升為獨立 node，否則留作 node 內部步驟（由 page-migration 的 `details/*.md` 驅動）：
1. 產出獨立可驗證的 artifact
2. 可被單獨快取／重跑（純函式最該切）
3. 需要不同模型／工具／能力
4. 是自然的 human-in-the-loop 暫停點

→ 因此：**萃取切細**（純／可快取／擋推測），**生成分兩步**（`plan` 讀 pas+dfm 產骨架藍圖＝第一步；`gen-*` 照藍圖實作＝第二步），**驗證單一 node 內跑 S1–S9**。

**生成第二步的 fragment 切法（2026-09-21 重構）**：
- **組合類（fan-out 全跑）**：`gen-ui.toolbar` / `gen-ui.grid`（含 filter 區＋欄位＋InCell＋DTO）/ `gen-ui.detail`（無明細則不啟動）。
- **呈現模式類（條件邊擇一）**：依 `skeleton.pages.view_mode` 只啟動一支——`incell`（留在 grid）/ `telerik-window`→`gen-ui.editwindow` / `tab-browse-detail`→`gen-ui.tabview`。
- **子視窗類（條件邊，有才跑）**：`skeleton.pages.subwindows` 非空→`gen-ui.subwindow`（多個內部序理；popup/picker/excel 三型，如 SAL046 備註窗/Excel 匯入窗、SAL0XXA/B/D）。2026-09-22 測 SAL046 補上。
- 原則：組合(全都要)用 fan-out、互斥模式(只要一種)＋子視窗(有才跑)用條件邊 → **不產空 node**。逐 fragment 檢查清單見 `nodes/fragment-check.md`。

---

## 與現有資產的接點（不重造）

| 本 engine 用到 | 現有來源 |
|---|---|
| 轉譯規則 | `.claude/skills/page-migration/`（SKILL.md + templates/ + details/） |
| 架構鐵則 | `CLAUDE.md` |
| 驗收判準 S1–S9 | `.claude/SelfFolder/checklist/acceptance-criteria.md` |
| DFM 權威解碼 | `.claude/skills/page-migration/tools/dfm_decode.py`、`dfm_audit.py` |
| 偏離／park 紀錄 | `.claude/SelfFolder/translation-log/<code>.md`（append-only reducer） |
| 全域待辦（改為 derived） | `.claude/SelfFolder/TODO彙整.md` |
| 既有執行者／規劃者 | `.claude/agents/migration-executor.md`、`thinking-planner.md`（後續併入對應 node） |

---

## 實作路線圖（每步收尾停下確認）

- **Step 1 ✅ 地基**：目錄 + `graph-spec.md` + `state-schema.md`
- **Step 2 ✅ 知識圖譜 index**：`tools/build_index.py` → `index.json`（餵 `fact-resolve`）
  - 索引四類事實：programs(91)、display_transforms(keycode 274 / name 253)、func_reuse(416 方法)、existing_pages(127)
  - 重建：`PYTHONIOENCODING=utf-8 py .claude/SelfFolder/graph-engine/tools/build_index.py`（repo 根執行）
  - `index.json` 為產物、勿手改；來源檔變動後重跑本 script 重建
- **Step 3 ✅ `extract` 三 node**：契約 `nodes/extract.md` + 查詢工具 `tools/query_index.py`
  - dfm-decode（用 dfm_decode.py）→ `manifest.fields`
  - field-cross-check（dfm×SQL×gettext）→ `manifest.crosscheck`
  - fact-resolve（用 query_index.py 查 index.json）→ `manifest.facts` / `open_questions`
  - 查詢：`py tools/query_index.py <prog|keycode|name|func|page|resolve> args`（回 UTF-8 JSON）
- **Step 4 ✅ `static-verify`（GATE 1）**：契約 `nodes/static-verify.md` + 機器判工具 `tools/verify_static.py`
  - C1 route/title、C2 標題=對照表名、C3 xform KEY 已註冊、C4 grid _Display 已接上
  - S2–S8 由 agent 覆核、執行期/人眼留 human-review
  - 用法：`py tools/verify_static.py <SALxxx> [--pretty]` → findings JSON
  - 實測即抓到 SAL095/096/099/100 標題非對照表正式名（人工複查漏掉者）
- **Step 5 ✅ `compile-gate`（GATE 2）**：契約 `nodes/compile-gate.md` + 工具 `tools/compile_gate.py`
  - 隔離 git worktree build（避 hot-reload 檔案鎖，鐵則 6）；只收 CS/RZ，忽略 MSB3021/3027
  - build 模式（需 dotnet+nuget feed）／parse 模式（解析既有 log，備援）
  - 用法：`py tools/compile_gate.py build IKSERPUI --files <razor…>`
- **Step 6 ✅ 編排慣例**：`ORCHESTRATION.md`（主迴圈、node→runner 對應、路由求值、人工暫停、續跑、trace）+ 唯讀助手 `tools/run_state.py`
  - 主 session 即 orchestrator：載入 state → 跑 stage 的 node → 寫回 → 依邊求下一步 → checkpoint → 重複
  - state 寫入由編排 agent 直接改 plans/<code>.md front-matter；`run_state.py show|next` 供巡檢/續跑（唯讀，免 pyyaml）
- **Step 7 ✅ 閉環**：契約 `nodes/human-review.md` + golden set `golden/goldenset.md` + 回歸工具 `tools/golden_check.py`
  - human-review 產候選 skill diff（記入既有 `_skill-feedback.md`）→ 套用前必跑 `golden_check.py`
  - golden set 全 PASS 才准套規則/index 變更；有回歸即擋下（避免改壞舊頁）
  - 實測：10 頁（SAL083–100）全綠

---

**✅ Step 1–7 全部落地。** graph-engine 骨幹完成：spec／state／知識圖譜／萃取／GATE1 檢察／GATE2 編譯／編排慣例／閉環回歸。

**節點契約覆蓋**（`nodes/*.md`）：`route-mode`、`extract`（三 node）、`plan`、`gen`（gen-backend/gen-ui.*/assemble）、`fragment-check`（GATE0 逐 area 清單）、`static-verify`、`compile-gate`、`human-review` — **全 node 皆有契約**。

後續為「啟用」與「擴充」（非骨幹）：
- **`migration-executor` scope 化**：gen-* 實跑前，需讓它認得 `scope=backend|toolbar|grid|detail|editwindow|tabview|subwindow|assemble`（見該 agent「graph-engine scope 模式」段）。
- `pas_extract.py`（輔助 field-cross-check，見 `tools/`）、擴大 golden set（涵蓋新 fragment 五分類與三種 view_mode）。
