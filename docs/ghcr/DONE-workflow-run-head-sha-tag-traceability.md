# workflow_run head_sha Image Tag Traceability 修正紀錄

整理日期：2026-04-30

## 文件目的

這份文件記錄 `publish-ghcr.yml` 在 `workflow_run` 觸發情境下，image `sha-<short_sha>` tag 來源修正的背景、判斷、實際修改與後續狀態。

handoff 目標是讓下一次全新 AI 即使沒有對話上下文，也能快速理解：

- 為什麼這次要修正 `publish-ghcr.yml`
- 修正前的可追溯性問題是什麼
- 已經改了哪些檔案
- 這件事對 WeaMind Phase 2 / W8 CD 學習主線的影響
- 是否還有待處理事項

## 背景

WeaMind app repo 的 `publish-ghcr.yml` 不是直接由 `push` 觸發，而是由 `CI` workflow 完成後的 `workflow_run` 事件觸發。

原本 workflow 的核心流程是：

1. `CI` workflow 在 `main` push 後執行。
2. `CI` 成功後，`publish-ghcr.yml` 被 `workflow_run` 觸發。
3. `actions/checkout` 使用 `github.event.workflow_run.head_sha` checkout 剛剛通過 CI 的 commit。
4. Docker image build 後 push 到 GHCR。
5. image tags 包含 `latest` 與 `sha-<short_sha>`。

修正前的問題在第 5 步：workflow checkout 的 commit 是 `github.event.workflow_run.head_sha`，但計算 `sha-<short_sha>` tag 時使用的是 `GITHUB_SHA`。

## Issue

在 `workflow_run` 事件中，GitHub Actions 的 `GITHUB_SHA` 語義不是「觸發前一個 workflow 的 commit」，而是 default branch 的最後一個 commit。

GitHub 官方文件在 `workflow_run` 事件表格中說明：

- `GITHUB_SHA`: Last commit on default branch
- `GITHUB_REF`: Default branch

參考文件：

- `https://docs.github.com/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run`

因此，修正前存在一個語義不穩定的情境：

1. commit `aaa1111` push 到 `main`
2. `CI` for `aaa1111` 開始跑
3. 使用者很快又 push commit `bbb2222` 到 `main`
4. `aaa1111` 的 `CI` 成功，觸發 `publish-ghcr.yml`
5. publish workflow checkout 的是 `aaa1111`
6. 但 `GITHUB_SHA` 可能指向 default branch 當下最後 commit，也就是 `bbb2222`
7. 最後 image 內容是 `aaa1111`，tag 卻可能是 `sha-bbb2222`

這會破壞 `sha-<short_sha>` tag 的可追溯性。debug production 或 rollback 時，使用者可能以為部署的是某個 commit，實際 image 內容卻是另一個 commit。

## 判斷

這次修正不改變 WeaMind Phase 2 / W8 的 CD 學習主線。

W8 的核心仍然是：

- WeaMind 目前有 CI 與 image publishing，但還沒有完整 CD
- 正式 deploy source 不應該追 `latest`
- infra repo 應保存 deployment state
- 第一版合理方向是 release 成功後開 PR 更新 infra repo 的 image version

這次修正只是把 W8 會依賴的 app repo image publishing 基線修得更合理。

更精確地說，這是 artifact traceability 修正，不是 CD 方向改變。

## 實際修改

### WeaMind app repo

修改檔案：

- `.github/workflows/publish-ghcr.yml`

修正內容：

- 在 `Compute tags` step 增加 `HEAD_SHA: ${{ github.event.workflow_run.head_sha }}`
- 使用 `HEAD_SHA` 計算 `SHORT_SHA`
- 額外輸出 `full_sha`

修正後語義：

- checkout ref 來自 `github.event.workflow_run.head_sha`
- image 內容來自同一個 commit
- `sha-<short_sha>` tag 也來自同一個 commit

### weamind-infra reference snapshot

因為 infra repo 保留 app repo workflow snapshot 作為學習與 W8 CD 設計 reference，也同步更新了以下檔案：

- `references/weamind-app-publish-ghcr.yml`
- `references/weamind-ci-to-k8s-flow.md`
- `references/phase2/w8-cd-minimum-spec.md`

同步內容：

- snapshot workflow 改用 `workflow_run.head_sha` 計算 short SHA
- 現況流程文件補充 checkout / build / tag 都應指向同一個 `workflow_run.head_sha`
- W8 minimum spec 補充 `workflow_run` 下 `sha-<short_sha>` tag 的 traceability 驗收點

## 驗證

已做的本地驗證：

- 使用 Ruby YAML parser 解析 `.github/workflows/publish-ghcr.yml`
- 使用 Ruby YAML parser 解析 infra repo 的 `references/weamind-app-publish-ghcr.yml`
- 使用 `rg` 確認 `publish-ghcr.yml` 內不再用 `GITHUB_SHA` 計算 image tag
- 使用 `git diff` 檢查修正範圍

驗證結果：

- YAML parse OK
- `publish-ghcr.yml` 的 checkout ref 與 tag 計算來源已一致

## 對 W8 的影響

對 W8 學習主線沒有負面影響。

這次修正會讓後續討論 CD、release version、rollback、deployment state 時，底層 image publishing 的 traceability 更一致。

可以這樣對外說：

> 這不是改 W8 的 CD 方向，而是修正 W8 依賴的 CI/image publishing 基線，讓 `sha-*` image tag 真正對應通過 CI 並被 build 的 commit。

## 待處理事項

沒有待處理事項。

如果未來要繼續加強，可以考慮在 image labels 或 build metadata 中加入 full commit SHA，但這不是本次修正的必要項目。
