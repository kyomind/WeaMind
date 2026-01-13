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

## 討論的選項

### 選項 A：`latest` = 最新穩定 release
- 移除 publish-ghcr.yml 的 `latest`，只保留 `sha-xxx`
- **適用場景**：企業專案、多人協作、需要明確區分穩定版和開發版

### 選項 B：`latest` = main 最新狀態 ✅ **採用**
- 移除 publish-release.yml 的 `latest`，只保留語義化版本號
- **適用場景**：個人專案、持續部署、需要快速測試最新功能

## 最終決策

**選擇選項 B**，理由如下：

1. **個人專案特性**：WeaMind 是個人專案，任何更新都需要立即部署
2. **K8s 部署便利性**：在 Kubernetes 上使用 `imagePullPolicy: Always` 配合 `latest` tag，可以快速拉取最新開發版本進行測試
3. **版本回滾機制完整**：保留語義化版本號（1.0.7, 1.0, 1）供穩定部署和回滾使用
4. **開發效率優先**：push to main → `latest` 自動更新 → K8s 立即可用新版本

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
