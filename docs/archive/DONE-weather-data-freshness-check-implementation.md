# DONE: 天氣資料新鮮度檢查功能實作紀錄

**實作日期**: 2025-09-26
**分支**: `feature/weather-data-freshness-check`
**功能範圍**: 防止提供過時天氣資料給使用者
**狀態**: ✅ 完成並測試通過

## 1. 問題背景與需求

### 原始問題
如果 weamind-data 微服務長時間無法正常更新天氣資料，WeaMind 可能會提供過時的預報資訊給使用者，造成誤導。

### 使用者需求
> "如果查到的是過時的資料(表示db資料沒有正確更新)，應該就不能回應天氣資料，以免誤導用戶"
> "此時應該要給出文字訊息告知目前天氣資料有問題"

### 技術需求
- 設定合理的資料新鮮度閾值
- 當資料過時時拒絶提供天氣預報
- 使用現有錯誤處理機制，不增加複雜度

## 2. 技術方案設計

### 2.1 架構決策：簡潔 vs 複雜

**考慮的方案**：
1. 複雜方案：新增專門的新鮮度檢查服務、獨立錯誤處理邏輯
2. **簡潔方案**：直接在現有查詢中加入新鮮度條件 ✅

**最終選擇**：簡潔方案
**決策原因**：用戶明確表達偏好 "我認為簡潔確實更好"，且能完美復用現有錯誤處理邏輯。

### 2.2 新鮮度閾值設計

**閾值選擇**: 6.5 小時
**設計理由**:
- weamind-data 微服務每 6 小時更新一次
- 6.5 小時提供 30 分鐘的緩衝時間
- 平衡資料時效性與系統容錯性

### 2.3 實作策略：雙重保護機制

```sql
-- 兩個互補的 fetched_at 條件
WHERE location_id = 123
  AND end_time > NOW()  -- 滑動窗口（過濾過期時段）
  AND fetched_at >= (   -- 批次一致性（同一次更新）
    SELECT MAX(fetched_at) - INTERVAL '5 minutes'
    FROM weather WHERE location_id = 123
  )
  AND fetched_at >= NOW() - INTERVAL '6.5 hours'  -- 絕對新鮮度
```

**雙重保護的互補關係**：
1. **批次一致性條件**: 確保資料來自同一次更新，避免混合不同批次
2. **絕對新鮮度條件**: 防止整批資料都過時的情況

## 3. 核心技術問題與解決方案

### 3.1 重大發現：時區一致性問題

#### 問題發現過程
在實作新鮮度檢查後，測試案例意外失敗，引發深度調查。

#### 初始假設（錯誤）
認為問題源於 VM 時區設定影響 PostgreSQL 容器的 `func.now()` 返回值。

#### 實際驗證結果
```bash
# PostgreSQL 容器檢查結果
docker compose exec db psql -U wea_bot -d weamind -c "SELECT now();"
# 結果: 2025-09-26 03:42:54.259425+00

docker compose exec db psql -U wea_bot -d weamind -c "SELECT current_setting('timezone');"
# 結果: Etc/UTC
```

#### 真正問題根源
**發現**: PostgreSQL 確實使用 UTC 時區，但問題在於 **SQLAlchemy timezone-aware vs timezone-naive datetime 比較**。

```python
# 問題分析
func.now()  # 返回: 2025-09-26 03:42:54+00 (timezone-aware)
# 但資料庫中的時間: 2025-09-23 15:45:00.343837 (timezone-naive)
# SQLAlchemy 比較時出現不一致
```

#### 解決方案
```python
# 錯誤的做法
Weather.end_time > func.now()
Weather.fetched_at >= func.now() - timedelta(hours=6.5)

# 正確的做法
utc_now = datetime.now(UTC)  # 明確的 UTC 時間
Weather.end_time > utc_now
Weather.fetched_at >= utc_now - timedelta(hours=6.5)
```

**技術決策理由**：
- 確保所有時間比較使用一致的時區處理
- Python `datetime.now(UTC)` 行為可預測，不依賴資料庫設定
- 測試環境和生產環境行為完全一致

### 3.2 為什麼舊寫法「看似」能工作

#### 隱藏的問題
在沒有新鮮度檢查之前：
```python
# 只有一個寬鬆的時間條件
Weather.end_time > func.now()
```

**為什麼之前沒發現**：
- 滑動窗口的容錯空間較大（24小時預報）
- 8小時時區差異對未來時段影響相對不明顯
- 可能已經在錯誤過濾資料，但未被察覺

#### 新鮮度檢查的「放大鏡效應」
```python
# 新增嚴格的時間比較後，問題被放大
Weather.fetched_at >= func.now() - timedelta(hours=6.5)
# 6.5小時的閾值直接受到8小時時區差異影響
```

**啟發**：新功能往往會暴露原本隱藏的設計缺陷。

## 4. 程式碼實作架構

### 4.1 核心修改：`get_weather_forecast_by_location`

**檔案**: `app/weather/service.py`

