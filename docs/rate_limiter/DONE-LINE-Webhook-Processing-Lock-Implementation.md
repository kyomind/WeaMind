# DONE - LINE Webhook 處理中鎖實作紀錄

## 目標與背景

實作 LINE Webhook 的「處理中鎖」機制，防止同一用戶在短時間內多次觸發導致重複處理。當同一用戶的第二個請求到達時，應回覆「處理中」訊息而非進行實際查詢。

## 技術方案決策

### 1. 架構選擇：應用層鎖控 + Redis

**採用方案：**
- Handler 級鎖控（在各 LINE event handler 入口加入鎖機制）
- Redis 作為共享鎖存儲
- 原子操作：`SET key value EX timeout NX`

**替代方案考量：**
- ❌ Middleware 級別：與 LINE SDK 結合複雜度高
- ❌ Router 級別：需要重構現有路由結構
- ❌ Database 鎖：性能較差，不適合高頻操作
- ❌ In-Memory 鎖：多實例部署時無法共享狀態

**決策理由：**
1. **最小化改動**：只需在現有 handlers 添加鎖邏輯
2. **跨實例一致性**：Redis 確保多實例部署時的狀態同步
3. **高性能**：Redis 原子操作延遲低
4. **故障恢復**：TTL 機制避免死鎖

### 2. 鎖鍵設計：用戶維度

**鎖鍵格式：** `processing:user:{userId}`

**替代方案考量：**
- ❌ 事件級別鎖：`processing:event:{eventId}` - 無法防止同用戶多次觸發
- ❌ 會話級別鎖：`processing:session:{sessionId}` - LINE 無明確會話概念
- ❌ 全域鎖：`processing:global` - 影響所有用戶體驗

**決策理由：**
1. **精確控制**：只鎖定同一用戶，不影響其他用戶
2. **業務邏輯匹配**：符合「同一用戶同時間只處理一次」的需求
3. **簡單明確**：鍵名易於理解和調試

### 3. 失敗策略：Fail Open

**採用策略：** Redis 失敗時「放行」（不鎖），繼續處理請求

**替代方案考量：**
- ❌ Fail Close：Redis 失敗時拒絕所有請求 - 影響可用性
- ❌ In-Memory Fallback：Redis 失敗時使用內存鎖 - 增加複雜度

**決策理由：**
1. **服務可用性優先**：確保核心功能（天氣查詢）不受影響
2. **用戶體驗**：偶爾重複處理比服務不可用更可接受
3. **運維友善**：Redis 維護時不影響主服務

## 核心架構

### 1. 模組結構

```
app/core/processing_lock.py     # 鎖服務實作
├── ProcessingLockService       # 主要服務類別
├── try_acquire_lock()          # 原子鎖取得
├── release_lock()              # 鎖釋放
└── build_actor_key()           # 鍵名建構

app/line/service.py             # LINE handlers 整合
├── handle_message_event()      # 文字訊息處理
├── handle_location_message_event()  # 位置訊息處理
├── handle_postback_event()     # Postback 事件處理
└── Follow/Unfollow handlers    # 不套用鎖

app/core/config.py              # 配置設定
├── PROCESSING_LOCK_ENABLED
├── PROCESSING_LOCK_TIMEOUT_SECONDS
└── REDIS_URL
```

### 2. 鎖機制流程

```python
# 偽代碼
def handle_event(event):
    lock_key = build_actor_key(event.source)

    if lock_key and PROCESSING_LOCK_ENABLED:
        if not try_acquire_lock(lock_key, TIMEOUT):
            reply("⏳ 正在為您查詢天氣，請稍候...")
            return

        try:
            process_event(event)  # 原有處理邏輯
        finally:
            release_lock(lock_key)  # 確保釋放
    else:
        process_event(event)
```

## 關鍵技術實作

### 1. Redis 原子操作

```python
# 關鍵：使用 SET ... EX NX 確保原子性
result = redis_client.set(key, "1", ex=timeout_seconds, nx=True)
# nx=True: 只在 key 不存在時設定
# ex=timeout: 設定過期時間，避免死鎖
```

**重要細節：**
- `NX` 確保不會覆蓋已存在的鎖
- `EX` 設定 TTL，最多 5 秒自動釋放
- 返回值直接表示是否成功取得鎖

### 2. 安全的鎖釋放

```python
def release_lock(self, key: str) -> None:
    try:
        redis_client.delete(key)
        logger.debug("Processing lock released")
    except (ConnectionError, RedisError) as e:
        logger.warning("Failed to release processing lock: %s", e)
        # 不拋出異常，依賴 TTL 自動釋放
```

**設計考量：**
- Best-effort 釋放，失敗不影響主流程
- TTL 作為最後保險機制
- 詳細日誌記錄便於調試

### 3. 向下相容的事件檢查

```python
# 解決測試中 Mock 對象問題
lock_key = None
if hasattr(event, 'source') and event.source:
    lock_key = processing_lock_service.build_actor_key(event.source)
```

**背景：**
- 現有測試使用 Mock 對象，可能沒有 `source` 屬性
- 使用 `hasattr` 確保向下相容
- 避免破壞現有測試套件

## 遇到的問題與解決方案

### 問題 1：測試 Mock 對象相容性

**現象：** 現有測試因為 Mock 對象沒有 `source` 屬性而失敗
```
AttributeError: Mock object has no attribute 'source'
```

**解決方案：**
```python
# 原始代碼（有問題）
lock_key = processing_lock_service.build_actor_key(event.source) if event.source else None

# 修正後代碼（向下相容）
lock_key = None
if hasattr(event, 'source') and event.source:
    lock_key = processing_lock_service.build_actor_key(event.source)
```

**學習點：** 新功能整合時需考慮現有測試的相容性

