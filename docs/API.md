# API Reference

## `Simulator.groundwater_model.GroundwaterModel`

Main solver class for 2D groundwater flow.

### Constructor
```python
GroundwaterModel(nx: int = 50, ny: int = 50, cell_size: float = 10.0,
                 relaxation_factor: float = 1.0, aquifer_thickness: float = 10.0)
```

### Key Methods

**`solve(iterations: int = 100, tolerance: float = 1e-3)`**  
Solve the steady-state flow equation using iterative relaxation.

**`set_background_conductivity(conductivity: float)`**  
Set uniform hydraulic conductivity across the domain.

**`set_zone(x_min: int, x_max: int, y_min: int, y_max: int, conductivity: float)`**  
Define a rectangular zone with different conductivity.

**`set_point_source(source_num: int, x: int, y: int, head_value: float)`**  
Set a fixed-head point source (1 to max_point_sources=6).

**`set_recharge(x_min: int, x_max: int, y_min: int, y_max: int, rate: float)`**  
Define recharge (infiltration) in a rectangular zone.

**`compute_flow() -> Tuple[np.ndarray, np.ndarray, np.ndarray]`**  
Compute specific discharge components (qx, qy) and magnitude q_mag from the solved head field.

**`get_summary() -> Dict[str, float]`**  
Return head/flow statistics: head_min, head_max, head_mean, flow_min, flow_max, flow_mean.

### Boundary Conditions

**Corner-based**: Set `use_corner_boundary=True` and define `head_top_left`, `head_top_right`, `head_bottom_left`, `head_bottom_right`. Edges are interpolated linearly.

## `Simulator.backend.simulation_service`

**`run_simulation(config: Dict[str, Any]) -> Dict[str, Any]`**

Execute a complete groundwater simulation. The config dict should contain:
- `nx`, `ny`: Grid dimensions
- `corner_tl`, `corner_tr`, `corner_bl`, `corner_br`: Boundary head values
- `background_k`: Conductivity (m/day)
- `point_sources`: List of dicts `{"x": int, "y": int, "h": float}`
- `conductivity_mode`, `zone_x_min`, `zone_x_max`, `zone_y_min`, `zone_y_max`, `selected_k`: Zone config
- `recharge_rate`, `recharge_x_min`, `recharge_x_max`, `recharge_y_min`, `recharge_y_max`: Recharge config
- `iterations`, `tolerance`: Solver parameters
- `aquifer_thickness`: Confined aquifer thickness (m)

Returns a dict with:
- `model`: The GroundwaterModel instance (live object)
- `head`, `qx`, `qy`, `q_mag`: Serializable lists of results
- `hydraulic_conductivity`, `recharge`: Serializable lists of parameters
- `summary`: Dict of statistics
