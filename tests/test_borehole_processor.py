"""
Unit tests for the Borehole Processor.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.borehole_processor import BoreholeProcessor
from src.dem_handler import DEMHandler
from src.config import BENCHMARK_DIR, DEM_DIR


@pytest.fixture
def sample_processor():
    csv_path = BENCHMARK_DIR / "boreholes_benchmark.csv"
    dem_path = DEM_DIR / "site_dem.tif"
    dem = DEMHandler(dem_path)
    return BoreholeProcessor(csv_path, dem_handler=dem)


def test_borehole_processing_layers(sample_processor):
    df = sample_processor.processed_df
    assert df is not None
    assert len(df) == 100
    assert "Layer_Bottom_RL_m" in df.columns
    assert "Thickness_m" in df.columns
    
    # Layer_Bottom_RL = Surface_RL - Depth_To
    diff = np.abs(df["Layer_Bottom_RL_m"] - (df["Surface_RL_m"] - df["Depth_To_m"]))
    assert np.all(diff < 0.05)


def test_borehole_summary(sample_processor):
    summary = sample_processor.borehole_summary
    assert summary is not None
    assert len(summary) == 20
    assert "Termination_RL_m" in summary.columns
    assert "Water_Table_RL_m" in summary.columns
    assert np.all(summary["Termination_RL_m"] < summary["Surface_RL_m"])
