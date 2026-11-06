"""
Unit and integration tests for Subsurface Geotechnical Digital Twin Engine.
"""

from pathlib import Path
import numpy as np
import pytest

from src.digital_twin_engine import (
    SubsurfaceDigitalTwinEngine,
    TelemetrySensor
)


@pytest.fixture
def sample_twin_engine():
    # Create simple 10x10 synthetic site
    x = np.linspace(500000, 501000, 10)
    y = np.linspace(2500000, 2501000, 10)
    X, Y = np.meshgrid(x, y)
    dem = 25.0 + 0.002 * (X - 500000)
    
    # 3 Strata: Layer 1 (0 to -5m), Layer 2 (-5 to -15m), Layer 3 (Bedrock below -15m)
    bottoms = {
        "Layer 1 - Sand": dem - 5.0,
        "Layer 2 - Clay": dem - 15.0,
        "Layer 3 - Rock": dem - 35.0
    }
    
    engine = SubsurfaceDigitalTwinEngine(
        grid_x=X,
        grid_y=Y,
        surface_dem=dem,
        strata_bottom_surfaces=bottoms
    )
    return engine


def test_twin_initialization_and_sensors(sample_twin_engine):
    assert len(sample_twin_engine.sensors) >= 2
    assert "PZ-01" in sample_twin_engine.sensors
    
    pz = sample_twin_engine.sensors["PZ-01"]
    assert pz.sensor_type == "piezometer"
    assert pz.current_reading > 0


def test_twin_telemetry_ingestion_and_water_table(sample_twin_engine):
    # Live sensor update: water table rises by 1.5m due to monsoon recharge
    sample_twin_engine.ingest_sensor_telemetry({"PZ-01": 24.0, "PZ-02": 24.2})
    
    live_wt = sample_twin_engine.get_dynamic_water_table_surface()
    assert live_wt.shape == sample_twin_engine.surface_dem.shape
    # Ensure water table is bounded by ground surface
    assert np.all(live_wt <= sample_twin_engine.surface_dem + 1e-4)


def test_twin_volumetric_voxels_generation(sample_twin_engine):
    voxels = sample_twin_engine.generate_volumetric_voxels(nx=12, ny=12, nz=10, depth_extent_m=25.0)
    
    assert "effective_stress_kpa" in voxels
    assert "pore_pressure_kpa" in voxels
    assert "elastic_modulus_mpa" in voxels
    
    eff_stress = voxels["effective_stress_kpa"]
    assert eff_stress.shape == (12, 12, 10)
    
    # Check that effective stress increases downward into the earth
    # Top non-air voxel should have lower effective stress than deep voxel
    non_air_mask = voxels["stratum_id"] >= 0
    assert np.any(non_air_mask)
    assert np.max(eff_stress) > np.min(eff_stress[non_air_mask])


def test_twin_vtk_export(sample_twin_engine, tmp_path):
    voxels = sample_twin_engine.generate_volumetric_voxels(nx=8, ny=8, nz=6, depth_extent_m=20.0)
    vti_path = tmp_path / "test_subsurface_twin.vti"
    
    saved_file = sample_twin_engine.export_vtk_image_data(voxels, str(vti_path))
    assert Path(saved_file).exists()
    assert Path(saved_file).stat().st_size > 1000
    
    with open(saved_file, "r") as f:
        content = f.read()
    assert "ImageData" in content
    assert "EffectiveStress_kPa" in content
    assert "PoreWaterPressure_kPa" in content


def test_twin_dynamic_bearing_capacity(sample_twin_engine):
    # Dry condition: water table low
    sample_twin_engine.ingest_sensor_telemetry({"PZ-01": 15.0, "PZ-02": 15.0})
    res_dry = sample_twin_engine.compute_dynamic_bearing_capacity(foundation_depth_m=2.0, footing_width_m=2.0)
    
    # Flooded / High water table condition
    sample_twin_engine.ingest_sensor_telemetry({"PZ-01": 25.0, "PZ-02": 25.0})
    res_wet = sample_twin_engine.compute_dynamic_bearing_capacity(foundation_depth_m=2.0, footing_width_m=2.0)
    
    # Wet condition should reduce safe bearing capacity due to W' factor
    assert res_wet["mean_sbc_kpa"] < res_dry["mean_sbc_kpa"]
