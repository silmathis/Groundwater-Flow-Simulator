# Documentation

## Structure

- **Groundwater_concept.md** — Educational overview of groundwater flow principles and the model's physical basis.
- **API.md** — Public API reference for `GroundwaterModel` and `simulation_service`.
- **ARCHITECTURE.md** — System design and module responsibilities.

## Getting Started

See [../README.md](../README.md) for quickstart and installation.

## Physical Model

The simulator solves the steady-state 2D flow equation:

$$\nabla \cdot (K \nabla h) + R = 0$$

where:
- $h$ is hydraulic head (m)
- $K$ is hydraulic conductivity (m/day)
- $R$ is recharge rate (m/day)

## Implementation

**Solver**: Iterative relaxation (Gauss-Seidel) on finite difference grid.

**Boundary conditions**: Fixed-head (Dirichlet) at edges; fixed-head point sources in domain.

See `Simulator/groundwater_model.py` for details.
