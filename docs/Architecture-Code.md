# WeaMind 主程式架構說明文件

## 專案概述

WeaMind 是一個基於 FastAPI 的 LINE Bot 天氣查詢服務，採用 Domain-Driven Design (DDD) 架構設計，提供快速、直觀的天氣查詢體驗。核心價值是解決使用者查詢「非預設區域」天氣時操作繁瑣的痛點。

## 技術架構

### 技術棧
- **後端框架**: FastAPI (Python)
- **資料庫**: PostgreSQL + SQLAlchemy 2.0 ORM
- **快取**: Redis (處理併發鎖定)
- **外部服務**: LINE Bot SDK v3
- **部署**: Docker + Docker Compose
- **套件管理**: uv

### 設計原則
- **Domain-Driven Design**: 清晰的領域邊界分離
- **類型安全**: 全面使用 Python type hints
- **快速回應**: Webhook ACK 優先，後台處理架構
- **錯誤處理**: 完整的例外處理與使用者友善訊息

## 核心模組架構

### 1. 應用程式入口 (`app/main.py`)

**功能**:
- FastAPI 應用程式初始化與設定
- 路由註冊與中介軟體配置
- 靜態檔案服務 (LIFF 支援)

**關鍵特性**:
```python
# 環境依賴的應用配置
if settings.is_development:
    app = FastAPI(title=settings.APP_NAME, description="API for WeaMind Weather LINE BOT")
else:
    # 生產環境隱藏 API 文件
    app = FastAPI(title=settings.APP_NAME, docs_url=None, redoc_url=None, openapi_url=None)

# 安全配置
app.add_middleware(CORSMiddleware, allow_origins=["https://liff.line.me"])

# 路由註冊
app.include_router(user_router, tags=["user"])
app.include_router(line_router, tags=["line"])
```

### 2. 核心基礎設施 (`app/core/`)

#### 2.1 設定管理 (`config.py`)
**功能**: 環境變數管理、日誌配置、應用程式設定
**關鍵設定**:
- LINE Bot 驗證資訊 (Channel Secret, Access Token)
- 資料庫連線設定
- Redis 設定 (併發鎖定機制)
- 處理鎖定機制控制

#### 2.2 資料庫管理 (`database.py`)
**功能**: SQLAlchemy 連線管理與 Session 提供
```python
# FastAPI 相依注入模式
def get_session() -> typing.Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

#### 2.3 行政區劃管理 (`admin_divisions.py`)
**功能**: 台灣行政區劃資料初始化與驗證
**用途**: 確保位置查詢的正確性與完整性

#### 2.4 使用者驗證 (`auth.py`)
**功能**: LINE Login 存取權杖驗證 (LIFF 應用使用)

#### 2.5 併發鎖定 (`processing_lock.py`)
**功能**: Redis 基於的處理鎖定，避免重複處理使用者請求

### 3. LINE Bot 模組 (`app/line/`)

#### 3.1 Webhook 路由 (`router.py`)
**設計哲學**: 快速 ACK + 後台處理

**處理流程**:
```python
@router.post("/webhook")
async def line_webhook(request, x_line_signature, background_tasks):
    # 1. 驗證內容類型 (快速檢查)
    # 2. 讀取請求內容
    # 3. 同步驗證 LINE 簽章 (避免安排無效工作)
    # 4. 記錄接收日誌
    # 5. 安排後台處理 (background_tasks.add_task)
    # 6. 立即回傳 200 OK (快速 ACK)
```

**優點**:
- 符合 LINE 平台 3 秒回應要求
- 避免使用者看到「處理中」狀態
- 後台例外不影響 ACK 回應

#### 3.2 事件處理服務 (`service.py`)
**功能**: LINE 事件的核心業務邏輯處理

**主要事件處理器**:
- `handle_message_event`: 文字訊息處理 (地點查詢)
- `handle_location_message_event`: GPS 位置分享處理
- `handle_follow_event`: 使用者加入好友
- `handle_unfollow_event`: 使用者封鎖/移除好友
- `handle_postback_event`: 互動元件回調處理

**文字訊息處理流程**:
1. 驗證 reply_token
2. 取得資料庫 Session
3. 呼叫 LocationService.parse_location_input (地點解析)
4. 根據解析結果決定回應類型:
   - 單一地點 → 直接查詢天氣
   - 多個地點 → Quick Reply 選項
   - 無結果/格式錯誤 → 錯誤訊息
5. 記錄使用者查詢歷史

#### 3.3 訊息處理 (`messaging.py`)
**功能**: LINE 訊息格式化與傳送邏輯
- 天氣資訊訊息格式化
- Quick Reply 選項建立
- LIFF 位置設定頁面連結
- 錯誤訊息統一處理

#### 3.4 Postback 處理 (`postback.py`)
**功能**: 處理 Rich Menu、Quick Reply 等互動元件回調
**主要功能**:
- 使用者位置天氣查詢 (住家/公司)
- 最近查詢歷史
- 設定頁面導引
- 其他選單功能

### 4. 使用者管理模組 (`app/user/`)

#### 4.1 資料模型 (`models.py`)
**User 模型**:
```python
class User(Base):
    line_user_id: Mapped[str]           # LINE 使用者 ID
    display_name: Mapped[str | None]    # 顯示名稱
    home_location_id: Mapped[int | None] # 住家地點 ID
    work_location_id: Mapped[int | None] # 公司地點 ID
    is_active: Mapped[bool]             # 帳號狀態
