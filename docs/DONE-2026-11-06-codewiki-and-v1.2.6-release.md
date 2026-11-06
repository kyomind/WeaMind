# CodeWiki 上線、DeepWiki 移除與 v1.2.6 發布部署

整理日期：2026-11-06

## MEMOS（全新 AI 先讀這裡）

> 給沒有任何上下文的下一個 AI：先讀完這一區，就能知道現在在哪、能不能直接動手。

- **現況（2026-11-06）**：本文件涵蓋的工作**全部完成**，沒有進行中的分支或 PR。WeaMind 與 weamind-infra 的 `main` 都是乾淨、已同步的。
- **線上版本**：正式環境 Deployment 跑 `ghcr.io/kyomind/weamind:1.2.6`（2 個 Pod，皆 Running，`/health` 200）。
- **兩個 wiki 都在線上**：
  - WeaMind：https://kyomind.github.io/WeaMind/wiki/ （22 頁，多頁）
  - weamind-infra：https://kyomind.github.io/weamind-infra/wiki/ （單頁）
- **DeepWiki 已全面移除**，只剩 `docs/archive/README-Enhancement-Session.md` 三處歷史字樣，**刻意保留，不要改**。
- **唯一未完成的事**：沒有人用 LINE 實際查過天氣來驗證 v1.2.6（只確認了 Pod 健康與 `/health`、`/metrics`）。需要 Kyo 自己在 LINE 查一次。
- **待觸發的提醒（不是現在要做）**：哪天要把 `replicas` 調到 4 以上，要把 `maxSurge: 1`、`maxUnavailable: 0` 明確寫進 `weamind-infra/manifests/deployment.yaml`（見「六、已知狀況」）。
- **不要假設有 GitOps**。合併 weamind-infra 的 bump PR 不會自動部署，部署是 Kyo 本機手動 `make deploy`。
- **Kyo 的工作偏好**（影響怎麼做事）：
  - 回覆用繁體中文；commit message 用英文祈使句、首字母大寫。
  - **能不開新 PR 就不要新開**；同一批相關變動用一個 PR。小的收尾改動，Kyo 有時會直接說「在 main 分支改」，但**要他明說才行**。
  - **release、部署這類不可逆動作，要一步一步來，每步停下等他確認**。
  - wiki 只描述現況，**不需要寫「為什麼」**。
  - 他用語音輸入，訊息可能有錯字，直接合理修正。

## 一、背景與目標

Kyo 要為 WeaMind 與 weamind-infra 兩個 repo 各做一份自行部署在 GitHub Pages 的 wiki，取代原本第三方的 DeepWiki；同時 WeaMind 很久沒發版，順便走完 v1.2.6 的 release 並部署到正式環境。

## 二、CodeWiki 產生與發布

### 工具

- 使用 `codewiki`（FSoft-AI4Code/CodeWiki，以 `uv tool` 安裝在 `~/.local/bin/codewiki`），provider 為 `codex` 訂閱模式，模型 `gpt-6.1-terra`。設定在 `~/.codewiki/config.json`。
- 用法以官方 README 為準：`gh repo view FSoft-AI4Code/CodeWiki`。升級：`uv tool upgrade codewiki`。
- **這個工具沒有 release 版本**，版本號 2.0.0 不會變，要看 git commit（2026-11-06 裝的是 `a1b9f4a`，等於當時 `main`）。
- 檢查版本：產出的 `docs/wiki/metadata.json` 會有 `generator_version`。**1.0.1 是舊版，會略過分群，只產一頁**；必須是 2.0.0。

### WeaMind（多頁）

```bash
codewiki generate -o docs/wiki --exclude "docs,tests" --github-pages \
  --language zh-TW --max-token-per-module 15000 --max-token-per-leaf-module 8000
```

踩過的坑：