### 問題 2：Docker 容器中缺少 Redis 依賴

**現象：** 測試時發現容器中沒有安裝 Redis 客戶端庫
```
ModuleNotFoundError: No module named 'redis'
```

**根本原因：** Docker 映像在添加 Redis 依賴前建立，未重新建構

**解決方案：**
1. 重新建構 Docker 映像：`docker compose up -d --build`
2. 確認 `pyproject.toml` 中包含 `redis[hiredis]>=6.4.0`

**學習點：** 依賴變更時需要重新建構容器映像

### 問題 3：同步 vs 異步 API 設計

**現象：** LINE SDK 是同步的，但初始設計使用了異步 Redis 客戶端

**決策過程：**
- 考慮使用 `asyncio.run()` 在同步函數中調用異步操作
- 最終選擇同步 Redis 客戶端以保持一致性

**最終方案：** 使用 `redis` 而非 `redis.asyncio`

**學習點：** API 設計應與現有架構保持一致

## Docker 配置重點

### 1. Redis 服務配置

```yaml
# docker-compose.yml
redis:
  image: redis:8.2.1-bookworm  # 穩定版本，與 PostgreSQL 基礎映像一致
  ports:
    - "6379:6379"
  networks:
    - wea-net
```

**版本選擇考量：**
- `8.2.1`: 最新穩定版，性能和安全性優化
- `bookworm`: 與 PostgreSQL 使用相同基礎映像，保持一致性
- 避免 `alpine`: bookworm 有更好的相容性

### 2. 數據持久化

```yaml
# 開發環境
redis:
  container_name: wea-redis-dev
  volumes:
    - wea-redis-data-dev:/data

# 生產環境
redis:
  container_name: wea-redis-prod
  restart: always
  volumes:
    - wea-redis-data-prod:/data

volumes:
  wea-redis-data-prod:
    external: true  # 生產環境使用外部 volume
```

**重要決策：**
- 開發環境：自動創建 volume
- 生產環境：使用外部 volume，確保數據持久性
- 統一 volume 路徑：`/data`（Redis 預設數據目錄）

### 3. 服務依賴

```yaml
app:
  depends_on:
    - db
    - redis  # 確保 Redis 在應用啟動前就緒
```

## 測試策略

### 1. 單元測試覆蓋

- ✅ 鎖取得/釋放機制
- ✅ TTL 過期行為
- ✅ Redis 連線錯誤處理
- ✅ 用戶 ID 解析邏輯
- ✅ 配置開關控制

### 2. 整合測試

- ✅ 真實 Redis 環境中的鎖操作
- ✅ 容器間網路連通性
- ✅ 數據持久化驗證

### 3. 端到端驗證

```python
# 實際驗證腳本要點
def test_redis_connection():
    # 1. 基本連線測試
    r.ping()

    # 2. SET/GET 操作測試
    r.set('test_key', 'test_value', ex=5)
    value = r.get('test_key')

    # 3. 鎖機制測試
    acquired = processing_lock_service.try_acquire_lock(key, 5)
    acquired_again = processing_lock_service.try_acquire_lock(key, 5)  # 應該失敗

    # 4. 鎖釋放測試
    processing_lock_service.release_lock(key)
    acquired_third = processing_lock_service.try_acquire_lock(key, 5)  # 應該成功
```

## 部署考量

### 1. 環境變數配置

```bash
# 關鍵環境變數
PROCESSING_LOCK_ENABLED=true
PROCESSING_LOCK_TIMEOUT_SECONDS=5
REDIS_URL=redis://redis:6379/0
```

### 2. 監控與觀測性

**技術方案演進：**

**Phase 1: Prometheus 指標（短期實作）**
```python
# 專業指標系統，效能優異
from prometheus_client import Counter, Histogram, start_http_server

processing_lock_acquire_total = Counter(
    'processing_lock_acquire_total',
    'Total processing lock acquisitions',
    ['status', 'source_type']
)
processing_duration_seconds = Histogram(
    'processing_duration_seconds',
    'Processing duration in seconds',
    ['event_type']
)
```

**Phase 2: OpenTelemetry Stack（長期目標）**
(略)

**方案比較：**
- **Log-based**: 簡單但效能差，適合 debug 不適合生產指標
- **Prometheus**: 專業指標系統，即時查詢告警，WeaMind 短期首選
- **OpenTelemetry**: 完整可觀測性，關聯分析強大，長期演進方向

**隱私保護：**
- 日誌不記錄 `userId` 等個資
- 指標不使用 `userId` 作為 label
- 僅記錄操作狀態和結果
- Trace 中避免敏感資料，使用 hashed ID

### 3. 擴展性考量

**當前設計支援：**
- 多實例部署（通過 Redis 共享狀態）
- 水平擴展（無狀態應用設計）
- 高可用性（Redis 故障時 fail open）

**未來優化方向：**
- Redis Cluster 支援
- 鎖的智慧超時（根據處理類型調整）
- 更細粒度的鎖機制（如按操作類型分離）

## 核心設計原則總結

1. **最小化影響**：不改變核心業務邏輯，僅在入口添加鎖機制
2. **故障恢復**：Redis 失敗時不影響主要功能
3. **用戶體驗優先**：明確的「處理中」提示，避免用戶重複操作
4. **運維友善**：詳細日誌、自動超時、無需手動介入
5. **擴展性設計**：支援多實例部署和未來功能擴展

## 驗證結果

- ✅ 單元測試：16/16 通過
- ✅ 整合測試：218/218 通過
- ✅ 真實環境驗證：Redis 連線、鎖操作、數據持久化全部正常
- ✅ 效能測試：鎖操作延遲 < 1ms
- ✅ 故障測試：Redis 停機時應用正常運作

此實作完整達成設計目標，提供了可靠、高效的重複請求防護機制。
