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

## 上線後手機觀察

- Kyo 確認新版入口已生效，可直接開啟地圖，體驗優於中間再提供兩個選項。
- Android 截圖顯示：選點並按「分享」後，LINE 原生位置畫面會詢問是否將該地址傳送至 WeaMind。確認傳送後才會產生位置訊息並進入 webhook。
- 此彈窗不是專案程式碼或 LIFF 畫面。官方位置 URL scheme 未提供略過確認的參數，因此設計上保留這一步；官方未保證所有裝置或版本皆呈現相同介面。
- 參考 [LINE 位置 URL scheme](https://developers.line.biz/en/docs/messaging-api/using-line-url-scheme/#sending-the-location-screen)。

## 未驗證與限制

- 上線前跳過手機驗收；上線後已由 Kyo 確認開圖與原生確認彈窗，但尚未明確確認最終天氣回覆。
- 地圖 URI 僅支援手機 LINE 的官方帳號一對一聊天室。
- 未變更任何個別使用者綁定；若使用者已有個別選單，其優先序仍高於全體預設。
- 本次未修正 Makefile 的腳本匯入問題，後續選單操作可使用模組入口；參考 `.github/prompts/manage-rich-menu.prompt.md`。

## v1.3.0 發布與 session 收尾

- [v1.3.0 Release](https://github.com/kyomind/WeaMind/releases/tag/v1.3.0) 已發布；CHANGELOG commit：`aedb37e`，版本 commit：`6a053e3`，annotated tag：`v1.3.0`。
- 更新檔案：`CHANGELOG.md`、`pyproject.toml`、`uv.lock`。CHANGELOG 只納入面向使用者的地圖入口改善。
- 本機 316 個測試、Ruff lint/format、Pyright 均通過。版本 commit 的 CI、CodeQL、Auto Release、版本映像與 latest 映像發布 workflow 全部成功。
- 已讀取 GHCR manifest，確認 `ghcr.io/kyomind/weamind:1.3.0` 包含 `linux/amd64` 與 `linux/arm64`；index digest：`sha256:148ada19189727291eca67668dbce4e9c490892642d88cfcaf9861b7423384ae`。
- 自動建立的 [weamind-infra PR #10](https://github.com/kyomind/weamind-infra/pull/10) 將部署映像從 `1.2.6` 更新為 `1.3.0`；session 收尾檢查時仍為 OPEN，未合併、未操作 k3s。選單更新已獨立生效，不需等待映像部署。
- Prompt 已整理為 7 個任務入口與 2 份 instructions，補齊索引、動詞開頭命名及有效引用。`github-maintenance.prompt.md` 因外部排程相容性保留原名與內容。
- 發布 prompt 已依本次回饋調整：先寫入未提交的 CHANGELOG 供檢視 diff，核可前不更新版本、不 commit/tag/push/release。
- 後續事項：是否合併 infra PR 由 Kyo 決定；Makefile 匯入問題留待需要時另修。此次不新增其他功能或自動化。
