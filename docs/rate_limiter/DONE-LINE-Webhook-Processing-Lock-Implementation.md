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

## 核心架構與實作

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
```

### 2. Redis 分散式鎖技術核心

```python
# 原子操作：SET ... EX NX 確保鎖的正確性
result = redis_client.set(key, "1", ex=timeout_seconds, nx=True)
# nx=True: 只在 key 不存在時設定（避免覆蓋現有鎖）
# ex=timeout: 設定 TTL 過期時間（避免死鎖）
# 返回值: 成功 True，失敗 None
```

**技術重點：**
- **原子性保證**：三個操作（檢查存在、設定值、設定TTL）合併為單一原子命令
- **競爭條件避免**：NX 參數確保同一時間只有一個客戶端能取得鎖
- **自動故障恢復**：TTL 機制確保即使程序崩潰，鎖也會自動釋放

### 3. 鎖機制整合流程

```python
# 處理流程偽代碼
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

### 4. 安全釋放與相容性設計

```python
# 鎖釋放：Best-effort 策略
def release_lock(self, key: str) -> None:
    try:
        redis_client.delete(key)
        logger.debug("Processing lock released")
    except (ConnectionError, RedisError) as e:
        logger.warning("Failed to release processing lock: %s", e)
        # 不拋出異常，依賴 TTL 自動釋放

# 向下相容：解決測試 Mock 對象問題
lock_key = None
if hasattr(event, 'source') and event.source:
    lock_key = processing_lock_service.build_actor_key(event.source)
```

**設計考量：**
- **優雅降級**：釋放失敗不影響主流程，TTL 作為安全網
- **測試相容**：使用 `hasattr` 檢查避免破壞現有 Mock 測試
- **詳細日誌**：便於問題診斷和系統監控

## 實作過程關鍵問題與解決

### 1. Mock 對象相容性問題

**問題**：現有測試 Mock 對象缺少 `source` 屬性導致 `AttributeError`

**解決**：使用 `hasattr` 進行安全檢查，確保向下相容
```python
# 修正前：event.source if event.source else None
# 修正後：hasattr(event, 'source') and event.source
```

### 2. 同步/異步 API 一致性

**問題**：LINE SDK 同步設計與異步 Redis 客戶端不匹配

**解決**：選用同步 Redis 客戶端 (`redis`) 保持架構一致性

### 3. 容器依賴管理

**問題**：Docker 映像缺少 Redis 客戶端庫 (`ModuleNotFoundError: No module named 'redis'`)

**解決**：依賴變更後重新建構映像 (`docker compose up -d --build`)

## 配置與部署

### 1. 環境變數配置

```bash
# 核心設定
PROCESSING_LOCK_ENABLED=true
PROCESSING_LOCK_TIMEOUT_SECONDS=5
REDIS_URL=redis://redis:6379/0
```

### 2. Docker 服務配置

```yaml
# Redis 服務
redis:
  image: redis:8.2.1-bookworm  # 與 PostgreSQL 基礎映像一致
  ports: ["6379:6379"]
  networks: [wea-net]
  volumes:
    - wea-redis-data:/data  # 數據持久化

# 應用服務依賴
app:
  depends_on: [db, redis]  # 確保啟動順序
```

**配置重點：**
- **版本選擇**：`8.2.1-bookworm` 提供穩定性和相容性
- **數據持久化**：開發環境自動創建，生產環境使用外部 volume
- **服務依賴**：確保 Redis 在應用啟動前就緒

## 測試與驗證

### 測試覆蓋範圍
- ✅ **單元測試** (16/16)：鎖機制、TTL 行為、錯誤處理、配置控制
- ✅ **整合測試** (218/218)：Redis 環境、網路連通、數據持久化
- ✅ **端到端驗證**：連線測試、鎖操作、故障恢復

### 關鍵驗證流程
```python
def test_lock_mechanism():
    # 連線測試
    redis_client.ping()

    # 鎖取得/競爭測試
    acquired = processing_lock_service.try_acquire_lock(key, 5)
    acquired_again = processing_lock_service.try_acquire_lock(key, 5)  # 失敗

    # 鎖釋放測試
    processing_lock_service.release_lock(key)
    acquired_third = processing_lock_service.try_acquire_lock(key, 5)  # 成功
```

### 3. 監控與可觀測性

**當前階段：日誌記錄**
- 鎖取得/釋放狀態記錄
- 錯誤情況詳細日誌
- 隱私保護：不記錄用戶個資

**未來規劃：Prometheus 指標**
```python
# 核心指標設計
processing_lock_acquire_total = Counter(
    'processing_lock_acquire_total', ['status', 'source_type']
)
processing_duration_seconds = Histogram(
    'processing_duration_seconds', ['event_type']
)
```

### 4. 擴展性設計
- **多實例支援**：Redis 共享狀態
- **水平擴展**：無狀態應用架構
- **高可用性**：故障時優雅降級 (fail-open)
- **未來擴展**：Redis Cluster、智慧超時、細粒度鎖控

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

## 實作成果總結

### 核心技術成就
1. **Redis 分散式鎖實作**：原子操作 `SET NX EX` 確保競爭條件安全
2. **Fail-Open 架構**：服務可用性優先，Redis 故障時優雅降級
3. **Python 進階技巧**：`TYPE_CHECKING` 解決循環導入，Union types 正確標註
4. **向下相容設計**：`hasattr` 安全檢查，不破壞現有測試

### 關鍵設計模式

#### Redis 原子操作深度應用
```python
# SET NX EX 將三個步驟合併為原子操作
# 1. 檢查鍵存在性  2. 設定鍵值  3. 設定 TTL
result = redis_client.set(key, "1", ex=timeout, nx=True)
```

#### TYPE_CHECKING 最佳實務
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from linebot.v3.webhooks.models.source import Source

def build_actor_key(self, source: "Source | None") -> str | None:
    # 字串標註避免執行時導入錯誤
```

### 驗證結果
- ✅ 單元測試：16/16 通過
- ✅ 整合測試：218/218 通過
- ✅ 效能測試：鎖操作延遲 < 1ms
- ✅ 故障測試：Redis 停機時應用正常運作

此實作為團隊建立了可靠的 Redis 分散式鎖技術範本，完整達成重複請求防護的設計目標。
