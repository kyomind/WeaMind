# TEST-Coverage-Improvement-Record

## 📋 文件概述

**文件名稱**: TEST-Coverage-Improvement-Record.md
**創建日期**: 2025年8月19日
**作者**: WeaMind 開發團隊
**目的**: 記錄專案測試覆蓋率從75%提升至96%的完整實作過程

## 🎯 專案目標

將 WeaMind 專案的測試覆蓋率從75%提升至80%以上，重點關注低於80%覆蓋率的核心模組。

## 📊 初始覆蓋率分析

### 覆蓋率檢查命令
```bash
cd /Users/kyo/Code/WeaMind
uv run pytest --cov=app --cov-report=term --cov-report=xml --cov-report=html
```

### 初始狀態 (2025-08-19 17:43)
- **整體覆蓋率**: 75%
- **問題模組**:
  - `app/core/auth.py`: 13% ❌ (最嚴重)
  - `app/user/service.py`: 70% ❌
  - `app/user/router.py`: 71% ❌
  - `app/line/service.py`: 83% ⚠️ (接近標準)
  - `app/main.py`: 88% ✅ (已達標)

## 🔍 測試不足分析

### 1. app/core/auth.py (覆蓋率: 13%)

**問題診斷**:
- 完全缺少測試檔案
- 包含關鍵的 LINE 身分驗證邏輯
- 有 Access Token 和 ID Token 兩種驗證方式

**缺失的測試範圍**:
- LINE Access Token 驗證流程
- LINE ID Token (JWT) 驗證流程
- 網路錯誤處理
- FastAPI 身分驗證依賴項

### 2. app/user/service.py (覆蓋率: 70%)

**問題診斷**:
- 現有測試只覆蓋部分 service 函式
- 缺少 CRUD 操作的完整測試
- 缺少地點設定相關函式測試

**缺失的測試範圍**:
- `create_user()`, `get_user()`, `update_user()`, `delete_user()`
- `get_location_by_county_district()`
- `set_user_location()` 的各種情境

### 3. app/user/router.py (覆蓋率: 71%)

**問題診斷**:
- 現有測試主要覆蓋正常情況
- 缺少錯誤處理測試
- 缺少 LIFF 地點設定端點測試

**缺失的測試範圍**:
- 404 錯誤處理
- 身分驗證失敗情況
- `/users/locations` 端點的各種情境

## 🛠️ 實作解決方案

### Phase 1: 創建 auth.py 完整測試

**檔案**: `/Users/kyo/Code/WeaMind/tests/core/test_auth.py`

#### 1.1 測試結構設計
```python
class TestVerifyLineAccessToken:
    """測試 LINE Access Token 驗證"""

class TestVerifyLineIdToken:
    """測試 LINE ID Token 驗證"""

class TestAuthDependencies:
    """測試 FastAPI 身分驗證依賴項"""
```

#### 1.2 關鍵測試案例

**LINE Access Token 驗證測試**:
- ✅ 成功驗證情境
- ✅ 驗證 API 失敗 (401)
- ✅ 回應缺少 client_id
- ✅ Token 過期
- ✅ Profile API 失敗
- ✅ Profile 缺少 userId
- ✅ 網路錯誤處理

**LINE ID Token (JWT) 驗證測試**:
- ✅ 成功驗證情境
- ✅ 無效 Token 格式
- ✅ 不支援的演算法
- ✅ 缺少過期時間
- ✅ Token 過期
- ✅ 無效發行者
- ✅ 缺少用戶 ID

**技術實作重點**:
```python
def create_valid_token(self, line_user_id: str, exp_offset: int = 3600) -> str:
    """創建有效的 JWT token 用於測試"""
    current_time = int(time.time())

    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": "https://access.line.me",
        "sub": line_user_id,
        "exp": current_time + exp_offset,
    }

    # Base64 編碼
    header_encoded = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip("=")
    payload_encoded = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode().rstrip("=")

    # 創建假簽名 (測試環境不驗證實際簽名)
    signature = base64.urlsafe_b64encode(b"dummy_signature").decode().rstrip("=")

    return f"{header_encoded}.{payload_encoded}.{signature}"
```

