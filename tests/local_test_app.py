#!/usr/bin/env python
"""
Local test app: Standalone Matplotlib-based groundwater simulator (relative solution).
Similar to streamlit_app.py but runs directly without Streamlit UI.
Plots are generated using Matplotlib with correct 1:1 aspect ratio.

All hydraulic head values are relative (dimensionless, normalized 0-1).
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add repo to path so imports work
sys.path.insert(0, '.')

from Simulator.groundwater_model import GroundwaterModel


def plot_field(ax, data, x_coords, y_coords, title, cmap='jet', cbar_label='Value', vmin=0, vmax=1):
    """Plot 2D field with correct aspect ratio (no compass)."""
    im = ax.contourf(x_coords, y_coords, data, levels=20, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.contour(x_coords, y_coords, data, levels=10, colors='black', alpha=0.2, linewidths=0.5)
    
    # Set aspect ratio to equal so 1 unit in x = 1 unit in y visually
    ax.set_aspect('equal')
    
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title(title)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    
    return im


def analytical_head_relative(x_coords, y_coords):
    """Analytical solution for relative (dimensionless) hydraulic head.
    
    Solution: h_rel(x, y) = (x / x_max) * (y / y_max)
    """
    x_max = x_coords[-1]
    y_max = y_coords[-1]
    xx, yy = np.meshgrid(x_coords, y_coords, indexing='xy')
    return (xx / x_max) * (yy / y_max)


def main():
    """Run local test simulation with configurable parameters."""
    
    print("=" * 70)
    print("LOCAL GROUNDWATER SIMULATOR (Matplotlib Backend)")
    print("=" * 70)
    
    # Simulation parameters (easy to modify)
    nx, ny = 50, 50
    cell_size = 10.0
    iterations = 4000
    tolerance = 1e-5
    
    # Corner boundary conditions (relative, dimensionless: 0-1)
    corner_tl = 0.0
    corner_tr = 1.0
    corner_bl = 0.0
    corner_br = 0.0
    
    # Point sources (list of dicts with x, y, h)
    point_sources = [
    ]
    
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
    head_analytical = analytical_head_relative(x_coords, y_coords)

    # Physical scaling for unit plot (user-configurable reference head)
    H_ref = 10.0  # reference hydraulic head in meters for the physical plot
    head_physical = model.head * H_ref
    head_analytical_physical = head_analytical * H_ref

    # Difference (relative): numerical - analytical (dimensionless)
    head_diff_rel = model.head - head_analytical

    # Create 2x2 plots
    print("\nGenerating plots...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Groundwater Flow Simulation', fontsize=16, fontweight='bold')

    ax_rel = axes[0, 0]
    ax_ana = axes[0, 1]
    ax_phys = axes[1, 0]
    ax_diff = axes[1, 1]

    # Top-left: Numerical relative solution
    plot_field(ax_rel, model.head, x_coords, y_coords,
               'Numerical (Relative)', cmap='viridis', cbar_label='Head [-]', vmin=0, vmax=1)

    # Top-right: Analytical relative solution
    plot_field(ax_ana, head_analytical, x_coords, y_coords,
               'Analytical (Relative)', cmap='viridis', cbar_label='Head [-]', vmin=0, vmax=1)

    # Bottom-left: Numerical physical units
    plot_field(ax_phys, head_physical, x_coords, y_coords,
               f'Numerical (Physical) - H_ref={H_ref} m', cmap='viridis', cbar_label='Head [m]', vmin=0, vmax=H_ref)

    # Bottom-right: Difference between numerical and analytical (relative)
    # Use a diverging colormap centered at zero
    vabs = max(abs(np.min(head_diff_rel)), abs(np.max(head_diff_rel)), 1e-6)
    im = ax_diff.contourf(x_coords, y_coords, head_diff_rel, levels=21, cmap='RdBu_r', vmin=-vabs, vmax=vabs)
    ax_diff.contour(x_coords, y_coords, head_diff_rel, levels=11, colors='k', linewidths=0.4, alpha=0.5)
    ax_diff.set_aspect('equal')
    ax_diff.set_xlabel('X (m)')
    ax_diff.set_ylabel('Y (m)')
    ax_diff.set_title('Difference (Numerical - Analytical) [relative]')
    cbar = plt.colorbar(im, ax=ax_diff)
    cbar.set_label('Delta Head [-]')
    
    plt.tight_layout()

    # Ensure output directory exists and save figure into it
    os.makedirs('output', exist_ok=True)
    output_file = os.path.join('output', 'local_test_output.png')
    print(f"Saving figure to {output_file}...")
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    
    # Show plot (skip if running in CI/automated environment)
    if '--no-show' not in sys.argv:
        print("Displaying plot (close window to exit)...")
        try:
            plt.show()
        except:
            print("(Could not display plot interactively)")
    
    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
