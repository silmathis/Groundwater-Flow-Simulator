from Simulator.backend.simulation_service import build_model_from_config, run_simulation


def _base_config():
    return {
        "nx": 12,
        "ny": 10,
        "aquifer_thickness": 8.0,
        "corner_tl": 9.0,
        "corner_tr": 6.0,
        "corner_bl": 3.0,
        "corner_br": 1.0,
        "point_sources": [
            {"x": 2, "y": 2, "h": 11.0},
            {"x": 5, "y": 6, "h": 7.5},
        ],
        "background_k": 0.5,
        "conductivity_mode": "Heterogeneous medium with zone",
        "zone_x_min": 3,
        "zone_x_max": 7,
        "zone_y_min": 1,
        "zone_y_max": 4,
        "selected_k": 4.0,
        "recharge_x_min": 4,
        "recharge_x_max": 6,
        "recharge_y_min": 2,
        "recharge_y_max": 5,
        "recharge_rate": 0.02,
        "iterations": 25,
        "tolerance": 1e-5,
    }


def test_build_model_from_config_applies_core_settings():
    # Check that config values are correctly copied into the model.
    config = _base_config()
    model = build_model_from_config(config)

    assert model.nx == 12
    assert model.ny == 10
    assert model.aquifer_thickness == 8.0

    assert model.use_corner_boundary is True
    assert model.head_top_left == 9.0
    assert model.head_top_right == 6.0
    assert model.head_bottom_left == 3.0
    assert model.head_bottom_right == 1.0

    assert model.point_sources[0] == (2, 2, 11.0)
    assert model.point_sources[1] == (5, 6, 7.5)

    assert model.hydraulic_conductivity[0, 0] == 0.5
    assert model.hydraulic_conductivity[2, 4] == 4.0
    assert model.recharge[3, 5] == 0.02


def test_build_model_caps_point_sources_to_model_limit():
    # Check that only the maximum allowed number of point sources is kept.
    config = _base_config()
    config["point_sources"] = [
        {"x": i % config["nx"], "y": i % config["ny"], "h": float(i)} for i in range(10)
    ]

    model = build_model_from_config(config)
    active = [src for src in model.point_sources if src is not None]

    assert len(active) == model.max_point_sources
    assert active[0] == (0, 0, 0.0)
    assert active[-1] == (5, 5, 5.0)


def test_run_simulation_returns_serializable_arrays_and_summary():
    # Check that simulation output has serializable arrays and a valid summary.
    config = _base_config()

    result = run_simulation(config)

    assert set(result.keys()) == {
        "model",
        "head",
        "qx",
        "qy",
        "q_mag",
        "hydraulic_conductivity",
        "recharge",
        "summary",
    }

    head = result["head"]
    qx = result["qx"]
    qy = result["qy"]
    q_mag = result["q_mag"]

    assert isinstance(head, list)
    assert isinstance(head[0], list)
    assert len(head) == config["ny"]
    assert len(head[0]) == config["nx"]

    assert len(qx) == config["ny"] and len(qx[0]) == config["nx"]
    assert len(qy) == config["ny"] and len(qy[0]) == config["nx"]
    assert len(q_mag) == config["ny"] and len(q_mag[0]) == config["nx"]

    summary = result["summary"]
    assert "head_min" in summary and "head_max" in summary
    assert summary["head_min"] <= summary["head_max"]
