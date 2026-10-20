---
name: review-title
description: review-engine area.title 審查清單（PageTitle/視窗標題/明細膠囊名稱與順序）
disable-model-invocation: true
---

# review-title — 標題名稱審查

> 規則來源：`page-migration/details/title.md`、`final-dfm-check.md` ②。finding 格式見 `.claude/SelfFolder/review-engine/finding-schema.md`。區代碼 **TTL**。

## 1. 範圍
| 側 | 審查對象 |
|---|---|
| Delphi／對照表 | `SAL程式編號對照表.md` 功能名稱；子 form 的 `Caption`；`TTabSheet` Caption 與檔案順序（含基底）；`.pas` 依旗標動態改的頁籤標題 |
| C# | `<PageTitle>`、`<WindowTitle>`、`iks-mode-switch` 膠囊文字與順序 |

## 2. 取基準
```
py .claude/SelfFolder/review-engine/tools/query.py <SAL> list razor            # 標題、膠囊
py … <SAL> list comps --type TRzTabSheet ; py … <SAL> list comps --type TTabSheet
py … <SAL> get comp <子form 的 form 名> --unit <子form>                          # 子 form Caption
py … <SAL> find "Caption\s*:=" --side delphi                                     # 執行期改標題
```
對照表名稱：state 的 `title` 欄（scope 已寫入）。

## 3. 檢查清單
| 編號 | 檢查 | type／預設 severity |
|---|---|---|
| TTL-01 | `<PageTitle>` 格式為 `(程式代號)程式名稱`，代號＝檔名 | rule-violation｜low |
| TTL-02 | 名稱與對照表功能名稱逐字一致；合併列例外依 title.md 允許清單 | mismatch｜low |
| TTL-03 | 子視窗元件不放 `PageTitle`；呼叫端 `<WindowTitle>` 依 Delphi 子 form Caption | mismatch｜low |
| TTL-04 | 編輯 Window 標題依 pageStatus（新增／修改／檢視＋名稱） | rule-violation｜low |
| TTL-05 | 明細頁籤（膠囊）名稱逐字＝TTabSheet Caption（去 `&X`），順序＝dfm 檔案順序；`Visible=False` 頁籤不出現 | mismatch｜low |
| TTL-06 | Delphi 依旗標動態改的頁籤/標題（如 `gbHASSER`），C# 照同條件 | missing｜low |

## 4. 邊界
欄位標籤文字 → filter／editform；grid 欄標題 → grid；按鈕文字 → button。

## 5. 輸出
同 `review-grid` §5（id `<SAL>-TTL-nnn`、逐字 quote、查無意圖寫 open_question、`review_state.py upsert`/`area … title done`）。