1. **不降低 token 上限就只會產一頁**（`Total modules: 0`，`module_tree.json` 為 `{}`）。專案不大，預設門檻不會觸發分群。加上面兩個參數才拆出 7 個頂層模組、共 22 頁。
2. **整個流程超過 10 分鐘**，要放背景執行（Bash `run_in_background`）。
3. **輸出目錄已有內容時會互動詢問 Overwrite**。非互動環境用 `yes Y | codewiki generate ...`。
4. **重跑前先 `rm -rf docs/wiki`**。我曾在已有舊輸出的情況下重跑，結果 `LLM calls: 0`、1 秒結束、什麼也沒更新（被快取跳過）。
5. `--exclude "docs"` 是為了避免把既有手寫文件（`Architecture.md`、`Tree.md` 等）當程式碼分析。
6. 產出會夾帶 `docs/wiki/temp/`（依賴圖暫存），已加進 `.gitignore`。
7. `docs/wiki/codewiki-icon.png` 原 546 KB，會被 pre-commit 的 `check-added-large-files`（上限 500 KB）擋下。用 `sips -Z 256` 縮成約 40 KB（它只是檢視器的 logo）。
8. pre-commit 的 `end-of-file-fixer` 會修改產出的 json 檔，第一次 commit 會失敗，重新 `git add` 再 commit 即可。

### weamind-infra（單頁）

```bash
codewiki generate -o docs/wiki \
  --exclude "learning,review,references,docs,.agents,.claude,.vscode,*.md" \
  --github-pages --language zh-TW \
  --max-token-per-module 15000 --max-token-per-leaf-module 8000
```

- 只有 16 個可分析元件（manifests、terraform、workflow、Makefile），**無法拆成子模組，產出單頁 `overview.md`**。這是預期結果，不是失敗。
- 該 repo 是公開的；排除 `learning`（194 個學習筆記）、`review` 等，只分析基礎設施本體。
- 同樣縮小了 icon（558 KB → 256px）。

### 發布到 GitHub Pages

兩個 repo 原本的 `.github/workflows/pages.yml` 只發布 `docs/site/`（架構圖）。改成：

- 觸發路徑加上 `docs/wiki/**`。
- 上傳前多一步 `cp -r docs/wiki docs/site/wiki`，wiki 發布在 `/wiki/`，架構圖維持在根路徑。

網址：`https://kyomind.github.io/<repo>/wiki/`。Pages 只在 push 到 `main` 且路徑符合時觸發（或手動 `workflow_dispatch`）。

## 三、品質檢查（兩輪）

### 第一輪：中國用語（用 news repo 的機制）

- 工具：`/Users/kyo/Code/news/scripts/check-zhtw-terms.ts`，對任意檔案用 `node scripts/check-zhtw-terms.ts --path <file>`（唯讀；加 `--fix` 才會改）。另有 `zhtw-mcp lint <file>`。對照表在 news repo 的 `src/lib/zhtw-terms.ts`。
- 方法：`auto` 層（確定錯誤）為 0；`review` 層與 `zhtw-mcp` 警告逐條看語境。
- 改了的詞：回滾→降版（Alembic downgrade；非遷移語境改「復原」）、程序→行程／腳本／應用程式、返回→結束、綁定→繫結、恢復→還原／復原、窗口→時間窗、匹配→符合／比對、語句→敘述、前綴／後綴→字首／字尾、排查→檢查／故障排除、報錯→顯示錯誤、終端→終端機、依賴（名詞）→相依套件／相依關係。
- **刻意保留**：分派、外鍵、原始碼、動詞的「依賴」、匯入（Python import）、異常、並行、「綁定掛載」（Docker 慣用）、「模板」（Bandit 講的是 Jinja 這類 Web 模板，曾誤改「範本」後還原）、「登入返回」（UI 導航）、前綴（Ingress `Prefix`）。
- 教訓：機械取代時，詞組可能互相重疊（曾把「Redis 的 `6379` 綁定至」弄成「繫定至」），改完要用 `rg` 抽查並看 diff。

