# Unit Tests

This directory contains unit tests for the Groundwater Simulator core modules.

## Running Tests

`pytest.ini` is stored in this `tests/` folder.
When running from the repository root, use:

```bash
pytest -c tests/pytest.ini -q
```

Or with verbosity:
```bash
pytest -c tests/pytest.ini -v
```

## Test Coverage

- **test_groundwater_model.py** — Tests for `GroundwaterModel` initialization, boundary conditions, and solver correctness.
- **test_simulation_service.py** — Tests for backend config mapping and simulation result payload structure.

