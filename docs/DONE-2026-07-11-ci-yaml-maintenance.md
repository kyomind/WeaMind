# DONE - CI YAML 維護與 Dependabot/GHCR 修正紀錄

整理日期：2026-07-11

## 背景

本文件記錄 2026-07-11 這輪 WeaMind GitHub maintenance 對 CI / workflow YAML 的調整。目的不只是留下變更紀錄，也讓下一個沒有上下文的 AI session 可以直接理解問題、沿用做法，或在類似情境中舉一反三。

本輪維護起點是 `.github/prompts/github-maintenance.prompt.md`。當時 live snapshot 顯示：

- Open Dependabot PR：3 個，皆為 GitHub Actions 版本更新。
- Open CodeQL alerts：0。
- Open Dependabot security alerts：0。
- 失敗的 GitHub Actions 主要集中在 Dependabot PR 的 `Code Quality & Tests`。

## 已完成項目

### 1. 修正 Dependabot PR 被 Codecov 擋住

相關檔案：

- `.github/workflows/ci.yml`

問題：

Dependabot PR 的 `Code Quality & Tests` 其實已經跑完 lint、format、type check、Bandit、pip-audit、pytest coverage，但最後 Codecov upload 失敗：

```text
Token required because branch is protected
```

原因是 Dependabot `pull_request` run 無法取得 `secrets.CODECOV_TOKEN`，而 Codecov step 設定了 `fail_ci_if_error: true`。這使低風險 GitHub Actions bump 被 coverage upload 權限問題卡住。

修正：

```yaml
- name: Upload coverage to Codecov
  # Dependabot pull_request runs cannot access CODECOV_TOKEN on protected branches.
  if: ${{ github.event_name != 'pull_request' || github.actor != 'dependabot[bot]' }}
  uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f
  with:
    fail_ci_if_error: true
    token: ${{ secrets.CODECOV_TOKEN }}
```

效果：

- Dependabot PR 照常跑測試、lint、type check、Bandit、pip-audit、Docker build validation。
- 只有 Dependabot 的 `pull_request` 事件略過 Codecov upload。
- main push 與非 Dependabot PR 仍保留 Codecov upload，且 `fail_ci_if_error: true` 不變。

對應 PR：

- #116 `Skip Codecov upload for Dependabot PRs`

### 2. 合併三個 Dependabot GitHub Actions PR

在 #116 合併後，更新下列 PR branch 並重新跑 checks：

- #111 `docker/build-push-action` 7.2.0 -> 7.3.0
- #112 `docker/setup-buildx-action` 4.1.0 -> 4.2.0
- #113 `docker/login-action` 4.2.0 -> 4.4.0

結果：

- 三個 PR 的 CI、CodeQL、SonarCloud、Docker build validation 全部通過。
- 三個 PR 皆已合併。
- `.github/workflows/ci.yml`、`.github/workflows/publish-ghcr.yml`、`.github/workflows/publish-release.yml` 中相關 action pin 已更新。

### 3. 修正 GHCR stale publish 被標成 failure

相關檔案：

- `.github/workflows/publish-ghcr.yml`

問題：

本 repo 的 GHCR publish workflow 由 `workflow_run` 觸發，且先前為了避免 privileged workflow checkout event-controlled SHA，採用「checkout trusted `main`，再驗證 checkout SHA 是否等於 CI passed commit」的安全模式。

連續合併 #111、#112、#113 時，較舊的 CI completed event 觸發 GHCR publish，但 `main` 已經移到更新 commit。workflow 正確偵測到 stale commit：

```text
main moved after CI completed; skip publishing stale commit.
```

原本行為是 `exit 1`，因此 GitHub Actions 顯示紅色 failure。這不是安全或發布失敗，而是 stale publish 被正確拒絕；但在日常維護 snapshot 中會造成假警訊。

修正：

`Verify published commit` step 改為輸出 `should_publish`：

