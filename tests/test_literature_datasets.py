"""
Integration test verifying that published literature datasets
(Vidarbha IndiaNGMMSM and Bengaluru IISc) run cleanly through the full pipeline.
"""

from pathlib import Path
import pytest
import numpy as np

from src.config import RAW_DIR, DEM_DIR, GeotechConfig
from src.dem_handler import DEMHandler
from src.borehole_processor import BoreholeProcessor
from src.spatial_interpolator import SpatialInterpolator
from src.geotech_engine import GeotechEngine


def test_vidarbha_literature_pipeline():
    dem_path = DEM_DIR / "vidarbha_dem.tif"
    bh_path = RAW_DIR / "vidarbha_boreholes_parsed.csv"
    
    assert dem_path.exists()
    assert bh_path.exists()
    
    dem = DEMHandler(dem_path)
    bh = BoreholeProcessor(bh_path, dem_handler=dem)
    summary = bh.borehole_summary
    assert len(summary) >= 12
    
    interpolator = SpatialInterpolator(dem.mesh_x, dem.mesh_y)
    interpolator.fit_survey_boundary(summary["Easting_m"].values, summary["Northing_m"].values)
    
    # Check layer interpolation
    strata = bh.processed_df["Layer_Name"].unique()
    pts = bh.get_layer_points(strata[0])
    valid_pts = pts[pts["Is_Present"] & pts["Layer_Bottom_RL_m"].notnull()]
    assert len(valid_pts) > 0
    surf = interpolator.interpolate_idw(valid_pts["Easting_m"].values, valid_pts["Northing_m"].values, valid_pts["Layer_Bottom_RL_m"].values)
    assert surf.shape == dem.data.shape


def test_bangalore_literature_pipeline():
    dem_path = DEM_DIR / "bangalore_dem.tif"
    bh_path = RAW_DIR / "bangalore_boreholes_parsed.csv"
    
    assert dem_path.exists()
    assert bh_path.exists()
    
    dem = DEMHandler(dem_path)
    bh = BoreholeProcessor(bh_path, dem_handler=dem)
    summary = bh.borehole_summary
    assert len(summary) == 15
    
    cfg = GeotechConfig(footing_width_b=2.5, footing_depth_df=2.0)
    engine = GeotechEngine(cfg)
    
    # Calculate bearing capacity on layer 2
    strata = bh.processed_df["Layer_Name"].unique()
    pts = bh.get_layer_points(strata[1])
    n_pts = pts[pts["Is_Present"] & (pts["Field_N"] > 0)]
    interpolator = SpatialInterpolator(dem.mesh_x, dem.mesh_y)
    interp_n = interpolator.interpolate_idw(n_pts["Easting_m"].values, n_pts["Northing_m"].values, n_pts["Field_N"].values)
    sbc_grid = engine.evaluate_grid_sbc(interp_n, summary["Water_Table_Depth_m"].mean())
    
    assert sbc_grid.shape == dem.data.shape
    assert np.all(sbc_grid > 50.0)  # Gneissic weathered soil bearing capacity > 50 kPa


def test_rotterdam_public_pipeline():
    dem_path = DEM_DIR / "rotterdam_dem.tif"
    bh_path = RAW_DIR / "rotterdam_boreholes_parsed.csv"
    
    assert dem_path.exists()
    assert bh_path.exists()
    
    dem = DEMHandler(dem_path)
    bh = BoreholeProcessor(bh_path, dem_handler=dem)
    summary = bh.borehole_summary
    assert len(summary) >= 20
    
    cfg = GeotechConfig(footing_width_b=2.0, footing_depth_df=1.5)
    engine = GeotechEngine(cfg)
    
    strata = bh.processed_df["Layer_Name"].unique()
    pts = bh.get_layer_points(strata[0])
    valid_pts = pts[pts["Is_Present"] & pts["Layer_Bottom_RL_m"].notnull()]
    assert len(valid_pts) > 0
    
    interpolator = SpatialInterpolator(dem.mesh_x, dem.mesh_y)
    surf = interpolator.interpolate_idw(valid_pts["Easting_m"].values, valid_pts["Northing_m"].values, valid_pts["Layer_Bottom_RL_m"].values)
    assert surf.shape == dem.data.shape


def test_coupled_markov_public_pipeline():
    dem_path = DEM_DIR / "coupled_markov_dem.tif"
    bh_path = RAW_DIR / "coupled_markov_boreholes_parsed.csv"
    
    assert dem_path.exists()
    assert bh_path.exists()
    
    dem = DEMHandler(dem_path)
    bh = BoreholeProcessor(bh_path, dem_handler=dem)
    summary = bh.borehole_summary
    assert len(summary) == 12
    
    strata = bh.processed_df["Layer_Name"].unique()
    assert len(strata) >= 3
