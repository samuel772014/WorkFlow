# 詳細規則：遇到商業邏輯的決策樹（怎麼判斷 + C# 落點）

> 轉譯遇到「含業務規則的邏輯段」（計算、帶值、DB 讀寫、共用函式）時讀本檔。
> 先分類、再決定落點，**不臆測共用函式內部規則**。
> 與 `details/shared-functions.md`「⚠️ 封裝成函式的商業邏輯 → 寫進 log」一節交叉：本檔講「怎麼分四類、各類落哪」，該節講「入 log 的格式與 TODO 佔位」，兩邊互相指路、勿重抄。

---

## 判斷順序（先問第 1 類，再分其餘）

> **一定先看有沒有踩共用 FUNC 函式（第 1 類優先）**；確定沒有，才往下分「計算 / 填值 / DB」。

```
遇到一段商業邏輯
      │
      ├─(1) 有依賴共用 FUNC 函式？ ──是──┬─(1a) 該 FUNC 已有 C# 版（Modules/FUNC，如 ERPFunc.GetMRateAsync）
      │            （否）              │        └─► 包一支共用 SALService 方法呼叫它，各頁 resolver 薄層轉發（不留 TODO）
      │                               └─(1b) 該 FUNC 尚未移植 C#（如授權層 SAL_DataCtrl）
      │                                        └─► 不重寫；留 // TODO(封裝商業邏輯) + 登記 TODO彙整.md + 告知使用者
      ├─(2) 有計算邏輯？ ──金額/稅額/匯率/數量或結果會存檔──► 後端（同 field-change「計算一律後端」）
      │                 └─僅顯示便利計算（不存檔、非金額稅額數量）──► 【第 2 類】前端 iksUiFunc.SAL.cs
      │            （否）
      ├─(3) 單純填值/帶值（選值帶出其他欄位、無業務計算）？ ──是──► 【第 3 類】直接在 razor 事件處理封裝
      │            （否）
      └─(4) 後端 DB 讀寫、無共用函式依賴 ──────────────────────► 【第 4 類】Service/Repository 直接實作
```

---

## 四類明細

### 【第 1 類】有依賴共用 FUNC 函式 → 先看該 FUNC 有沒有 C# 版

- **怎麼判斷**：邏輯段呼叫到共用/FUNC 封裝函式，如 `Get_MRATE` / `Calcu_MNYTAX` / `CalcNTMNY` / `GetTaxRate` / `GetCUSTNSN` / `Get_PAYTERM` / `SALGetUp` 等（完整常用表見 `details/shared-functions.md`「常用（SAL 相關）」）。
- **關鍵：先查 `Modules/FUNC`（ERPFunc/SALFunc…）是否已有該函式的 C# 版**（見 details/shared-functions.md），分兩條路：

#### 1a. 共用 FUNC 已有 C# 版 → 包共用 SALService 方法 + 各頁 resolver 轉發（**不留 TODO**）

- 例：`Get_MRATE` → `ERPFunc.GetMRateAsync` 已存在。
- 作法：在共用 `SALService.cs` 包一支頁面無關方法（如 `GetSALCurMrateAsync`）**呼叫該 FUNC**，把「參數差異」（如 MTP/IOTP/日期）用 arg 帶入並給預設值；**各頁 GraphQL resolver（`salXXX_GetCUR_MRATE`）薄層轉發同一份**，勿各頁自寫或另查 SS_MRATE。詳見 `details/shared-functions.md`「後端共用函式抽取規則」。
- **不留 TODO、不入 log 待辦**（已接妥共用層）；若這是把原本各頁重複實作收斂，於回報說明即可。

#### 1b. 共用 FUNC 尚未移植 C#（無對應 C# 函式）→ 留 TODO + 入 log 告知

