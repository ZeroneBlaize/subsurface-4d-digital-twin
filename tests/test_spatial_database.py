"""
Unit and integration tests for the Subsurface Spatial Database Engine.
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.spatial_database import SubsurfaceSpatialDatabase
from src.config import DB_DIR


@pytest.fixture
def spatial_db(tmp_path):
    """Provides a temporary DuckDB/SQLite database instance."""
    db_file = tmp_path / "test_geotech.duckdb"
    db = SubsurfaceSpatialDatabase(db_path=db_file, use_duckdb=True)
    return db


def test_spatial_database_init(spatial_db):
    stats = spatial_db.get_database_stats()
    assert stats["total_boreholes"] == 0
    assert stats["total_strata_layers"] == 0
    assert stats["backend"] in ["DuckDB", "SQLite3"]


def test_spatial_database_seeding(spatial_db):
    results = spatial_db.auto_seed_all_datasets()
    assert len(results) >= 5
    assert results.get("Howrah", 0) == 14
    assert results.get("Vidarbha", 0) >= 12
    assert results.get("Bangalore", 0) == 15
    assert results.get("RegionalClusters", 0) == 12

    stats = spatial_db.get_database_stats()
    assert stats["total_boreholes"] >= 90
    assert stats["total_strata_layers"] >= 900
    assert stats["total_regional_clusters"] == 12


def test_spatial_database_queries(spatial_db):
    spatial_db.auto_seed_all_datasets()
    
    # 1. Radius Query around Shalimar Howrah (22.56N, 88.31E)
    hwr_bh = spatial_db.query_radius(22.56, 88.31, radius_km=25.0)
    assert not hwr_bh.empty
    assert len(hwr_bh) == 14
    assert "distance_from_center_km" in hwr_bh.columns
    assert hwr_bh["distance_from_center_km"].iloc[0] < 5.0
    
    # 2. Bounding Box Query for Bangalore
    blr_bh = spatial_db.query_bounding_box(min_lat=12.0, max_lat=14.0, min_lon=76.0, max_lon=79.0)
    assert not blr_bh.empty
    assert len(blr_bh) == 15
    
    # 3. Stratigraphy retrieval
    first_gid = hwr_bh["global_id"].iloc[0]
    strata = spatial_db.get_borehole_stratigraphy(first_gid)
    assert not strata.empty
    assert len(strata) >= 3
    assert "field_n" in strata.columns
    assert "layer_name" in strata.columns


def test_spatial_geodataframe_export(spatial_db):
    spatial_db.auto_seed_all_datasets()
    gdf = spatial_db.get_spatial_geodataframe()
    assert not gdf.empty
    assert "geometry" in gdf.columns
    assert gdf.crs.to_string() == "EPSG:4326"
    assert gdf.iloc[0].geometry.geom_type == "Point"
