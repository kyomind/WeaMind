# Docker 環境變數與安全性完全指南

**目標讀者**: 容器化部署初學者、對環境變數注入有疑惑的開發者
**核心問題**: 環境變數（特別是敏感資料）該在哪個階段注入？會不會進入 Docker image？

---

## 核心概念：Build Time vs Runtime

### 🏗️ Build Time（製作 Image）

**時機**: 執行 `docker build` 或 GitHub Actions build 時

**發生的事**:
```dockerfile
FROM python:3.12
WORKDIR /code
COPY . /code              # ← 決定什麼檔案進 image
ENV STATIC_CONFIG=value   # ❌ 寫在這裡會烤進 image（不可變）
RUN pip install -r requirements.txt
```

**特性**:
- ✅ **固定不變**: 任何人 pull 這個 image 都會得到一樣的內容
- ✅ **可共享**: 可以推送到 registry 給其他人用
- ❌ **不應包含敏感資料**: 因為無法改變，也可能被別人看到

**結果**: 產生一個 **Image**（唯讀模板）

---

### 🚀 Runtime（啟動容器）

**時機**: 執行 `docker run` 或 `docker compose up` 時

**發生的事**:
```yaml
# docker-compose.yml
services:
  app:
    image: myapp:latest
    env_file:
      - .env              # ← 啟動時才讀取，不進 image
    environment:
      - DEBUG=true        # ← 同上
```

**特性**:
- ✅ **動態可變**: 每次啟動可以用不同的環境變數
- ✅ **環境隔離**: local/dev/prod 用不同的 .env 檔案
- ✅ **適合敏感資料**: 不會進入 image，只在記憶體中

**結果**: 產生一個 **Container**（執行實例）

---

## Image vs Container

### 📦 Image（唯讀模板）

```
myapp:latest
├── OS 基礎層（Debian/Ubuntu）
├── Python runtime
├── 應用程式碼
├── 依賴套件
└── ❌ 沒有 .env 檔案
```

**類比**: 烤好的蛋糕（固定配方）
- 任何人買這個蛋糕都一樣
- 不含客製化調味料（環境變數）

---

### 🏃 Container（執行實例）

```
執行中的容器
├── 來自 image 的所有檔案（唯讀）
├── ✅ Runtime 注入的環境變數（來自 .env）
├── ✅ 掛載的 volumes
└── ✅ 容器內產生的暫存資料
```

**類比**: 端上桌的蛋糕
- 可以淋不同醬料（環境變數）
- 每個客人（環境）加自己的料
- 但蛋糕本體（image）不變

---

## 環境變數注入的三種方式

### ❌ 方式 1: 寫在 Dockerfile（危險）

```dockerfile
# Dockerfile
FROM python:3.12
ENV DATABASE_PASSWORD=secret123  # ❌ 會烤進 image！
```

**後果**:
```bash
# 任何人都能看到
docker history myapp:latest
docker inspect myapp:latest
```

**適用場景**: 只能用於**公開、不敏感**的設定
- `PYTHONUNBUFFERED=1`
- `TZ=Asia/Taipei`
- `APP_NAME=WeaMind`

---

### ✅ 方式 2: env_file（推薦用於 docker-compose）

```yaml
# docker-compose.yml
services:
  app:
    image: myapp:latest
    env_file:
      - .env              # ← Runtime 讀取
```

```bash
# .env（不進 Git、不進 Image）
DATABASE_PASSWORD=secret123
LINE_CHANNEL_SECRET=abc123
API_KEY=xyz789
```

**優點**:
- ✅ 敏感資料不進 image
- ✅ 不同環境用不同 .env
- ✅ 符合 12-Factor App 原則

---

### ✅ 方式 3: environment（適用於單一變數）

```yaml
# docker-compose.yml
services:
  app:
    image: myapp:latest
    environment:
      - ENV=production
      - DEBUG=false
```

**適用場景**: 非敏感的環境設定

---

## 如何確保 .env 不進 Image

### 1. 使用 .dockerignore（必須）

```
# .dockerignore
.env
.env.*
*.key
*.pem
secrets/
```

**作用**: 類似 `.gitignore`，控制 `COPY . /code` 時哪些檔案**不會**進入 image

---

### 2. 永遠不要在 Dockerfile 寫死敏感資料

```dockerfile
# ❌ 錯誤示範
ENV API_KEY=secret123

# ✅ 正確做法（讓 runtime 注入）
# 什麼都不寫
```

---

### 3. 驗證 Image 內容

```bash
# 檢查 image 內是否有 .env
docker run --rm myapp:latest ls -la /code

# 查看環境變數歷史
docker history myapp:latest

# 深入檢查
docker save myapp:latest -o /tmp/myapp.tar
tar -xf /tmp/myapp.tar
grep -r "DATABASE_PASSWORD" .
```

---

## WeaMind 的實踐

### Build Time（GitHub Actions）

```yaml
# .github/workflows/publish-ghcr.yml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    push: true
    tags: ghcr.io/kyomind/weamind:latest
    # ⚠️ 注意：這裡不會讀取 .env
```

**結果**: 產生乾淨的 image
```
ghcr.io/kyomind/weamind:latest
├── FastAPI 應用程式
├── Python 依賴
└── ❌ 沒有任何敏感資料
```

---

### Runtime（Bastion / Local）