### Phase 2: 擴展 user service 測試

**檔案**: `/Users/kyo/Code/WeaMind/tests/user/test_user.py`

#### 2.1 新增測試類別
```python
class TestUserServiceAdditional:
    """用戶服務額外測試案例"""
```

#### 2.2 補強的測試範圍

**CRUD 操作測試**:
- ✅ `test_create_user()` - 創建用戶
- ✅ `test_get_user()` / `test_get_user_not_exists()` - 查詢用戶
- ✅ `test_update_user()` / `test_update_user_not_exists()` - 更新用戶
- ✅ `test_delete_user()` / `test_delete_user_not_exists()` - 刪除用戶

**地點相關測試**:
- ✅ `test_get_location_by_county_district()` - 地點查詢
- ✅ `test_set_user_location_*()` - 地點設定的各種情境

**地點設定測試情境**:
```python
# 測試成功設定住家地點
def test_set_user_location_home_success(self, session: Session) -> None:
    # 創建地點、設定、驗證

# 測試成功設定工作地點
def test_set_user_location_work_success(self, session: Session) -> None:
    # 創建地點、設定、驗證

# 測試無效地點類型
def test_set_user_location_invalid_type(self, session: Session) -> None:
    # 驗證錯誤處理

# 測試地點不存在
def test_set_user_location_location_not_exists(self, session: Session) -> None:
    # 驗證錯誤處理
```

#### 2.3 資料模型問題解決

**遇到的問題**:
```
TypeError: 'station_id' is an invalid keyword argument for Location
```

**解決方案**:
檢查 `app/weather/models.py` 確認正確的 Location 模型欄位：
```python
# 正確的 Location 欄位
location = Location(
    geocode="test001",        # ✅ 正確
    county="台北市",          # ✅ 正確
    district="中正區",        # ✅ 正確
    full_name="台北市中正區",  # ✅ 正確
)

# 錯誤示範 (不存在的欄位)
location = Location(
    station_id="466920",     # ❌ 不存在
    station_name="臺北",     # ❌ 不存在
)
```

### Phase 3: 擴展 user router 測試

#### 3.1 新增測試類別
```python
class TestUserRouterAdditional:
    """用戶路由額外測試案例"""
```

#### 3.2 API 錯誤處理測試
- ✅ `test_create_user_duplicate_line_id()` - 重複 LINE ID
- ✅ `test_get_user_not_found()` - 用戶不存在
- ✅ `test_update_user_not_found()` - 更新不存在用戶
- ✅ `test_delete_user_not_found()` - 刪除不存在用戶

#### 3.3 LIFF 地點設定端點測試

**身分驗證 Mock 處理**:
```python
from unittest.mock import patch

# Mock LINE 身分驗證
with patch("app.core.auth.verify_line_access_token") as mock_auth:
    mock_auth.return_value = "test_line_user_id"

    payload = {
        "location_type": "home",
        "county": "台北市",
        "district": "中正區",
    }
    response = client.post(
        "/users/locations",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )
```

**測試情境覆蓋**:
- ✅ 成功設定住家地點
- ✅ 成功設定工作地點
- ✅ 無效地點類型錯誤
- ✅ 地點不存在錯誤
- ✅ 身分驗證失敗

## 🔧 技術實作細節

### 測試資料庫隔離

**問題**: geocode 欄位 UNIQUE 約束衝突
```
sqlite3.IntegrityError: UNIQUE constraint failed: location.geocode
```

**解決方案**: 為每個測試使用唯一的 geocode
```python
# 不同測試使用不同的 geocode
location1 = Location(geocode="test001", ...)  # 測試1
location2 = Location(geocode="test002", ...)  # 測試2
location3 = Location(geocode="test003", ...)  # 測試3
```

