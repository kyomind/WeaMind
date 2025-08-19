---
applyTo: 'tests/**/*.py'
---

# WeaMind Testing Guidelines

## 測試檔案結構與組織

### 檔案結構對應
- 保持測試檔案結構與 `app/` 目錄結構一致
- 測試檔案命名: `test_<module_name>.py`
- 每個模組建立對應的 `conftest.py` 存放專用 fixtures

```
tests/
├── conftest.py              # 全域 fixtures
├── core/
│   ├── conftest.py         # core 模組專用 fixtures
│   └── test_*.py
├── user/
│   ├── conftest.py         # user 模組專用 fixtures
│   └── test_user.py
└── <module>/
    ├── conftest.py
    └── test_*.py
```

## Pytest Fixtures 命名約定

### Helper Functions (動詞開頭)
```python
@pytest.fixture()
def create_user() -> Callable[..., dict]:
    """Return a helper for creating test users."""
    def _create(display_name: str = "Alice") -> dict:
        # 實作
        return result
    return _create

@pytest.fixture()
def setup_mock_weather_api() -> Generator[Mock, None, None]:
    """Setup and teardown mock weather API."""
    # 實作
```

### Objects/Values (名詞)
```python
@pytest.fixture()
def user() -> dict:
    """Return a test user object."""
    return {"line_user_id": "test_id", "display_name": "Alice"}

@pytest.fixture()
def client() -> TestClient:
    """Provide a FastAPI test client."""
    return TestClient(app)
```

## 測試類別組織

### 類別命名與結構
```python
class TestLocationService:
    """Test cases for LocationService class."""

    def test_validate_location_input_valid(self) -> None:
        """Test valid location input validation."""
        # 測試實作

    def test_validate_location_input_invalid_length(self) -> None:
        """Test location input validation with invalid length."""
        # 測試實作
```

### 測試方法命名模式
- `test_<method_name>_<scenario>`
- 範例: `test_validate_location_input_valid`, `test_create_user_duplicate_line_id`

## API 測試最佳實踐

### HTTP 狀態碼檢查
```python
def test_create_user(client: TestClient) -> None:
    """Create a new user."""
    data = {"line_user_id": str(uuid4()), "display_name": "Alice"}
    response = client.post("/users", json=data)
    assert response.status_code == 201  # noqa: S101
    body = response.json()
    assert body["line_user_id"] == data["line_user_id"]  # noqa: S101
```

### 使用 Helper Fixtures
```python
def test_get_user(create_user: Callable[..., dict], client: TestClient) -> None:
    """Retrieve an existing user."""
    created = create_user()  # 使用 helper 建立測試資料
    user_id = created["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200  # noqa: S101
```

## Mock 與外部服務測試

### Mock 外部 API
```python
@patch('app.weather.service.external_weather_api')
def test_weather_api_integration(mock_api: Mock) -> None:
    """Test weather API integration with mocked response."""
    mock_api.return_value = {"temperature": 25, "condition": "sunny"}
    # 測試實作
```

### LINE Bot Event 測試
```python
def test_handle_follow_event() -> None:
    """Test handling LINE follow event."""
    mock_event = FollowEvent(
        source={"type": "user", "userId": "test_user"},
        timestamp=1234567890
    )
    # 測試實作
```

## 異常處理測試

### 使用 pytest.raises
```python
def test_validate_location_input_invalid_length(self) -> None:
    """Test location input validation with invalid length."""
    with pytest.raises(LocationParseError) as exc_info:
        LocationService.validate_location_input("區")
    assert "輸入的字數不對" in exc_info.value.message
```

## 資料庫測試

### 使用內存資料庫
- 全域 conftest.py 已設定 SQLite 內存資料庫
- 每個測試使用乾淨的資料庫狀態

### Service Layer 測試
```python
def test_create_user_if_not_exists(session: Session) -> None:
    """Test user creation service logic."""
    line_user_id = "test_user_123"
    display_name = "Test User"

    user = create_user_if_not_exists(session, line_user_id, display_name)
    assert user.line_user_id == line_user_id
    assert user.display_name == display_name
```

## 測試文件與斷言

### Docstring 格式
```python
def test_webhook_invalid_signature(client: TestClient) -> None:
    """Test webhook with invalid LINE signature."""
    # 測試實作
```

### 斷言風格
- 使用 `assert` 而非 `self.assert*`
- 加上 `# noqa: S101` 避免 ruff 警告
- 斷言順序: 先檢查狀態碼，再檢查回應內容

## 測試覆蓋率目標

### 優先覆蓋範圍
1. **Service Layer**: 業務邏輯核心
2. **API Endpoints**: 所有 HTTP 介面
3. **Model Validation**: 資料驗證邏輯
4. **Error Handling**: 異常情況處理

### 覆蓋率檢查
```bash
# 執行測試並生成覆蓋率報告
uv run pytest --cov=app --cov-report=html

# 查看覆蓋率報告
open coverage_html_report/index.html
```

## 常見測試模式

### 1. 建立測試資料的 Helper Pattern
```python
@pytest.fixture()
def create_user(client: TestClient) -> Callable[..., dict]:
    """Return a helper for creating test users."""
    def _create(display_name: str = "Alice") -> dict:
        data = {"line_user_id": str(uuid4()), "display_name": display_name}
        response = client.post("/users", json=data)
        assert response.status_code == 201
        return response.json()
    return _create
```

### 2. 參數化測試
```python
@pytest.mark.parametrize("input_location,expected", [
    ("永和區", "永和區"),
    ("台北", "臺北"),
    (" 中山區 ", "中山區"),
])
def test_location_input_normalization(input_location: str, expected: str) -> None:
    """Test location input normalization."""
    result = LocationService.validate_location_input(input_location)
    assert result == expected
```

### 3. 類別化測試組織
```python
class TestLineWebhook:
    """Test LINE webhook endpoint."""

    def test_invalid_content_type(self, client: TestClient) -> None:
        """Test webhook with invalid content type."""
        # 測試實作

    def test_webhook_processing_error(self, client: TestClient) -> None:
        """Test webhook processing error handling."""
        # 測試實作
```

## 測試執行指導

### VS Code 整合
- 優先使用 `runTests` 工具進行測試
- 利用 VS Code Test Explorer 瀏覽和執行個別測試

### 命令列執行
```bash
# 執行全部測試
uv run pytest

# 執行特定模組測試
uv run pytest tests/user/

# 執行特定測試
uv run pytest tests/user/test_user.py::test_create_user

# 執行測試並顯示詳細輸出
uv run pytest -v
```

## 效能考量

### Fixture 設計原則
- 使用 module-level singleton 避免重複建立昂貴資源
- 範例: `_client = TestClient(app)` 在模組層級建立

### 測試隔離
- 每個測試應該獨立執行
- 避免測試間的狀態依賴
- 使用適當的 scope 管理 fixture 生命週期

---

**注意**: 這些指導原則基於 WeaMind 專案的實際測試實踐，遵循 pytest 最佳實踐與專案的編碼標準。
