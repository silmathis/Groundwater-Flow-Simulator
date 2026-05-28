import numpy as np
import pytest
from Simulator.groundwater_model import GroundwaterModel


def test_initialization_and_boundary():
    # Check that the model starts with the expected grid size and array shapes.
    m = GroundwaterModel(nx=10, ny=8, cell_size=1.0)
    assert m.nx == 10 and m.ny == 8
    # default conductivity shape
    assert m.hydraulic_conductivity.shape == (8, 10)
    assert m.recharge.shape == (8, 10)
    assert m.head.shape == (8, 10)


def test_invalid_aquifer_thickness_raises():
    # Check that invalid aquifer thickness values are rejected.
    with pytest.raises(ValueError, match="aquifer_thickness"):
        GroundwaterModel(aquifer_thickness=0)


def test_corner_boundary_requires_all_corners():
    # Check that corner-boundary mode fails if one corner value is missing.
    m = GroundwaterModel(nx=8, ny=8)
    m.use_corner_boundary = True
    m.head_top_left = 10.0
    m.head_top_right = 8.0
    m.head_bottom_left = 2.0

    with pytest.raises(ValueError, match="corner values"):
        m.prepare_initial_state()


def test_corner_boundary_interpolation_on_edges():
    # Check that edge head values are correctly linearly interpolated from corners.
    m = GroundwaterModel(nx=6, ny=5)
    m.use_corner_boundary = True
    m.head_top_left = 10.0
    m.head_top_right = 4.0
    m.head_bottom_left = 2.0
    m.head_bottom_right = 8.0

    m.prepare_initial_state()

    assert np.allclose(m.head[-1, :], np.linspace(10.0, 4.0, 6))
    assert np.allclose(m.head[0, :], np.linspace(2.0, 8.0, 6))
    assert np.allclose(m.head[:, 0], np.linspace(2.0, 10.0, 5))
    assert np.allclose(m.head[:, -1], np.linspace(8.0, 4.0, 5))


def test_set_and_clear_point_source_and_index_validation():
    # Check point source index validation and that setting/clearing works.
    m = GroundwaterModel(nx=10, ny=10)

    with pytest.raises(ValueError, match="source_num"):
        m.set_point_source(0, 3, 3, 12.0)
    with pytest.raises(ValueError, match="source_num"):
        m.clear_point_source(7)

    m.set_point_source(1, 3, 4, 12.5)
    m.prepare_initial_state()
    assert m.head[4, 3] == pytest.approx(12.5)

    m.clear_point_source(1)
    m.prepare_initial_state()
    assert m.head[4, 3] == pytest.approx(0.0)


def test_solve_keeps_point_source_head_fixed():
    # Check that a fixed-head point source keeps its value during solving.
    m = GroundwaterModel(nx=20, ny=20, cell_size=1.0)
    m.set_background_conductivity(1.0)
    m.set_point_source(1, 10, 10, 17.0)

    m.solve(iterations=120, tolerance=1e-8)

    assert m.head[10, 10] == pytest.approx(17.0)


def test_zero_forcing_stays_zero_field():
    # Check that with no recharge and no forcing, the head stays at zero.
    m = GroundwaterModel(nx=12, ny=12, cell_size=1.0)
    m.set_background_conductivity(1.0)

    m.solve(iterations=40, tolerance=1e-10)

    assert np.allclose(m.head, 0.0)


def test_progress_callback_emits_start_and_completion():
    # Check that progress callback is called at start and ends with done=True.
    m = GroundwaterModel(nx=10, ny=10, cell_size=1.0)
    calls = []

    def cb(iteration, head, done):
        calls.append((iteration, np.asarray(head).shape, done))

    m.solve(iterations=7, tolerance=0.0, progress_callback=cb, progress_interval=2)

    assert len(calls) >= 2
    assert calls[0][0] == 0
    assert calls[0][1] == (10, 10)
    assert calls[0][2] is False
    assert calls[-1][2] is True


def test_compute_flow_is_zero_for_flat_head():
    # Check that a flat head field produces zero flow everywhere.
    m = GroundwaterModel(nx=9, ny=7, cell_size=2.0)
    m.head[:, :] = 3.0

    qx, qy, qmag = m.compute_flow()

    assert np.allclose(qx, 0.0)
    assert np.allclose(qy, 0.0)
    assert np.allclose(qmag, 0.0)


def test_get_summary_returns_expected_keys():
    # Check that summary contains expected fields and values for a flat field.
    m = GroundwaterModel(nx=6, ny=6)
    m.head[:, :] = 2.5

    summary = m.get_summary()

    assert set(summary.keys()) == {
        "head_min",
        "head_max",
        "head_mean",
        "flow_min",
        "flow_max",
        "flow_mean",
    }
    assert summary["head_min"] == pytest.approx(2.5)
    assert summary["head_max"] == pytest.approx(2.5)
    assert summary["head_mean"] == pytest.approx(2.5)
    assert summary["flow_max"] == pytest.approx(0.0)


def test_corner_boundary_and_solve():
    # Check that solved heads stay within the min/max values set at corners.
    m = GroundwaterModel(nx=12, ny=12, cell_size=1.0)
    m.use_corner_boundary = True
    m.head_top_left = 10.0
    m.head_top_right = 5.0
    m.head_bottom_left = 0.0
    m.head_bottom_right = 0.0

    m.solve(iterations=200, tolerance=1e-6)

    summary = m.get_summary()
    # head range must be within the provided corner bounds
    assert summary["head_min"] >= 0.0 - 1e-8
    assert summary["head_max"] <= 10.0 + 1e-8
    # shapes remain consistent
    assert m.head.shape == (12, 12)
