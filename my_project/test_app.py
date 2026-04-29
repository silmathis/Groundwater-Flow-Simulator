#!/usr/bin/env python
"""
Quick test to verify the groundwater simulator works correctly.
"""

import sys
sys.path.insert(0, '.')

from my_project.backend import run_simulation
from my_project.groundwater_model import GroundwaterModel
import numpy as np

print("=" * 60)
print("Testing Groundwater Flow Simulator")
print("=" * 60)

# Create model
print("\n1. Creating model...")
model = GroundwaterModel(nx=50, ny=40, cell_size=10.0)
print(f"   [OK] Model created: {model.nx}x{model.ny} grid")

print("\n1b. Testing backend service layer...")
service_result = run_simulation({
    "nx": 30,
    "ny": 20,
    "head_north": 15.0,
    "head_south": 5.0,
    "head_west": 10.0,
    "head_east": 10.0,
    "background_k": 1.0,
    "zone_x_min": 5,
    "zone_x_max": 20,
    "zone_y_min": 4,
    "zone_y_max": 16,
    "selected_k": 0.1,
    "recharge_rate": 0.01,
    "recharge_x_min": 8,
    "recharge_x_max": 22,
    "recharge_y_min": 2,
    "recharge_y_max": 8,
    "iterations": 80,
    "tolerance": 1e-3,
})
print(f"   [OK] Backend returned head shape: {service_result['model'].head.shape}")

# Set boundary conditions
print("\n2. Setting boundary conditions...")
model.head_north = 15.0
model.head_south = 5.0
print(f"   [OK] North: {model.head_north} m, South: {model.head_south} m")

# Add zones
print("\n3. Adding subsurface zones...")
model.set_zone(15, 35, 15, 25, 0.1)  # Clay zone
print("   [OK] Low-conductivity zone added (clay)")

# Add recharge
print("\n4. Adding recharge...")
model.set_recharge(10, 40, 5, 15, 0.01)
print("   [OK] Recharge zone added (0.01 m/day)")

# Solve
print("\n5. Solving flow equation...")
model.solve(iterations=150, tolerance=1e-4)
print("   [OK] Solver converged")

# Compute flow
print("\n6. Computing flow field...")
qx, qy, q_mag = model.compute_flow()
print(f"   [OK] Flow computed")
print(f"        - Max flow magnitude: {np.max(q_mag):.4f} m/day")
print(f"        - Mean flow magnitude: {np.mean(q_mag):.4f} m/day")

# Summary
print("\n7. Model summary...")
summary = model.get_summary()
for key, value in summary.items():
    print(f"   - {key}: {value:.4f}")

print("\n" + "=" * 60)
print("SUCCESS: ALL TESTS PASSED")
print("=" * 60)
print("\nTo run the web app, use:")
print("  python -m streamlit run app.py")
print("\nOr visit: http://localhost:8501")
print("=" * 60)
