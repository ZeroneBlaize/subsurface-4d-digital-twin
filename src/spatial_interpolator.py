"""
Spatial Interpolator: Multi-Algorithm 2D/3D Strata Boundary Reconstruction with Monotonic Stacking Constraints.
"""

from pathlib import Path
from typing import Union, Tuple, List, Optional, Dict
import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.spatial import ConvexHull
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union


class SpatialInterpolator:
    """
    Interpolates scattered borehole point observations onto continuous 2D/3D grids
    using Inverse Distance Weighting (IDW) or Radial Basis Functions (RBF / Splines).
    Enforces strict physical stratigraphic non-crossing rules and boundary convex hull clipping.
    """
    def __init__(
        self,
        mesh_x: np.ndarray,
        mesh_y: np.ndarray,
        boundary_buffer_m: float = 60.0
    ):
        self.mesh_x = mesh_x  # 2D grid Easting (Ny, Nx)
        self.mesh_y = mesh_y  # 2D grid Northing (Ny, Nx)
        self.ny, self.nx = mesh_x.shape
        self.boundary_buffer_m = boundary_buffer_m
        self.convex_hull_polygon: Optional[Polygon] = None
        self.survey_mask: Optional[np.ndarray] = None

    def fit_survey_boundary(self, eastings: np.ndarray, northings: np.ndarray):
        """
        Builds a buffered convex hull around borehole survey points to prevent unconstrained edge extrapolation.
        """
        pts = np.column_stack([eastings, northings])
        if len(pts) < 3:
            self.survey_mask = np.ones((self.ny, self.nx), dtype=bool)
            return
            
        hull = ConvexHull(pts)
        hull_pts = pts[hull.vertices]
        poly = Polygon(hull_pts).buffer(self.boundary_buffer_m)
        self.convex_hull_polygon = poly
        
        # Create vectorized boolean mask over the grid
        flat_x = self.mesh_x.ravel()
        flat_y = self.mesh_y.ravel()
        
        # Check containment via shapely / bounding box pre-filter for speed
        minx, miny, maxx, maxy = poly.bounds
        in_bbox = (flat_x >= minx) & (flat_x <= maxx) & (flat_y >= miny) & (flat_y <= maxy)
        
        mask_flat = np.zeros(len(flat_x), dtype=bool)
        # Detailed check on points inside bounding box
        idx_to_check = np.where(in_bbox)[0]
        for idx in idx_to_check:
            p = Point(flat_x[idx], flat_y[idx])
            if poly.contains(p):
                mask_flat[idx] = True
                
        self.survey_mask = mask_flat.reshape(self.ny, self.nx)

    def interpolate_idw(
        self,
        x_pts: np.ndarray,
        y_pts: np.ndarray,
        z_vals: np.ndarray,
        power: float = 2.0,
        epsilon: float = 1e-6
    ) -> np.ndarray:
        """
        Inverse Distance Weighting (IDW) interpolation.
        """
        valid = ~np.isnan(z_vals)
        x_v, y_v, z_v = x_pts[valid], y_pts[valid], z_vals[valid]
        
        if len(z_v) == 0:
            return np.full((self.ny, self.nx), np.nan, dtype=np.float32)
            
        flat_x = self.mesh_x.ravel()
        flat_y = self.mesh_y.ravel()
        flat_z = np.zeros(len(flat_x), dtype=np.float32)
        
        # Chunked vectorized distance evaluation to stay memory efficient
        chunk_size = 5000
        for start_idx in range(0, len(flat_x), chunk_size):
            end_idx = min(start_idx + chunk_size, len(flat_x))
            cx = flat_x[start_idx:end_idx, np.newaxis]  # (C, 1)
            cy = flat_y[start_idx:end_idx, np.newaxis]  # (C, 1)
            
            # Distance from each grid point to each borehole observation point
            dists = np.sqrt((cx - x_v)**2 + (cy - y_v)**2)  # (C, N)
            
            # Check for exact co-located hits
            zero_mask = dists < epsilon
            weights = 1.0 / np.maximum(dists, epsilon)**power
            weights_sum = np.sum(weights, axis=1)
            
            chunk_vals = np.sum(weights * z_v, axis=1) / weights_sum
            
            # Where point is exactly at a borehole, assign the exact value
            any_zero = np.any(zero_mask, axis=1)
            if np.any(any_zero):
                for i in np.where(any_zero)[0]:
                    col = np.where(zero_mask[i])[0][0]
                    chunk_vals[i] = z_v[col]
                    
            flat_z[start_idx:end_idx] = chunk_vals
            
        grid_z = flat_z.reshape(self.ny, self.nx)
        
        # Apply convex hull mask if configured
        if self.survey_mask is not None:
            grid_z[~self.survey_mask] = np.nan
            
        return grid_z

    def interpolate_rbf(
        self,
        x_pts: np.ndarray,
        y_pts: np.ndarray,
        z_vals: np.ndarray,
        kernel: str = "thin_plate_spline",
        smoothing: float = 0.0
    ) -> np.ndarray:
        """
        Radial Basis Function (RBF / Spline) interpolation.
        """
        valid = ~np.isnan(z_vals)
        x_v, y_v, z_v = x_pts[valid], y_pts[valid], z_vals[valid]
        
        if len(z_v) < 3:
            return self.interpolate_idw(x_pts, y_pts, z_vals)
            
        obs_coords = np.column_stack([x_v, y_v])
        grid_coords = np.column_stack([self.mesh_x.ravel(), self.mesh_y.ravel()])
        
        rbf = RBFInterpolator(obs_coords, z_v, kernel=kernel, smoothing=smoothing)
        flat_z = rbf(grid_coords).astype(np.float32)
        grid_z = flat_z.reshape(self.ny, self.nx)
        
        if self.survey_mask is not None:
            grid_z[~self.survey_mask] = np.nan
            
        return grid_z

    def enforce_stratigraphic_stacking(
        self,
        ground_dem: np.ndarray,
        raw_strata_surfaces: List[np.ndarray],
        is_hard_contact: Optional[List[bool]] = None
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Enforces monotonic vertical stacking (Z_0 >= Z_1 >= Z_2 >= ... >= Z_K)
        and computes non-negative thickness rasters: Thickness_k = Z_{k-1} - Z_k >= 0.
        
        Reconciles layer pinch-outs (where a stratum pinches out, thickness=0, Z_k = Z_{k-1}).
        """
        num_layers = len(raw_strata_surfaces)
        if is_hard_contact is None:
            # By default, the final layer (bedrock) is hard
            is_hard_contact = [False] * (num_layers - 1) + [True]
            
        corrected_surfaces = []
        thicknesses = []
        
        current_ceiling = ground_dem.copy()
        
        for k in range(num_layers):
            raw_surface = raw_strata_surfaces[k].copy()
            valid = ~np.isnan(raw_surface)
            
            # Floor constraint: Layer bottom cannot be higher than its ceiling
            constrained = np.minimum(raw_surface, current_ceiling)
            
            if is_hard_contact[k]:
                # Hard Contact (e.g. Bedrock Refusal): It defines a rigid floor
                # Where valid data exists, keep elevation; where missing, match previous ceiling
                z_k = np.where(valid, constrained, current_ceiling)
            else:
                # Soft layer: If layer is absent/pinched out, surface matches the ceiling (thickness=0)
                z_k = np.where(valid, constrained, current_ceiling)
                
            # Non-negative thickness: T_k = Ceiling - Z_k
            t_k = np.maximum(0.0, current_ceiling - z_k)
            
            # Invalidate thickness outside survey mask where ground_dem was valid
            if self.survey_mask is not None:
                t_k[~self.survey_mask] = np.nan
                z_k[~self.survey_mask] = np.nan
                
            corrected_surfaces.append(z_k)
            thicknesses.append(t_k)
            
            # Update current ceiling downward for next stratum
            current_ceiling = np.where(np.isnan(z_k), current_ceiling, z_k)
            
        return corrected_surfaces, thicknesses
