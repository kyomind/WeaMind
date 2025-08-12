-- WeaMind 天氣與行政區資料庫 Schema DDL
-- 建立日期: 2025-08-12
-- 說明: 包含行政區 (locations) 和天氣預報 (weather_forecasts) 兩個主要資料表

-- =============================================================================
-- 行政區資料表
-- =============================================================================
CREATE TABLE location (
    id SERIAL PRIMARY KEY,
    geocode VARCHAR(10) NOT NULL UNIQUE,  -- 地理編碼，如 "10002010"
    county VARCHAR(10) NOT NULL,          -- 縣市名稱，如 "宜蘭縣"
    district VARCHAR(10) NOT NULL,        -- 鄉鎮市區名稱，如 "宜蘭市"
    latitude DECIMAL(9,6),                -- 緯度，如 24.753707
    longitude DECIMAL(9,6),               -- 經度，如 121.745083
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 地理編碼索引（常用於查詢）
CREATE INDEX idx_location_geocode ON location(geocode);

-- 縣市索引（可能用於按縣市查詢）
CREATE INDEX idx_location_county ON location(county);

-- =============================================================================
-- 天氣預報資料表
-- =============================================================================
CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES location(id),
    start_time TIMESTAMP NOT NULL,        -- 預報開始時間（台灣時間 +08:00）
    end_time TIMESTAMP NOT NULL,          -- 預報結束時間（台灣時間 +08:00）
    
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
    
    -- 確保同一地點同一時間區間不重複
    CONSTRAINT unique_location_time_range UNIQUE (location_id, start_time, end_time)
);

-- 常用查詢索引：特定地點的天氣預報（按時間排序）
CREATE INDEX idx_weather_location_time ON weather(location_id, start_time);

-- 時間範圍查詢索引
CREATE INDEX idx_weather_time_range ON weather(start_time, end_time);

-- =============================================================================
-- 範例資料註解
-- =============================================================================

-- location 範例資料：
-- INSERT INTO location (geocode, county, district, latitude, longitude) VALUES
-- ('10002010', '宜蘭縣', '宜蘭市', 24.753707, 121.745083),
-- ('10002020', '宜蘭縣', '羅東鎮', 24.678673, 121.758763);

-- weather 範例資料：
-- INSERT INTO weather (location_id, start_time, end_time, weather_condition, weather_emoji, precipitation_probability, min_temperature, max_temperature, raw_description) VALUES
-- (1, '2025-08-13 00:00:00+08', '2025-08-13 03:00:00+08', '短暫陣雨或雷雨', '🌦️', 40, 27, 28, '短暫陣雨或雷雨。降雨機率40%。溫度攝氏27至28度。悶熱。偏南風 平均風速<= 1級(每秒1公尺)。相對濕度93至95%。');

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
