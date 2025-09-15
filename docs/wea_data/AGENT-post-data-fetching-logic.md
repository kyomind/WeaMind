# AGENT 開發規格：天氣資料抓取邏輯

本文件提供給 AI Agent 作為 WeaMind 主專案中「天氣資料抓取邏輯」實作的開發依據。

---

## 1. WHY：為何需要此功能？

- **問題**: 目前的天氣查詢功能使用的是一個臨時性的 placeholder 邏輯（例如，僅回傳「找到有xxx」的訊息）。這無法提供真實的天氣預報，使用者體驗不完整。
- **目標**: 實作一個穩定、高效的查詢邏輯，從資料庫中抓取由 `wea-data` 服務更新的最新天氣資料，並確保使用者無論何時查詢，都能獲得一致且完整的未來 24 小時天氣預報。

---

## 2. WHAT：需要實作什麼？

1.  **實作新的查詢服務**: 在 `app/weather/service.py` 中，建立一個新的函式（例如 `get_weather_forecast_by_location`）。
2.  **採用滑動窗口查詢**: 此函式需實作「滑動窗口」SQL 查詢，以確保總是能從最新的一批資料中，選取從當下時間點開始的未來 24 小時（8 筆）預報。
3.  **取代舊有邏輯**: 修改 `app/line/router.py` 中的 webhook handler，將處理天氣查詢的部分替換為呼叫新的查詢服務，並將結果格式化後回傳給使用者。

---

## 3. HOW：如何實作？

### 3.1 核心查詢邏輯 (滑動窗口)

- **檔案位置**: `app/weather/service.py`
- **核心 SQL**: 必須嚴格遵循 `weather-query-logic.md` 中定義的查詢策略。這是確保使用者體驗一致性的關鍵。

```sql
-- 這是 SQL 邏輯示意，請使用 SQLAlchemy Core 或 ORM 實作
SELECT * FROM weather
WHERE
    location_id = :location_id
    AND end_time > NOW()  -- 關鍵 1: 過濾掉已過期的預報時段
    AND fetched_at >= (   -- 關鍵 2: 確保只從最新的一批資料中選取
        SELECT MAX(fetched_at) - INTERVAL '5 minutes'
        FROM weather
        WHERE location_id = :location_id
    )
ORDER BY start_time      -- 關鍵 3: 按時間順序排列
LIMIT 8;                 -- 關鍵 4: 只取未來 24 小時 (8 * 3h)
```

### 3.2 服務層實作

- 建立一個函式，接收 `location_id` 作為參數。
- 執行上述的 SQLAlchemy 查詢。
- 回傳一個包含 8 筆 `Weather` model 物件的列表。如果找不到資料，則回傳空列表或 `None`。

### 3.3 路由與輸出整合

- 在 `app/line/router.py` 中，當收到使用者查詢天氣的訊息時：
    1. 呼叫 `location` 服務找到對應的 `location_id`。
    2. 呼叫新的 `weather` 服務函式取得天氣資料。
    3. 將回傳的 8 筆天氣資料，依照 `weather-query-logic.md` 中定義的 LINE Bot 輸出格式進行排版。
    4. 回傳格式化後的文字訊息給使用者。

---

## 4. Memory Hooks for AI Agent

- **核心提醒 (Memento)**:
    - **一致性是首要目標**: 此任務的核心是**保證使用者體驗的一致性**。無論使用者在 08:00 還是 10:55 查詢，都應該看到從下一個時段（例如 09:00-12:00）開始的完整 24 小時預報。
    - **滑動窗口是唯一解**: 「滑動窗口」查詢是達成此目標的唯一指定方法，請勿嘗試其他複雜的 `CASE` 或 `OFFSET` 邏輯。`end_time > NOW()` 是實現滑動的關鍵。
    - **`fetched_at` 的重要性**: `fetched_at` 搭配 `INTERVAL '5 minutes'` 的過濾條件是為了隔離出「同一次更新」的所有資料，避免新舊資料混雜。這是確保資料一致性的命脈。
    - **假設資料已存在**: 開發此功能時，請**假設 `wea-data` 服務已經成功運作**，且 `weather` 表中有正確的資料。你的任務是專注於「如何正確地查詢和呈現」。
    - **輸出格式**: 最終呈現給使用者的文字格式，請參考 `weather-query-logic.md` 中的範例，特別是溫度的顯示方式（`27～28°C` vs `26°C`）。

---
**相關文件**:
- `prd/wea_data/weather-query-logic.md` (最重要的核心邏輯文件)
- `prd/wea_data/MEMO-for-next-conversation.md` (高階決策)
