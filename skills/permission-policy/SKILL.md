---
name: permission-policy
description: IKSERP 權限 Policy 的規則與用法（頁面/按鈕/API 權限、EIP 控件權限、claims）。當使用者要「擋一個頁面/按鈕」「加權限控制」「這個功能誰能看/能按」「VIEW/APRV/EXPO 怎麼設」，或問「權限怎麼擋 / 為什麼被擋 / Policy 怎麼寫」時觸發。以 EIP 控件權限（SYSID.PROGID.CTRLCLASS 黑名單）與身分屬性（EipClaim）兩套為準。
---

# IKSERP 權限 Policy 規則

> 一句話：**Policy 管「能不能」、Claim 管「顯示什麼」。** 權限權威在 EIP，子系統不自查、不直連 EIP DB。
> 完整背景：`IKSERPPRJ/IKSERP開發文件/EIP權限設定與Policy.md`。測試頁：`/BaseTemplate/PermissionDemo`。

## 觸發時機

要擋頁面/按鈕/API、加權限控制、問「誰能看/能按」「為什麼被擋」「VIEW/APRV 怎麼設」。

## 三種 Policy 格式（靠名稱自動分流，`Auth/Auth/PermissionPolicyProvider.cs`）

| 格式 | 範例 | 判斷 | Handler |
|---|---|---|---|
| **① 身分屬性** `EipClaim:{型別}:{值}` | `EipClaim:ENTID:DEMO001` | 直接比對交接 claim 相等，**不查 DB** | `ClaimValueHandler` |
| **② 操作層級** `SYSID.PROGID.CTRLCLASS` | `ERPTW.SAL055.APRV` | 拿 `USRID` 問 EIP `/module/permission` 拿**被禁清單** | UI:`EipPermissionHandler`／API:`DbPermissionHandler` |
| **③ 靜態具名** | `SalesOnly`/`HROnly` | `RequireClaim` | 退回 `DefaultAuthorizationPolicyProvider` |

## 控制點地圖：讀取 vs 按鈕 vs API 分別在哪擋

「讀取」和「按鈕」走**同一套②機制**，差別只在 **CTRLCLASS 值**與**掛的層**：

| 想控制 | 在哪掛 | CTRLCLASS |
|---|---|---|
| **選單看不看得到** | 資料 `EIP_GRPMENU`（`ModuleMenuService` 過濾） | —（比對 MENUID） |
| **能不能進頁（讀取/檢視）** | 頁面 `@attribute [Authorize(Policy="ERPTW.SAL055.VIEW")]` → `Routes.razor` 的 `AuthorizeRouteView` | **`VIEW`** |
| **按鈕/操作（核准/匯出…）** | 按鈕外包 `<AuthorizeView Policy="ERPTW.SAL055.APRV">` | **`APRV`/`EXPO`/`APLY`…** |
| **API 端真正把關** | resolver/controller `[Authorize(Policy=...)]` | `DbPermissionHandler` |

```
① 選單(EIP_GRPMENU) → 看不到入口   ② 頁面 VIEW → 進不去   ③ 按鈕 CTRLCLASS → 按不了   ④ API → 真正安全邊界
```
> ⚠️ ①②③ 都是**前端層**（改網址/F12 可繞），**只有第 ④ 層 API 才算安全**。目前 API 端 `DbPermissionHandler` 還需 IKSERPUI→IKSERPAPI 身分橋接（`EipApiTokenAccessor`）才生效，是待辦；現階段前端擋屬「體驗/引導」。

## 判斷語意（鐵則）

1. **黑名單制**：②回的是「被禁清單」，**空 = 全開**；「有存取權 + 不在被禁清單 + 是合法操作」三者皆成立才放行。
2. **fail-closed**：`CTRLCLASS` 必須是該程式 `EIP_PROG.CTRLCLASS` **登記過**的合法操作；打錯字（`APRV`→`ARPV`）或沒登記 → **不管誰登入都被擋**。
3. **沒 `USRID` claim → 一律不放行**（非 EIP 交接的 session）。
4. **UI 已接 EIP**，不再讀 permission claim、不查 `SS_` 舊表。
5. **EIP 連不上**：`EipPermissionClient` fail-closed 回拒絕，失敗**不進快取**（下次重試）；正常結果快取 5 分鐘。

## 怎麼用（抄法）

```razor
@* 擋整頁（讀取/檢視）*@
@attribute [Authorize(Policy = "ERPTW.SAL055.VIEW")]

@* 擋按鈕/區塊（操作）*@
<AuthorizeView Policy="ERPTW.SAL055.APRV">
    <Authorized>通過才看得到（核准鈕放這）</Authorized>
    <NotAuthorized>沒通過（可省略）</NotAuthorized>
</AuthorizeView>

@* 身分屬性型 *@
@attribute [Authorize(Policy = "EipClaim:ENTID:DEMO001")]
```

- **前提**：要用 `SAL055.APRV`，得先在 `EIP_PROG.CTRLCLASS` 登記該程式有哪些操作（如 `'VIEW;APRV;EXPO'`），否則 fail-closed 全擋。
- **Claim 只管顯示**（「你好，○○○」）：`state.User.FindFirst("USRNM")?.Value`，與權限無關。
- 可用 claim type：`USRID、USRNM、ENTID、ENTNM、UNITID、UNITNM、LANGID、EMPLYID、OBJTP`。

## 測試畫面（`/BaseTemplate/`）

| 頁面 | 展示 |
|---|---|
| `PermissionDemo` | **主範本**：claims 表、`AuthorizeView`、頁面級 `[Authorize]`、操作權限三段式、抄法 snippet。經典案例 `BUY014`：`developer`(BUYADM)全綠、`user`(BUYUSE) APRV/EXPO 紅、`ARPV`(typo)恆紅 |
| `PermissionDemoBlocked` | 掛 `EipClaim:UNITID:U999`，一定被路由擋，看被拒畫面 |
| `PermissionApiDemo` | 進階：打 IKSERPAPI，權限在 **API 端**擋，看 HTTP 狀態碼 |

## details 索引

| 主題 | 位置 |
|---|---|
| 完整觀念 / SDK 註冊 / 抄作業 | `IKSERP開發文件/EIP權限設定與Policy.md` |
| Policy 名稱分流 | `Auth/Auth/PermissionPolicyProvider.cs` |
| 靜態 Policy / 註冊 | `Auth/Auth/PolicyExtensions.cs`、`Policies.cs` |
| UI 操作權限 handler | `IKSERPUI/Components/Auth/EipPermissionHandler.cs` |
| API 操作權限 handler | `IKSERPAPI/Auth/DbPermissionHandler.cs` |
| 身分屬性 handler | `Auth/Auth/ClaimValueHandler.cs` |
| EIP 控件權限 client（快取/fail-closed） | `IKS.Eip.Client/EipPermissionClient.cs` |
| CTRLCLASS 資料表 / 授權資料 | `EIP_PROG.CTRLCLASS`、`EIP_GRPMENU` |
