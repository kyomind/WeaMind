# App Config 重構

## 改進內容

這個重構簡化了應用程式的配置管理，主要改進如下：

### 1. 更好的配置結構
- 保持原有的配置變數名稱，確保向後相容
- 新增 `database_url` 屬性方法，簡化資料庫連線字串的取得
- 改進環境判斷邏輯

### 2. 程式碼簡化
- 移除過度複雜的配置類別分離
- 保持簡潔的單一 `Settings` 類別
- 維持原有的使用方式

### 3. 主要變更

#### `app/core/config.py`
- 新增 `database_url` 屬性方法
- 改進 `is_development` 和 `is_production` 的判斷邏輯
- 保持所有原有的配置變數

#### `app/core/database.py`
- 使用 `settings.database_url` 取得資料庫連線字串
- 移除不必要的複雜邏輯

#### `app/main.py`
- 保持原有的 FastAPI 應用程式建立邏輯
- 根據環境決定是否顯示 API 文檔

## 使用方式

所有原有的配置使用方式都保持不變：

```python
from app.core.config import settings

# 環境檢查
if settings.is_development:
    print("開發環境")

# 資料庫連線
db_url = settings.database_url

# 其他配置
app_name = settings.APP_NAME
debug = settings.DEBUG
```

## 向後相容性

這個重構完全向後相容，不需要修改任何現有的程式碼。
