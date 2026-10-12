# agent-progress-bar（背景作業進度條）

所有背景作業在 Claude Code 輸入框上方以彩色進度條顯示：完成幾項、目前幾項執行中。

```
背景作業 ██████████░░░░░░░░░░ 2/4 (50%)  執行中 2  [收合]
◐ [Agent] 寫API (general-purpose)       ← 紅：執行中
◐ [指令] 等待 build 完成 (Bash)          ← 紅：執行中
✔ [監看] 監看 log (Monitor)             ← 綠：完成
✗ [Agent] 讀標題 (Explore)              ← 紅：失敗
```

## 追蹤的背景作業

| 類型 | 來源 | 結束判定 |
|---|---|---|
| Agent | Agent / subagent（前景、背景皆算） | 子代理該輪結束 |
| 指令 | Bash／PowerShell 背景執行（run_in_background、Ctrl+B、逾時轉背景） | 背景作業完成通知 |
| 監看 | Monitor | 背景作業完成通知 |
| 其他 | 每輪結束時 app 回報的執行中背景作業（workflow 等漏追的） | 每輪結束對帳 |

- 每輪結束時會與 app 的「執行中背景作業」清單對帳：補上漏追的，已不在清單上的標記完成
- teammate 不計入（多輪、沒有明確完成點）

## 畫面

- 總進度條：已完成綠色 `█`、未完成紅色 `░`，顯示 `完成數/總數 (百分比)` 與「執行中 N」，有失敗時加 `✗N`
- 每項作業一行：執行中 `◐`／失敗 `✗` 紅色，完成 `✔` 綠色
- 「收合／展開」按鈕；全部成功時自動收合，有新作業啟動時自動展開
- 狀態列同步顯示一行文字進度
- 只有使用者自己送出新訊息、且沒有執行中的作業時才清空（作業回報、背景通知不會清空）

## 安裝

在 terminal 版 Claude Code 輸入框執行（安裝在 user 範圍後，桌面 app 的 Code 分頁也會載入）：

```
/plugin install agent-progress-bar --marketplace samuel772014/WorkFlow
```

出現 `Add marketplace?` 回答 `y`，範圍選 user。

或在 shell 執行：

```bash
claude plugin marketplace add samuel772014/WorkFlow
```

```bash
claude plugin install agent-progress-bar@samuel-workflow --scope user
```

## 更新 / 停用

```bash
claude plugin marketplace update samuel-workflow
```

```bash
claude plugin disable agent-progress-bar@samuel-workflow
```

## 開發

- 主程式：`hooks/register.tsx`；狀態型別：`types/index.d.ts`
- 檢查：`claude plugin validate mods/agent-progress-bar`
- 測試：`claude plugin test mods/agent-progress-bar`
- 本機直接改檔測試：`claude --plugin-dir mods/agent-progress-bar`