```

**UserQuery 模型**: 查詢歷史記錄，支援「最近查詢」功能

#### 4.2 API 路由 (`router.py`)
**功能**: LIFF 應用的 RESTful API
**主要端點**:
- `POST /users/locations`: 設定使用者住家/公司位置

#### 4.3 業務邏輯 (`service.py`)
**主要函式**:
- `create_user_if_not_exists`: 使用者建立/重新啟用
- `get_user_by_line_id`: 使用者查詢
- `set_user_location`: 位置設定 (含行政區劃驗證)
- `record_user_query`: 查詢歷史記錄
- `get_recent_queries`: 最近查詢取得

### 5. 天氣服務模組 (`app/weather/`)

#### 5.1 資料模型 (`models.py`)
**Location 模型**: 台灣行政區劃位置資料
**Weather 模型**: 天氣資料 (目前為模擬資料結構)

#### 5.2 位置服務 (`service.py` - LocationService)
**核心功能**:

**地點輸入驗證與解析**:
```python
def validate_location_input(text: str) -> str:
    # 1. 字數驗證 (2-7 字)
    # 2. 中文字元驗證
    # 3. 輸入正規化 (台→臺)
```

**地點搜尋策略**:
```python
def search_locations_by_name(session: Session, name: str) -> list[Location]:
    # 1. 精確匹配 (county + district)
    # 2. 縣市匹配
    # 3. 鄉鎮市區匹配
    # 4. 模糊匹配
```

**GPS 地址解析**:
```python
def extract_location_from_address(address: str) -> tuple[str, str] | None:
    # 地址優先策略: 從 LINE GPS 地址資訊解析縣市區資訊
```

**最近位置計算**:
```python
def find_nearest_location(session: Session, lat: float, lon: float) -> Location | None:
    # Haversine 公式計算最短距離
```

## 核心業務流程

### 文字訊息查詢流程

1. **使用者輸入** → "台北市信義區"
2. **Webhook 接收** → 快速驗證 + 後台處理
3. **地點解析** → LocationService.parse_location_input
4. **輸入驗證** → 字數、中文、格式檢查
5. **地點搜尋** → 資料庫模糊查詢
6. **結果處理**:
   - 0 筆: "找不到相符的地點"
   - 1 筆: 直接查詢天氣
   - 2-3 筆: Quick Reply 選項讓使用者選擇
   - >3 筆: "太多相符地點，請輸入更精確的地名"
7. **天氣查詢** → WeatherService (目前回傳模擬資料)
8. **歷史記錄** → 記錄查詢以支援「最近查詢」
9. **回應傳送** → LINE MessagingApi

### GPS 位置分享流程

1. **使用者分享位置** → GPS 座標 + 地址資訊
2. **地址優先策略** → 嘗試從地址解析縣市區
3. **GPS 備援策略** → 地址解析失敗時使用座標計算最近位置
4. **台灣範圍驗證** → 確保查詢範圍在台灣
5. **天氣查詢** → 同文字查詢流程

### Rich Menu 互動流程

1. **Postback 事件** → 使用者點擊 Rich Menu 按鈕
2. **事件解析** → 解析 postback data (action + parameters)
3. **動作分派** → 根據 action 類型分派到對應處理器:
   - `weather_home`: 查詢住家天氣
   - `weather_work`: 查詢公司天氣
   - `recent_queries`: 顯示最近查詢
   - `settings`: 導向設定頁面
4. **資料查詢** → 從資料庫取得使用者設定位置
5. **天氣回應** → 同基本天氣查詢流程

## 設計特色

### 1. 快速回應架構
- **Webhook ACK 優先**: 立即回傳 200 OK，避免 LINE 平台重送
- **後台處理**: 所有業務邏輯在背景執行，不阻塞 ACK
- **例外隔離**: 後台例外不影響 ACK 成功

### 2. 智慧地點解析
- **多層次搜尋策略**: 精確 → 縣市 → 鄉鎮 → 模糊匹配
- **地址優先 + GPS 備援**: GPS 分享時優先解析地址，失敗才用座標
- **使用者友善回饋**: 根據搜尋結果數量給予適當回應

### 3. 併發安全設計
- **Redis 鎖定機制**: 防止同一使用者重複處理
- **資料庫 Session 管理**: 確保交易一致性
- **冪等性設計**: 重複請求產生相同結果

### 4. 可擴展架構
- **DDD 模組化**: 清晰的領域邊界，易於擴展
- **依賴注入**: FastAPI 原生支援，便於測試
- **類型安全**: 全面 type hints，減少執行期錯誤

## AI 快速理解要點

1. **專案本質**: LINE Bot 天氣查詢服務，重點在快速、準確的位置解析
2. **架構設計**: FastAPI + PostgreSQL，DDD 分層，快速 ACK + 後台處理
3. **核心流程**: 文字→地點解析→天氣查詢→回應，支援 GPS 和 Rich Menu
4. **技術亮點**: 智慧地點搜尋、併發鎖定、地址優先+GPS備援策略
5. **擴展性**: 模組化設計，易於添加新功能或外部服務整合

這個架構為 V1.0 MVP 版本，後續會演進到 K8s 部署和完整監控體系。
