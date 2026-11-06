"""
Exporter: Generates Standard GeoTIFF Rasters, GeoPackage Vector Layers, and GIS Assets for QGIS.
"""

from pathlib import Path
from typing import Union, Dict, List, Optional
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt

from src.config import RASTERS_DIR, VECTORS_DIR, DEFAULT_CRS


class GISExporter:
    """
    Exports continuous 2D/3D subsurface model outputs to GIS formats (GeoTIFF, GeoPackage)
    with complete spatial metadata and color-ramp compatibility for QGIS.
    """
    def __init__(
        self,
        transform: Affine,
        crs_str: Union[str, CRS] = DEFAULT_CRS,
        nodata_val: float = -9999.0
    ):
        self.transform = transform
        if isinstance(crs_str, CRS):
            self.crs = crs_str
        else:
            self.crs = CRS.from_string(str(crs_str))
        self.nodata = nodata_val
        RASTERS_DIR.mkdir(parents=True, exist_ok=True)
        VECTORS_DIR.mkdir(parents=True, exist_ok=True)

    def export_raster(
        self,
        grid_data: np.ndarray,
        filename: str,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Exports a 2D numpy array to GeoTIFF.
        """
        out_dir = output_dir if output_dir is not None else RASTERS_DIR
        out_path = out_dir / filename
        if not out_path.name.endswith(".tif"):
            out_path = out_path.with_suffix(".tif")
            
        ny, nx = grid_data.shape
        clean_data = grid_data.copy().astype(np.float32)
        clean_data[np.isnan(clean_data)] = self.nodata
        
        with rasterio.open(
            out_path,
            "w",
            driver="GTiff",
            height=ny,
            width=nx,
            count=1,
            dtype="float32",
            crs=self.crs,
            transform=self.transform,
            nodata=self.nodata,
        ) as dst:
            dst.write(clean_data, 1)
            
        return out_path

    def export_boreholes_geopackage(
        self,
        borehole_summary_df,
        filename: str = "subsurface_geotechnical.gpkg",
        layer_name: str = "boreholes",
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Exports borehole collars with all geotechnical summary attributes into a GeoPackage vector layer.
        """
        out_dir = output_dir if output_dir is not None else VECTORS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        gpkg_path = out_dir / filename
        
        geometry = [Point(xy) for xy in zip(borehole_summary_df["Easting_m"], borehole_summary_df["Northing_m"])]
        gdf = gpd.GeoDataFrame(borehole_summary_df, geometry=geometry, crs=self.crs)
        
        gdf.to_file(gpkg_path, layer=layer_name, driver="GPKG")
        return gpkg_path

    def export_contour_vector(
        self,
        grid_data: np.ndarray,
        mesh_x: np.ndarray,
        mesh_y: np.ndarray,
        filename: str = "sbc_contours.gpkg",
        layer_name: str = "sbc_contours_kpa",
        levels: Optional[List[float]] = None,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Computes contour isolines from an interpolated raster grid and exports as GeoPackage linestring layer.
        """
        from shapely.geometry import LineString
        
        out_dir = output_dir if output_dir is not None else VECTORS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        gpkg_path = out_dir / filename
        if levels is None:
            min_v = np.nanmin(grid_data)
            max_v = np.nanmax(grid_data)
            if np.isnan(min_v) or np.isnan(max_v) or (max_v - min_v) < 1e-3:
                return gpkg_path
            levels = list(np.linspace(min_v, max_v, 10))
        elif len(np.unique(levels)) < 2:
            return gpkg_path
            
        fig, ax = plt.subplots()
        cs = ax.contour(mesh_x, mesh_y, grid_data, levels=levels)
        
        lines = []
        val_attrs = []
        for level_idx, level_val in enumerate(cs.levels):
            # In modern matplotlib, allsegs contains line segments for each contour level
            if level_idx < len(cs.allsegs):
                for vertices in cs.allsegs[level_idx]:
                    if len(vertices) >= 2:
                        lines.append(LineString(vertices))
                        val_attrs.append(round(float(level_val), 1))
        plt.close(fig)
        
        if len(lines) > 0:
            gdf = gpd.GeoDataFrame({"Value": val_attrs}, geometry=lines, crs=self.crs)
            gdf.to_file(gpkg_path, layer=layer_name, driver="GPKG")
            
        return gpkg_path
