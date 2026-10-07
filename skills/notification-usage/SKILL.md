---
name: notification-usage
description: IKSERP 通知系統的使用方式（發送通知 / 訂閱接收 / 未讀數 / 除錯）。當使用者要在某個動作後「發一則通知」「推播訊息給使用者」、在頁面「訂閱/接收即時通知」、顯示未讀數/小鈴鐺，或問「通知怎麼用 / 通知收不到怎麼查」時觸發。以 IKS.Notifications.Client（發送）與 IKS.Notifications.Blazor（接收）兩個 NuGet SDK 為準。
---

# IKSERP 通知系統使用方式

> 架構一句話：**發送 = POST 到通知服務(:5186) → 先寫 DB(真相) + 寫 Redis(未讀計數/快取) + 依 tag 用 SignalR 推播；接收 = Blazor 端 `NotificationHubService` 連 Hub、訂閱事件。** 識別 ID 一律用 **`USRID`**（不是 EmplyId、不是數字）。
> 完整 API 與設定：`IKSERPPRJ/IKSERP開發文件/通知服務使用方法.md`。實測頁：`/BaseTemplate/NotificationTest`。

## 觸發時機

某業務動作後要通知使用者（核准/退回/指派…）、頁面要接即時推播、顯示未讀數/鈴鐺、或除錯「通知收不到」。

## 發送（後端服務 / GraphQL Mutation / 頁面皆可）

注入 `IKS.Notifications.Client.NotificationClient`，送一個 `NotificationRequest`：

```csharp
await notifClient.SendAsync(new NotificationRequest
{
    TargetUserIds = ["developer"],   // ⚠ EIP_USR.USRID 字串陣列，不是數字/EmplyId
    Level         = 100,             // 100 一般 / 200 重要 / 300 緊急
    Title         = "訂單已審核",     // ≤256
    Body          = "SO-2026-0001 已核准", // ≤MaxBodyLength(預設4000)
    Source        = "SAL",           // 來源模組，≤64（選填）
    Route         = "SAL/SAL055",    // 點通知的導向路徑，≤512（選填）
    Tags          = ["GLOBAL", "SAL"], // ⚠ 必填、且要是 notification_tags 已定義的
    // TargetChannels 省略＝["ALL"]
});
```

- GraphQL Mutation 用 `[Service] NotificationClient notifClient` 注入；其餘方法：`GetNotificationsAsync` / `MarkAsReadAsync` / `GetUnreadCountAsync`。

## 接收（Blazor 頁面 / 元件）

連線通常**不用自己開**——ERP 端由 EIP SDK 的 `AuthFreeze.InitializeAsync` 在登入後代呼叫 `ConnectAsync(usrid, ["GLOBAL"], clientSessionId)`。元件只要**訂閱事件**：

```razor
@inject IKS.Notifications.Blazor.NotificationHubService NotifHub
@implements IDisposable
@code {
    protected override void OnInitialized()
    {
        NotifHub.NotificationReceived += OnNotif;      // 新通知
        NotifHub.NotificationReadReceived += OnRead;   // 已讀多裝置同步（選）
    }
    void OnNotif(object payload) { /* NotificationPayload */ InvokeAsync(StateHasChanged); }
    void OnRead(object payload) { InvokeAsync(StateHasChanged); }
    public void Dispose() { NotifHub.NotificationReceived -= OnNotif; NotifHub.NotificationReadReceived -= OnRead; }
}
```

`NotificationHubService` 是 **Scoped**（每 Circuit 一個），同 Circuit 內所有元件共用同一條 HubConnection。狀態：`IsConnected` / `ConnectedUserId` / `LastError`。

## ⚠ 關鍵眉角（讀 code 才知道，最常踩）

1. **收得到的前提＝tag 要對得上**。ERP app 連線只訂閱 **`["GLOBAL"]`**（外加強制併入的 `GLOBAL`+`SYSTEM`，見 `NotificationHubService.ConnectAsync`）。所以要讓使用者收到，**發送時務必帶 `GLOBAL`**；只掛模組 tag（如 `SAL`）而連線沒訂閱該 tag → **收不到即時推播**（DB 仍有）。
2. **發送端不強制 GLOBAL**：要全域自己帶 `GLOBAL`；純系統事件才只掛 `SYSTEM`（會觸發凍結機制，不進小鈴鐺一般清單）。
3. **USRID，不是 EmplyId**：`TargetUserIds`、連線、查詢一律用 `USRID` 字串。
4. **靜音只擋推播、不擋 DB**：`level.IsMuted` 或使用者靜音時仍寫 `notifications`，只是不推。
5. **先寫 DB 才推播**：發給 N 人＝`notifications` 寫 N 列（各自 `is_read`）；推播失敗不影響已落地的資料。
6. **標已讀不是刪除**：`is_read=1`+`read_at`，Redis 未讀數 -1，並廣播 `NotificationRead` 給同帳號其他分頁。

## 合法值（種子預設，填錯會 400）

- **Level**：`100` 一般 / `200` 重要 / `300` 緊急（`notification_levels`）
- **Tags**：`GLOBAL` / `SYSTEM` / `STK` / `BUY` / `SAL` / `FIN` / `HR`（`notification_tags`；要新增得先進表）

## 測試與除錯

- **實測頁** `/BaseTemplate/NotificationTest`：左收右發、自己測自己，收件者預帶自己的 USRID，四個樣板（一般/系統公告/強制登出/恢復連線）。
- **收不到照順序查**：① 測試頁左上連線狀態是否綠(Hub/:5186/redis:6381) → ② 收件者 USRID 對不對 → ③ 有沒有帶 `GLOBAL`（app 只訂 GLOBAL）→ ④ 發送有無回綠色「已送出」(紅色會寫被擋原因) → ⑤ 查 DB `notifications` 有沒有落地（有＝發送 OK，問題在推播/訂閱）。

## details 索引（要深入哪塊看哪支）

| 主題 | 位置 |
|---|---|
| 完整 API / NuGet / appsettings / REST | `IKSERPPRJ/IKSERP開發文件/通知服務使用方法.md` |
| 發送與持久化邏輯 | `IKSNOTIFICATIONSERVICE/Services/NotificationService.cs` |
| Redis key 結構 / Lua 原子腳本 / 未讀計數 / 連線名冊 | `IKSNOTIFICATIONSERVICE/Services/RedisService.cs` |
| SignalR 推播路由（tag 交集） | `IKSNOTIFICATIONSERVICE/Services/Channels/SignalRChannel.cs` |
| Hub 連線註冊 / 心跳 | `IKSNOTIFICATIONSERVICE/Hubs/NotificationHub.cs` |
| 前端 SDK（連線/事件） | `IKS.Notifications.Blazor/NotificationHubService.cs` |
| 發送 SDK（送/查/已讀/未讀） | `IKS.Notifications.Client/NotificationClient.cs` |
| GLOBAL/SYSTEM 不對稱規則 | `EIP入口平台架構設計.md` 第 11.5 節 |
