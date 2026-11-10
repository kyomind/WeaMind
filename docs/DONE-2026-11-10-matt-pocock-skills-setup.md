# Matt Pocock 工程技能設定紀錄與交接

整理日期：2026-11-10

## MEMOS：全新 AI Session 先讀這裡

- **狀態：設定已完成，沒有本次設定遺留的待處理事項。** 不需要重新執行初始化或再次詢問已確認的選項。
- 本專案為 `kyomind/WeaMind`，issue tracker 使用 **GitHub Issues**，操作工具為 `gh`。
- 設定入口為根目錄 `AGENTS.md` 的 `## Agent skills`；詳細規則在 `docs/agents/` 三份文件。
- 採 **single-context**：根目錄 `GLOSSARY.md` 為共用領域詞彙，`docs/adr/` 放決策紀錄。ADR 目錄未建立是刻意的，等有實際決策再建立。
- 原 `CONTEXT.md` 已用 `git mv` 改名為 `GLOSSARY.md`，內容完全不變；不要再建立平行的 `CONTEXT.md`。
- GitHub 已具備五個預設 triage 標籤；本次只新增缺少的四個，既有 `wontfix` 未改動。
- 本次未提交或推送。交接當下，改名已 staged（`git mv` 的效果），`AGENTS.md` 尚未 staged，`docs/agents/` 為新檔；開始新工作前應重新查看 `git status`，不要把此快照當成永久狀態。
- 工作開始前已有大量 staged 的技能安裝／更新（含 `.agents/skills/`、`.claude/skills/`、`skills-lock.json`）；這些不是本次設定新增的變更，未替使用者重設或提交。

## 目的與範圍

使用 `.agents/skills/setup-matt-pocock-skills/SKILL.md`，補齊工程技能所需的每個儲存庫設定：issue tracker、triage 標籤對應及領域文件讀取規則。

本次只調整文件與 GitHub 標籤，沒有修改應用程式、測試、依賴、部署設定或技能本身。既有技能安裝不在本次設定工作的範圍內。

## 探索結果與使用者確認

| 項目 | 探索結果 | 最終決定 |
| --- | --- | --- |
| Remote | `origin` 為 `git@github.com:kyomind/WeaMind.git`，`gh repo view` 成功 | 使用該儲存庫的 GitHub Issues |
| Agent 指引 | 有 `AGENTS.md`，沒有 `CLAUDE.md`，沒有既有 Agent skills 區塊 | 在既有 `AGENTS.md` 新增區塊 |
| Tracker 設定 | 沒有 `docs/agents/` 或 `.scratch/` 慣例 | 新增 GitHub tracker 文件，不另建本地 tracker |
| Triage | 已安裝 `.agents/skills/triage/`；預設標籤僅 `wontfix` 已存在 | 使用五個預設名稱，只補缺少標籤 |
| 領域文件 | 有 `CONTEXT.md`；沒有 `GLOSSARY.md`、map 文件或 ADR 目錄 | 原樣改名為 `GLOSSARY.md`，ADR 按需建立 |
| Repo 結構 | 未發現多套件 monorepo 訊號 | single-context，不建立 glossary map |

依技能流程，先確認 tracker，再單獨確認是否保留預設標籤；展示完整文件草稿後，使用者明確選擇「照草稿並改名」，才開始寫入及建立遠端標籤。

## 實際完成內容

### 1. Agent 設定入口

在 `AGENTS.md` 新增 `## Agent skills`，包含：

- `### Issue tracker`：指向 `docs/agents/issue-tracker.md`。
- `### Triage labels`：指向 `docs/agents/triage-labels.md`。
- `### Domain docs`：說明 single-context，指向 `docs/agents/domain.md`。

保留周圍原有內容，沒有建立 `CLAUDE.md` 或重複指引檔。

### 2. Issue tracker 規則

`docs/agents/issue-tracker.md` 記錄：

- 目標為 `kyomind/WeaMind`，透過 `gh` 建立、讀取、列出、留言、標記與關閉 issue。
- 使用 GitHub 原生 sub-issues 及 issue dependencies；不支援依賴時，以 child issue 頂部的 `Blocked by: #<n>` 作備援。
- 每次 session 第一次建立 issue 前，先用 `gh repo view --json nameWithOwner` 驗證目標；遇到非預期目標須確認，避免把 issue 發到技能上游。
- 關閉 issue 前先獨立留言，不依賴已關閉 issue 的 `close --comment` 行為。
- 技能要求 publish ticket 時建立 GitHub issue，fetch ticket 時讀取 GitHub issue。
- 文件保留 `PRs as a request surface: no` 的預設值，未將外部 PR 納入需求分流。

文件以技能的 GitHub 範本為起點，採使用者確認的精簡版；沒有加入未使用的 wayfinder 工作流程。當次環境的 `gh` 為 2.97.0，未實際建立 issue 測試 sub-issue／dependency 指令。

### 3. Triage 標籤

`docs/agents/triage-labels.md` 將 canonical role 與實際名稱做一對一對應：

| 角色／標籤 | 用途 | 本次操作 |
| --- | --- | --- |
| `needs-triage` | 維護者待評估 | 新建 |
| `needs-info` | 等待回報者補充資訊 | 新建 |
| `ready-for-agent` | 規格完整，可交由 agent | 新建 |
| `ready-for-human` | 需要人類實作 | 新建 |
| `wontfix` | 不處理 | 沿用既有標籤 |