- 例：資料權限 `SAL_DataCtrl` 授權層尚未移植。
- **不重寫共用函式內部規則**，在 C# 對應位置留佔位：

  ```csharp
  // TODO(封裝商業邏輯): {函式名} 待接共用層，見 TODO彙整.md
  ```

- **回報**：把該函式登記進 `.claude/SelfFolder/TODO彙整.md`（**待辦權威**；格式 `檔名:行 說明`，分類見 `details/shared-functions.md` 該節），`translation-log` 只記流水帳；並在轉譯回報中**明確告知使用者**有這幾個待接共用層的項目。

### 【第 2 類】顯示便利計算（例外）→ 前端 iksUiFunc.SAL.cs 封裝

- **怎麼判斷**：只是算術/組值/格式換算（例如把兩欄位相乘、依規則組字串），**沒有踩到任何共用 FUNC 函式**。
- **C# 落點**：寫在前端共用 helper —— `IKSERPUI\iksUiFunc\iksUiFunc.SAL.cs`，是 `IKSERPUI\iksUiFunc\iksUiFunc.cs` **同一個 class 的 partial**（`partial class iksUiFunc { ... }`，SAL 模組專用方法集中於此）。razor 事件呼叫封裝好的方法。

  ```csharp
  // IKSERPUI\iksUiFunc\iksUiFunc.SAL.cs（namespace IKSERPUI.iksUiFunc）
  // 與 iksUiFunc.cs 同一個 class 的 partial；該 class 為 public static partial class IksUiFunc（大寫 I）
  public static partial class IksUiFunc
  {
      // SAL 模組純計算：無共用函式依賴才放這
      public static decimal? CalcNtByRate(decimal? money, decimal? mrate)
          => (mrate is > 0) ? money * mrate : money;
  }
  ```
  ```razor
  @* razor 事件呼叫（完整命名空間 IKSERPUI.iksUiFunc.IksUiFunc，或 @using 後直接 IksUiFunc）*@
  current.NTMNY = IksUiFunc.CalcNtByRate(current.MNY, current.MRATE);
  ```
  ⚠ 若 `iksUiFunc.cs` 的 class 原本非 `partial`，改成 `partial` 才能分檔（Agent B 已於 SAL045 補上）。

- ⚠️ **可放前端的判準（三者皆須成立）**：① 無共用函式依賴；② 結果**不存檔**（只顯示）；③ 不是金額/稅額/匯率/數量計算。任一不成立 → 後端（與 `details/field-change.md`「計算一律後端」一致，本類為其唯一例外）。不確定就當後端並問使用者。

### 【第 3 類】單純填值/帶值（無業務計算）→ razor 事件直接封裝

- **怎麼判斷**：選一個值就帶出其他欄位、清空相依欄、切換顯示，**沒有計算、沒有共用函式**。
- **C# 落點**：直接寫在 razor 的 change 事件處理（`@bind-Value:after`）。ComboBox 只回代碼名稱要帶其他欄位就打後端連動查詢（見 `details/field-change.md`）；EditPick 多欄用 Apply row 前端帶。

### 【第 4 類】後端 DB 讀寫、無共用函式依賴 → Service/Repository 直接實作

- **怎麼判斷**：純資料查詢/寫入，**沒有踩共用函式**（若這段查詢會被 ≥2 頁重用，改走 `details/shared-functions.md`「後端共用函式抽取規則」）。
- **C# 落點**：當前模組的 `SALService.SALxxx.cs` / `SALRepository.SALxxx.cs` 直接實作；GraphQL resolver 薄層轉發（見 details/crud-handlers.md「後端分層」）。

---

## 指路

- 第 1 類入 log 格式、常用函式表 → `details/shared-functions.md`
- 後端查詢被多頁重用要抽共用 → `details/shared-functions.md`「後端共用函式抽取規則」
- 欄位連動/計算送後端 → `details/field-change.md`
- 後端 SQL/交易、resolver 薄層 → `details/backend-sql.md`、見 details/crud-handlers.md「後端分層」
