# 測試資料庫 PostgreSQL 遷移專案

## 🎯 專案目標與最終決策

**將單元測試資料庫從 SQLite 完全遷移至 PostgreSQL，使用 Testcontainers-Python 實現完全隔離的測試環境。**

### 🏆 最終採用方案：Testcontainers-Python
- **完全隔離**：每次測試都是全新 PostgreSQL 容器
- **環境一致**：本地開發、CI、生產環境使用相同的 PostgreSQL 17.5
- **安全優先**：測試專用認證，絕不暴露生產密碼
- **零配置**：新開發者 clone 下來即可執行測試

### 核心問題與解決方案
| 問題             | 現況                                    | 解決後                             |
| ---------------- | --------------------------------------- | ---------------------------------- |
| **方言差異風險** | SQLite vs PostgreSQL 語法不一致         | 統一使用 PostgreSQL                |
| **具體案例**     | `get_recent_queries` 避免 `DISTINCT ON` | 直接使用 PostgreSQL 最佳化語法     |
| **環境不一致**   | 測試 SQLite，生產 PostgreSQL            | 全環境 PostgreSQL 17.5             |
| **安全風險**     | 測試可能暴露生產認證                    | Testcontainers 隔離 + 測試專用認證 |

### 成功指標
- [x] 技術方案確定：Testcontainers-Python
- [ ] 所有測試使用 PostgreSQL 執行
- [ ] CI 管道正常運作
- [ ] `get_recent_queries` 使用 PostgreSQL 最佳化語法
- [ ] 測試執行時間合理（冷啟動 +2-5 秒可接受）

## 🛠 實作方案：Testcontainers-Python

### 為什麼選擇 Testcontainers？

| 考量因素      | Testcontainers-Python | GitHub Actions Service | docker-compose 手刻 |
| ------------- | --------------------- | ---------------------- | ------------------- |
| 本地=CI一致性 | ✅ 100%一致            | ❌ 雙套機制             | ⚠️ 複雜維護          |
| 安全隔離      | ✅ 完全隔離            | ✅ 隔離良好             | ⚠️ 看實作品質        |
| 維護負擔      | ✅ 單一機制            | ❌ 分叉維護             | ❌ 自製輪子          |
| 專業程度      | ✅ 業界標準            | ✅ 官方推薦             | ❌ 重複造輪          |

### 技術架構
```python
# 核心原理
@pytest.fixture(scope="session")
def postgres_container():
    """啟動 PostgreSQL 容器，測試結束後自動銷毀"""
    with PostgreSqlContainer("postgres:17.5") as container:
        yield container

@pytest.fixture
def db_session(postgres_container):
    """為每個測試提供獨立的事務，結束後回滾"""
    engine = create_engine(postgres_container.get_connection_url())
    # 執行 Alembic 升級
    # 創建事務，測試結束後回滾
```

### 優勢總結
- **絕對隔離**：每個測試會話都是全新 PostgreSQL 實例
- **零污染**：測試結束後容器完全銷毀，無狀態殘留
- **CI 友善**：本地和 CI 使用完全相同的邏輯
- **安全性**：使用測試專用認證 (`test/test`)，絕不暴露生產密碼

### 合理代價
- **冷啟動時間**：+2-5 秒（PostgreSQL 容器啟動）
- **學習成本**：需要了解 Testcontainers 基本用法

## 📋 實作計劃

### 階段一：測試基礎建設 (20-25 分鐘)
1. **安裝依賴**
   - 安裝 Testcontainers：`uv add testcontainers[postgresql]`

2. **重寫測試配置**
   - 完全重寫 `tests/conftest.py`
   - 實作 PostgreSQL 容器管理（session scope）
   - 建立事務回滾機制（function scope）
   - FastAPI 依賴覆寫：`app.dependency_overrides[get_db]`

3. **Alembic 整合**
   - 容器啟動後自動執行 `alembic upgrade head`
   - 確保測試 schema 與生產一致

### 階段二：CI 環境配置 (5-10 分鐘)
1. **GitHub Actions 更新**
   - CI 直接執行 `uv run pytest`
   - **不需要**額外的 PostgreSQL 服務配置
   - Testcontainers 會自動處理容器管理

### 階段三：查詢最佳化 (10-15 分鐘)
1. **重構 `get_recent_queries`**
   - 使用 PostgreSQL 的 `DISTINCT ON` 語法
   - 移除 SQLite 相容性 workaround
   - 更新相關註解和文檔

### 關鍵檔案清單
- `tests/conftest.py` - 核心測試配置（需完全重寫）
- `app/user/service.py:get_recent_queries` - 具體的方言差異案例
- `.github/workflows/ci.yml` - 可能需要微調（移除不必要的服務）
- `pyproject.toml` - 添加 testcontainers 依賴

## 📋 實作檢查清單

### 預備階段
- [ ] 確認目前測試覆蓋率作為基準
- [ ] 安裝 Testcontainers 依賴：`uv add testcontainers[postgresql]`

