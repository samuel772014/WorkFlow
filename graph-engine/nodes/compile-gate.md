# Node 契約 — compile-gate（GATE 2，Step 5）

> **這是什麼**：static-verify 通過後的編譯守門，攔 CS/RZ 型別與 Razor 錯。
> **這是缺口 #3 的解**：鐵則 6 禁在 IKSERPUI 工作目錄 build（hot-reload 鎖檔、噴 MSB3021/3027 假錯），
> 導致型別錯要到 IDE 才爆。本 node 改在**隔離 git worktree** build，兩不相干。
> **kind: pure**（同輸入必同輸出）。

---

## 為什麼用 worktree（不是直接 build）

- IKSERPUI 常在 hot reload → 直接 `dotnet build` 卡檔案鎖 → MSB3021/3027（**假錯**，非編譯錯）。
- `git worktree add --detach <tmp> HEAD` 在別的目錄開一份複本，共用 `.git` 物件庫（快、省空間），
  build 在那裡跑，**不動、也不被** IKSERPUI 工作目錄影響。
- worktree 取的是 HEAD（已提交），故要把**未提交的產出檔**（gen-* 剛寫的）覆蓋進去再 build。

## compile_errors 結構

```yaml
compile_errors:
  - {file: SAL084.razor, line: 199, code: RZ1031, msg: "..."}
  - {file: SALRepository.SAL084.cs, line: 47, code: CS0246, msg: "..."}
```
**過濾規則**：只收 `error CS####` / `error RZ####`；**忽略 MSB3021/3027/3026**（檔案鎖假錯）；同 (file,line,code) 去重。

---

## 執行

**模式 1 — 隔離 build（正式）**
```
py .claude/SelfFolder/graph-engine/tools/compile_gate.py build IKSERPUI --files \
   IKSERPPRJ/IKSERPUI/Components/Pages/SAL/SAL084.razor
```
`--files` 帶入本次 gen-* 產出的檔（自 `state.artifacts`）；或用 `--changed` 疊入 git 工作區全部改動（修正輪建議用此，避免漏帶共用檔）。
- **預設離線**：複製 gitignore 的 `nuget.config` 與主 checkout 各專案 `obj/` 還原資產（project.assets.json 等）進 worktree，跑 `--no-restore`，不需連內部 feed／Telerik feed。目標專案從未在 IDE restore 過（無 project.assets.json）才自動走線上 restore；`--restore` 可強制線上。
- **結束碼把關**：dotnet 結束碼非 0 但抽不到 CS/RZ（如 NU1301 feed 不通、NETSDK1004）一律判失敗（`file:"-"`、code 取原錯誤碼），輸出帶 `exit_code`。2026-10-16 前的版本不檢查結束碼且不帶 nuget.config，UI 會因 restore 401 失敗卻誤判 pass。

**模式 2 — 解析既有 log（備援）**
```
py .claude/SelfFolder/graph-engine/tools/compile_gate.py parse <build.log>
```
IDE build 後貼出 log、或 CI 產物，只做錯誤過濾。當隔離 build 環境不可用時用這個。

---

## 路由（見 graph-spec.md）
- `compile_errors.none` → `human-review`（最終人工收尾）
- `compile_errors.any(file~cs)` → `gen-backend`（attempts<max）
- `compile_errors.any(file~razor)` → `gen-ui.assemble`（attempts<max）
- `attempts>=max` → `human-review`

---

## 現況
`compile_gate.py` 已實作 build/parse 兩模式；**錯誤過濾邏輯已用樣本驗證**（正確保留 CS/RZ、忽略 MSB302x、去重；非 CS/RZ 的 NU/NETSDK 於結束碼非 0 時採計）。2026-10-16 以 SAL055 實測：`build IKSERPAPI --changed`、`build IKSERPUI --changed` 離線 `--no-restore` 皆 exit_code=0。
