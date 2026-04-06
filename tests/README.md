# Test Suite for things_sentiment_poller

This directory contains the pytest-based test suite for the `things_sentiment_poller` module.

## Structure

```
tests/
├── conftest.py           # Shared fixtures and test configuration
├── fixtures/             # Reusable test data generators
│   ├── demo_tasks.py    # Deterministic demo task generation with seeds
│   └── __init__.py
├── integration/          # Integration tests (CLI, full workflow)
│   ├── test_poller_cli.py
│   └── __init__.py
├── unit/                 # Unit tests for individual functions
│   ├── test_poller_core.py      # Emotion mapping, intensity, sentiment
│   ├── test_poller_state.py     # State persistence, duplicate detection
│   └── __init__.py
└── README.md            # This file
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit -v

# Run only integration tests
pytest tests/integration -v

# Run with coverage
pytest tests/ --cov=things_sentiment_poller --cov-report=html

# Run tests matching a specific marker
pytest tests/ -m "unit" -v
```

## Fixtures

### Core Fixtures (conftest.py)

- **`temp_dir`**: Temporary directory for file I/O tests
- **`sample_task`**: Minimal valid task dictionary
- **`sample_tasks(count)`**: Generate multiple tasks
- **`memory_file` / `state_file`**: Paths in temp directory
- **`empty_memory`**: Fresh memory structure
- **`emotion_boundary_tasks`**: Tasks designed to hit emotion/intensity boundaries

### Demo Task Fixtures (fixtures/demo_tasks.py)

- **`generate_demo_tasks(seed, count, base_time)`**: Deterministic task generator for reproducible tests
- **`generate_boundary_task(now, task_type)`**: Create boundary condition tasks (exact thresholds)

## Test Coverage Areas

### Unit Tests

1. **IsoToDatetime**: ISO8601 parsing edge cases
2. **MapToEmotion**: All emotion mappings, tag priority, fallbacks
3. **CalculateIntensity**: Intensity values for each emotion type
4. **DetermineSentiment**: Sentiment polarity, threshold boundaries
5. **UpdateStats**: Counter increments and unknown sentiment handling
6. **Boundary Conditions**: Edge cases, threshold boundaries, empty/missing fields
7. **State Management**: State file I/O, partial updates
8. **Duplicate Detection**: Skipping `last_task_id` logic
9. **Memory Structure**: Defaults and existing data loading

### Integration Tests

1. **CLI Flags**: `--now` override for deterministic time injection (pending poller implementation)
2. **Demo Mode**: `--seed` reproducibility (pending implementation)
3. **Duplicate Detection**: State persistence across runs (pending integration)
4. **Intensity Thresholds**: Configurable threshold verification
5. **Boundary Conditions**: Exact threshold edge cases
6. **Verify Mode**: `--verify` flag validation-only (pending)

## Expected Poller Enhancements

The following features are required for full test coverage:

- [x] Test suite structure ✓
- [ ] `--now` parameter to override current time (ISO8601 string)
- [ ] `--seed` parameter for reproducible demo task generation
- [ ] `--verify` flag to validate memory without polling
- [ ] Intensity thresholds as configurable constants (currently hardcoded)
- [ ] Improved duplicate detection using persisted `poller_state.json` (partially implemented)

## Writing New Tests

1. Place unit tests in `tests/unit/` that test single functions/classes
2. Place integration tests in `tests/integration/` that test full workflows
3. Use fixtures from `conftest.py` to avoid duplication
4. Mark tests appropriately:
   ```python
   @pytest.mark.unit
   def test_something():
       ...
   ```

5. For tests requiring realistic task data, use `fixtures.demo_tasks.generate_demo_tasks()`

## Notes

- All tests should be deterministic (no reliance on actual `datetime.now()` without `--now` override)
- File I/O should use `temp_dir` fixture to avoid polluting workspace
- Mock external dependencies (e.g., Things CLI) using `monkeypatch` when needed
- The poller's `main()` function is difficult to test directly; consider extracting core logic into testable functions with injectable dependencies
