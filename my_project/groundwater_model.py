"""
Simplified 2D groundwater flow model based on Darcy's law.

This module implements a basic groundwater flow simulator using a 2D grid
and iterative solving of the steady-state flow equation. It is designed
for educational and exploratory purposes, not for engineering predictions.
"""

import numpy as np
from typing import Tuple, Dict


class GroundwaterModel:
    """
    A simplified 2D steady-state groundwater flow model.
    
    The model solves a simplified version of the groundwater flow equation
    using finite differences on a regular 2D grid. Users can define zones
    with different hydraulic conductivity values and fixed-head point sources.
    """
    
    def __init__(self, nx: int = 50, ny: int = 50, cell_size: float = 10.0):
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
        """
        
        self.nx = nx
        self.ny = ny
        self.cell_size = cell_size
        
        # Initialize fields
        self.hydraulic_conductivity = np.ones((ny, nx)) * 1.0  # m/day
        self.recharge = np.zeros((ny, nx))  # m/day
        self.head = np.ones((ny, nx)) * 0.0  # m (initial)
        self.head_initial = self.head.copy()
        
        # Point sources with fixed hydraulic head.
        # Each point is (x, y, head_value), or None if not set.
        self.max_point_sources = 6
        self.point_sources = [None] * self.max_point_sources

        # Optional fixed-head boundary conditions.
        self.use_boundary_conditions = False
        self.head_north = 30.0
        self.head_south = 0.0
        self.head_east = 0.0
        self.head_west = 0.0

        self._initialize_head()

    def _initialize_head(self):
        """Initialize the head field from a neutral starting condition."""
        self.head = np.ones((self.ny, self.nx)) * 0.0
        self.head_initial = self.head.copy()

    def _active_point_sources(self):
        """Return active point sources as (x, y, head_value) tuples."""
        return [src for src in self.point_sources if src is not None]

    def _apply_point_sources(self):
        """Apply fixed-head values for all active point sources."""
        for x, y, h in self._active_point_sources():
            self.head[y, x] = h

    def _apply_boundary_conditions(self):
        """Apply fixed-head boundary values when the option is enabled."""
        if not self.use_boundary_conditions:
            return

        self.head[0, :] = self.head_north
        self.head[-1, :] = self.head_south
        self.head[:, 0] = self.head_west
        self.head[:, -1] = self.head_east

    def _apply_edge_conditions(self):
        """Apply the currently selected edge conditions."""
        if self.use_boundary_conditions:
            self._apply_boundary_conditions()
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
    
    def solve(self, iterations: int = 100, tolerance: float = 1e-3):
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
        self._initialize_head()
        self._apply_edge_conditions()
        self._apply_point_sources()
        
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
                    
                    # Discretized form of Laplace equation with recharge
                    # ∇²h + R/K = 0 (simplified form)
                    numerator = (
                        k_north * head_old[i + 1, j] +
                        k_south * head_old[i - 1, j] +
                        k_east * head_old[i, j + 1] +
                        k_west * head_old[i, j - 1]
                    )
                    denominator = k_north + k_south + k_east + k_west
                    
                    # Add recharge term (simplified)
                    source_term = (self.recharge[i, j] * 
                                 (self.cell_size ** 2) / k_center)
                    
                    self.head[i, j] = (numerator / denominator) + 0.1 * source_term
            
            self._apply_edge_conditions()

            # Re-apply fixed-head point sources.
            self._apply_point_sources()
            
            # Check convergence
            change = np.max(np.abs(self.head - head_old))
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