### 第二輪：AI 味（用 ai-smell skill）

- skill：`~/.claude/skills/ai-smell`；確定性檢查：`python3 ~/.agents/skills/ai-smell/scripts/check.py <檔案>`。案例索引在 `references/cases.md`。
- wiki 是機器生成的文件，不是 Kyo 改寫過的稿，所以建議修改的門檻比對他的文章低。
- 採用並已修改：
  1. **防禦性否定**（「不代表…」「不等同…」「並非…」，全站約 20 處）：刪掉沒人會誤會、只是替讀者設假想敵的後半句；保留糾正程式碼實際行為的（例如 Ruff `--fix` 會改工作樹、推送會帶上所有本地 tag、重試門檻不是硬上限、發布映像不等於已部署）。
  2. **重複的「維護重點／注意事項」條目**：刪掉與前文重複的 5 處。
- 判斷不改：各模組導言與 `overview.md` 的摘要雖相近，但都多了模組邊界、檔案路徑與交叉連結，是單頁閱讀所需；只刪了 `operational_and_development_scripts.md` 導言的空話「，服務於不同的維護需求」。「系統位置」類 H2 各頁內容不同（附依賴圖），保留。

## 四、移除 DeepWiki

- WeaMind：`README.md`、`README.en.md` 刪除徽章，連結改 `https://kyomind.github.io/WeaMind/wiki/`；`docs/weamind-infra/README.md`、`README.en.md`（infra README 副本）改連 infra wiki。
- weamind-infra：`README.md`、`README.en.md` 改連 infra wiki；`docs/WeaMind-README.md`（WeaMind README 副本）改連 WeaMind wiki；`.vscode/settings.json` 刪掉 cspell 的 `deepwiki` 字。
- `docs/archive/` 的歷史紀錄**保留**（Kyo 明確說不用動）。

## 五、v1.2.6 release 與部署

### Release（照 `.github/prompts/changelog.prompt.md`，需先核可）

流程：`make changelog-status` → `make changelog-prepare VERSION=1.2.6` → 草稿給 Kyo → **明確核可** → 寫入 `CHANGELOG.md` → `make changelog-release VERSION=1.2.6`（會更新 `pyproject.toml`、`uv lock`、分兩個 commit、**直接 push `main` 並推送 tag**，不可逆）→ 驗證。

- 版本選 patch：自 v1.2.5（2026-08-10）以來主要是相依套件安全更新。
- CHANGELOG 規則排除文件、重構、CI、例行依賴升級；但「新增一個對外的 wiki 網站與架構圖網頁」被判斷為使用者可見的新增，納入「新增」段落（這是邊界案例，Kyo 選擇納入）。
- 結果：`31b2b2f`（CHANGELOG）、`de0eae1`（版本檔）、tag `v1.2.6`。CI、CodeQL、Auto Release、Publish Release to GHCR 全成功；GHCR `weamind:1.2.6` 含 `linux/amd64`、`linux/arm64`。

### weamind-infra 版本 PR

- 推 tag 後會**自動**在 weamind-infra 開 `Bump weamind image to x.y.z` PR（腳本 `scripts/open_infra_version_pr.sh`）。
- #9（1.2.6）已合併；更早未合併的 #6（1.2.4）、#7（1.2.5）已關閉（被取代）。Kyo 習慣跳過中間版本。

### 部署（手動）

