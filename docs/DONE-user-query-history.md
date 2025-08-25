# 用戶查詢記錄與最近查詢功能實作紀錄

## 概述

實作用戶查詢歷史記錄功能，提供「最近查過」快捷查詢，解決多地點查詢的效率問題。此功能為 Rich Menu 核心體驗的重要組成部分。

**實作日期**：2025-08-24
**分支**：`feature/user-query-history`
**相關 Todo**：#27

## 技術架構

### 資料模型設計

```python
class UserQuery(Base):
    __tablename__ = "user_query"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"), nullable=False)
    query_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
```

**設計考量**：
- `user_id` 和 `query_time` 設置索引以優化查詢效能
- 使用 UTC 時間戳記避免時區問題
- 建立 Foreign Key 關聯確保資料完整性

### 核心服務方法

#### 1. 查詢記錄功能
```python
def record_user_query(session: Session, user_id: int, location_id: int) -> None:
    query_record = UserQuery(user_id=user_id, location_id=location_id, query_time=datetime.now(UTC))
    session.add(query_record)
    session.commit()
```

#### 2. 最近查詢檢索
```python
def get_recent_queries(session: Session, user_id: int, limit: int = 3) -> list[Location]:
    # 動態排除用戶的住家/公司地點
    excluded_location_ids = []
    if user.home_location_id:
        excluded_location_ids.append(user.home_location_id)
    if user.work_location_id:
        excluded_location_ids.append(user.work_location_id)

    # 取得最近查詢且去重的地點
    recent_queries = []
    seen_locations = set()

    for user_query in query.all():
        if user_query.location_id not in seen_locations:
            recent_queries.append(user_query)
            seen_locations.add(user_query.location_id)
            if len(recent_queries) >= limit:
                break
```

## 關鍵技術決策

### 1. 跨資料庫相容性問題

**問題**：初始實作使用 PostgreSQL 的 `DISTINCT ON` 語法，但測試環境可能使用 SQLite。

**解決方案**：採用 Python 層面的去重邏輯：
```python
# 避免使用 PostgreSQL 特定語法
# query.distinct(UserQuery.location_id)  # 會報錯

# 改為 Python 層面處理
recent_queries = []
seen_locations = set()
for user_query in query.all():
    if user_query.location_id not in seen_locations:
        recent_queries.append(user_query)
        seen_locations.add(user_query.location_id)
```

**技術考量**：雖然犧牲了部分資料庫層面的效能，但確保了跨資料庫的相容性。

### 2. 住家/公司地點智慧排除

**需求**：用戶不希望在「最近查詢」中看到已設定的住家/公司地點。

**實作策略**：
```python
excluded_location_ids = []
if user.home_location_id:
    excluded_location_ids.append(user.home_location_id)
if user.work_location_id:
    excluded_location_ids.append(user.work_location_id)

if excluded_location_ids:
    query = query.filter(~UserQuery.location_id.in_(excluded_location_ids))
```

**處理情境**：
- 只設定住家
- 只設定公司
- 兩者都設定
- 都沒設定

### 3. 查詢記錄時機選擇

**決策**：僅記錄成功的單一地點查詢。

**邏輯實作**：
```python
# 在 LINE Bot 訊息處理中
if len(locations) == 1:  # 只有單一匹配結果
    user = get_user_by_line_id(session, user_id)
    if user:
        record_user_query(session, user.id, locations[0].id)
```

**不記錄的情況**：
- 模糊查詢（2-3 個結果）
- 查詢失敗（0 個結果）
- 太多結果（>3 個結果）
- 住家/公司查詢（避免重複記錄）

## LINE Bot 整合

### Rich Menu 點擊處理

```python
def handle_recent_queries_postback(event: PostbackEvent) -> None:
    user = get_user_by_line_id(session, user_id)
    recent_locations = get_recent_queries(session, user.id, limit=3)

    if not recent_locations:
        # 顯示引導訊息
        return

    # 建立 Quick Reply 選項
    quick_reply_items = [
        QuickReplyItem(
            action=MessageAction(
                label=location.full_name,
                text=location.full_name,
            )
        )
        for location in recent_locations
    ]
```

### 使用者體驗考量

- **無查詢記錄**：顯示友善的引導訊息
- **Quick Reply 介面**：提供直觀的點選體驗
- **動態內容**：根據用戶實際查詢歷史生成選項

## API 端點設計

### 查詢歷史 API

