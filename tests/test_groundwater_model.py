import numpy as np
from Simulator.groundwater_model import GroundwaterModel


def test_initialization_and_boundary():
    m = GroundwaterModel(nx=10, ny=8, cell_size=1.0)
    assert m.nx == 10 and m.ny == 8
    # default conductivity shape
    assert m.hydraulic_conductivity.shape == (8, 10)


def test_corner_boundary_and_solve():
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
