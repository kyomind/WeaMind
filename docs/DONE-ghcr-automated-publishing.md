# DONE: GitHub Actions 自動發布 Docker Image 到 GHCR

**完成日期**: 2026-01-12
**對應 Todo**: #37, #38

## 目標

實作自動化容器 image 發布流程，讓每次 push 到 main 或建立 git tag 時，自動 build 並推送 Docker image 到 GitHub Container Registry (GHCR)，並將 Bastion Host 部署從本地 build 改為使用 GHCR image。

## 實作內容

### 1. 建立 GitHub Actions Workflows

#### 1.1 `publish-ghcr.yml` - 開發版自動發布
- **觸發時機**: CI workflow 成功後（僅 main 分支）
- **產出**:
  - `ghcr.io/kyomind/weamind:latest`
  - `ghcr.io/kyomind/weamind:sha-xxxxxxx`
- **關鍵設定**:
  ```yaml
  on:
    workflow_run:
      workflows: ["CI"]
      types: [completed]
      branches: [main]

  permissions:
    contents: read
    packages: write
  ```

#### 1.2 `publish-release.yml` - 正式版發布
- **觸發時機**: 建立 `v*` 格式的 git tag
- **產出**: 語義化版本號 tags
  - `ghcr.io/kyomind/weamind:1.0.7` (完整版本)
  - `ghcr.io/kyomind/weamind:1.0` (minor)
  - `ghcr.io/kyomind/weamind:1` (major)
  - `ghcr.io/kyomind/weamind:latest`
- **用途**: 未來正式發版時使用

### 2. 多平台支援

為兩個 workflows 添加多平台 build：
```yaml
platforms: linux/amd64,linux/arm64
```

**原因**: 支援 x86_64 伺服器和 Apple Silicon Mac

### 3. 修改部署配置

#### 3.1 docker-compose.yml
```yaml
# 修改前
services:
  app:
    image: wea-image
    build: .

# 修改後
services:
  app:
    image: ghcr.io/kyomind/weamind:latest
```

#### 3.2 Makefile
```makefile
# 修改前
deploy:
	docker compose ... up --build -d

# 修改後
deploy:
	docker compose ... pull app  # 先 pull image
	docker compose ... up -d     # 再啟動
```

### 4. GHCR Package 權限設定

- **Visibility**: Public（允許無認證 pull）
- **Access**: 繼承 source repository 權限（推薦）

## 遇到的問題與解決方案

### 問題 1: Invalid tag format
**錯誤訊息**:
```
ERROR: invalid tag "ghcr.io/kyomind/weamind:latest # latest = 永遠指向最新版"
```

**原因**: YAML 的 `|` 多行字串會把行內註解也包進去

**解決方案**: 將註解移到步驟說明上方
```yaml
# 同時推送兩個 tag：latest 和 sha-xxx
tags: |
  ghcr.io/kyomind/weamind:latest
  ghcr.io/kyomind/weamind:sha-xxx
```

### 問題 2: No matching manifest for linux/arm64
**錯誤訊息**:
```
no matching manifest for linux/arm64/v8 in the manifest list entries
```

**原因**: GitHub Actions 預設只 build x86_64 架構

**解決方案**: 添加多平台支援
```yaml
platforms: linux/amd64,linux/arm64
```

## 驗證結果

### 本地驗證（Mac）
```bash
❯ docker pull ghcr.io/kyomind/weamind:latest
latest: Pulling from kyomind/weamind
✓ Success

❯ docker image inspect ghcr.io/kyomind/weamind:latest | grep Architecture
"Architecture": "arm64"
```

### 部署流程變化

| 階段        | 修改前                   | 修改後                           |
| ----------- | ------------------------ | -------------------------------- |
| 更新程式碼  | `git pull`               | `git pull` (最後一次)            |
| Build image | 本地 build 3-5 分鐘      | GitHub Actions 自動 build        |
| 部署        | `make deploy` (含 build) | `make deploy` (只 pull，30 秒內) |
| 版本追溯    | Git commit               | Image tag (sha-xxx)              |

## 檔案變更清單

```bash
新增:
- .github/workflows/publish-ghcr.yml
- .github/workflows/publish-release.yml

修改:
- docker-compose.yml (移除 build, 改用 GHCR image)
- Makefile (deploy 指令移除 --build)
- docs/Todo.md (標記 #37 完成, 新增 #38)
```

## 後續優化建議

1. **設定 image 保留政策**: 避免舊 tag 堆積
2. **加入版本號到 commit message**: 方便追蹤
3. **監控 build 時間**: 多平台 build 較耗時
4. **考慮 staging tag**: 例如 `staging` tag 指向 develop 分支

## 相關連結

- **GitHub Packages**: https://github.com/kyomind/WeaMind/pkgs/container/weamind
- **Actions Workflows**: https://github.com/kyomind/WeaMind/actions
- **PR #71**: https://github.com/kyomind/WeaMind/pull/71

## 總結

✅ **完成自動化發布流程**
- 每次 push main 自動產生新 image
- 支援多平台（x86_64 + ARM64）
- Bastion 部署不再需要本地 build
- 版本可追溯（SHA tag）
- 為 K8s 部署鋪路

**實際效益**:
- 部署速度提升 80% (3-5 分鐘 → 30 秒)
- 環境一致性提升（CI 與 Bastion 使用同一 image）
- 減少 Bastion 依賴（不需要 build tools、source code）
