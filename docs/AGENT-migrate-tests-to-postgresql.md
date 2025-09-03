# 測試資料庫 PostgreSQL 遷移專案

## 🎯 專案目標
**將單元測試資料庫從 SQLite 完全遷移至 PostgreSQL，消除資料庫方言差異，確保測試環境與生產環境一致。**

## 💭 背景與問題分析

### 核心問題
- **方言差異風險**：SQLite 和 PostgreSQL 在語法和行為上存在差異，可能導致測試通過但生產環境出錯
- **具體案例**：`app/user/service.py` 中的 `get_recent_queries` 函式刻意避免使用 PostgreSQL 的 `DISTINCT ON` 語法，因為 SQLite 不支援
- **技術債累積**：為了相容 SQLite，犧牲了 PostgreSQL 的效能優勢

### 現況分析
- **測試環境**：SQLite in-memory (`sqlite+pysqlite:///:memory:`)
- **生產環境**：PostgreSQL 17.5 (透過 Docker 容器)
- **既有容器**：運行在 port 5433
- **CI 環境**：GitHub Actions with uv container

## 🎯 實作目標

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

## 🛠 技術實作方案

### ⚠️ 架構決策演進

#### ❌ 失敗方案：延用既有 PostgreSQL 容器
**2025-09-03 程式碼審查發現重大缺陷，已廢棄**

**原始計畫**：
- 使用既有 PostgreSQL 容器 (port 5433)
- 在其中建立 `weamind_test` 資料庫
- 本地和 CI 共用此策略

**發現的關鍵問題**：

1. **🔒 安全性風險 - 生產認證暴露**
   ```python
   # tests/conftest.py - 危險實作
   os.environ["POSTGRES_USER"] = "REDACTED_PRODUCTION_USER"
   os.environ["POSTGRES_PASSWORD"] = "REDACTED_PRODUCTION_PASSWORD"  # 😱 生產密碼  # pragma: allowlist secret
   ```
   - 測試程式碼包含真實生產資料庫認證
   - 任何 fork 或貢獻者都能獲得生產資料庫存取權限
   - 違反最小權限原則

2. **🔗 環境耦合問題**
   - 測試依賴真實的生產 PostgreSQL 容器
   - 新開發者必須先設置完整生產環境才能跑測試
   - 測試和生產共用同一個 PostgreSQL 實例（即使不同資料庫）

3. **🏗️ 架構隔離不足**
   - 不符合「測試環境完全獨立」的最佳實踐
   - 潛在的資源競爭和意外影響風險

### ✅ 推薦方案：完全無狀態容器管理

**核心理念**：pytest 執行時建立專用容器，結束後完全銷毀

**優勢**：
- ✅ **絕對隔離**：每次測試都是全新、乾淨的 PostgreSQL 實例
- ✅ **CI 友善**：GitHub Actions 可以並行執行多個測試任務
- ✅ **零污染**：不會有殘留數據影響後續測試
- ✅ **安全性**：測試結束後完全銷毀，無資料殘留
- ⏱️ **代價**：PostgreSQL 冷啟動需要 2-5 秒

### 容器管理策略比較

#### 策略 A：程式碼控制（Python 直接管理 Docker）
```python
import docker
@pytest.fixture(scope="session")
def postgres_container():
    client = docker.from_env()
    container = client.containers.run("postgres:17.5", ...)
    yield container
    container.stop()
```
**優點**：
- ✅ 完全控制，精確管理生命週期
- ✅ 動態連接埠分配，避免衝突
- ✅ 專業做法（pytest-databases 模式）

**缺點**：
- ❌ 複雜度高，需要處理 Docker API
- ❌ 需要額外依賴（docker Python 庫）

#### 策略 B：docker-compose.yml 控制
```python
subprocess.run(["docker", "compose", "-f", "docker-compose.test.yml", "up", "-d"])
```
**優點**：
- ✅ 配置清晰，容器設定一目了然
- ✅ 可重複使用於本地、CI
- ✅ 符合基礎設施即程式碼理念

