"""
Simplified 2D groundwater flow model based on Darcy's law.

This module implements a basic groundwater flow simulator using a 2D grid
and iterative solving of the steady-state flow equation. It is designed
for educational and exploratory purposes, not for engineering predictions.
"""

import numpy as np
from typing import Callable, Dict, Optional, Tuple


class GroundwaterModel:
    """
    A simplified 2D steady-state groundwater flow model.
    
    The model solves a simplified version of the groundwater flow equation
    using finite differences on a regular 2D grid. Users can define zones
    with different hydraulic conductivity values and fixed-head point sources.
    """
    
    def __init__(
        self,
        nx: int = 50,
        ny: int = 50,
        cell_size: float = 10.0,
        relaxation_factor: float = 1.0,
        aquifer_thickness: float = 10.0,
    ):
        """
        Initialize the groundwater model.
        
        Parameters
        ----------
        nx : int
            Number of cells in x-direction
        ny : int
            Number of cells in y-direction
        cell_size : float
            Physical size of each cell (m)
        relaxation_factor : float
            Relaxation factor for iterative solver (1.0 = exact update from discretized PDE,
            <1.0 damps convergence for stability, typically 0.1-0.5 for heterogeneous K)
        aquifer_thickness : float
            Confined aquifer thickness b (m). Recharge input is treated as N (m/day)
            and converted to source term N/b (1/day).
        """
        
        self.nx = nx
        self.ny = ny
        self.cell_size = cell_size
        self.relaxation_factor = relaxation_factor
        if aquifer_thickness <= 0:
            raise ValueError("aquifer_thickness must be > 0")
        self.aquifer_thickness = float(aquifer_thickness)
        
        # Initialize fields
        self.hydraulic_conductivity = np.ones((ny, nx)) * 1.0  # m/day
        self.recharge = np.zeros((ny, nx))  # m/day
        self.head = np.ones((ny, nx)) * 0.0  # m (initial)
        self.head_initial = self.head.copy()
        
        # Point sources with fixed hydraulic head.
        # Each point is (x, y, head_value), or None if not set.
        self.max_point_sources = 6
        self.point_sources = [None] * self.max_point_sources

        # Corner-based boundary option: if enabled, define values at the four
        # corners and interpolate linearly along edges. All corner values must
        # be provided when `use_corner_boundary` is True.
        self.use_corner_boundary = False
        self.head_top_left = None
        self.head_top_right = None
        self.head_bottom_left = None
        self.head_bottom_right = None

        self._initialize_head()

    def _initialize_head(self):
        """Initialize the head field from a neutral starting condition."""
        self.head = np.ones((self.ny, self.nx)) * 0.0
        self.head_initial = self.head.copy()

    def prepare_initial_state(self):
        """Reset the head field and apply boundary and point-source conditions."""
        self._initialize_head()
        self._apply_edge_conditions()
        self._apply_point_sources()

    def _active_point_sources(self):
        """Return active point sources as (x, y, head_value) tuples."""
        return [src for src in self.point_sources if src is not None]

    def _apply_point_sources(self):
        """Apply fixed-head values for all active point sources."""
        for x, y, h in self._active_point_sources():
            self.head[y, x] = h

    def _apply_boundary_conditions(self):
        """Apply fixed-head boundary values when the option is enabled."""
        # If corner-based boundaries are not enabled, nothing to do here.
        if not self.use_corner_boundary:
            return

        # Corner-based boundaries: all four corner values must be set.
        nx = self.nx
        ny = self.ny

        if (
            self.head_top_left is None
            or self.head_top_right is None
            or self.head_bottom_left is None
            or self.head_bottom_right is None
        ):
            raise ValueError("Corner boundary mode enabled but one or more corner values are not set.")

        tl = float(self.head_top_left)
        tr = float(self.head_top_right)
        bl = float(self.head_bottom_left)
        br = float(self.head_bottom_right)

        # Linear interpolation along edges (inclusive of corners)
        top_edge = np.linspace(tl, tr, nx)
        bottom_edge = np.linspace(bl, br, nx)
        left_edge = np.linspace(bl, tl, ny)
        right_edge = np.linspace(br, tr, ny)

        # Assign to head array.
        # Model array indexing uses row 0 at the bottom (y=0) and row -1 at the top.
        # Place `top_edge` on the top row and `bottom_edge` on the bottom row.
        self.head[-1, :] = top_edge
        self.head[0, :] = bottom_edge
        self.head[:, 0] = left_edge
        self.head[:, -1] = right_edge

    def _apply_edge_conditions(self):
        """Apply the currently selected edge conditions."""
        # If corner-based boundaries are enabled, apply them. Otherwise use
        # the no-flow copy behaviour.
        if self.use_corner_boundary:
            self._apply_boundary_conditions()
            return
        else:
            # No-flow boundaries: copy adjacent interior values.
            self.head[0, 1:-1] = self.head[1, 1:-1]
            self.head[-1, 1:-1] = self.head[-2, 1:-1]
            self.head[1:-1, 0] = self.head[1:-1, 1]
            self.head[1:-1, -1] = self.head[1:-1, -2]
            self.head[0, 0] = self.head[1, 1]
            self.head[0, -1] = self.head[1, -2]
            self.head[-1, 0] = self.head[-2, 1]
            self.head[-1, -1] = self.head[-2, -2]
    
    def set_zone(self, x_min: int, x_max: int, y_min: int, y_max: int, 
                 conductivity: float):
        """
        Set hydraulic conductivity in a rectangular zone.
        
        Parameters
        ----------
        x_min, x_max : int
            Column range [x_min, x_max)
        y_min, y_max : int
            Row range [y_min, y_max)
        conductivity : float
            Hydraulic conductivity for this zone (m/day)
        """
        self.hydraulic_conductivity[y_min:y_max, x_min:x_max] = conductivity

    def set_background_conductivity(self, conductivity: float):
        """Set hydraulic conductivity for the full domain."""
        self.hydraulic_conductivity[:, :] = conductivity
    
    def set_recharge(self, x_min: int, x_max: int, y_min: int, y_max: int,
                     rate: float):
        """
        Set recharge rate in a rectangular zone.
        
        Parameters
        ----------
        x_min, x_max : int
            Column range [x_min, x_max)
        y_min, y_max : int
            Row range [y_min, y_max)
        rate : float
            Recharge rate (m/day)
        """
        self.recharge[y_min:y_max, x_min:x_max] = rate
    
    def set_point_source(self, source_num: int, x: int, y: int, head_value: float):
        """
        Set a point source with fixed hydraulic head.
        
        Parameters
        ----------
        source_num : int
            Point source number (1 to max_point_sources)
        x : int
            Column index (0 to nx-1)
        y : int
            Row index (0 to ny-1)
        head_value : float
            Fixed hydraulic head at this point (m)
        """
        if not 1 <= source_num <= self.max_point_sources:
            raise ValueError(f"source_num must be between 1 and {self.max_point_sources}")
        self.point_sources[source_num - 1] = (int(x), int(y), float(head_value))
    
    def clear_point_source(self, source_num: int):
        """
        Clear a point source.
        
        Parameters
        ----------
        source_num : int
            Point source number (1 to max_point_sources)
        """
        if not 1 <= source_num <= self.max_point_sources:
            raise ValueError(f"source_num must be between 1 and {self.max_point_sources}")
        self.point_sources[source_num - 1] = None
    
    def solve(
        self,
        iterations: int = 100,
        tolerance: float = 1e-3,
        progress_callback: Optional[Callable[[int, np.ndarray, bool], None]] = None,
        progress_interval: int = 50,
    ):
        """
        Solve the steady-state flow equation using iterative relaxation.
        
        This uses a simple finite-difference approach with fixed-head point
        sources and either fixed-head or no-flow boundaries at the model edges.
        
        Parameters
        ----------
        iterations : int
            Maximum number of iterations
        tolerance : float
            Convergence tolerance (change in max head)
        """
        # Start each solve from a clean field so previous runs do not leak in.
        self.prepare_initial_state()

        if progress_callback is not None:
            progress_callback(0, self.head.copy(), False)

        progress_interval = max(1, int(progress_interval))
        
        for iteration in range(iterations):
            head_old = self.head.copy()
            point_source_cells = {(x, y) for x, y, _ in self._active_point_sources()}
            
            # Get conductivity at interior points and neighbors
            k = self.hydraulic_conductivity
            
            # Simple 5-point stencil: average of neighbors weighted by conductivity
            # dh/dx and dh/dy approximated by centered differences
            for i in range(1, self.ny - 1):
                for j in range(1, self.nx - 1):
                    # Keep fixed-head point-source cells unchanged.
                    if (j, i) in point_source_cells:
                        continue  # Keep the fixed head value
                    
                    # Harmonic mean conductivity approximation
                    k_center = k[i, j]
                    k_north = (k[i + 1, j] + k[i, j]) / 2
                    k_south = (k[i - 1, j] + k[i, j]) / 2
                    k_east = (k[i, j + 1] + k[i, j]) / 2
                    k_west = (k[i, j - 1] + k[i, j]) / 2
                    
                    # Discretized form of ∇·(K∇h) + R = 0 using finite volumes.
                    # For non-homogeneous K, the update rule is:
                    #   h_C = (Σ K_face * h_neigh + R*Δx²) / (Σ K_face)
                    numerator = (
                        k_north * head_old[i + 1, j] +
                        k_south * head_old[i - 1, j] +
                        k_east * head_old[i, j + 1] +
                        k_west * head_old[i, j - 1]
                    )
                    denominator = k_north + k_south + k_east + k_west
                    
                    # Recharge input is N (m/day); convert to N/b (1/day) for
                    # ∇·(K∇h) + N/b = 0, then multiply by Δx².
                    source_term = (
                        self.recharge[i, j] * (self.cell_size ** 2) / self.aquifer_thickness
                    )
                    
                    # Exact update from discretized PDE (relaxation_factor=1.0),
                    # or damped update for stability (relaxation_factor<1.0)
                    h_new = (numerator + source_term) / denominator
                    self.head[i, j] = (self.relaxation_factor * h_new + 
                                      (1.0 - self.relaxation_factor) * head_old[i, j])
            
            self._apply_edge_conditions()

            # Re-apply fixed-head point sources.
            self._apply_point_sources()
            
            # Check convergence
            change = np.max(np.abs(self.head - head_old))
            should_emit = (
                progress_callback is not None
                and (
                    (iteration + 1) % progress_interval == 0
                    or change < tolerance
                    or iteration == iterations - 1
                )
            )
            if should_emit:
                progress_callback(iteration + 1, self.head.copy(), change < tolerance or iteration == iterations - 1)
            if change < tolerance:
                print(f"Converged after {iteration + 1} iterations (change: {change:.2e})")
                break
    
    def compute_flow(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute groundwater flow velocities using Darcy's law.
        
        Returns
        -------
        qx, qy : np.ndarray
            Specific discharge components (m/day)
        magnitude : np.ndarray
            Flow magnitude
        """
        # Compute gradients (central differences)
        dh_dx = np.gradient(self.head, self.cell_size, axis=1)
        dh_dy = np.gradient(self.head, self.cell_size, axis=0)
        
        # Darcy's law: q = -K * ∇h
        qx = -self.hydraulic_conductivity * dh_dx
        qy = -self.hydraulic_conductivity * dh_dy
        
        magnitude = np.sqrt(qx**2 + qy**2)
        
        return qx, qy, magnitude
    
    def reset_head(self):
        """Reset head field to initial condition."""
        self._initialize_head()
    
    def get_summary(self) -> Dict:
        """Get summary statistics of the current solution."""
        qx, qy, q_mag = self.compute_flow()
        
        return {
            'head_min': float(np.min(self.head)),
            'head_max': float(np.max(self.head)),
            'head_mean': float(np.mean(self.head)),
            'flow_min': float(np.min(q_mag)),
            'flow_max': float(np.max(q_mag)),
            'flow_mean': float(np.mean(q_mag)),
        }
