# Changelog

## v0.1.0 (2026-05-27)

### Added
- Unit tests for `GroundwaterModel` core solver
- GitHub Actions CI workflow (pytest + ruff)
- Serializable outputs in `simulation_service` (head, qx, qy, q_mag, conductivity, recharge as lists)
- LICENSE (MIT)
- CONTRIBUTING.md guidelines
- requirements-dev.txt for development tools
- Comprehensive docs: API.md, ARCHITECTURE.md

### Fixed
- Fixed package import mismatch (`my_project` → `Simulator`)
- Resolved merge conflict in streamlit_app.py

### Changed
- Reorganized local test apps from `tests/` to `examples/`
- Enhanced simulation_service to return both live model object (backward compat) and serializable arrays (forward compat)

### Improved
- Project structure clarity and documentation
- Added reproducibility via CI and lockfile guidance

---

## Known Issues / Limitations

- Solver uses explicit Python loops (slow for large grids); SciPy sparse backend recommended for production.
- Visualizations lack colorblind-safe palettes and export options.
- No transient/time-dependent simulation.
