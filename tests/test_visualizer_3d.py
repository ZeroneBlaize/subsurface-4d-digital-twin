"""
Unit tests for 3D WebGL subsurface and digital twin visualizer.
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.config import DEM_DIR, BENCHMARK_DIR
from src.dem_handler import DEMHandler
from src.borehole_processor import BoreholeProcessor
from src.digital_twin_engine import SubsurfaceDigitalTwinEngine
from src.visualizer_3d import build_interactive_3d_digital_twin_scene, build_interactive_3d_borehole_scene


def test_3d_digital_twin_scene():
    dem = DEMHandler(DEM_DIR / "site_dem.tif")
    twin = SubsurfaceDigitalTwinEngine(
        grid_x=dem.mesh_x,
        grid_y=dem.mesh_y,
        surface_dem=dem.data,
        strata_bottom_surfaces=[dem.data - 4.0, dem.data - 10.0],
        strata_names=["Upper Silt", "Lower Clay"]
    )
    
    fig = build_interactive_3d_digital_twin_scene(twin, stress_metric="effective_stress_kpa")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 4  # DTM, water table, strata surfaces, voxels, sensors
    
    # Check that trace types include Surface and Scatter3d
    types = [t.type for t in fig.data]
    assert "surface" in types
    assert "scatter3d" in types


def test_3d_borehole_scene():
    dem = DEMHandler(DEM_DIR / "site_dem.tif")
    bh = BoreholeProcessor(BENCHMARK_DIR / "boreholes_benchmark.csv", dem_handler=dem)
    
    fig = build_interactive_3d_borehole_scene(dem, bh.processed_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 10
    types = [t.type for t in fig.data]
    assert "surface" in types
    assert "scatter3d" in types