```yaml
- name: Verify published commit
  id: verify-commit
  env:
    HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
  run: |
    CHECKED_OUT_SHA="$(git rev-parse HEAD)"
    if [ "$CHECKED_OUT_SHA" != "$HEAD_SHA" ]; then
      echo "main moved after CI completed; skip publishing stale commit."
      echo "checked_out_sha=$CHECKED_OUT_SHA"
      echo "workflow_run_head_sha=$HEAD_SHA"
      echo "should_publish=false" >> "$GITHUB_OUTPUT"
      exit 0
    fi
    echo "should_publish=true" >> "$GITHUB_OUTPUT"
```

後續 Docker steps 加上條件：

```yaml
if: ${{ steps.verify-commit.outputs.should_publish == 'true' }}
```

效果：

- stale publish run 不再被標成 failure。
- 安全 invariant 保留：只 publish CI passed 且仍是 current `main` 的 commit。
- Docker setup、GHCR login、build/push 只有在 verified commit match 時才執行。

對應 PR：

- #117 `Treat stale GHCR publish as skipped`

### 4. 修正 action pin 註解不一致

Dependabot 將 `docker/setup-buildx-action` 更新到 v4.2.0 後，有些註解仍寫 v3.7.1。本輪順手把註解修正為 v4.2.0。

相關檔案：

- `.github/workflows/ci.yml`
- `.github/workflows/publish-ghcr.yml`
- `.github/workflows/publish-release.yml`

這是註解一致性修正，不改變 workflow 行為。

## 驗證結果

本輪修正過程中使用過的驗證：

```bash
git diff --check
ruby -e 'require "yaml"; %w[.github/workflows/ci.yml .github/workflows/publish-ghcr.yml .github/workflows/publish-release.yml].each { |f| YAML.load_file(f) }; puts "workflow yaml parses"'
gh pr checks 116 --repo kyomind/WeaMind --watch
gh pr checks 117 --repo kyomind/WeaMind --watch
gh run watch 29113712449 --repo kyomind/WeaMind --exit-status
gh run watch 29113714144 --repo kyomind/WeaMind --exit-status
```

最後狀態：

- Open PR：0。
- Open CodeQL alerts：0。
- Open Dependabot security alerts：0。
- #117 merge 後 main CI：success。
- #117 merge 後 CodeQL：success。
- #117 merge 後 GHCR publish：success。
- local `main` 與 `origin/main` 對齊。

## 後續處理方式

如果下次又遇到 Dependabot PR 的 CI failure，先讀 failed log，不要只看紅色 status。判斷順序：

1. 如果第一個真實錯誤是 Codecov token / protected branch / Dependabot secret access，通常是 bot 權限問題，不是 dependency bump 本身壞掉。
2. 確認測試、lint、type check、Bandit、pip-audit、Docker validation 是否其實都已通過。
3. 若是新的 secret-restricted step，優先用 `if:` 對 Dependabot `pull_request` 做窄範圍 skip，不要放寬 main push 或一般 PR 的驗證。
4. 若 GHCR publish 因 stale commit 被 skip，要看最新 `Publish to GHCR` run 是否成功；中間 commit 的 stale run 不代表 latest image 發布失敗。

## 待處理事項

沒有。

## MEMOS

- 這輪的核心不是 dependency code bug，而是 CI 權限與 workflow 狀態呈現問題。
- Codecov：Dependabot PR 拿不到 `CODECOV_TOKEN` 時，保留測試與品質檢查，只略過 Codecov upload。
- GHCR：trusted `main` checkout + SHA verify 是安全設計，不能改回 checkout `github.event.workflow_run.head_sha`，否則可能重新觸發 CodeQL privileged workflow / untrusted checkout 類警示。
- GHCR stale publish 應該成功 skip，不應該紅燈失敗；真正要確認的是最新 main commit 的 GHCR publish 是否成功。
- action pin 更新後，記得同步檢查旁邊版本註解是否 stale。
- 這輪已合併：#116、#111、#112、#113、#117。
