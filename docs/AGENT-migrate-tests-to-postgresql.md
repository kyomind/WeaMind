# AGENT-migrate-tests-to-postgresql.md

## 🎯 Mission Statement
**將單元測試資料庫從 SQLite 完全遷移至 PostgreSQL，消除資料庫方言差異，確保測試環境與生產環境一致。**

## 💭 Context & Problem (Why)

### 核心問題
- **方言差異風險**：SQLite 和 PostgreSQL 在語法和行為上存在差異，可能導致測試通過但生產環境出錯
- **具體案例**：`app/user/service.py` 中的 `get_recent_queries` 函式刻意避免使用 PostgreSQL 的 `DISTINCT ON` 語法，因為 SQLite 不支援
- **技術債累積**：為了相容 SQLite，犧牲了 PostgreSQL 的效能優勢

### 現況分析
- 測試環境：SQLite in-memory (`sqlite+pysqlite:///:memory:`)
- 生產環境：PostgreSQL 17.5 (透過 Docker 容器)
- 已存在 PostgreSQL 容器：運行在 port 5433
- CI 環境：GitHub Actions with uv container

## 🎯 Objectives (What)

### 主要目標
1. **完全移除 SQLite**：測試不再使用 SQLite
2. **統一資料庫環境**：本地測試、CI、生產環境都使用 PostgreSQL
3. **效能優化**：利用 PostgreSQL 特性改善查詢效能
4. **維護簡化**：移除環境差異處理邏輯

### 成功指標
- [ ] 所有測試使用 PostgreSQL 執行
- [ ] CI 管道正常運作
- [ ] `get_recent_queries` 使用 PostgreSQL 最佳化語法
- [ ] 測試執行時間合理（不超過原本的 150%）

## 🛠 Technical Implementation (How)

### Architecture Decision
**選擇方案：GitHub Actions Services + 現有 PostgreSQL 容器**
- ✅ 一步到位，避免過渡性方案
- ✅ 環境一致性
- ✅ 維護簡單
- ❌ 需要同時修改本地和 CI 配置

### 實作階段

#### 階段一：本地測試配置 (20-25 分鐘)
1. **建立測試資料庫**
   - 在現有 PostgreSQL 容器中建立 `weamind_test` 資料庫
   - 不需要新的容器或服務

2. **修改測試配置**
   - 更新 `tests/conftest.py` 的 `DATABASE_URL`
   - 實作測試資料隔離機制

3. **測試隔離策略**
   - 每個測試會話：`Base.metadata.create_all()`
   - 每個測試後：事務回滾或 TRUNCATE

#### 階段二：CI 配置 (10-15 分鐘)
1. **GitHub Actions Services**
   - 在 `.github/workflows/ci.yml` 添加 PostgreSQL service
   - 設定健康檢查和連線參數

2. **環境變數配置**
   - 測試專用的資料庫連線設定
   - 確保 CI 和本地設定一致

#### 階段三：查詢最佳化 (10-15 分鐘)
1. **修改 `get_recent_queries`**
   - 使用 PostgreSQL 的 `DISTINCT ON`
   - 移除相容性 workaround
   - 更新相關 TODO 註解

### Technical Constraints

#### 必須考慮的限制
- **容器依賴**：本地測試需要 PostgreSQL 容器運行
- **CI 服務依賴**：CI 環境需要添加 PostgreSQL service 配置
- **效能影響**：目前測試只需 1 秒，PostgreSQL 可能增加啟動時間
- **並發測試**：當前測試速度足夠快，無需考慮 pytest-xdist

#### 風險緩解
- **回滾計畫**：保留原 SQLite 設定在 git history 中
- **漸進驗證**：先在本地完整測試，再推送 CI 變更
- **監控指標**：測試執行時間、CI 成功率

## 🧠 Memory Hooks (重要決策記錄)

### 💡 核心決策
> "過渡性的做法常常是自找麻煩" - 用戶智慧
- **決策**：拒絕環境變數控制策略，選擇一步到位
- **理由**：避免維護複雜的條件邏輯和環境差異

> "在現有 PostgreSQL 容器中建立測試資料庫，不需要新容器"
- **決策**：本地使用邏輯資料庫分離，CI 使用 GitHub Actions service
- **理由**：本地資源效率、CI 環境隔離

> "目前測試 1 秒完成，無需 pytest-xdist"
- **決策**：暫不引入並行測試複雜性
- **理由**：當前效能已足夠，避免過度工程化

### ⚠️ 避免的陷阱
- **❌ 新建 PostgreSQL 容器**：本地過度複雜化（但 CI 仍需要 service）
- **❌ 環境變數控制**：維護負擔高
- **❌ 部分遷移**：容易產生技術債
- **❌ 過度最佳化**：目前測試 1 秒完成，無需 pytest-xdist

### 🔍 關鍵檔案
- `tests/conftest.py` - 測試資料庫配置核心
- `app/user/service.py:get_recent_queries` - 具體的方言差異案例
- `.github/workflows/ci.yml` - CI PostgreSQL service 配置
- `app/core/database.py` - 資料庫連線設定

### 🎯 成功模式
```python
# 目標：從這樣的 workaround
for user_query in query.limit(100):
    if user_query.location_id not in seen_locations:
        # ...手動去重邏輯

# 變成：直接使用 PostgreSQL 特性
query = session.query(UserQuery).distinct(UserQuery.location_id)...
```

## 📋 Implementation Checklist

### Pre-flight
- [ ] 確認 PostgreSQL 容器運行狀態
- [ ] 檢查目前測試覆蓋率作為基準

### Phase 1: Local
- [ ] 建立 `weamind_test` 資料庫
- [ ] 修改 `tests/conftest.py`
- [ ] 更新所有模組的 conftest.py
- [ ] 本地執行完整測試套件

### Phase 2: CI
- [ ] 修改 `.github/workflows/ci.yml`
- [ ] 添加 PostgreSQL service 配置
- [ ] 驗證 CI 測試通過

### Phase 3: Optimization
- [ ] 重構 `get_recent_queries` 使用 `DISTINCT ON`
- [ ] 移除相關 TODO 註解
- [ ] 效能測試和比較

### Post-implementation
- [ ] 更新相關文檔
- [ ] 標記此 TODO 為完成
- [ ] 考慮是否有其他類似的方言相容性問題

---
*Generated: 2025-09-03*
*Agent: Claude Code*
*Status: Ready for Implementation*
