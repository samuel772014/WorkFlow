---
name: review-permission
description: review-engine area.permission 審查清單（佔位，尚未實作，area-plan 一律 skip）
disable-model-invocation: true
---

# review-permission — 權限審查（佔位）

> **狀態：佔位，未實作**（2026-10-08 使用者裁決：權限另開一區、後續補上）。`area-plan` 一律將本區列入 `skip`（理由「佔位」），`review_state.py` 驗證也禁止 permission 出現在 `areas.run`。
> 區代碼 **PRM**。

## 待補項目
- page-migration 增加權限索引（指向 skill `permission-policy`）。
- 以 Delphi 權限控制（按鈕 Enabled 依權限、`SAL_DataCtrl` 等）為基準，對照 C# EIP 控件權限（`SYSID.PROGID.CTRLCLASS`）與 Policy 的檢查清單。
- 與 `review-button`（啟用條件）、`review-special-logic`（資料權限）的邊界。
