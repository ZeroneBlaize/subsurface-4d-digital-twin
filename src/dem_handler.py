"""
DEM Handler: GeoTIFF Ingestion, Coordinate Reprojection & High-Fidelity Bilinear Elevation Sampling.
"""

from pathlib import Path
from typing import Union, Tuple, List, Optional
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine
from pyproj import Transformer


class DEMHandler:
    """
    Manages Digital Elevation Model (DEM) rasters, handles coordinate reference systems,
    and performs sub-pixel bilinear elevation sampling for borehole collar locations.
    """
    def __init__(self, dem_path: Union[str, Path]):
        self.dem_path = Path(dem_path)
        if not self.dem_path.exists():
            raise FileNotFoundError(f"DEM raster file not found: {self.dem_path}")
            
        with rasterio.open(self.dem_path) as src:
            self.crs = src.crs
            self.transform = src.transform
            self.width = src.width
            self.height = src.height
            self.bounds = src.bounds
            self.nodata = src.nodata if src.nodata is not None else -9999.0
            self.data = src.read(1).astype(np.float32)
            
        # Mask out nodata values
        self.valid_mask = self.data != self.nodata
        
        # Grid coordinate vectors
        res_x = self.transform.a
        res_y = -self.transform.e
        self.x_coords = self.bounds.left + (np.arange(self.width) + 0.5) * res_x
        self.y_coords = self.bounds.top - (np.arange(self.height) + 0.5) * res_y
        self.mesh_x, self.mesh_y = np.meshgrid(self.x_coords, self.y_coords)
        
    def reproject_point(
        self,
        x: float,
        y: float,
        source_crs: str = "EPSG:4326"
    ) -> Tuple[float, float]:
        """
        Reprojects coordinates (e.g. Latitude/Longitude in WGS84) to the DEM's native projected CRS.
        """
        if self.crs == CRS.from_string(source_crs):
            return x, y
        transformer = Transformer.from_crs(source_crs, self.crs, always_xy=True)
        return transformer.transform(x, y)

    def sample_elevation(self, x: float, y: float, method: str = "bilinear") -> float:
        """
        Samples surface ground elevation (Reduced Level in meters) at a given (X, Y) coordinate.
        Supports 'nearest' or 'bilinear' interpolation.
        """
        # Convert map coordinates to continuous fractional pixel coordinates
        inv_transform = ~self.transform
        col_f, row_f = inv_transform * (x, y)
        
        if not (0 <= col_f < self.width - 1 and 0 <= row_f < self.height - 1):
            # Check edge boundaries
            col_c = int(np.clip(round(col_f), 0, self.width - 1))
            row_c = int(np.clip(round(row_f), 0, self.height - 1))
            val = float(self.data[row_c, col_c])
            return val if val != self.nodata else np.nan
            
        if method == "nearest":
            col_idx = int(round(col_f))
            row_idx = int(round(row_f))
            return float(self.data[row_idx, col_idx])
            
        # Bilinear interpolation
        c0 = int(np.floor(col_f))
        c1 = c0 + 1
        r0 = int(np.floor(row_f))
        r1 = r0 + 1
        
        dx = col_f - c0
        dy = row_f - r0
        
        q11 = self.data[r0, c0]
        q12 = self.data[r1, c0]
        q21 = self.data[r0, c1]
        q22 = self.data[r1, c1]
        
        elev = (
            q11 * (1.0 - dx) * (1.0 - dy) +
            q21 * dx * (1.0 - dy) +
            q12 * (1.0 - dx) * dy +
            q22 * dx * dy
        )
        return float(elev)

    def sample_elevation_batch(
        self,
        x_arr: np.ndarray,
        y_arr: np.ndarray,
        method: str = "bilinear"
    ) -> np.ndarray:
        """
        Vectorized sampling of elevations for an array of coordinates.
        """
        elevations = np.zeros(len(x_arr), dtype=np.float32)
        for i, (x, y) in enumerate(zip(x_arr, y_arr)):
            elevations[i] = self.sample_elevation(x, y, method=method)
        return elevations

    def get_grid_shape(self) -> Tuple[int, int]:
        return self.height, self.width

    def get_profile_slice(
        self,
        p_start: Tuple[float, float],
        p_end: Tuple[float, float],
        num_points: int = 200
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extracts a 2D topographic cross-section line across the DEM.
        Returns: distances_m, x_pts, y_pts, elevations_m
        """
        x_pts = np.linspace(p_start[0], p_end[0], num_points)
        y_pts = np.linspace(p_start[1], p_end[1], num_points)
        dists = np.sqrt((x_pts - p_start[0])**2 + (y_pts - p_start[1])**2)
        elevs = self.sample_elevation_batch(x_pts, y_pts)
        return dists, x_pts, y_pts, elevs
