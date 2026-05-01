# DONE: WeaMind Release 後自動開 Infra 版本更新 PR

整理日期：2026-05-01

## 文件目的

這份文件用來交接 WeaMind 這次的 CD 最小骨架實作結果，讓下一次全新的 AI 在沒有前文的情況下，也能直接理解目前已完成什麼、卡過什麼、現在還剩什麼。

這次主線不是單純寫 CHANGELOG，而是把「Release 發生後，自動對 `weamind-infra` 開版本更新 PR」這條最小 CD 路徑打通。

## 一句話結論

WeaMind 已經完成第一版 release-to-infra PR 自動化：當 app repo 產生新的 release tag 時，`publish-release.yml` 會在推送 GHCR image 後呼叫 `scripts/open_infra_version_pr.sh`，自動到 `kyomind/weamind-infra` 建 branch、更新 `manifests/deployment.yaml` 的 image、推 commit、push branch，並建立對應的 PR。

## 最終成果

- `publish-release.yml` 已串接 release 後的 infra PR 流程。
- 新增 `scripts/open_infra_version_pr.sh`，負責跨 repo 的最小 Git automation。
- 第一版只更新 `weamind-infra/manifests/deployment.yaml` 的 image 行，從 `latest` 改成完整 release version。
- 已成功建立 `weamind-infra` PR #4，分支名稱為 `bump-weamind-1.2.2`，標題是 `Bump weamind image to 1.2.2`。
- Release 版本 `v1.2.2` 已推送到 WeaMind app repo，並成功觸發相關 GitHub Actions。

## CD 設計收斂

### 1. 第一版的核心目標

今天的 CD 不是要一次做到完整部署自動化，而是先完成最小可運作骨架：

1. app repo 發生 release。
2. release workflow 發布 GHCR image。
3. 同一條流程自動對 infra repo 開 PR。
4. PR 只更新 deployment image version，不額外擴張責任。

### 2. 為什麼不是直接做完整 deploy automation

這次有意識地把範圍壓到最小，原因是第一版需要的是可驗證、可回溯、可交接的 repo-backed 流程，而不是一次把 infra apply、rollout、環境切換全部做完。

當時的收斂方向是：

- 先確認 infra repo 的 deployment state 還在追 `latest`。
- 先把 version state 的更新寫成 repo-backed PR。
- deploy 的後續處理先保留到下一階段。

### 3. 版本更新的最小變更面

目前 `weamind-infra` 的最小變更面就是：

- `manifests/deployment.yaml`

第一版 PR 的內容只需要改這一個檔案，且只更新 image tag。

### 4. release tag 的目標格式

第一版已確認應使用完整 release version tag，例如：

- `ghcr.io/kyomind/weamind:1.2.2`

而不是：

- `latest`
- `minor`
- `major`

這樣版本更新 PR 才能代表正式發版對應的 deployment state。

## 主要實作內容

### 1. 新增跨 repo PR script

新增檔案：

- `scripts/open_infra_version_pr.sh`

這支 script 的責任邊界如下：

- 驗證輸入的 release version。
- 確認必要工具存在：`gh`、`git`、`sed`、`grep`、`mktemp`。
- clone `kyomind/weamind-infra` 的 `main`。
- 建立 branch：`bump-weamind-<version>`。
- 更新 `manifests/deployment.yaml` 的 image tag。
- 若沒有 diff，直接結束，不送 PR。
- commit 變更。
- push branch。
- 若同 branch 的 PR 已存在，就更新 title/body；否則建立新的 PR。

### 2. 串接 release workflow

修改檔案：

- `.github/workflows/publish-release.yml`

release workflow 的最後一步會呼叫：

- `bash ./scripts/open_infra_version_pr.sh "${{ steps.version.outputs.full }}"`

也就是說，只要 release image 成功推到 GHCR，後面就會接著開 infra PR。

### 3. release 觸發與 artifact 行為

`publish-release.yml` 的觸發條件仍是 `v*` tag push。這代表：

- 普通 `main` push 不會開 infra PR。
- 只有正式 release 才會進入這條 CD 路徑。

## 遇到的問題與修正

### 問題 1：release workflow 在開 infra PR 時失敗

第一次跑 `make changelog-release VERSION=1.2.2` 時，release workflow 先完成 GHCR build/push，但在 `Open infra version PR` step 失敗。

#### 失敗原因

錯誤是：

- `fatal: could not read Username for 'https://github.com': No such device or address`

原因不是 repo 不存在，而是 `git push` 沒有拿到可用的 HTTPS 認證。`gh repo clone` 可以正常 clone，但進到新的工作目錄後，git push 仍需要先把 GH token 安裝成 git 認證來源。

#### 修正方式

在 `scripts/open_infra_version_pr.sh` 裡，於 clone 完成並 `cd` 進 repo 後，新增：

- `gh auth setup-git`

這一步會把目前的 `GH_TOKEN` 轉成 git 可用的認證設定，讓後續 `git push` 正常工作。

### 問題 2：需要手動補開 infra PR

因為第一次 release workflow 已經失敗，而且 GitHub Actions 不會自動重跑舊 run，所以在修完 script 後，直接手動執行 script 補開 PR：

- `GH_TOKEN="$(gh auth token)" bash ./scripts/open_infra_version_pr.sh 1.2.2`

這次成功建立了：

- `https://github.com/kyomind/weamind-infra/pull/4`

## 驗證結果

### 已完成的驗證

- `make changelog-release VERSION=1.2.2` 已成功推送 `main` 與 `v1.2.2` tag。
- `gh run list` 顯示 release 相關 workflow 已被觸發。
- `publish-release.yml` 的失敗點已定位到 `Open infra version PR` step。
- 修正後的 `scripts/open_infra_version_pr.sh` 已通過 `bash -n`。
- 修正後的 `scripts/open_infra_version_pr.sh` 已通過 `git diff --check`。
- 手動執行修正版 script 後，成功建立 `weamind-infra` PR #4。

### 目前可觀察到的結果

- WeaMind app repo 已有 release `v1.2.2`。
- `weamind-infra` 已有對應的版本更新 PR。
- 工作樹已清乾淨。

## 現在的狀態

### 已完成

- release 後自動開 infra 版本更新 PR 的第一版骨架。
- release workflow 串接跨 repo PR script。
- git push 認證問題的修正。
- `weamind-infra` PR #4 已建立。

### 待處理事項

1. `weamind-infra` PR #4 目前仍是 OPEN，還需要 review / merge。
2. 如果下一次要驗證「完全自動」的 release path，仍建議再做一次新的 release tag，確認修正後的 workflow 可以不靠手動補跑而直接成功。

## 下一次 AI 接手時的優先順序

1. 先看 `scripts/open_infra_version_pr.sh` 是否還維持目前的最小責任邊界。
2. 再看 `publish-release.yml` 是否還是只做 release 後呼叫 script，不把邏輯繼續塞進 workflow YAML。
3. 若要繼續驗證 CD，優先確認 `weamind-infra` PR #4 的 review / merge 狀態。
4. 如果要做下一輪端到端驗證，建立下一個 release tag，再觀察 release workflow 是否能直接成功開出新的 infra PR。

## 備註

這份文件的重點是 handoff，不是完整操作手冊。若未來要補更完整的 lesson 或設計取捨，建議另寫到對應的 note 文件，避免這份文件被撐得太大。