**缺點**：
- ❌ 生命週期管理較粗糙
- ❌ 固定連接埠，容易衝突

#### 🌟 策略 C：混合做法（建議採用）
- 用 `docker-compose.yml` 定義容器配置（清晰、可重用）
- 用 Python 程式碼管理生命週期（精確控制、錯誤處理）
- 在 CI 環境中可直接重用相同的 docker-compose 配置

**為什麼選擇混合做法**：
- 平衡可維護性和控制力
- WeaMind 團隊已熟悉 docker-compose
- CI 和本地環境可共用配置檔案

#### ❌ 策略 D：常駐測試容器（不推薦）
- ❌ 狀態管理複雜，測試間可能互相影響
- ❌ 需要手動管理容器生命週期
- ❌ 不適合 CI 環境
- ❌ 長期運行容器可能累積問題

## 📋 實作階段規劃

### 階段一：本地測試環境建置 (20-25 分鐘)
1. **設計測試專用容器**
   - 建立 `docker-compose.test.yml`
   - 使用測試專用認證（如 `test/test`）
   - 配置臨時儲存，測試後自動清除

2. **重寫測試配置**
   - 完全重寫 `tests/conftest.py`
   - 實作混合容器管理策略
   - 加入容器健康檢查和錯誤處理

3. **測試隔離機制**
   - 每個測試會話：自動建立/銷毀容器
   - 每個測試案例：事務回滾保證隔離

### 階段二：CI 環境配置 (10-15 分鐘)
1. **GitHub Actions 服務**
   - 在 `.github/workflows/ci.yml` 添加 PostgreSQL 服務
   - 重用本地的容器配置
   - 設定健康檢查和連線參數

2. **環境一致性驗證**
   - 確保 CI 和本地使用相同的 PostgreSQL 版本
   - 驗證測試結果一致性

### 階段三：查詢最佳化 (10-15 分鐘)
1. **重構 `get_recent_queries`**
   - 使用 PostgreSQL 的 `DISTINCT ON` 語法
   - 移除 SQLite 相容性 workaround
   - 更新相關 TODO 註解和文檔

## 🧠 決策記錄與經驗學習

### 💡 核心決策原則

**原則一：「安全性優於便利性」**
- 不能為了實作簡便而妥協安全性
- 測試環境絕不能暴露生產認證

**原則二：「完全隔離勝過部分隔離」**
- 拒絕「過渡性做法」，一步到位採用最佳實踐
- 測試環境必須完全獨立於生產環境

**原則三：「混合策略平衡複雜度與控制力」**
- 用 docker-compose 定義配置（清晰可維護）
- 用 Python 管理生命週期（精確控制）

### 🚨 失敗實作的關鍵教訓（2025-09-03）

**問題根源**：
1. 測試程式碼包含生產資料庫認證 `REDACTED_PRODUCTION_USER/REDACTED_PRODUCTION_PASSWORD`
2. 新開發者必須啟動生產環境才能跑測試
3. 測試和生產共用 PostgreSQL 實例

**核心學習**：
- **安全性考量必須優於便利性**
- **測試環境隔離是不可妥協的原則**
- **架構決策需要考慮長期維護和團隊協作**

### ⚠️ 必須避免的陷阱
- ❌ **延用生產容器**：安全性風險，真實認證暴露
- ❌ **環境耦合**：測試依賴生產環境配置
- ❌ **常駐測試容器**：狀態污染、維護負擔
- ❌ **部分遷移**：容易產生技術債
- ❌ **過度最佳化**：目前測試 1 秒完成，無需 pytest-xdist

### 🎯 最佳實踐模式

**程式碼轉換目標**：
```python
# 目前：為了 SQLite 相容性的 workaround
for user_query in query.limit(100):
    if user_query.location_id not in seen_locations:
        # ...手動去重邏輯

# 目標：直接使用 PostgreSQL 特性
query = session.query(UserQuery).distinct(UserQuery.location_id)...
```