```python
@router.get("/query-history")
async def get_user_query_history(
    line_user_id: Annotated[str, Depends(get_current_line_user_id_from_access_token)],
    session: Annotated[Session, Depends(get_session)],
    limit: int = 3,
) -> QueryHistoryResponse
```

**安全考量**：
- 使用 LINE Access Token 認證
- 僅返回當前用戶的查詢記錄
- 限制查詢數量避免資料洩露

### 響應結構

```python
class QueryHistoryResponse(BaseModel):
    success: bool
    message: str
    recent_queries: list[QueryHistoryItem]

class QueryHistoryItem(BaseModel):
    location_id: int
    location_name: str
    county: str
    district: str
    last_query_time: datetime
```

## 測試策略

### 測試覆蓋範圍

1. **基礎功能測試**
   - 查詢記錄功能
   - 最近查詢檢索
   - 住家/公司排除邏輯

2. **邊界條件測試**
   - 無查詢記錄情況
   - 查詢數量限制
   - 非存在用戶處理

3. **API 端點測試**
   - 成功響應
   - 認證失敗
   - 用戶不存在

### 關鍵測試案例

```python
def test_get_recent_queries_excludes_home_work(self, session: Session) -> None:
    # 設置住家和公司地點
    user.home_location_id = home_location.id
    user.work_location_id = work_location.id

    # 記錄所有地點查詢
    record_user_query(session, user.id, home_location.id)
    record_user_query(session, user.id, work_location.id)
    record_user_query(session, user.id, other_location.id)

    recent_locations = get_recent_queries(session, user.id)

    # 驗證只返回其他地點
    assert len(recent_locations) == 1
    assert recent_locations[0].id == other_location.id
```

## 遇到的問題與解決

### 1. SQLAlchemy DISTINCT 相容性警告

**問題**：`DISTINCT ON` 語法在非 PostgreSQL 資料庫報錯。

**解決**：改為 Python 層面去重，確保跨資料庫相容性。

### 2. 程式碼品質問題

**問題**：Ruff 檢查發現未使用變數和格式問題。

**解決**：
```python
# 使用 _ 標記未使用變數
_, response_message = LocationService.parse_location_input(session, location_text)
_ = data  # Acknowledge unused parameter
```

### 3. 測試資料庫連線

**問題**：Alembic 遷移需要資料庫連線但容器未啟動。

**解決**：使用 Makefile 指令確保容器運行：
```bash
make revision  # 自動在容器中執行遷移生成
make migrate   # 應用遷移到資料庫
```

## 效能考量

### 索引策略
- `user_id` 索引：加速用戶查詢過濾
- `query_time` 索引：優化時間排序
- 複合索引考量：未來可考慮 `(user_id, query_time)` 複合索引

### 查詢優化
- 限制查詢數量（預設 3 筆）
- 使用 Python 去重避免複雜 SQL
- 分離查詢時間資訊的專用方法

## 資料清理策略

**設計決策**：查詢記錄的清理由 `wea-data` 模組負責，本專案僅負責資料結構設計。

**清理策略**：保留最近 30 天的查詢記錄（由外部模組實作）。

## 檔案異動清單

### 新增檔案
- 無（所有變更都在既有檔案中）

### 修改檔案
```
app/user/models.py          # 新增 UserQuery 模型
app/user/service.py         # 新增查詢記錄相關服務方法
app/user/schemas.py         # 新增 API 響應結構
app/user/router.py          # 新增查詢歷史 API 端點
app/line/service.py         # 整合查詢記錄和 Rich Menu 功能
migrations/env.py           # 匯入 UserQuery 模型
tests/user/test_user.py     # 新增完整測試覆蓋
docs/Todo.md               # 標記任務完成
```

### 資料庫遷移
```
migrations/versions/5c81b38eccbc_feature_user_query_history_20250824_.py
```

## 後續優化建議

1. **效能優化**：考慮實作複合索引 `(user_id, query_time)`
2. **功能擴展**：添加查詢頻率統計
3. **使用者體驗**：考慮顯示查詢時間資訊
4. **監控機制**：添加查詢歷史增長趨勢監控

## 結論

此功能成功實作了用戶查詢歷史記錄和最近查詢功能，解決了多地點查詢的效率問題。通過智慧排除邏輯和 Quick Reply 介面，提升了用戶體驗。技術實作考慮了跨資料庫相容性、安全性和效能，並提供了完整的測試覆蓋。
