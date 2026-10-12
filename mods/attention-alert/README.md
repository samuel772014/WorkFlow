# attention-alert（注意提醒）

Claude 工作告一段落或需要你回應時，用醒目色塊標記，並推播到手機。

| 情況 | 畫面 | 何時消失 |
|---|---|---|
| Claude 問你選擇題（AskUserQuestion） | 選擇題框頂端紅底「⚠ 需要你裁決」 | 回答後 |
| 需要核准工具權限 | 輸入框上方黃色「⚠ 等待你核准」＋對話框下方一行提示 | 核准／拒絕後 |
| 主對話一輪結束 | 輸入框上方綠色「✔ 工作完成，等你下一步」＋回覆開頭與時間 | 按「知道了」或送出新訊息 |
| 因錯誤中斷 | 輸入框上方紅色「✗ 工作中斷」 | 按「知道了」或送出新訊息 |

- 狀態列同步顯示同一則提醒
- 子代理（subagent）完成不提醒，只有主對話才提醒
- 會與 agent-progress-bar 的進度帶並存（疊在其上方）

## 手機推播

每種提醒都會呼叫 PushNotification。前提：

1. session 連上 Remote Control（桌面 app 設定「Connect new sessions to Remote Control」開啟）
2. 手機安裝 Claude App、同帳號登入並允許通知

你正在看畫面時，系統會判斷 `user_present` 自動略過，不會重複推。

## 建議一併開啟的桌面 app 設定

- Draw attention on notifications：視窗不在前景時工作列閃爍
- Connect new sessions to Remote Control：手機推播前提

## 安裝

在 terminal 版 Claude Code 輸入框執行（user 範圍安裝後桌面 app 也會載入）：

```
/plugin install attention-alert --marketplace samuel772014/WorkFlow
```

或在 shell 執行：

```bash
claude plugin marketplace add samuel772014/WorkFlow
```

```bash
claude plugin install attention-alert@samuel-workflow --scope user
```

## 開發

- 主程式：`hooks/register.tsx`；狀態型別：`types/index.d.ts`
- 檢查：`claude plugin validate mods/attention-alert`
- 測試：`claude plugin test mods/attention-alert`
