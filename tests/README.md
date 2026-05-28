# Unit Tests

This directory contains unit tests for the Groundwater Simulator core modules.

## Running Tests

```bash
pytest -q
```

Or with verbosity:
```bash
pytest -v
```

## Test Coverage

- **test_groundwater_model.py** — Tests for `GroundwaterModel` initialization, boundary conditions, and solver correctness.

## Adding Tests

New tests should:
1. Use pytest conventions (`test_*.py`, `def test_*()`)
2. Test a single responsibility (unit tests, not integration)
3. Be fast (< 1 second per test)
4. Include docstrings explaining what is tested

## CI Integration

Tests run automatically on every push to `main` and `Silas` via GitHub Actions (`.github/workflows/ci.yml`).