```yaml
# docker-compose.yml
services:
  app:
    image: ghcr.io/kyomind/weamind:latest  # ← 從 GHCR pull
    env_file:
      - .env                                 # ← 啟動時注入
```

```bash
# Bastion 上的 .env
DATABASE_PASSWORD=prod_secret
LINE_CHANNEL_SECRET=prod_channel_secret

# Local 上的 .env
DATABASE_PASSWORD=dev_password
LINE_CHANNEL_SECRET=dev_channel_secret
```

**流程**:
```
1. docker compose pull app
   ↓
   下載 image（不含敏感資料）

2. docker compose up -d
   ↓
   讀取本地 .env
   ↓
   注入環境變數到容器記憶體
   ↓
   啟動應用程式
```

---

## 常見誤區與解答

### Q1: docker-compose.yml 中的 env_file 會讓 .env 進入 image 嗎？

**A**: ❌ **不會！**

```yaml
services:
  app:
    build: .        # ← Build Time: 讀取 Dockerfile
    env_file:
      - .env        # ← Runtime: 啟動容器時才讀取
```

兩個階段完全獨立：
- `build: .` 只會執行 Dockerfile 的指令
- `env_file: .env` 只在啟動容器時生效

---

### Q2: 如果 Dockerfile 有 COPY . /code，.env 會進去嗎？

**A**: ❌ **不會（如果有 .dockerignore）**

```dockerfile
COPY . /code  # ← 會排除 .dockerignore 列出的檔案
```

```
# .dockerignore
.env  # ← 這行確保 .env 不會被 COPY 進去
```

**驗證方式**:
```bash
docker run --rm myapp:latest cat /code/.env
# cat: /code/.env: No such file or directory ✅
```

---

### Q3: 改用 GHCR image 後，環境變數注入方式有變嗎？

**A**: ❌ **沒變！**

```yaml
# 修改前（本地 build）
services:
  app:
    build: .
    env_file:
      - .env  # ← Runtime 注入

# 修改後（GHCR）
services:
  app:
    image: ghcr.io/kyomind/weamind:latest
    env_file:
      - .env  # ← Runtime 注入（完全一樣）
```

**改變的只有**:
- Image 來源: 本地 build → GHCR
- Build 速度: 3-5 分鐘 → 30 秒（pull）

**沒變的**:
- 環境變數注入方式
- .env 不進 image
- 安全性

---

### Q4: Image 是 public 的，敏感資料會外洩嗎？

**A**: ❌ **不會（如果正確設定）**

**原因**:
1. `.dockerignore` 排除了 .env
2. 環境變數在 runtime 注入，不在 build time
3. Image 內只有程式碼，沒有敏感資料

**任何人 pull 你的 image**:
```bash
docker pull ghcr.io/kyomind/weamind:latest
docker run myapp:latest

# 會看到錯誤（因為沒有環境變數）
Error: DATABASE_URL is not set
```

他們需要自己提供 .env 才能啟動。

---

## 安全檢查清單

部署前確認：

- [ ] `.dockerignore` 包含 `.env`、`*.key`、`*.pem`
- [ ] Dockerfile 沒有寫死敏感資料（檢查 `ENV` 指令）
- [ ] `.env` 加入 `.gitignore`（不進版控）
- [ ] 不同環境有各自的 .env 檔案
- [ ] 使用 `env_file` 或 `environment` 注入環境變數
- [ ] 驗證過 image 內沒有敏感檔案
- [ ] CI/CD 使用 secrets 管理，不寫在 workflow 檔案

---

## 實戰範例：完整流程

### 開發階段

```bash
# 1. 本地開發
cat > .env << EOF
DATABASE_URL=postgresql://localhost/dev_db
DEBUG=true
EOF

docker compose up --build
```

---

### CI/CD 階段

```yaml
# .github/workflows/publish-ghcr.yml
jobs:
  build:
    steps:
      - name: Build and push
        run: docker build -t ghcr.io/myapp:latest .
        # ⚠️ 這裡不會讀取 .env
```

**產生的 image**: 乾淨、無敏感資料

---

### 生產部署

```bash
# Bastion Host
cat > .env << EOF
DATABASE_URL=postgresql://prod-db/prod_weamind
DEBUG=false
SECRET_KEY=super-secret-production-key
EOF

docker compose pull app  # ← 拉取乾淨的 image
docker compose up -d     # ← 注入生產環境變數
```

---

## 總結

| 概念         | Build Time        | Runtime                 |
| ------------ | ----------------- | ----------------------- |
| **時機**     | docker build      | docker run / compose up |
| **產物**     | Image（唯讀）     | Container（執行中）     |
| **環境變數** | ❌ 寫死（危險）    | ✅ 動態注入（安全）      |
| **敏感資料** | ❌ 不應放這裡      | ✅ 應該放這裡            |
| **可變性**   | 固定不變          | 每次可不同              |
| **共享性**   | 可推送到 registry | 僅本地執行              |

**黃金法則**:
1. Image = 程式碼 + 依賴（公開、可共享）
2. Container = Image + 環境變數（私密、環境特定）
3. 永遠用 `.dockerignore` 排除敏感檔案
4. 永遠在 runtime 注入環境變數

---

## 延伸閱讀

- [The Twelve-Factor App: Config](https://12factor.net/config)
- [Docker Environment Variables Best Practices](https://docs.docker.com/compose/environment-variables/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