這些標籤已在 GitHub 建立，不只是本地文件宣告。未替既有 issue 套用或移除任何標籤。

### 4. 領域文件與舊檔遷移

- 執行 `git mv CONTEXT.md GLOSSARY.md`，保留原詞彙內容，包括 Weather Query、Location resolution、Query History、Preset Location、PostBack Action。
- `docs/agents/domain.md` 要求探索前讀取 `GLOSSARY.md`，並讀取相關 ADR。
- 文件不存在時應安靜繼續，不要只為滿足結構建立空文件。`domain-modeling` 在術語或決策真正確定時再新增內容。
- 輸出使用詞彙表定義的名稱；若提案與 ADR 衝突，須明確指出，不可默默覆蓋。
- 未建立 `GLOSSARY-MAP.md`、多 context 結構或空 `docs/adr/`。

## 驗證紀錄

已完成：

1. `gh repo view --json nameWithOwner,url` 確認可存取正確儲存庫。
2. `gh label list` 確認五個預設標籤皆存在。
3. `git diff --check` 及 `git diff --cached --check` 通過。
4. 比較原 `HEAD:CONTEXT.md` 與新 `GLOSSARY.md` 的 Git blob hash，相同；Git 亦顯示 `rename ... (100%)`。
5. 搜尋專案文件中的舊檔名引用，未發現需要同步修正的既有引用；新設定均指向 `GLOSSARY.md`。

未執行：應用程式測試、型別檢查、部署、實際技能全流程及 issue 建立／關閉測試。原因是本次沒有程式邏輯變更，且避免為驗證設定製造測試 issue。

## 下一次如何接手／延伸

### 在本專案使用

1. 先讀 `AGENTS.md` 與任務相關的 `docs/agents/*.md`，以這些現行設定為準，本文件只是完成快照。
2. `to-tickets`、`to-spec`、`triage` 的 tracker 操作依 issue-tracker 文件；triage 的狀態依標籤對應。
3. `domain-modeling`、`grill-with-docs`、`improve-codebase-architecture` 等領域工作，以 `GLOSSARY.md` 及相關 ADR 為準。
4. 若要更新標籤詞彙，修改 `triage-labels.md` 的實際標籤欄，另確認 GitHub 存在對應標籤；改文件不會自動遷移遠端標籤或 issue。
5. 可直接編輯 `docs/agents/*.md`。只有切換 tracker 或希望重新初始化，才需要重跑 setup 技能。

### 在其他儲存庫如法炮製

- 重新閱讀 setup 技能及其範本，重新探索 remote、指引檔、既有領域文件、tracker 慣例與 monorepo 訊號，不要硬套 WeaMind 的結果。
- 有 `CLAUDE.md` 就更新它，否則更新既有 `AGENTS.md`；兩者皆無才詢問要建立哪個。已有區塊須原位更新。
- tracker 必須經使用者確認；GitHub／GitLab 須先驗證可存取專案，不可猜測目標。
- 只有安裝 triage 才詢問、建立標籤設定；標籤僅補缺少者。
- 預設 single-context；只有實際 monorepo 訊號才提出 multi-context 選項。
- 如有 `CONTEXT.md`／`CONTEXT-MAP.md`，先提出保留內容的改名方案並確認，再更新引用；不要把舊檔直接丟棄。
- 先展示草稿、取得確認，再寫入；保留既有 staged／unstaged 變更，勿直接 commit 全部檔案。

### 快速重驗命令

```bash
git status --short
gh repo view --json nameWithOwner,url
gh label list --repo kyomind/WeaMind --limit 100 --json name
git diff --check
git diff --cached --check
```

若未來要驗證檔名引用，應排除歷史紀錄（包含本文件）及技能範本，避免把紀錄中的 `CONTEXT.md` 當成待修正的有效路徑。

## 後續提交紀錄（同日）

使用者在紀錄完成後要求 commit，決定分為兩筆，不推送：

1. `92fff8b` — `Install and update Matt Pocock engineering skills`：提交既有技能安裝／更新與 lockfile，並同步更新 `.secrets.baseline`。
2. `Configure engineering skills and document the setup`：提交 `AGENTS.md`、三份 `docs/agents/` 設定、詞彙表改名及本交接文件；commit hash 請由 `git log` 查詢。

第一筆提交起初被 detect-secrets 擋下，原因為 `skills-lock.json` 的十二個 `computedHash` 被當成高熵密鑰。確認均為技能內容雜湊後，沿用既有 baseline 做法，只更新對應紀錄；沒有排除整個檔案或略過 hook。重新提交時所有適用的 pre-commit 檢查通過。

MEMOS 與上述「未提交」敘述描述的是提交前快照，並非目前狀態；接手時應以 `git status` 與 `git log` 為準。

## 待處理事項與風險

- **本次設定沒有待處理 issue 或未完成事項，也沒有新建工作 issue。** 這不代表已盤點整個儲存庫的既有 issue。
- 提交已依後續要求分批處理，未推送；之後是否推送由使用者決定。
- GitHub 標籤是遠端變更，還原本地文件不會還原它們。不要未經檢查就刪除，之後可能已有 issue 使用。
- 技能版本或 `gh` 版本變更時，應重新核對操作規則；本次僅驗證設定與標籤，未做所有技能的端到端執行。