### Session 狀態管理

**問題**: 測試中物件狀態不同步
```python
# 錯誤：直接比較可能失敗
assert user.home_location_id == location.id
```

**解決方案**: 刷新物件狀態
```python
# 正確：刷新後再比較
session.refresh(user)
assert user.home_location_id == returned_location.id
```

### Import 組織

**新增的 Import**:
```python
# test_auth.py
from unittest.mock import AsyncMock, Mock, patch
import base64
import json
import time
import httpx
import pytest

# test_user.py
from unittest.mock import patch  # 新增
```

## 📈 實作成果

### 最終覆蓋率 (2025-08-19 17:52)

| 模組                  | 改善前  | 改善後  | 提升     | 狀態       |
| --------------------- | ------- | ------- | -------- | ---------- |
| `app/core/auth.py`    | 13%     | 100%    | +87%     | ✅ 完成     |
| `app/user/service.py` | 70%     | 99%     | +29%     | ✅ 完成     |
| `app/user/router.py`  | 71%     | 100%    | +29%     | ✅ 完成     |
| **整體專案**          | **75%** | **96%** | **+21%** | ✅ **超標** |

### 測試統計
- **新增測試檔案**: 1 個 (`tests/core/test_auth.py`)
- **新增測試案例**: 約 40+ 個
- **測試通過率**: 100%

## 🎓 經驗總結

### 成功因素

1. **系統性分析**: 先分析覆蓋率報告，找出具體缺失
2. **分階段實作**: 按模組重要性分階段改善
3. **遵循規範**: 遵循專案測試指導原則
4. **完整覆蓋**: 不只測試正常情況，也測試錯誤處理

### 技術學習

1. **Mock 技巧**: 學會 mock 外部 API 和身分驗證
2. **JWT 測試**: 學會創建測試用的 JWT token
3. **資料庫測試**: 學會處理測試資料庫的約束和狀態
4. **錯誤測試**: 學會設計各種錯誤情境的測試

### 最佳實務

1. **測試命名**: 使用描述性的測試名稱
   ```python
   def test_verify_line_access_token_expired(self) -> None:
       """Test LINE Access Token verification when token is expired."""
   ```

2. **測試組織**: 使用類別組織相關測試
   ```python
   class TestVerifyLineAccessToken:
       """Test LINE Access Token verification."""
   ```

3. **斷言順序**: 先檢查狀態碼，再檢查內容
   ```python
   assert response.status_code == 200  # noqa: S101
   assert response.json()["success"] is True  # noqa: S101
   ```

4. **錯誤處理**: 每個正常功能都要有對應的錯誤測試
   ```python
   def test_function_success(self):
       # 測試成功情況

   def test_function_failure(self):
       # 測試失敗情況
   ```

## 🔄 維護指引

### 新增功能時的測試策略

1. **新 API 端點**: 必須包含成功和錯誤情況測試
2. **新 Service 函式**: 必須測試各種輸入情況
3. **新驗證邏輯**: 必須測試有效和無效情況

### 測試維護檢查點

1. **定期執行**: 每次 commit 前執行完整測試
   ```bash
   uv run pytest --cov=app --cov-report=term
   ```

2. **覆蓋率監控**: 保持整體覆蓋率 > 90%
3. **失敗分析**: 測試失敗時優先修復，不要跳過

### 常見問題處理

1. **Mock 失效**: 檢查函式路徑是否正確
2. **資料庫衝突**: 使用唯一的測試資料
3. **狀態不同步**: 適時使用 `session.refresh()`

## 📚 參考資源

- [WeaMind Testing Guidelines](/.github/instructions/testing-guidelines.md)
- [Testing Functions Guidelines](/.github/instructions/testing-functions.instructions.md)
- [Testing Fixtures Guidelines](/.github/instructions/testing-fixtures.instructions.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

**文件版本**: v1.0
**最後更新**: 2025年8月19日
**下次審查**: 建議每季度檢查一次測試覆蓋率和測試品質
