# WeaMind 資料庫 ERD (Entity Relationship Diagram)

建立日期: 2025-08-12  
描述: WeaMind 天氣與行政區資料庫的實體關係圖

## ERD 圖表

```mermaid
erDiagram
    location {
        int id PK "Primary Key"
        varchar_10 geocode UK "Unique Geocode"
        varchar_10 county "County Name"
        varchar_10 district "District Name"
        decimal_9_6 latitude "Latitude"
        decimal_9_6 longitude "Longitude"
        timestamp created_at "Created At"
        timestamp updated_at "Updated At"
    }
    
    weather {
        int id PK "Primary Key"
        int location_id FK "Location Foreign Key"
        timestamp start_time "Forecast Start Time"
        timestamp end_time "Forecast End Time"
        varchar_30 weather_condition "Weather Condition"
        varchar_10 weather_emoji "Weather Emoji"
        int precipitation_probability "Precipitation 0-100"
        int min_temperature "Min Temperature Celsius"
        int max_temperature "Max Temperature Celsius"
        text raw_description "Raw Description Backup"
        timestamp created_at "Created At"
        timestamp updated_at "Updated At"
    }
    
    location ||--o{ weather : "one-to-many"
```

## 資料表關係說明

### 1. location (行政區)
- **用途**: 儲存台灣所有縣市鄉鎮的基本資訊
- **資料量**: 約 368 筆（全台灣行政區）
- **特色**: 相對靜態，需要初始化資料

### 2. weather (天氣預報)
- **用途**: 儲存各行政區的天氣預報資料
- **資料量**: 每日約 368 × 8 = 2,944 筆（每個行政區每天8個3小時區間）
- **特色**: 動態資料，由 wea-data 微服務定期更新

### 3. 關係說明
- **一對多關係**: 一個行政區對應多筆天氣預報記錄
- **外鍵約束**: weather.location_id → location.id
- **唯一約束**: 同一地點同一時間區間不可重複

## 索引策略

```mermaid
graph TD
    A[查詢需求] --> B[location.geocode 索引]
    A --> C[location.county 索引]
    A --> D[weather 複合索引]
    
    D --> E[location_id + start_time]
    D --> F[start_time + end_time]
    
    B --> G[根據地理編碼查詢行政區]
    C --> H[根據縣市查詢所有鄉鎮]
    E --> I[查詢特定地點的天氣預報]
    F --> J[查詢特定時間範圍的預報]
```

## 資料流程

```mermaid
sequenceDiagram
    participant API as 氣象局 API
    participant WD as wea-data 微服務
    participant DB as PostgreSQL
    participant WB as wea-bot (LINE Bot)
    
    API->>WD: 取得 WeatherDescription
    WD->>WD: 解析天氣描述字串
    WD->>DB: 更新 weather
    WB->>DB: 查詢用戶所在地天氣
    DB->>WB: 回傳結構化天氣資料
    WB->>WB: 組合訊息 (emoji + 文字)
```

## 備註

1. **時區**: 全部使用台灣時間 (+08:00)，無需時區轉換
2. **資料更新**: weather 採覆蓋式更新，保持最新預報
3. **備援機制**: raw_description 保留原始資料用於除錯和驗證
4. **emoji 映射**: 在應用層或資料庫觸發器中處理天氣狀況到 emoji 的映射
