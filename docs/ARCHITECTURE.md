# Architecture

## Project Structure

```
Simulator/              Main package
├── __init__.py
├── groundwater_model.py     Core solver (GroundwaterModel class)
├── backend/
│   ├── __init__.py
│   └── simulation_service.py   Run-simulation orchestrator (returns serializable results)
└── frontend/
    ├── __init__.py
    └── streamlit_app.py    Interactive web UI (Streamlit)

tests/
├── test_groundwater_model.py   Unit tests for solver

examples/
├── local_test_app.py    Standalone Matplotlib example (homogeneous domain)
├── local_test_app2.py   Standalone Matplotlib example (with point sources)
└── README.md

docs/
├── README.md            Documentation overview
├── API.md              Public API reference
├── Groundwater_concept.md   Educational background

.github/workflows/
└── ci.yml              GitHub Actions: tests + linting
```

## Data Flow

1. **Frontend** (`streamlit_app.py`): User input → config dict
2. **Backend** (`simulation_service.py`): config → GroundwaterModel instance → solve → return results
3. **Core** (`groundwater_model.py`): Discretization, solver, flow computation
4. **Tests** (`test_groundwater_model.py`): Unit tests for core solver
5. **Examples** (`local_test_app.py`, `local_test_app2.py`): Standalone scripts for demonstration/validation

## Key Design Principles

- **Modularity**: Core model is independent of UI; can be imported/reused.
- **Serialization**: `simulation_service` returns plain Python lists/dicts alongside the model object for safe data transfer.
- **Education**: Model uses explicit finite differences (loops) for clarity; advanced backends (sparse solvers) can coexist.
- **Testability**: Core solver is pure Python/NumPy; no Streamlit or file I/O in `GroundwaterModel`.

## Future Enhancements

- [ ] SciPy sparse solver backend for large grids
- [ ] Time-dependent (transient) flow
- [ ] Particle tracking / pathline visualization
- [ ] Unsaturated zone (vadose) modeling
- [ ] Performance profiling and benchmarking suite
