---
applyTo: 'tests/**/test_*.py'
---

# WeaMind Testing Functions Guidelines

## Test File Structure
- Keep test file structure consistent with `app/` directory structure
- Test file naming: `test_<module_name>.py`

## Test Class Organization

### Class Naming and Structure
```python
class TestLocationService:
    """Test cases for LocationService class."""

    def test_validate_location_input_valid(self) -> None:
        """Test valid location input validation."""
        # Test implementation
```

### Test Method Naming Pattern
- `test_<method_name>_<scenario>`
- Examples: `test_validate_location_input_valid`, `test_create_user_duplicate_line_id`

## Variable Naming in Tests
- Use descriptive names: `payload`, `response_body`, `created_user`
- Avoid generic terms: `data`, `result`, `response`
- Be specific: `expected_location` not `expected`

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

## Assertion Style
- Use `assert` instead of `self.assert*`
- Add `# noqa: S101` to avoid ruff warnings
- Assertion order: Check status code first, then response content

## Exception Testing
```python
def test_validate_location_input_invalid_length(self) -> None:
    """Test location input validation with invalid length."""
    with pytest.raises(LocationParseError) as exc_info:
        LocationService.validate_location_input("區")
    assert "輸入的字數不對" in exc_info.value.message
```

## Mock Testing
```python
@patch('app.weather.service.external_weather_api')
def test_weather_api_integration(mock_weather_api: Mock) -> None:
    """Test weather API integration with mocked response."""
    mock_weather_api.return_value = {"temperature": 25, "condition": "sunny"}
    # Test implementation
```

## Parameterized Testing
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