### � 關鍵檔案清單
- `tests/conftest.py` - 測試資料庫配置核心（需完全重寫）
- `app/user/service.py:get_recent_queries` - 具體的方言差異案例
- `.github/workflows/ci.yml` - CI PostgreSQL 服務配置
- `app/core/database.py` - 資料庫連線設定
- `docker-compose.test.yml` - 測試專用容器定義（新增）
- `scripts/test_with_clean_db.sh` - 測試執行腳本（新增）

## 📋 實作檢查清單（基於深度研究的最終版本）

#### 預備階段
- [ ] 確認目前測試覆蓋率作為基準
- [ ] 備份現有 SQLite 測試配置
- [ ] 安裝 Testcontainers 依賴：`pip install testcontainers[postgresql]`

#### 階段一：Testcontainers 核心基礎建設
- [ ] 完全重寫 `tests/conftest.py`（使用 Testcontainers-Python）
- [ ] 實作 PostgreSQL 容器管理（session scope）
- [ ] 使用測試專用認證（test/test，絕不用生產認證）
- [ ] 加入 Alembic `upgrade head` 到 engine fixture
- [ ] 實作 function scope 交易回滾機制
- [ ] 更新所有模組的 conftest.py
- [ ] FastAPI 依賴覆寫：`app.dependency_overrides[get_db]`
- [ ] 本地執行完整測試套件
- [ ] 驗證無任何生產環境依賴

#### 階段二：CI 環境統一
- [ ] 修改 `.github/workflows/ci.yml`
- [ ] **不添加** PostgreSQL 服務配置（讓 Testcontainers 自動處理）
- [ ] 確保 CI 直接執行 `pytest -q`
- [ ] 驗證 CI 測試通過
- [ ] 確認本地=CI 完全一致

#### 階段三：PostgreSQL 最佳化
- [ ] 重構 `get_recent_queries` 使用 `DISTINCT ON`
- [ ] 移除 SQLite workaround 和相關 TODO 註解
- [ ] 效能測試和比較
- [ ] 搜尋其他類似的方言相容性問題
- [ ] 釘版本：固定 postgres:17.5 和相關依賴

#### 安全性與維護階段
- [ ] 加入失敗時自動 dump 容器 log 機制
- [ ] 建立「不含生產認證」檢查清單
- [ ] 更新專案文檔，記錄「測試架構升級」經驗
- [ ] 建立 PR 檢查清單：「測試啟動必跑 Alembic」

#### 完成階段
- [ ] 標記此 TODO 為完成
- [ ] 清理舊的 SQLite 相關程式碼
- [ ] 將失敗經驗寫入專案指南
- [ ] 慶祝完成「測試基礎架構 DevOps 升級」！

---

## � 實作狀態追蹤

### 🚨 2025-09-03 - 第一次實作失敗
**執行代理**：Claude Code
**分支**：`feature/migrate-tests-to-postgresql`
**狀態**：❌ 已廢棄 - 程式碼審查發現架構缺陷

**發現的問題**：
1. **安全性風險**：生產認證 (`REDACTED_PRODUCTION_USER/REDACTED_PRODUCTION_PASSWORD`) 暴露在測試程式碼中
2. **環境耦合**：測試依賴生產 PostgreSQL 容器
3. **隔離違反**：測試和生產共用同一個 PostgreSQL 實例

**需撤回的檔案**：
- `tests/conftest.py` - 包含生產認證
- `docker-compose.test.yml` - 錯誤方法
- `scripts/run_tests.sh` - 基於有缺陷的架構

**關鍵學習**：安全性和隔離性絕不能為了便利性而妥協。

### 🔄 下次實作計畫（基於深度研究的最終決策）

#### 核心架構決定
**採用 Testcontainers-Python 方案**：
- 使用測試專用認證（`test/test`）
- 實作 Testcontainers 容器管理（**不是** docker-compose 混合管理）
- 確保完全環境隔離
- 驗證無生產環境依賴
- 本地=CI 完全一致

