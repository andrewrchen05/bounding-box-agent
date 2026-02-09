# Unit Tests

This directory contains unit tests for the tool-calling-from-scratch project.

## Structure

```
tests/
├── __init__.py                    # Package initialization
├── conftest.py                    # Shared pytest fixtures (used by both unit and integration tests)
├── unit/                          # Unit tests
│   ├── __init__.py
│   ├── test_draw_bounding_box.py       # Unit tests for DrawBoundingBox tool
│   └── test_detect_bounding_box.py    # Unit tests for DetectBoundingBox tool
├── integration/                   # Integration tests
│   ├── __init__.py
│   ├── conftest.py                # Integration test fixtures
│   └── test_agent_integration.py  # Agent integration tests
└── README.md                      # This file
```

## Test Organization

Tests are organized by component/module:

- **`test_draw_bounding_box.py`**: Comprehensive unit tests for the `DrawBoundingBox` tool, including:
  - Input/Output dataclass tests
  - Box parsing logic tests
  - Tool execution tests
  - Helper method tests (color conversion, path generation)

- **`test_detect_bounding_box.py`**: Unit tests for the `DetectBoundingBox` tool, including:
  - BoundingBox validation tests
  - JSON extraction tests
  - Tool execution tests with mocked model provider

- **`integration/test_agent_integration.py`**: Integration tests for the Agent orchestrating tool calls, including:
  - Single tool call flow
  - Tool chaining (detect → draw)
  - Multiple tools in single response
  - Multi-turn conversations
  - Error handling
  - Max iterations limit
  - Tool result formatting
  - Conversation history management

## Running Tests

**Note:** By default, pytest is configured to show verbose output (each test and its status). This is configured in `pytest.ini` at the project root.

### Run all tests:
```bash
python3 -m pytest tests/
```

### Run unit tests:
```bash
python3 -m pytest tests/unit/
```
This will show each test with its status (PASSED/FAILED) and progress percentage.

### Run specific test file:
```bash
python3 -m pytest tests/unit/test_draw_bounding_box.py
```

### Run integration tests:
```bash
python3 -m pytest tests/integration/
```

### Output Options

**Verbose (default):** Shows each test with status
```bash
python3 -m pytest tests/unit/ -v
```

**Very verbose:** Shows more details for each test
```bash
python3 -m pytest tests/unit/ -vv
```

**Quiet mode:** Minimal output (just summary)
```bash
python3 -m pytest tests/unit/ -q
```

**Show print statements:**
```bash
python3 -m pytest tests/unit/ -s
```

### Run with coverage:
```bash
python3 -m pytest tests/ --cov=tools --cov-report=html
```

### Run specific test class:
```bash
python3 -m pytest tests/unit/test_draw_bounding_box.py::TestDrawBoundingBoxInput
```

### Run specific test method:
```bash
python3 -m pytest tests/unit/test_draw_bounding_box.py::TestDrawBoundingBoxInput::test_from_dict_minimal
```

**Note:** If `pytest` is not in your PATH, use `python3 -m pytest` instead of just `pytest`.

## Test Fixtures

### Shared Fixtures (in `tests/conftest.py`)

These fixtures are available to both unit and integration tests:

- **`temp_dir`**: Creates a temporary directory that's automatically cleaned up
- **`test_image`**: Creates a simple 100x100 white test image
- **`test_image_large`**: Creates a larger 1920x1080 test image for coordinate scaling tests
- **`sample_boxes_list`**: Sample bounding boxes in list format
- **`sample_boxes_bbox_output`**: Sample bounding boxes in BoundingBoxOutput format
- **`sample_boxes_normalized`**: Sample bounding boxes with normalized coordinates

### Integration Test Fixtures (in `tests/integration/conftest.py`)

- **`mock_llm_provider`**: Mock LLM provider for controlling responses
- **`agent_with_tools`**: Agent instance with detect and draw tools
- **`agent_without_tools`**: Agent instance without tools

## Test Coverage

The unit tests cover:

1. **Input/Output Classes**:
   - Parsing from dictionaries
   - Type conversions
   - Serialization to dictionaries

2. **Box Parsing**:
   - List format (recommended)
   - BoundingBoxOutput format
   - Edge cases (missing fields, invalid formats)
   - Coordinate type conversions

3. **Tool Execution**:
   - Successful execution with various configurations
   - Error handling (missing parameters, invalid paths)
   - Output path generation
   - Multiple boxes
   - Normalized vs pixel coordinates

4. **Helper Methods**:
   - Color conversion (names, hex codes, short hex)
   - Output path generation
   - Edge cases

## Writing New Tests

When adding new tests:

1. **Use fixtures**: Leverage shared fixtures from `conftest.py` to avoid code duplication
2. **Follow naming**: Test classes should start with `Test` and test methods should start with `test_`
3. **Add docstrings**: Include descriptive docstrings for test methods
4. **Test edge cases**: Include tests for error conditions and edge cases
5. **Keep tests isolated**: Each test should be independent and not rely on other tests

## Example Test Structure

```python
class TestMyComponent:
    """Test description."""
    
    @pytest.fixture
    def component(self):
        """Create component instance for testing."""
        return MyComponent()
    
    def test_basic_functionality(self, component):
        """Test basic functionality."""
        result = component.do_something()
        assert result == expected_value
    
    def test_error_handling(self, component):
        """Test error handling."""
        with pytest.raises(ValueError, match="expected error message"):
            component.do_something_invalid()
```

## Test Types

### Unit Tests
Unit tests verify individual components in isolation:
- Test individual tools with mocked dependencies
- Test dataclasses and parsing logic
- Fast execution, no external dependencies

### Integration Tests
Integration tests verify multiple components working together:
- Test agent orchestrating tool calls
- Test tool chaining workflows
- Test conversation flow and context
- Mock LLM provider to control responses

## Future Test Files

As the project grows, additional test files can be added:

- `test_agent.py`: Additional unit tests for agent logic
- `test_providers.py`: Tests for model providers
- `test_tool.py`: Tests for the base Tool class
