# Docker Image Tag 策略：解決 `latest` 標籤衝突

## 問題背景

WeaMind 專案有兩個 GitHub Actions workflow 會推送 Docker image 到 GHCR：

1. **publish-ghcr.yml**：CI 成功後自動推送（追蹤 main 分支）
2. **publish-release.yml**：建立 release tag 時推送（語義化版本號）

兩者原本都會更新 `latest` tag，導致語義不明確。

## Workflow 功能分析

### publish-ghcr.yml
- **觸發時機**：CI workflow 成功完成，且是 main 分支的 push 事件
- **推送的 tags**：
  - `latest`
  - `sha-xxxxxxx`（commit SHA 前 7 碼）
- **用途**：持續追蹤 main 分支最新開發狀態

### publish-release.yml
- **觸發時機**：建立 `v*` 格式的 tag（如 v1.0.7）
- **推送的 tags**（修改前）：
  - `1.0.7`（完整版本號）
  - `1.0`（minor 版本）
  - `1`（major 版本）
  - `latest` ← **衝突點**
- **用途**：正式發布版本，提供穩定版本號供回滾使用

## 衝突說明

當兩個 workflow 都管理 `latest` tag 時，會出現以下時間線問題：

1. **T1**：main 有新 commit → publish-ghcr.yml 推送 `latest`（指向 commit abc123）
2. **T2**：打 tag v1.0.7 → publish-release.yml 推送 `latest`（指向 v1.0.7）
3. **T3**：main 又有新 commit → publish-ghcr.yml 再次推送 `latest`（又指向新 commit def456）

**結果**：`latest` 有時是穩定 release，有時是開發中的 commit，使用者無法確定其含義。

### 問題的本質：競爭覆蓋導致的不可預測性

這是一個**大問題**，因為：

1. **Tag 競爭覆蓋**：兩個 workflow 會互相覆蓋對方推送的 `latest` tag
   - 你無法控制哪個 workflow 會最後執行
   - `latest` 永遠指向「最後推送的那一個」，而非「最穩定的那一個」

2. **部署時的不可預測性**：
   ```bash
   # 在 K8s 上執行 kubectl rollout restart
   # 你以為會拉取 v1.0.7 穩定版本
   # 實際上可能拉到 commit def456 開發中的版本（可能有 bug）
   ```

3. **破壞性場景範例**：
   - **T1**：發布 v1.0.7，`latest` 指向穩定版本 ✓
   - **T2**：開發新功能，commit 推送到 main（包含未完成的重構）
   - **T3**：publish-ghcr.yml 自動執行，覆蓋 `latest` ✗
   - **T4**：生產環境重啟服務，拉取到**未完成的開發版本** → **系統故障** 💥

4. **無法回答的問題**：
   - 「現在 `latest` 是穩定的嗎？」→ 不知道，取決於最近的 workflow 執行順序
   - 「`latest` 是哪個版本？」→ 可能是 v1.0.7，也可能是某個隨機 commit
   - 「能用 `latest` 部署到生產環境嗎？」→ **絕對不行**，風險太高

**核心問題**：`latest` 失去了語義一致性，變成「最後推送的版本」而非「最合適的版本」。

## 與業界標準做法的差異

**一般公開供人使用的 Docker image**（如 nginx、postgres、node）：
- `latest` 通常指向**最新的穩定 release tag**
- 目的：讓使用者能安全地使用 `latest`，不會拉到不穩定的開發版本
- 範例：`nginx:latest` = `nginx:1.25.3`（穩定版本）

**WeaMind 的特殊性**：
- **個人 Side Project 性質**：雖然 image 是公開的，但主要使用者是作者本人
- **需求優先級不同**：需優先滿足「demo、測試」的快速迭代需求，而非外部使用者的穩定性需求
- **main 分支品質保證**：通過完整 CI 驗證，main 本身就是生產就緒狀態

## 解決方案選項

### 選項 A：`latest` = 最新穩定 release
- 移除 publish-ghcr.yml 的 `latest`，只保留 `sha-xxx`
- **適用場景**：企業專案、多人協作、公開 library

### 選項 B：`latest` = main 最新狀態 ✅ **採用**
- 移除 publish-release.yml 的 `latest`，只保留語義化版本號
- **適用場景**：個人專案、持續部署、快速迭代優先

## 最終決策與執行

**選擇選項 B**，核心優勢：

1. **快速部署流程**：push to main → CI 通過 → `latest` 自動更新 → K8s 立即可用
2. **完整版本管理**：語義化版本號（1.0.7, 1.0, 1）提供穩定部署和回滾機制
3. **靈活測試環境**：`latest` 配合 `imagePullPolicy: Always` 方便快速測試新功能

## 實施修改

修改 `.github/workflows/publish-release.yml`，從 tags 列表中移除 `latest`：

```yaml
# 修改前
tags: |
  ghcr.io/${{ github.repository_owner }}/weamind:${{ steps.version.outputs.full }}
  ghcr.io/${{ github.repository_owner }}/weamind:${{ steps.version.outputs.minor }}
  ghcr.io/${{ github.repository_owner }}/weamind:${{ steps.version.outputs.major }}
  ghcr.io/${{ github.repository_owner }}/weamind:latest  # ← 移除此行

# 修改後
tags: |
  ghcr.io/${{ github.repository_owner }}/weamind:${{ steps.version.outputs.full }}
  ghcr.io/${{ github.repository_owner }}/weamind:${{ steps.version.outputs.minor }}
  ghcr.io/${{ github.repository_owner }}/weamind:${{ steps.version.outputs.major }}
```

## 最終 Tag 策略

### 日常開發流程
- Push to main → CI 通過 → publish-ghcr.yml 推送：
  - `latest`（永遠指向 main 最新 commit）
  - `sha-abc1234`（可追溯特定 commit）

### 正式發布流程
- 建立 tag v1.0.7 → publish-release.yml 推送：
  - `1.0.7`（完整版本號）
  - `1.0`（minor 版本，方便鎖定小版本）
  - `1`（major 版本，方便鎖定大版本）

## 使用建議

### 在 K8s 上的部署策略

**開發/測試環境**：
```yaml
image: ghcr.io/kyomind/weamind:latest
imagePullPolicy: Always
```

**生產環境**：
```yaml
image: ghcr.io/kyomind/weamind:1.0.7  # 使用完整版本號
imagePullPolicy: IfNotPresent
```

**彈性部署**（鎖定 minor 版本，自動獲取 patch 更新）：
```yaml
image: ghcr.io/kyomind/weamind:1.0
imagePullPolicy: Always
```

## 參考資料

- [GitHub Actions: publish-ghcr.yml](../.github/workflows/publish-ghcr.yml)
- [GitHub Actions: publish-release.yml](../.github/workflows/publish-release.yml)
- [Docker Tag Best Practices](https://docs.docker.com/engine/reference/commandline/tag/)

---

**決策日期**：2026-01-13
**討論參與者**：kyomind, GitHub Copilot
