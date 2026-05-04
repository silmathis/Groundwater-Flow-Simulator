from typing import Dict, Any

from my_project.groundwater_model import GroundwaterModel


def run_simulation(config: Dict[str, Any]) -> Dict[str, Any]:
    """Run one groundwater simulation and return data for the frontend."""
    model = GroundwaterModel(nx=config["nx"], ny=config["ny"])

    model.head_north = config["head_north"]
    model.head_south = config["head_south"]
    model.head_west = config["head_west"]
    model.head_east = config["head_east"]

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
