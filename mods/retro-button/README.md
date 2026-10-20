# retro-button（回顧按鈕）

在 Claude Code 輸入框上方畫一列，session 收尾時一鍵執行 `/retro`：

```
Session 要結束了嗎？ [回顧此 session (/retro)] [隱藏]
```

- 第一輪工作完成後才出現；模型工作中或有問卷時不顯示
- 按「回顧」等同輸入 `/retro`，執行後收起；手動打過 `/retro` 也不再顯示
- 按「隱藏」只在本 session 內關掉

需搭配專案的 `retro` skill（`.claude/skills/retro/`），找不到時會跳提示。
