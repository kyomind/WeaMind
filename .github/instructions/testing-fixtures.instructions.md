---
applyTo: 'tests/**/conftest.py'
---

# WeaMind Testing Fixtures Guidelines

## Pytest Fixtures Naming Conventions

### Helper Functions (Verb prefix)
```python
@pytest.fixture()
def create_user() -> Callable[..., dict]:
    """Return a helper for creating test users."""
    def _create(display_name: str = "Alice") -> dict:
        payload = {"line_user_id": str(uuid4()), "display_name": display_name}
        response = client.post("/users", json=payload)
        assert response.status_code == 201
        return response.json()
    return _create

@pytest.fixture()
def setup_mock_weather_api() -> Generator[Mock, None, None]:
    """Setup and teardown mock weather API."""
    with patch('app.weather.service.external_weather_api') as mock_api:
        mock_api.return_value = {"temperature": 25, "condition": "sunny"}
        yield mock_api
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

## Fixture Organization

### File Structure
- Keep fixture files structured to mirror `app/` directory
- Global fixtures in `tests/conftest.py`
- Module-specific fixtures in `tests/<module>/conftest.py`

### Performance Considerations
- Use module-level singleton for expensive resources
- Example: `_client = TestClient(app)` created at module level
- Use appropriate scope to manage fixture lifecycle

### Naming Guidelines
- Use descriptive names, avoid generic terms like `data`, `result`
- Helper functions: verb prefix (`create_`, `setup_`, `build_`)
- Objects/values: noun (`user`, `client`, `weather_data`)
