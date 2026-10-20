---
name: retro
description: 對一段工作 session 做回顧，提出 agent 環境（skill／CLAUDE.md／GATE 檢查／工具）的改進候選
disable-model-invocation: true
---

# retro — 工作 session 回顧

> 改編自 mattpocock/skills `retro`（原版：`.claude/SelfFolder/reference/mattpocock-skills/retro/SKILL.md`）。
> 目標是改**環境**讓下一輪更好，不是改這次的程式碼。

## 步驟

1. **讀寫作準則**：`.claude/SelfFolder/reference/mattpocock-skills/writing-for-agents/SKILL.md`（＋同目錄 `SKILL-MECHANICS.md`）。完成＝提案措辭依其 context pointer／leading word／否定句／pruning 原則。
2. **讀 session 原始紀錄**：使用者指定的 session；未指定＝目前這個。舊 session 在 `~/.claude-acct2/projects/D--demo-repository/<session-id>.jsonl`。完成＝每個工具錯誤、使用者更正、重做、長時間找檔都已列出。
3. **逐類找候選**（下表）。完成＝每類都有結論（有候選或「無」）。
4. **呈報**：候選依嚴重度排序，每條寫「現象（附 session 證據）→ 建議改哪個檔的哪段」；用 AskUserQuestion 讓使用者勾選要做哪些（推薦項排第一），選定後先列預期修改再動手。

## 候選類別

| 類別 | 何時看 | 改進落點 |
|---|---|---|
| **導覽** | 花很久才找到某資訊、讀錯檔、漏讀隱性相依 | `page-migration/SKILL.md` details 索引、node `rules_ref`、details「指路」段補 navigation pointer |
| **自動檢查** | agent 犯了可用 regex／結構判定的錯 | 加進 GATE1 `graph-engine/tools/verify_static.py`（C 系列）；先查既有 C1–C12 是否已有但沒接上或失效 |
| **審查規則** | review-engine 漏抓、或規則本身有誤 | 先分類：**機械式**（固定語法、禁用 API、檔案位置）→ 做成 verify_static 檢查；**需判斷**（跨檔一致、語意對 Delphi）→ 補進對應 `review-*/SKILL.md` 檢查清單 |
| **CLAUDE.md 膨脹** | `CLAUDE.md` 或使用者全域設定變長 | 會演進的慣例移到 skills/details，CLAUDE.md 只留鐵則與指路 |
| **工具耗費** | 整檔讀大檔、重複呼叫、輸出過長的工具 | 改用 `query.py`／`query_index.py` 局部查、或為工具加篩選參數 |
| **無效規則（no-op）** | steering 檔長且雜 | 刪掉不改變行為的句子；太弱的 leading word 換更強的詞 |
| **資訊可得性** | 關鍵資訊 agent 拿不到（執行期 log、DB 結構、Delphi 子 form 未索引） | 補索引（`index.json`、review-engine scope）、或提供唯讀查詢工具 |

## 原則

- **實作 vs 審查**：實作 agent context 壓力最大，規範盡量交給審查端（review-engine）或機器（verify_static）擋，不堆在實作端的常駐指示。
- **鐵則 4 同樣適用**：每條候選都要有 session 裡的具體證據（哪一步、哪個錯誤訊息）；沒有證據的「感覺可以更好」不列。
