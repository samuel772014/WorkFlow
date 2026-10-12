# agent-progress-bar（Agent 進度條）

使用 Agent / subagent 時，在 Claude Code 輸入框上方顯示彩色進度條。

```
Agents ██████████░░░░░░░░░░ 1/2 (50%)  [收合]
◐ 寫API [general-purpose]       ← 紅：執行中
✔ 查欄位 [Explore]              ← 綠：完成
✗ 讀標題 [Explore]              ← 紅：失敗
```

## 功能

- 總進度條：已完成部分綠色 `█`、未完成紅色 `░`，顯示 `完成數/總數 (百分比)`，有失敗時加 `✗N`
- 每個 agent 一行：執行中 `◐`／失敗 `✗` 為紅色，完成 `✔` 為綠色
- 「收合／展開」按鈕；全部成功時自動收合，有新 agent 啟動時自動展開
- 狀態列同步顯示一行文字進度
- 只有使用者自己送出新訊息時才清空上一批（agent 回報、背景通知不會清空）
- teammate 不計入（多輪、沒有明確完成點）

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