- **沒有 GitOps**。weamind-infra 合併 PR 只更新 repo 內 `manifests/deployment.yaml`。
- 正式部署：在 `weamind-infra` 目錄執行 `make deploy`（= `kubectl apply -f manifests/` + `kubectl rollout status deployment/weamind -n weamind`）；退回：`make rollback`。
- 本機 kubectl context 是 `default`，連到 3 節點 k3s（`weamind-001` control-plane、`002`、`003` worker），可直接用。macOS 沒有 `timeout` 指令，要逾時請用 `--request-timeout=10s`。
- 部署前先 `kubectl diff -f manifests/` 預覽。結果：Deployment 從 1.2.2 → 1.2.6（注意：manifest 原本寫 1.2.3，但線上實際是 1.2.2，所以一次跨過 1.2.3～1.2.6）。
- 部署後驗證：2 個 Pod `1/1 Running`、0 重啟；Pod 日誌 `/health`、`/metrics` 200；`https://k8s.kyomind.tw/health` 200。

## 六、已知狀況

- **線上設定漂移（已被覆蓋，Kyo 決定不補回）**：部署前線上 Deployment 有 repo 沒有的設定——標籤 `app.kubernetes.io/name`、`app.kubernetes.io/part-of`、`revisionHistoryLimit: 3`、滾動更新 `maxSurge: 1 / maxUnavailable: 0`。查過 `manifests/` 的全部 git 歷史與 `~/Code` 其他 repo，**從未提交過**，推測是學習 CKA 時用暫存檔套用（無證據）。證據（`last-applied-configuration`）已被這次 `apply` 覆蓋。另有 2026-09-04 一次 `kubectl` 直接改 probe 的 `initialDelaySeconds`，該值現與 repo 一致。
  - 影響：2 個副本時，預設 `25%` 與 `1 / 0` 等價，行為無差；標籤沒有東西在選它；`revisionHistoryLimit` 變成 10 無害。
  - **觸發條件**：要把 `replicas` 調到 4 以上時，把 `maxSurge: 1`、`maxUnavailable: 0` 寫進 manifest，否則會允許 1 個不可用。
- **WeaMind 的 wiki 是對 commit `d5bb54d` 附近的程式碼產生的**。v1.2.6 沒有程式邏輯變動需要更新 wiki（只有套件升級）。之後程式碼有大改時再重跑（流程見第二節，記得先 `rm -rf docs/wiki`）。

## 七、待處理事項

- **有一項**：請 Kyo 在 LINE 實際查一次天氣，確認 v1.2.6 整條路徑（webhook → 天氣查詢 → 回覆）正常。v1.2.5 之後有天氣查詢與 LINE 回覆模組的內部重構，CHANGELOG 判定不影響行為，但沒有實測。
- 其餘沒有。

## 八、如何延伸

- **新增 repo 的 wiki**：照第二節流程；先用預設參數試，若只有一頁（`Total modules: 0`）再降低 token 上限；若可分析元件很少（像 weamind-infra）就接受單頁。再複製 `pages.yml` 的 `cp -r docs/wiki docs/site/wiki` 作法。
- **重新產生 WeaMind wiki**：`rm -rf docs/wiki` → 第二節指令（背景執行）→ 縮 icon → 第三節兩輪檢查 → 開 PR。
- **下一次 release**：照第五節，永遠先給 CHANGELOG 草稿並等明確核可；推 tag 後會自動開 weamind-infra bump PR，是否部署由 Kyo 決定。

## 九、關鍵資料索引

| 項目 | 位置或編號 |
| --- | --- |
| WeaMind PR | #142 多頁 wiki＋Pages、#143 用語與 AI 味修正、#144 導言空話＋README 換連結（皆已合併） |
| weamind-infra PR | #8 wiki＋換連結（已合併）、#9 bump 1.2.6（已合併）、#6／#7 已關閉 |
| 直接推到 `main` 的 commit | `754b79a`（weamind-infra README 副本換連結）、`31b2b2f`＋`de0eae1`（v1.2.6） |
| 相關文件 | `docs/DONE-2026-11-04-architecture-diagram.md`（架構圖，Pages 根路徑的來源） |
| 相關 prompt | `.github/prompts/changelog.prompt.md`、`.github/prompts/github-maintenance.prompt.md`（每週六排程維護，**搬移或改名前要先確認**，見 `AGENTS.md`） |