#### 禁忌清單（踩到就回頭）
- ❌ **重用本地既有容器**當測試 DB：高風險、易污染、又容易洩憑證
- ❌ **部分遷移**（一半 SQLite、一半 Postgres）：只會堆技術債
- ❌ **用 `create_all` 取代 migration**：久了 schema 會分叉
- ❌ **GitHub Actions service + 本地 Testcontainers**：分叉維護，增加複雜度

#### 成功指標
- 測試完全隔離（每個 pytest session 一顆全新 DB）
- 安全第一（測試只用 test/test 帳密）
- 釘版本（postgres:17.5 與依賴版本固定）
- 失敗時自動 dump 容器 log
- 單一機制跑到底（Testcontainers + pytest）

## 💡 研究討論精華摘要

### 關鍵洞察與決策理由

#### 為什麼選擇 Testcontainers 而不是其他方案？
**核心比較結果**：

| 考量因素      | Testcontainers-Python | GitHub Actions Service | docker-compose 手刻 |
| ------------- | --------------------- | ---------------------- | ------------------- |
| 本地=CI一致性 | ✅ 100%一致            | ❌ 雙套機制             | ✅ 可做到一致        |
| 維護複雜度    | ✅ 單一機制            | ❌ 分叉維護             | ⚠️ 中等複雜          |
| 隔離程度      | ✅ 完全隔離            | ✅ 完全隔離             | ⚠️ 看實作品質        |
| 啟動速度      | ⚠️ +2-5秒              | ✅ 快                   | ⚠️ +2-5秒            |
| 專業程度      | ✅ 業界標準            | ✅ 官方推薦             | ❌ 自製輪子          |

**最終決策理由**：
- **單一機制、零分叉**：測試碼自己起/關容器，本地、CI 都走同一條路
- **隔離到位**：每個 pytest session 一顆全新 PostgreSQL，資料不殘留
- **可維護性高**：生命週期寫在 fixture，其他地方只要讀 DATABASE_URL
- **上手快**：新成員只要會 pytest，其他交給 Testcontainers

#### 為什麼 FastAPI 比 Django 複雜？
**根本差異**：
- **Django 優勢**：有 `pytest-django` 標準化了測試 DB 的建立/回滾/清理，幾乎免思考
- **FastAPI 現實**：生態是「自己挑資料庫與測試工具」，常見組合是 FastAPI + SQLAlchemy + Pytest，你得自己決定 DB 的生命週期、交易回滾與依賴注入

這就是為什麼以前在 Django 感覺超簡單，現在卻一堆細節要處理。

#### Django「複用既有 DB」的歷史真相
**為什麼以前 Django 看起來很輕鬆？**
- **pytest-django 的魔法**：`@pytest.mark.django_db` 自動處理測試資料庫建立和清理
- **單人開發 + 無CI環境**：沒有並行測試衝突、狀態污染、環境重現等問題
- **全家桶哲學**：Django 幫你做了大部分決策，隱藏了複雜度

**但這不是最佳實踐的原因**：
```python
# 如果當時有 CI 會發生什麼？
Job 1: pytest tests/user/    # 搶同一個 test_db
Job 2: pytest tests/order/   # 隨機失敗 💥

# 狀態污染問題
def test_a(): User.objects.create(username="admin")
def test_b(): assert User.objects.filter(username="admin").count() == 0  # 💥
```

**現代 Django 最佳實踐也在進化**：
很多 Django 專案現在也開始用 Testcontainers 來做完全隔離的測試環境。

| 測試策略 | Django (早期) | Django (現代) | FastAPI + Testcontainers |
| -------- | ------------- | ------------- | ------------------------ |
| 上手難度 | ✅ 超簡單      | ⚠️ 中等        | ⚠️ 中等                   |
| 隔離程度 | ❌ 依賴既有DB  | ✅ 完全隔離    | ✅ 完全隔離               |
| CI 友善  | ❌ 需預配置    | ✅ 零配置      | ✅ 零配置                 |

**結論**：WeaMind 選擇 Testcontainers 其實是技術需求升級後（多人協作 + CI + 長期維護）的明智選擇，而非 FastAPI 本身更複雜。

