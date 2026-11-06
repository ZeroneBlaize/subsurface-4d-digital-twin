"""
Unit tests for BoreholeLiteratureScraper.
"""

from pathlib import Path
import pytest
import pandas as pd

from src.borehole_scraper import BoreholeLiteratureScraper
from src.spatial_database import SubsurfaceSpatialDatabase


@pytest.fixture
def test_scraper(tmp_path):
    db_file = tmp_path / "test_scraper.duckdb"
    db = SubsurfaceSpatialDatabase(db_path=db_file)
    scraper = BoreholeLiteratureScraper(spatial_db=db)
    return scraper


def test_column_normalization(test_scraper):
    raw_df = pd.DataFrame({
        "Bore_ID": ["BH-101", "BH-101"],
        "From_Depth": [0.0, 3.0],
        "To_Depth": [3.0, 8.0],
        "Lithology": ["Topsoil", "Silty Clay"],
        "SPT_N": [4, 12],
        "Ground_Level": [25.4, 25.4]
    })
    
    clean_df = test_scraper.normalize_tabular_columns(raw_df)
    assert "Borehole_ID" in clean_df.columns
    assert "Depth_Top_m" in clean_df.columns
    assert "Depth_Bottom_m" in clean_df.columns
    assert "Layer_Name" in clean_df.columns
    assert "Field_N" in clean_df.columns
    assert "Ground_RL_m" in clean_df.columns


def test_borehole_synthesis(test_scraper):
    df = test_scraper.synthesize_scraped_boreholes(
        city="Delhi", state="Delhi NCR", province="Indo-Gangetic Deep Alluvium",
        center_lat=28.6139, center_lon=77.2090, count=4, depth_m=20.0
    )
    assert not df.empty
    assert len(df["Borehole_ID"].unique()) == 4
    assert "Field_N" in df.columns
    assert "Layer_Name" in df.columns
    assert "IS_1498_Class" in df.columns
    assert df["Depth_Bottom_m"].max() <= 21.0


def test_auto_harvest_and_ingest(test_scraper):
    res = test_scraper.auto_harvest_and_ingest(
        query="geotechnical borehole India", limit=2, target_city="Chennai"
    )
    assert res["status"] == "SUCCESS"
    assert res["boreholes_ingested"] >= 4
    stats = test_scraper.spatial_db.get_database_stats()
    assert stats["total_boreholes"] >= 4
    assert stats["total_strata_layers"] >= 12
