# Architecture

## Project Structure

```
app.py                         Streamlit app entrypoint
Simulator/                      Main package
├── __init__.py
├── groundwater_model.py        Core solver (`GroundwaterModel`)
├── backend/
│   ├── __init__.py
│   └── simulation_service.py   Orchestrator: prepares config, runs model, returns serializable results
└── frontend/
    ├── __init__.py
    └── streamlit_app.py       Interactive web UI (Streamlit) — imports `simulation_service`

tests/
├── pytest.ini
├── test_groundwater_model.py
├── test_simulation_service.py

examples/
├── local_test_app.py
├── local_test_app2.py
└── README.md

docs/
├── README.md
├── ARCHITECTURE.md
├── API.md
└── Groundwater_concept.md

pyproject.toml
requirements.txt
README.md
```

## Data Flow

1. **UI** (`app.py` / `streamlit_app.py`): User sets parameters → configuration dictionary
2. **Service** (`simulation_service.py`): Validates/normalizes config → creates `GroundwaterModel` → calls `solve()` → packages results
3. **Core** (`groundwater_model.py`): Discretization, iterative solver, flow computation (`compute_flow()`)
4. **Presentation**: UI consumes results (head field, qx/qy, magnitudes) and visualizes them
5. **Examples & Tests**: `examples/` contain minimal usage scripts; `tests/` verify correctness

## Key Design Principles

- **Modularity:** Core solver is independent from Streamlit UI and can be imported by other scripts or services.
- **Clarity / Education:** Numerical methods are implemented in plain Python/NumPy for readability and teaching purposes.
- **Backward compatibility:** `GroundwaterModel` aims to keep a simple API so examples/tests remain usable.
- **Testability:** Unit tests cover core math and the simulation service; avoid side effects in the model core.