#### 最小落地方案（6個步驟）
1. `conftest.py` 起 `postgres:17.5`（Testcontainers）→ 設 `DATABASE_URL`
2. `engine` 建好後：**Alembic 升級**
3. `function` scope **交易回滾** fixture
4. FastAPI 覆寫 `get_db`，讓 API 測試吃同一個 session
5. CI 直接 `pytest -q`（不要 GitHub Actions service）
6. 失敗時自動 dump 容器 log，第一時間定位

#### 血淋淋的教訓與金句
- **「這不是在'把 SQLite 換成 Postgres'，而是在'把你團隊的測試文化，換成能上戰場的標準'」**
- **安全性考量必須優於便利性**：第一次實作就是因為貪圖便利而暴露生產密碼
- **硬派、正確，但代價高的設計才是長久之計**
- **接受合理代價**：冷啟動 +2-5 秒，換來絕對隔離，這個代價值得

## 🤖 Claude Code 的技術認同分析

### 為什麼 Claude Code 完全認同 Testcontainers-Python 選擇

作為 AI 編程助手，從技術架構與長期維護角度分析，Testcontainers-Python 確實是當前最佳選擇：

#### 🎯 決定性優勢

**1. 架構一致性（最關鍵因素）**
- **本地=CI 零差異**：同一套代碼邏輯，徹底消除「我這邊可以跑」的經典問題
- **單一真相來源**：不用維護兩套不同的容器管理機制
- **團隊協作友善**：新成員 clone 下來就能跑測試，無需額外環境配置

**2. 安全性與隔離（無可妥協）**
- **天然隔離**：每次測試都是全新容器，物理上不可能有狀態污染
- **零認證洩漏風險**：測試容器用完即毀，不會有生產認證殘留問題
- **符合最小權限原則**：測試環境在架構上完全獨立於生產環境

**3. 維護負擔合理化**
```
代價：2-5 秒冷啟動時間
收益：
  ✅ 零配置衝突（動態 port 分配）
  ✅ 零手動清理（容器自動銷毀）
  ✅ 零狀態管理（每次都是乾淨開始）
  ✅ 零環境依賴（不需要預先起 DB）
```

**4. 專業標準與生態成熟度**
- **業界認可**：Testcontainers 就是容器化測試的事實標準
- **生態完整**：PostgreSQL、Redis、MongoDB 等都有現成的高品質支援
- **長期可維護**：基於成熟開源項目，不是自製輪子

#### 🚫 其他方案的致命缺陷分析

| 方案                       | 致命缺陷                                         | 長期風險                       |
| -------------------------- | ------------------------------------------------ | ------------------------------ |
| **GitHub Actions Service** | 分叉維護：本地一套、CI 一套                      | 環境不一致導致的調試地獄       |
| **docker-compose 手刻**    | 重複造輪：要處理所有 Testcontainers 已解決的問題 | 維護負擔隨時間指數增長         |
| **重用既有容器**           | 安全風險：如實作中發現的生產認證洩漏             | 團隊協作與新人 onboarding 困難 |

#### 🏆 最關鍵的判斷標準：可重現性

**作為 AI 編程助手，我最看重的是「可重現性」**：
- 任何開發者在任何環境下都能得到一致的測試結果
- CI 失敗時，開發者能在本地完全重現
- 測試結果不會因為「誰先跑」、「跑幾次」而不同

**「本地=CI 完全一致」這個特性，對於 WeaMind 這種需要長期維護的專案來說，價值無法估量。**

#### 💎 投資回報率分析

```
初始投資：
- 學習 Testcontainers 使用方法
- 重寫 conftest.py
- 接受 2-5 秒冷啟動時間

長期收益：
- 測試結果 100% 可重現
- 新成員零配置上手
- 安全性問題根本性解決
- 維護負擔最小化
```

**結論：這是典型的「短期痛、長期爽」的技術決策，完全符合工程最佳實踐。**

---
*建立日期：2025-09-03*
*最後更新：2025-09-03（整合深度研究討論）*
*執行代理：Claude Code*
*狀態：📋 準備實作（基於 Testcontainers 最終方案）*
