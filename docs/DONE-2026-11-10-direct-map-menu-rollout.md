# 地圖查詢入口正式更新

## 變更與授權

- PR：[#148](https://github.com/kyomind/WeaMind/pull/148)，merge commit：`3f995980b474e9c6194eef24a47de035b84b7fb2`。
- 使用者明確選擇跳過單帳號與手機驗收，直接更新正式預設選單。
- 「地圖查詢」改用 URI `https://line.me/R/nv/location/`，直接開 LINE 原生位置畫面；不再先送 Postback 取得 Quick Reply。
- 六宮格圖片、名稱、點擊區域與其他按鈕不變；舊 Postback 處理仍保留。
- 這是 LINE 平台端的選單更新，未操作 k3s 或修改後端查詢程式。

## 正式選單與回復

| 用途 | Rich Menu ID |
| --- | --- |
| 新正式預設 | `richmenu-7dae5b21b98c6c67847aed1beadd10c6` |
| 舊預設（保留供回復） | `richmenu-133053dd2e7375a8ab18ced0deb51708` |

新舊選單及圖片均留在 LINE 平台，未刪除任何既有選單。需要回復時，確認授權後可用既有 helper 將舊 ID 設回預設：

```sh
uv run python - <<'PY'
from scripts.rich_menu_manager import set_default_rich_menu

if not set_default_rich_menu('richmenu-133053dd2e7375a8ab18ced0deb51708'):
    raise SystemExit('Rollback request failed; inspect LINE state before retrying')
PY
```

操作後須讀取 `GET /v2/bot/user/all/richmenu` 確認實際預設，不能只依命令輸出判定成功。

## 執行與驗證

- `make upload-list` 因 `ModuleNotFoundError: No module named 'app'` 失敗；改用 `uv run python -m scripts.rich_menu_manager list` 成功讀取。
- 讀取正式預設、完整設定與圖片，確認新版 JSON 只變更地圖按鈕 action。
- 正式圖片與 `docs/rich_menu/rich_menu.png` 位元組一致：PNG、2500×1686、130645 bytes。
- 透過既有 `create_rich_menu()`、`upload_rich_menu_image()` 建立新版，先讀回設定與圖片確認一致，再用 `set_default_rich_menu()` 切換。
- 切換後再讀回預設 ID、完整設定與圖片，全部符合預期；也確認舊選單與圖片仍可讀取。
- GitHub 不允許 squash merge，首次嘗試未合併；改用允許的 merge commit 完成 PR 合併。

## 未驗證與限制

- 未做手機實際開圖、送出位置及天氣回覆驗收；API 驗證不代表手機操作已驗證。
- 地圖 URI 僅支援手機 LINE 的官方帳號一對一聊天室。
- 未變更任何個別使用者綁定；若使用者已有個別選單，其優先序仍高於全體預設。
- 本次未修正 Makefile 的腳本匯入問題，後續選單操作可使用模組入口；參考 `.github/prompts/manage-rich-menu.prompt.md`。
