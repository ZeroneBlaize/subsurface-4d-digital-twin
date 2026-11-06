"""
Unit and integration tests for Indian Borehole Literature and Geospatial Map Generator.
"""

from pathlib import Path
import pytest
import pandas as pd
import folium

from src.indian_borehole_map import (
    INDIAN_BOREHOLE_STUDIES,
    BoreholeStudy,
    IndianBoreholeMapGenerator
)


def test_borehole_studies_catalog_integrity():
    assert len(INDIAN_BOREHOLE_STUDIES) >= 10
    
    valid_statuses = {
        "Open Access Repository",
        "Published Tables/Appendix",
        "Restricted/Archival"
    }
    
    for study in INDIAN_BOREHOLE_STUDIES:
        # Check basic identity
        assert isinstance(study.id, str) and len(study.id) > 0
        assert isinstance(study.city, str) and len(study.city) > 0
        assert isinstance(study.state, str) and len(study.state) > 0
        
        # Check Indian landmass bounding box (Lat: ~6°N to 38°N, Lon: ~68°E to 98°E)
        assert 6.0 <= study.latitude <= 38.0, f"Latitude {study.latitude} out of Indian bounds for {study.id}"
        assert 68.0 <= study.longitude <= 98.0, f"Longitude {study.longitude} out of Indian bounds for {study.id}"
        
        # Check geotechnical fields
        assert study.borehole_count > 0
        assert len(study.predominant_strata) >= 2
        assert len(study.spt_n_range) > 0
        assert study.data_access_status in valid_statuses
        assert study.doi_or_url.startswith("http")


def test_map_generator_dataframe():
    generator = IndianBoreholeMapGenerator()
    df = generator.get_summary_dataframe()
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(INDIAN_BOREHOLE_STUDIES)
    assert "city" in df.columns
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "borehole_count" in df.columns
    assert "data_access_status" in df.columns
    assert df["borehole_count"].sum() > 3000


def test_map_generator_folium_build():
    generator = IndianBoreholeMapGenerator()
    m = generator.build_folium_map()
    
    assert isinstance(m, folium.Map)
    html_repr = m.get_root().render()
    assert "Subsurface Borehole Studies Across India" in html_repr
    assert "OpenStreetMap" in html_repr


def test_map_export_html(tmp_path):
    generator = IndianBoreholeMapGenerator()
    out_html = tmp_path / "test_map.html"
    res = generator.export_html(str(out_html))
    
    assert Path(res).exists()
    assert Path(res).stat().st_size > 10000
    with open(res, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Shalimar, Howrah" in content
    assert "Krishna-Godavari Delta" in content
    assert "Bengaluru" in content