```python
@staticmethod
def get_weather_forecast_by_location(session: Session, location_id: int) -> list[Weather]:
    try:
        # 關鍵：使用明確的 UTC 時間
        utc_now = datetime.now(UTC)
        freshness_threshold = utc_now - timedelta(hours=6.5)

        # 新鮮度預過濾：只查詢新鮮的 fetched_at
        latest_fetched_subquery = (
            session.query(func.max(Weather.fetched_at))
            .filter(
                Weather.location_id == location_id,
                Weather.fetched_at >= freshness_threshold  # 新增條件
            )
            .scalar_subquery()
        )

        # 主查詢：結合三個條件
        weather_data = (
            session.query(Weather)
            .filter(
                Weather.location_id == location_id,
                Weather.end_time > utc_now,           # 滑動窗口
                Weather.fetched_at == latest_fetched_subquery  # 批次一致性+新鮮度
            )
            .order_by(Weather.start_time)
            .limit(8)
            .all()
        )
        return weather_data
    except Exception:
        logger.exception(f"Error retrieving weather forecast for location_id={location_id}")
        return []
```

### 4.2 錯誤處理設計

**統一錯誤處理策略**：
- 當資料不符合新鮮度要求時，查詢結果為空
- 觸發現有的「查無資料」錯誤處理邏輯
- 使用者收到：「抱歉，目前無法取得 {location} 的天氣資料，請稍後再試。」

**設計優勢**：
- 無需額外的錯誤處理邏輯
- 復用成熟的錯誤處理流程
- 使用者體驗一致

### 4.3 測試策略

**測試覆蓋範圍**：
1. **正常情況**: 3小時前的新鮮資料
2. **邊界情況**: 6.4小時的邊界資料
3. **過時情況**: 8小時前的過時資料
4. **錯誤訊息**: 驗證過時資料的錯誤訊息

**關鍵測試設計**：
```python
# 測試中統一使用 UTC 時間
base_time = datetime.now(UTC) - timedelta(hours=8)
current_time = datetime.now(UTC)

# 確保時區一致性
weather = Weather(
    start_time=current_time + timedelta(hours=i * 3),
    end_time=start_time + timedelta(hours=3),
    fetched_at=base_time,  # 明確的過時時間
    # ...
)
```

## 5. 額外發現與清理

### 5.1 Task 模型的時區問題

**發現問題**：
```python
# app/weather/models.py 中的潛在問題
start_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
```

**分析結果**：
- weamind-data 服務實際上會明確提供 `start_time` 值
- Model 中的 `default=func.now()` 永遠不會被使用
- 但為保持程式碼一致性，建議移除

**解決方案**：
```python
# 修正後：移除不必要的預設值
start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
```

**重要認知**：
- **SQLAlchemy Model `default`** ≠ **Database `DEFAULT`**
- Model default 只在 Python 層面生效
- 資料庫 schema 沒有改變，因此不需要 migration

## 6. 文件更新

### 6.1 更新查詢邏輯文件

**檔案**: `docs/wea_data/weather-query-logic.md`

**新增內容**：
- 資料新鮮度保證機制說明
- 6.5小時閾值的設計理念
- 雙重 fetched_at 條件的互補關係
- 統一錯誤處理方式的說明

**更新的 SQL 範例**：
```sql
-- 新增第三個條件
AND fetched_at >= NOW() - INTERVAL '6.5 hours'
```

## 7. 技術決策總結

### 7.1 關鍵技術選擇

| 決策點     | 選擇                | 替代方案     | 選擇理由                 |
| ---------- | ------------------- | ------------ | ------------------------ |
| 實作策略   | 簡潔方案            | 複雜獨立服務 | 使用者偏好，復用現有邏輯 |
| 新鮮度閾值 | 6.5小時             | 6小時/8小時  | 提供合理緩衝，平衡時效性 |
| 時間處理   | `datetime.now(UTC)` | `func.now()` | 避免timezone混淆問題     |
| 錯誤處理   | 復用現有機制        | 新增專用處理 | 保持系統一致性           |

### 7.2 架構影響

**正面影響**：
- ✅ 提升資料可靠性，避免誤導使用者
- ✅ 保持系統架構簡潔
- ✅ 解決了隱藏的時區處理問題
- ✅ 建立了時間處理的最佳實踐

**學習收穫**：
- 🎯 新功能開發可能暴露隱藏問題
- 🎯 時區處理需要全專案一致性
- 🎯 簡潔方案往往更可靠
- 🎯 測試是發現深層問題的關鍵

## 8. 未來維護建議

### 8.1 監控要點
- 關注 weamind-data 服務的更新頻率
- 監控「查無資料」錯誤的頻率變化
- 考慮添加新鮮度相關的 metrics

### 8.2 擴展可能性
- 可考慮動態調整新鮮度閾值
- 未來可添加管理介面顯示資料新鮮度狀態
- 考慮在 LOG 中記錄新鮮度檢查結果

## 9. 結論

本次實作成功解決了天氣資料過時的問題，同時發現並修正了系統中隱藏的時區處理問題。通過採用簡潔的技術方案，不僅滿足了功能需求，還提升了整體程式碼品質和系統可靠性。

**核心成就**：
- 🎯 防止過時資料誤導使用者
- 🔧 修正timezone-aware vs timezone-naive問題
- 📚 建立時間處理最佳實踐
- ✅ 保持系統架構簡潔性

這個功能為 WeaMind 的資料品質保證奠定了重要基礎。
