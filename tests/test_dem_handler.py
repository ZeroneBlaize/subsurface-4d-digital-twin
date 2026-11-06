"""
Unit tests for the DEM Handler and Coordinate Reprojection.
"""

from pathlib import Path
import pytest
import numpy as np

from src.dem_handler import DEMHandler
from src.config import DEM_DIR


@pytest.fixture
def dem_instance():
    dem_path = DEM_DIR / "site_dem.tif"
    if not dem_path.exists():
        from data.generate_benchmark_data import generate_synthetic_dem
        generate_synthetic_dem(dem_path)
    return DEMHandler(dem_path)


def test_dem_metadata(dem_instance):
    assert dem_instance.width == 200
    assert dem_instance.height == 200
    assert dem_instance.data.min() > 200.0
    assert dem_instance.data.max() < 400.0


def test_dem_sampling_center(dem_instance):
    center_x = (dem_instance.bounds.left + dem_instance.bounds.right) / 2.0
    center_y = (dem_instance.bounds.top + dem_instance.bounds.bottom) / 2.0
    elev = dem_instance.sample_elevation(center_x, center_y, method="bilinear")
    assert not np.isnan(elev)
    assert 250.0 < elev < 350.0


def test_dem_sampling_boundary_clip(dem_instance):
    # Sample point slightly outside bounds
    outside_x = dem_instance.bounds.left - 50.0
    outside_y = dem_instance.bounds.top + 50.0
    elev = dem_instance.sample_elevation(outside_x, outside_y)
    assert not np.isnan(elev)  # Should clip safely to edge
