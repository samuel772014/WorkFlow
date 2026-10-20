# 詳細規則：Delphi 共用函式庫 ↔ C# 對照（指路）

> **權威對照表＝`.claude/SelfFolder/共用函式對照表.md`**（Delphi 函式名 → C# 方法名 / 所在 .cs / 狀態 / 用途）。本檔不再重抄，避免兩份不同步。
> 狀態（✅/🚧）以程式碼為準，定期重掃：`py .claude/SelfFolder/graph-engine/tools/func_status_scan.py`（加 `--apply` 寫回）。
> 處理策略與佔位規則見 `details/shared-functions.md`；分類落點見 `details/business-logic.md`。

## 函式庫 → C# 檔

| Delphi 函式庫 | C# 檔案（`IKSERPAPI/Modules/FUNC/`） |
|---|---|
| `ERPFunc` | `ERPFunc.cs` |
| `SALFunc` | `SALFunc.cs` |
| `MPSFunc` / `MPSFunc1` / `MPSFunc2` / `MPSFunc3` / `MPSFuncP` | 同名 `.cs` |
| `MPS_Gfunc` | `MPS_GFunc.cs` |
| `StkFunc` | `STKFunc.cs` |
| `BseFunc` / `BuyFunc` / `CstFunc` / `Bsalem_uncf` | 無（作廢或併入個別程式） |

查不到對應或狀態 🚧 → 依 `details/shared-functions.md`「封裝成函式的商業邏輯」留 TODO 並登記 `TODO彙整.md`，不自行重寫。
