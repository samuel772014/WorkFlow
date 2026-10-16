# handoff（交接按鈕）

Context 用到 70% 時，在 Claude Code 輸入框上方出現「交接」按鈕。按下去會：

1. 依目前對話寫一份交接摘要：目前的目標、已完成、尚未完成、改過的檔案、注意事項
2. 存成 `.claude/handoff/handoff-<YYYYMMDD-HHmmss>.md`（相對於工作目錄）
3. 執行 `/clear` 清空對話
4. 把摘要當成新對話的第一句送出

摘要失敗時顯示錯誤訊息與「重試交接」按鈕。會保留同一條帶上其他 mod（如 usage-band）畫的內容。
