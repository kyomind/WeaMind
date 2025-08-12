-- WeaMind 天氣與行政區資料庫 Schema DDL
-- 建立日期: 2025-08-12
-- 說明: 包含行政區 (locations) 和天氣預報 (weather_forecasts) 兩個主要資料表

-- =============================================================================
-- 行政區資料表
-- =============================================================================
CREATE TABLE location (
    id SERIAL PRIMARY KEY,
    geocode VARCHAR(10) NOT NULL UNIQUE,  -- 地理編碼，如 "10002010"
    county VARCHAR(10) NOT NULL,          -- 縣市名稱，如 "新北市"
    district VARCHAR(10) NOT NULL,        -- 鄉鎮市區名稱，如 "永和區"
    full_name VARCHAR(20) NOT NULL,       -- 完整行政區名稱，如 "新北市永和區"（用於模糊搜尋）
    latitude DECIMAL(9,6),                -- 緯度，如 24.753707
    longitude DECIMAL(9,6),               -- 經度，如 121.745083
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 地理編碼索引（氣象局 API 查詢時使用）
CREATE INDEX idx_location_geocode ON location(geocode);

-- 完整名稱索引（用於模糊搜尋，支援使用者輸入2-6個字）
CREATE INDEX idx_location_full_name ON location(full_name);

-- =============================================================================
-- 天氣預報資料表
-- =============================================================================
CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES location(id),
    start_time TIMESTAMP NOT NULL,        -- 預報開始時間（台灣時間 +08:00）
    end_time TIMESTAMP NOT NULL,          -- 預報結束時間（台灣時間 +08:00）
    fetched_at TIMESTAMP NOT NULL,        -- 資料獲取時間（記錄從氣象局 API 取得的時間）
    
    -- 解析後的結構化資料（實際使用）
    weather_condition VARCHAR(30) NOT NULL,  -- 天氣狀況，如 "短暫陣雨或雷雨"
    weather_emoji VARCHAR(10),               -- 對應的 emoji 符號，如 "🌦️"
    precipitation_probability INTEGER CHECK (precipitation_probability >= 0 AND precipitation_probability <= 100), -- 降雨機率 0-100%
    min_temperature INTEGER,                 -- 最低溫度（攝氏度）
    max_temperature INTEGER,                 -- 最高溫度（攝氏度）
    
    -- 原始資料備援（用於除錯和驗證）
    raw_description TEXT NOT NULL,          -- 原始 WeatherDescription 字串
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 確保同一地點同一時間區間同一次獲取不重複
    CONSTRAINT unique_location_time_fetched UNIQUE (location_id, start_time, end_time, fetched_at)
);

-- 常用查詢索引：特定地點的天氣預報（wea-data 微服務更新時使用）
CREATE INDEX idx_weather_location_time ON weather(location_id, start_time);

-- =============================================================================
-- 範例資料註解
-- =============================================================================

-- location 範例資料：
-- INSERT INTO location (geocode, county, district, full_name, latitude, longitude) VALUES
-- ('10002010', '宜蘭縣', '宜蘭市', '宜蘭縣宜蘭市', 24.753707, 121.745083),
-- ('10002020', '宜蘭縣', '羅東鎮', '宜蘭縣羅東鎮', 24.678673, 121.758763),
-- ('65000100', '新北市', '永和區', '新北市永和區', 25.017891, 121.515406),
-- ('65000010', '新北市', '板橋區', '新北市板橋區', 25.012366, 121.462887);

-- weather 範例資料：
-- INSERT INTO weather (location_id, start_time, end_time, fetched_at, weather_condition, weather_emoji, precipitation_probability, min_temperature, max_temperature, raw_description) VALUES
-- (1, '2025-08-13 00:00:00+08', '2025-08-13 03:00:00+08', '2025-08-12 17:45:00+08', '短暫陣雨或雷雨', '🌦️', 40, 27, 28, '短暫陣雨或雷雨。降雨機率40%。溫度攝氏27至28度。悶熱。偏南風 平均風速<= 1級(每秒1公尺)。相對濕度93至95%。'),
-- (1, '2025-08-13 00:00:00+08', '2025-08-13 03:00:00+08', '2025-08-12 23:45:00+08', '短暫陣雨或雷雨', '🌦️', 50, 26, 28, '短暫陣雨或雷雨。降雨機率50%。溫度攝氏26至28度。悶熱。偏南風 平均風速<= 1級(每秒1公尺)。相對濕度93至95%。');

-- =============================================================================
-- 資料清理策略（建議每日凌晨 2:00 執行，避開資料更新時間）
-- =============================================================================

-- 刪除 14 天前的天氣預報資料
-- DELETE FROM weather WHERE fetched_at < NOW() - INTERVAL '14 days';

-- =============================================================================
-- 搜尋查詢範例
-- =============================================================================

-- 使用者輸入地點搜尋（支援 2-6 個字的模糊搜尋）
-- SELECT id, full_name, county, district 
-- FROM location 
-- WHERE full_name LIKE '%永和%'
-- ORDER BY LENGTH(full_name), full_name;

-- =============================================================================
-- 天氣狀況與 Emoji 映射參考
-- =============================================================================

-- 常見天氣狀況對應 emoji：
-- "晴" → "☀️"
-- "多雲" → "☁️"
-- "陰" → "☁️"
-- "短暫陣雨" → "🌦️"
-- "陣雨" → "🌧️"
-- "雷雨" → "⛈️"
-- "短暫陣雨或雷雨" → "🌦️"
-- "陣雨或雷雨" → "⛈️"
