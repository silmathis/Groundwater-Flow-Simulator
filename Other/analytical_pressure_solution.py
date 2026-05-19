"""
Plot the closed-form analytical solution for the steady-state pressure field
of the 2D Laplace problem shown in the reference.

Solution (relative):
    p_rel(x, y) = (x / L) * (y / L)  [dimensionless, 0 to 1]

Boundary conditions:
    p_rel(x, 0) = 0
    p_rel(0, y) = 0
    p_rel(x, L) = x / L
    p_rel(L, y) = y / L
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def pressure_field_relative(x: np.ndarray, y: np.ndarray, L: float) -> np.ndarray:
    """Closed-form steady-state relative pressure solution (dimensionless, normalized 0-1)."""
    return (x / L) * (y / L)


def main() -> None:
    # Editable parameters
    L = 1.0      # domain length [m]
    nx = 80
    ny = 80

    x = np.linspace(0.0, L, nx)
    y = np.linspace(0.0, L, ny)
    xx, yy = np.meshgrid(x, y, indexing="xy")

    # Compute relative (dimensionless) pressure field
    pp_rel = pressure_field_relative(xx, yy, L)

    fig = plt.figure(figsize=(14, 6))
    ax_surface = fig.add_subplot(121, projection="3d")
    ax_contour = fig.add_subplot(122)

    # 3D surface plot
    surface = ax_surface.plot_surface(xx, yy, pp_rel, cmap="viridis", linewidth=0, antialiased=True)
    ax_surface.set_xlabel("x [m]")
    ax_surface.set_ylabel("y [m]")
    ax_surface.set_zlabel("p_rel [-]")
    ax_surface.set_title(r"Analytical relative pressure field: $p_{rel}(x,y)=(x/L)\,(y/L)$")
    fig.colorbar(surface, ax=ax_surface, shrink=0.75, pad=0.1, label="p_rel [-]")

    # Contour plot
    levels = np.linspace(0.0, 1.0, 21)
    contour = ax_contour.contourf(xx, yy, pp_rel, levels=levels, cmap="viridis")
    contour_lines = ax_contour.contour(xx, yy, pp_rel, levels=levels[::2], colors="k", linewidths=0.5, alpha=0.4)
    ax_contour.clabel(contour_lines, inline=True, fontsize=8, fmt="%.2f")
    ax_contour.set_xlabel("x [m]")
    ax_contour.set_ylabel("y [m]")
    ax_contour.set_title("Contour diagram of the analytical relative pressure solution")
    ax_contour.set_aspect("equal")
    fig.colorbar(contour, ax=ax_contour, shrink=0.85, label="p_rel [-]")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()