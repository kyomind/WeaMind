---
applyTo: 'tests/**/*.py'
---

# WeaMind Testing Guidelines

## Test File Structure and Organization

### File Structure Mapping
- Keep test file structure consistent with `app/` directory structure
- Test file naming: `test_<module_name>.py`
- Create corresponding `conftest.py` for each module to store dedicated fixtures

```
tests/
├── conftest.py              # Global fixtures
├── core/
│   ├── conftest.py         # Core module specific fixtures
│   └── test_*.py
├── user/
│   ├── conftest.py         # User module specific fixtures
│   └── test_user.py
└── <module>/
    ├── conftest.py
    └── test_*.py
```

## Pytest Fixtures Naming Conventions

### Helper Functions (Verb prefix)
```python
@pytest.fixture()
def create_user() -> Callable[..., dict]:
    """Return a helper for creating test users."""
    def _create(display_name: str = "Alice") -> dict:
        # Implementation
        return created_user
    return _create

@pytest.fixture()
def setup_mock_weather_api() -> Generator[Mock, None, None]:
    """Setup and teardown mock weather API."""
    # Implementation
```

### Objects/Values (Noun)
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

## Test Class Organization

### Class Naming and Structure
```python
class TestLocationService:
    """Test cases for LocationService class."""

    def test_validate_location_input_valid(self) -> None:
        """Test valid location input validation."""
        # Test implementation

    def test_validate_location_input_invalid_length(self) -> None:
        """Test location input validation with invalid length."""
        # Test implementation
```

### Test Method Naming Pattern
- `test_<method_name>_<scenario>`
- Examples: `test_validate_location_input_valid`, `test_create_user_duplicate_line_id`

## API Testing Best Practices

### HTTP Status Code Validation
```python
def test_create_user(client: TestClient) -> None:
    """Create a new user."""
    payload = {"line_user_id": str(uuid4()), "display_name": "Alice"}
    response = client.post("/users", json=payload)
    assert response.status_code == 201  # noqa: S101
    response_body = response.json()
    assert response_body["line_user_id"] == payload["line_user_id"]  # noqa: S101
```

### Using Helper Fixtures
```python
def test_get_user(create_user: Callable[..., dict], client: TestClient) -> None:
    """Retrieve an existing user."""
    created_user = create_user()  # Use helper to create test data
    user_id = created_user["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200  # noqa: S101
```

## Mock and External Service Testing

### Mock External APIs
```python
@patch('app.weather.service.external_weather_api')
def test_weather_api_integration(mock_weather_api: Mock) -> None:
    """Test weather API integration with mocked response."""
    mock_weather_api.return_value = {"temperature": 25, "condition": "sunny"}
    # Test implementation
```

### LINE Bot Event Testing
```python
def test_handle_follow_event() -> None:
    """Test handling LINE follow event."""
    follow_event = FollowEvent(
        source={"type": "user", "userId": "test_user"},
        timestamp=1234567890
    )
    # Test implementation
```

## Exception Handling Testing

### Using pytest.raises
```python
def test_validate_location_input_invalid_length(self) -> None:
    """Test location input validation with invalid length."""
    with pytest.raises(LocationParseError) as exc_info:
        LocationService.validate_location_input("區")
    assert "輸入的字數不對" in exc_info.value.message
```

## Database Testing

### Using In-Memory Database
- Global conftest.py has configured SQLite in-memory database
- Each test uses clean database state

### Service Layer Testing
```python
def test_create_user_if_not_exists(session: Session) -> None:
    """Test user creation service logic."""
    line_user_id = "test_user_123"
    display_name = "Test User"

    created_user = create_user_if_not_exists(session, line_user_id, display_name)
    assert created_user.line_user_id == line_user_id
    assert created_user.display_name == display_name
```

## Test Documentation and Assertions

### Docstring Format
```python
def test_webhook_invalid_signature(client: TestClient) -> None:
    """Test webhook with invalid LINE signature."""
    # Test implementation
```

### Assertion Style
- Use `assert` instead of `self.assert*`
- Add `# noqa: S101` to avoid ruff warnings
- Assertion order: Check status code first, then response content

## Test Coverage Goals

### Priority Coverage Areas
1. **Service Layer**: Core business logic
2. **API Endpoints**: All HTTP interfaces
3. **Model Validation**: Data validation logic
4. **Error Handling**: Exception scenarios

### Coverage Checking
```bash
# Run tests and generate coverage report
uv run pytest --cov=app --cov-report=html

# View coverage report
open coverage_html_report/index.html
```

## Common Testing Patterns

### 1. Test Data Creation Helper Pattern
```python
@pytest.fixture()
def create_user(client: TestClient) -> Callable[..., dict]:
    """Return a helper for creating test users."""
    def _create(display_name: str = "Alice") -> dict:
        payload = {"line_user_id": str(uuid4()), "display_name": display_name}
        response = client.post("/users", json=payload)
        assert response.status_code == 201
        return response.json()
    return _create
```

### 2. Parameterized Testing
```python
@pytest.mark.parametrize("input_location,expected_location", [
    ("永和區", "永和區"),
    ("台北", "臺北"),
    (" 中山區 ", "中山區"),
])
def test_location_input_normalization(input_location: str, expected_location: str) -> None:
    """Test location input normalization."""
    normalized_location = LocationService.validate_location_input(input_location)
    assert normalized_location == expected_location
```

### 3. Class-based Test Organization
```python
class TestLineWebhook:
    """Test LINE webhook endpoint."""

    def test_invalid_content_type(self, client: TestClient) -> None:
        """Test webhook with invalid content type."""
        # Test implementation

    def test_webhook_processing_error(self, client: TestClient) -> None:
        """Test webhook processing error handling."""
        # Test implementation
```

## Test Execution Guidelines

### VS Code Integration
- Prefer using `runTests` tool for testing
- Utilize VS Code Test Explorer to browse and execute individual tests

### Command Line Execution
```bash
# Run all tests
uv run pytest

# Run specific module tests
uv run pytest tests/user/

# Run specific test
uv run pytest tests/user/test_user.py::test_create_user

# Run tests with verbose output
uv run pytest -v
```

## Performance Considerations

### Fixture Design Principles
- Use module-level singleton to avoid recreating expensive resources
- Example: `_client = TestClient(app)` created at module level

### Test Isolation
- Each test should run independently
- Avoid state dependencies between tests
- Use appropriate scope to manage fixture lifecycle

---

**Note**: These guidelines are based on WeaMind project's actual testing practices, following pytest best practices and project coding standards.
