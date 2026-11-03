# WeaMind 架構圖：以 stack-diagram 產生並取代 README Mermaid

整理日期：2026-11-04

## MEMOS

- `README.md` 與 `README.en.md` 的「開發者技術亮點／Engineering Highlights」區塊已從 Mermaid 改為 `<picture>` 嵌入 PNG，GitHub 依讀者主題自動切換亮/暗圖
- 做法完全比照 weamind-infra（見該 repo `docs/DONE-2026-11-03-architecture-diagram.md`），這份只記 WeaMind 特有的部分
- 圖的唯一原始檔是 `docs/architecture-diagram/src.html`；`docs/site/index.html` 與兩張 PNG 都是產物，**不要直接改產物**
- HTML 網頁版公開在 https://kyomind.github.io/WeaMind/ ；`.github/workflows/pages.yml` 只部署 `docs/site/`，`docs/` 其他檔案在 Pages 上是 404
- **skill 沒有 vendor 進 WeaMind**：重建時直接用 `../weamind-infra/.agents/skills/stack-diagram`，所以本機必須有 weamind-infra 這個 sibling repo
- CSS 與字級從 weamind-infra 調整後的 `src.html` 原樣複製（節點名稱 18px、群組標籤 17px、role 與箭頭標籤 15px，canvas 外的標題／圖例／頁尾 12–30px）。兩邊若要調字，記得同步
- PR #141 已 merge（merge commit `6a74ec3`），Pages 已啟用（`build_type=workflow`）並驗證過內容

## 圖的內容與依據

依據舊 Mermaid 與程式碼（`app/line/router.py`、`app/line/messaging.py`），內容沒有擴充，只把 Mermaid 換成同內容的工程圖。

| 群組 | 節點 |
| --- | --- |
| （外部） | LINE Platform、Redis、PostgreSQL、weamind-data |
| FastAPI LINE Bot | Webhook Handler、Background Tasks |

邊：

- 藍色實線（請求路徑）：LINE →`webhook`→ Webhook Handler →`ack <50ms`→ LINE；Webhook Handler →`non-blocking`→ Background Tasks →`reply api <2s`→ LINE（從上方繞回）
- 灰色實線（內部）：Background Tasks →`selective lock`→ Redis；Background Tasks ↔`read / write`↔ PostgreSQL；weamind-data →`etl every 6h`→ PostgreSQL

與舊 Mermaid 的差異（都是更正）：

- 英文版 Mermaid 寫「Push reply」，但程式碼用的是 `reply_message`（Reply API），圖上改為 `reply api`
- 英文版 Mermaid 寫 sub-100ms，README 內文寫 Sub-50ms，圖上依內文用 `<50ms`

圖上文字用英文，中英文 README 共用同一張圖（與 weamind-infra 一致）。

## 檔案結構

```
docs/
├── architecture-diagram/
│   ├── src.html          # 唯一原始檔
│   └── icons/            # 圖示 + manifest.json（每個圖示的來源）
├── site/
│   └── index.html        # build 產物（約 106 KB，自包含），Pages 只部署這個資料夾
├── weamind-architecture.png       # render 產物（亮色）
└── weamind-architecture-dark.png  # render 產物（暗色）
.github/workflows/pages.yml        # 照搬 weamind-infra 的 workflow
```

圖示：LINE、FastAPI、Redis、PostgreSQL 從 weamind-infra 的 `icons/` 複製；Webhook Handler（`lucide/webhook`）、Background Tasks（`lucide/cog`）、weamind-data（`lucide/cloud-download`）用 `fetch_icons.py` 抓 Lucide。

## 如何修改並重建

1. 編輯 `docs/architecture-diagram/src.html`（座標規則見 `../weamind-infra/.agents/skills/stack-diagram/references/geometry.md`）
2. 從 repo 根目錄重建（指令也寫在 `src.html` 開頭）：

   ```bash
   S=../weamind-infra/.agents/skills/stack-diagram
   python3 $S/scripts/build.py docs/architecture-diagram/src.html docs/architecture-diagram/icons docs/site/index.html --fonts $S/assets/fonts
   uv run --with playwright python $S/scripts/render_png.py docs/site/index.html docs/weamind-architecture.png --selector .canvas --scale 2
   ```

3. 打開兩張 PNG 實際看過，也要看整頁（`render_png.py ... --full-page`），PNG 不含 canvas 外的標題、圖例、頁尾
4. `src.html`、`icons/`、`docs/site/index.html`、兩張 PNG 一起 commit。CI 不會 build，只會把 `docs/site/` 原樣部署
5. 驗證線上要比對內容，不能只看 HTTP 200：

   ```bash
   curl -sL "https://kyomind.github.io/WeaMind/?v=$(date +%s)" | cmp - docs/site/index.html && echo IDENTICAL
   ```

### 座標速記（現行版面）

- canvas 1000×500（weamind-infra 是 1160 寬；字級相同，所以 README 縮到欄寬後 WeaMind 的字看起來略大）
- 列的 tile top：第一列 140、第二列 340
- 欄的 centerX：LINE 100、Webhook Handler 340、Background Tasks / PostgreSQL 580、Redis / weamind-data 860
- 群組 FastAPI LINE Bot：`250,80,420×210`
- reply 邊走 y=50 的上方通道（群組上緣 80 之上）

## 過程中的問題與教訓

- **節點名稱折行**：`Background Tasks` 在 18px 下超過 164px 文字區，折成兩行並擠到 role 字。修法：只把該節點加寬到 196px，`left = centerX + 16 - width/2`（因為 `.node` 有 `margin-left:-16px`），即 `left:498px;width:196px`
- **箭頭標籤壓到群組框線**：`webhook`、`ack <50ms` 原本置中在 x=220，跨過群組左緣 x=250。標籤改置中在 x=190。水平邊標籤只要避開 tile 即可，但也要避開群組框線
- **pre-commit `end-of-file-fixer` 會改 SVG**：從 weamind-infra 複製的 SVG 沒有結尾換行，第一次 commit 被 hook 擋下並自動補上。SVG 會以 base64 內嵌進 HTML，所以補完換行後要**重新 build 再 commit**，否則成品與原始檔不一致
- **Pages 需另外啟用**：workflow 進 repo 不會自動啟用 Pages。已用 `gh api -X POST repos/kyomind/WeaMind/pages -f build_type=workflow` 設定。`github-pages` environment 預設只允許 main 部署，所以 merge 前 README 的 HTML 連結是 404
- **user site 自訂網域會劫持 project pages**：weamind-infra 遇過 `kyomind.github.io/*` 被轉到 `blog.kyomind.tw` 的問題（已修）。WeaMind 的 Pages 網址同樣受影響；若連結突然壞掉，先查 `gh api repos/kyomind/kyomind.github.io/pages -q .cname` 是否為 `null`

## 待處理事項

1. 若 WeaMind 架構有變（例如新增服務），更新 `src.html` 並重建
2. 若之後要讓 WeaMind 能獨立重建（不依賴 weamind-infra），再把 skill vendor 進來