### 階段一：Testcontainers 基礎建設
- [ ] 完全重寫 `tests/conftest.py`
- [ ] 實作 PostgreSQL 容器管理（session scope）
- [ ] 加入 Alembic `upgrade head` 到容器初始化
- [ ] 實作事務回滾機制（function scope）
- [ ] FastAPI 依賴覆寫：`app.dependency_overrides[get_db]`
- [ ] 更新所有模組的 conftest.py
- [ ] 本地執行完整測試套件
- [ ] 驗證無任何生產環境依賴

### 階段二：CI 環境統一
- [ ] 確認 `.github/workflows/ci.yml` 配置
- [ ] CI 直接執行 `uv run pytest`（讓 Testcontainers 自動處理）
- [ ] 驗證 CI 測試通過
- [ ] 確認本地=CI 完全一致

### 階段三：PostgreSQL 最佳化
- [ ] 重構 `get_recent_queries` 使用 `DISTINCT ON`
- [ ] 移除 SQLite workaround 和相關 TODO 註解
- [ ] 搜尋其他類似的方言相容性問題
- [ ] 效能測試和比較

### 完成階段
- [ ] 移除舊的 SQLite 相關程式碼
- [ ] 更新專案文檔
- [ ] 將成功經驗寫入專案指南

## 📚 歷史決策記錄與經驗學習

### 🚨 失敗經驗：第一次實作（2025-09-03）
**執行代理**：Claude Code
**分支**：`feature/migrate-tests-to-postgresql`
**狀態**：❌ 已廢棄

#### 失敗的方案：延用既有 PostgreSQL 容器
**問題一：安全性風險**
```python
# tests/conftest.py - 危險實作
os.environ["POSTGRES_USER"] = "REDACTED_PRODUCTION_USER"
os.environ["POSTGRES_PASSWORD"] = "REDACTED_PRODUCTION_PASSWORD"  # 生產密碼暴露  # pragma: allowlist secret
```

**問題二：環境耦合**
- 測試依賴生產 PostgreSQL 容器
- 新開發者必須先設置完整生產環境才能跑測試
- 測試和生產共用同一個 PostgreSQL 實例

#### 關鍵教訓
1. **安全性優於便利性**：絕不能為了實作簡便而暴露生產認證
2. **完全隔離勝過部分隔離**：測試環境必須完全獨立於生產環境
3. **一步到位勝過過渡方案**：避免「臨時解決方案」變成長期技術債

### 💡 為什麼選擇 Testcontainers 而非其他方案？

#### 與 Django 測試環境的比較
| 特性     | Django (早期) | Django (現代) | FastAPI + Testcontainers |
| -------- | ------------- | ------------- | ------------------------ |
| 上手難度 | ✅ 超簡單      | ⚠️ 中等        | ⚠️ 中等                   |
| 隔離程度 | ❌ 依賴既有DB  | ✅ 完全隔離    | ✅ 完全隔離               |
| CI 友善  | ❌ 需預配置    | ✅ 零配置      | ✅ 零配置                 |

**為什麼以前 Django 感覺簡單？**
- `pytest-django` 標準化了測試 DB 管理
- 單人開發無並行測試衝突問題
- 全家桶哲學隱藏了複雜度

**現代最佳實踐的演進**：
連 Django 專案現在也開始用 Testcontainers 做完全隔離的測試環境。

### 🎯 核心決策原則
1. **「安全性優於便利性」**：不能為了實作簡便而妥協安全性
2. **「完全隔離勝過部分隔離」**：拒絕過渡性做法，直接採用最佳實踐
3. **「一致性勝過靈活性」**：本地=CI 完全一致，避免「我這邊可以跑」問題

### ⚠️ 禁忌清單（踩到就回頭）
- ❌ **重用生產容器**：安全風險，認證暴露
- ❌ **環境耦合**：測試依賴生產環境配置
- ❌ **部分遷移**：一半 SQLite、一半 PostgreSQL 只會堆技術債
- ❌ **常駐測試容器**：狀態污染、維護負擔
- ❌ **分叉維護**：本地一套機制、CI 另一套機制

### 📝 程式碼轉換範例
```python
# 目前：為了 SQLite 相容性的 workaround
for user_query in query.limit(100):
    if user_query.location_id not in seen_locations:
        # ...手動去重邏輯

# 目標：直接使用 PostgreSQL 特性
query = session.query(UserQuery).distinct(UserQuery.location_id)...
```

### 🏆 最終決策理由
- **單一機制、零分叉**：測試程式碼自己起/關容器，本地、CI 都走同一條路
- **隔離到位**：每個 pytest session 一顆全新 PostgreSQL，資料不殘留
- **可維護性高**：生命週期寫在 fixture，其他地方只要讀 DATABASE_URL
- **上手容易**：新成員只要會 pytest，其他交給 Testcontainers
