#!/usr/bin/env python
"""
Local validation app: standalone Matplotlib-based groundwater test.
Similar to streamlit_app.py but runs directly without Streamlit UI.
Plots are generated using Matplotlib with correct 1:1 aspect ratio.

This version keeps the same kinds of inputs as the main test app so the
model itself is what gets exercised. The analytical comparison is exact only
for the corner-boundary base case; with point sources, it is a consistency
check rather than a closed-form proof.
"""

import sys
import os

import matplotlib.pyplot as plt
import numpy as np

# Add repo to path so imports work
sys.path.insert(0, ".")

from Simulator.groundwater_model import GroundwaterModel


def plot_field(ax, data, x_coords, y_coords, title, cmap="jet", cbar_label="Value", vmin=0, vmax=1):
    """Plot 2D field with correct aspect ratio."""
    im = ax.contourf(x_coords, y_coords, data, levels=20, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.contour(x_coords, y_coords, data, levels=10, colors="black", alpha=0.2, linewidths=0.5)
    ax.set_aspect("equal")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title(title)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    return im

def analytical_green_relative(x_coords, y_coords, x0, y0, n_terms=100):
    """
    Relative stationary Green's function for a 2D point source
    in a rectangular domain with homogeneous Dirichlet boundaries.

    Boundary condition:
        h = 0 at all boundaries

    Output:
        h_rel in range 0–1 [-]
    """

    x_min = x_coords[0]
    x_max = x_coords[-1]
    y_min = y_coords[0]
    y_max = y_coords[-1]

    Lx = x_max - x_min
    Ly = y_max - y_min

    if Lx <= 0:
        raise ValueError("Lx must be > 0 m.")

    if Ly <= 0:
        raise ValueError("Ly must be > 0 m.")

    # Shift coordinates to [0, Lx] and [0, Ly]
    x = x_coords - x_min
    y = y_coords - y_min
    x0_shift = x0 - x_min
    y0_shift = y0 - y_min

    xx, yy = np.meshgrid(x, y, indexing="xy")

    G = np.zeros_like(xx, dtype=float)

    for m in range(1, n_terms + 1):
        for n in range(1, n_terms + 1):

            lambda_mn = (m * np.pi / Lx)**2 + (n * np.pi / Ly)**2

            G += (
                np.sin(m * np.pi * xx / Lx)
                * np.sin(m * np.pi * x0_shift / Lx)
                * np.sin(n * np.pi * yy / Ly)
                * np.sin(n * np.pi * y0_shift / Ly)
                / lambda_mn
            )

    G *= 4 / (Lx * Ly)

    # Remove tiny negative numerical artefacts from truncated series
    G = np.maximum(G, 0)

    G_max = np.max(G)

    if G_max == 0:
        raise ValueError("Green function maximum is zero. Check source position and boundaries.")

    G_rel = G / G_max

    return G_rel


def main():
    """Run local test simulation with configurable parameters."""

    print("=" * 70)
    print("LOCAL GROUNDWATER VALIDATION TEST (Matplotlib Backend)")
    print("=" * 70)

    # Simulation parameters (same input style as the main test app)
    nx, ny = 100, 100
    cell_size = 10.0
    iterations = 4000
    tolerance = 1e-5

    # Corner boundary conditions
    corner_tl = 0.0
    corner_tr = 0.0
    corner_bl = 0.0
    corner_br = 0.0

    # Point sources (list of dicts with x, y, h)
    point_sources = [({"x": 25, "y": 25, "h": 1.0})]
    nterms = 100  # Number of terms in analytical series (higher = more accurate but slower)

    # Conductivity and zone
    background_k = 1.0
    conductivity_mode = "Homogeneous medium"
    zone_x_min, zone_x_max = 20, 40
    zone_y_min, zone_y_max = 10, 30
    selected_k = 0.1

    # Recharge
    recharge_rate = 0.00
    recharge_x_min, recharge_x_max = 15, 45
    recharge_y_min, recharge_y_max = 5, 15

    print(f"\nConfiguration:")
    print(f"  Grid: {nx} x {ny} cells ({cell_size} m/cell)")
    print(f"  Corners: TL={corner_tl}, TR={corner_tr}, BL={corner_bl}, BR={corner_br}")
    print(f"  Point sources: {len(point_sources)}")
    print(f"  Background K: {background_k} m/day")
    if conductivity_mode == "Heterogeneous medium with zone":
        print(f"  Zone K: {selected_k} m/day (x=[{zone_x_min}, {zone_x_max}], y=[{zone_y_min}, {zone_y_max}])")
    print(f"  Recharge: {recharge_rate} m/day")
    print()

    # Create and configure model
    print("Creating model...")
    model = GroundwaterModel(nx=nx, ny=ny, cell_size=cell_size)

    # Apply corner boundary conditions
    model.use_corner_boundary = True
    model.head_top_left = corner_tl
    model.head_top_right = corner_tr
    model.head_bottom_left = corner_bl
    model.head_bottom_right = corner_br

    # Apply point sources
    for idx, src in enumerate(point_sources, start=1):
        model.set_point_source(idx, src["x"], src["y"], src["h"])

    # Set conductivity
    model.set_background_conductivity(background_k)
    if conductivity_mode == "Heterogeneous medium with zone":
        model.set_zone(zone_x_min, zone_x_max, zone_y_min, zone_y_max, selected_k)

    # Set recharge
    model.set_recharge(recharge_x_min, recharge_x_max, recharge_y_min, recharge_y_max, recharge_rate)

    # Solve
    print(f"Solving (max {iterations} iterations, tolerance {tolerance})...")
    model.solve(iterations=iterations, tolerance=tolerance)

    # Get summary
    summary = model.get_summary()
    print(f"\nResults (relative, dimensionless):")
    print(f"  Head range: {summary['head_min']:.3f} to {summary['head_max']:.3f} [-]")

    # Create coordinate arrays
    x_coords = np.arange(nx) * cell_size
    y_coords = np.arange(ny) * cell_size

    # Compute analytical solution
    head_analytical = analytical_green_relative(x_coords, y_coords, x0=25*10, y0=25*10, n_terms= nterms)

    # Physical scaling for unit plot (user-configurable reference head)
    H_ref = 10.0
    head_physical = model.head * H_ref
    head_analytical_physical = head_analytical * H_ref

    # Difference (relative): numerical - analytical (dimensionless)
    head_diff_rel = model.head - head_analytical

    # Create 2x2 plots
    print("\nGenerating plots...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Groundwater Flow Simulation", fontsize=16, fontweight="bold")

    ax_rel = axes[0, 0]
    ax_ana = axes[0, 1]
    ax_phys = axes[1, 0]
    ax_diff = axes[1, 1]

    # Top-left: Numerical relative solution
    plot_field(ax_rel, model.head, x_coords, y_coords, "Numerical (Relative)", cmap="viridis", cbar_label="Head [-]", vmin=0, vmax=1)

    # Top-right: Analytical relative solution
    plot_field(ax_ana, head_analytical, x_coords, y_coords, "Analytical (Relative)", cmap="viridis", cbar_label="Head [-]", vmin=0, vmax=1)

    # Bottom-left: Numerical physical units
    plot_field(ax_phys, head_physical, x_coords, y_coords, f"Numerical (Physical) - H_ref={H_ref} m", cmap="viridis", cbar_label="Head [m]", vmin=0, vmax=H_ref)

    # Bottom-right: Difference between numerical and analytical (relative)
    vabs = max(abs(np.min(head_diff_rel)), abs(np.max(head_diff_rel)), 1e-6)
    im = ax_diff.contourf(x_coords, y_coords, head_diff_rel, levels=21, cmap="RdBu_r", vmin=-vabs, vmax=vabs)
    ax_diff.contour(x_coords, y_coords, head_diff_rel, levels=11, colors="k", linewidths=0.4, alpha=0.5)
    ax_diff.set_aspect("equal")
    ax_diff.set_xlabel("X (m)")
    ax_diff.set_ylabel("Y (m)")
    ax_diff.set_title("Difference (Numerical - Analytical) [relative]")
    cbar = plt.colorbar(im, ax=ax_diff)
    cbar.set_label("Delta Head [-]")

    plt.tight_layout()

    # Ensure output directory exists and save figure into it
    os.makedirs('output', exist_ok=True)
    output_file = os.path.join('output', 'local_test2_output.png')
    print(f"Saving figure to {output_file}...")
    plt.savefig(output_file, dpi=150, bbox_inches="tight")

    # Show plot (skip if running in CI/automated environment)
    if "--no-show" not in sys.argv:
        print("Displaying plot (close window to exit)...")
        try:
            plt.show()
        except Exception:
            print("(Could not display plot interactively)")

    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
