from typing import Dict, Any

from Simulator.groundwater_model import GroundwaterModel


def run_simulation(config: Dict[str, Any]) -> Dict[str, Any]:
    """Run one groundwater simulation and return data for the frontend."""
    model = GroundwaterModel(
        nx=config["nx"],
        ny=config["ny"],
        aquifer_thickness=float(config.get("aquifer_thickness", 10.0)),
    )

    # Use corner-defined boundary conditions only (top-left, top-right, bottom-left, bottom-right).
    # This replaces the previous scalar-per-side API.
    if any(k in config for k in ("corner_tl", "corner_tr", "corner_bl", "corner_br")):
        model.use_corner_boundary = True
        model.head_top_left = float(config.get("corner_tl", 10.0))
        model.head_top_right = float(config.get("corner_tr", 10.0))
        model.head_bottom_left = float(config.get("corner_bl", 5.0))
        model.head_bottom_right = float(config.get("corner_br", 5.0))

    # Apply fixed-head point sources (up to model.max_point_sources).
    for idx, source in enumerate(config.get("point_sources", [])[: model.max_point_sources], start=1):
        model.set_point_source(idx, source["x"], source["y"], source["h"])

    model.set_background_conductivity(config["background_k"])

    if config["conductivity_mode"] == "Heterogeneous medium with zone":
        model.set_zone(
            config["zone_x_min"],
            config["zone_x_max"],
            config["zone_y_min"],
            config["zone_y_max"],
            config["selected_k"],
        )

    model.set_recharge(
        config["recharge_x_min"],
        config["recharge_x_max"],
        config["recharge_y_min"],
        config["recharge_y_max"],
        config["recharge_rate"],
    )

    model.solve(iterations=config["iterations"], tolerance=config["tolerance"])
    qx, qy, q_mag = model.compute_flow()

    return {
        "model": model,
        "qx": qx,
        "qy": qy,
        "q_mag": q_mag,
        "summary": model.get_summary(),
    }
