"""
Automated Unit and Integration Tests for the Indian Landmass Generative Subsurface Engine.
Verifies Coupled Markov Chain, Gaussian random fields, province auto-detection,
borehole synthesis, real dataset calibration, and end-to-end pipeline execution.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.generative_subsurface import (
    IndianGeologicalProvince,
    PROVINCE_REGISTRY,
    StratumProfile,
    ProvinceMetadata,
    CoupledMarkovModel,
    SpatialFieldSynthesizer,
    GeotechnicalCalibrator,
    IndianSubsurfaceSynthesizer,
)
from src.dem_handler import DEMHandler
from src.borehole_processor import BoreholeProcessor
from src.spatial_interpolator import SpatialInterpolator
from src.geotech_engine import GeotechEngine
from src.config import GeotechConfig, PROJECT_ROOT


# ---------------------------------------------------------------------------
# 1. PROVINCE REGISTRY & AUTO-DETECTION TESTS
# ---------------------------------------------------------------------------

def test_province_registry_completeness():
    """Verify that all 5 major Indian provinces are registered with complete strata and metadata."""
    assert len(PROVINCE_REGISTRY) == 5
    for prov in IndianGeologicalProvince:
        assert prov in PROVINCE_REGISTRY
        meta = PROVINCE_REGISTRY[prov]
        assert len(meta.strata) >= 4
        assert len(meta.typical_cities) >= 2
        assert meta.elevation_range[1] > meta.elevation_range[0]
        assert meta.water_table_depth_mean > 0.0
        assert len(meta.horizontal_k_values) == len(meta.strata)

        # Check refusal on final bedrock stratum
        assert meta.strata[-1].is_refusal is True


def test_auto_detect_province():
    """Verify coordinate classification across representative Indian cities."""
    synth = IndianSubsurfaceSynthesizer(calibrate_on_defaults=False)

    # Northern Alluvium
    assert synth.auto_detect_province(28.6139, 77.2090) == IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM  # Delhi
    assert synth.auto_detect_province(26.4499, 80.3319) == IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM  # Kanpur
    assert synth.auto_detect_province(25.5941, 85.1376) == IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM  # Patna

    # Deccan Basalt Traps
    assert synth.auto_detect_province(19.0760, 72.8777) == IndianGeologicalProvince.DECCAN_BASALT_TRAPS  # Mumbai
    assert synth.auto_detect_province(18.5204, 73.8567) == IndianGeologicalProvince.DECCAN_BASALT_TRAPS  # Pune
    assert synth.auto_detect_province(21.1458, 79.0882) == IndianGeologicalProvince.DECCAN_BASALT_TRAPS  # Nagpur

    # Peninsular Archaean
    assert synth.auto_detect_province(12.9716, 77.5946) == IndianGeologicalProvince.PENINSULAR_ARCHAEAN  # Bengaluru
    assert synth.auto_detect_province(17.3850, 78.4867) == IndianGeologicalProvince.PENINSULAR_ARCHAEAN  # Hyderabad

    # Coastal Deltaic
    assert synth.auto_detect_province(22.5600, 88.3100) == IndianGeologicalProvince.COASTAL_DELTAIC  # Howrah
    assert synth.auto_detect_province(22.5726, 88.3639) == IndianGeologicalProvince.COASTAL_DELTAIC  # Kolkata

    # Himalayan Foreland
    assert synth.auto_detect_province(30.3165, 78.0322) == IndianGeologicalProvince.HIMALAYAN_FORELAND  # Dehradun
    assert synth.auto_detect_province(32.7266, 74.8570) == IndianGeologicalProvince.HIMALAYAN_FORELAND  # Jammu


def test_auto_detect_province_out_of_bounds():
    """Verify that coordinates outside India raise ValueError in strict mode."""
    synth = IndianSubsurfaceSynthesizer(calibrate_on_defaults=False)

    # Southern hemisphere / Africa
    with pytest.raises(ValueError, match="fall outside the geographic bounds of the Indian landmass"):
        synth.auto_detect_province(-10.0, 20.0, strict=True)

    # High latitude Europe / Russia
    with pytest.raises(ValueError, match="fall outside the geographic bounds of the Indian landmass"):
        synth.auto_detect_province(52.5200, 13.4050, strict=True)

    # Pacific Ocean
    with pytest.raises(ValueError, match="fall outside the geographic bounds of the Indian landmass"):
        synth.auto_detect_province(15.0, 140.0, strict=True)

    # Soft mode (strict=False) returns nearest centroid without error
    soft_res = synth.auto_detect_province(-10.0, 20.0, strict=False)
    assert isinstance(soft_res, IndianGeologicalProvince)


def test_utm_epsg_calculation():
    """Verify WGS84 UTM Zone EPSG selection across longitudes in India."""
    # Mumbai ~72.8°E -> UTM Zone 43N -> EPSG:32643
    assert IndianSubsurfaceSynthesizer.get_utm_epsg(72.8) == "EPSG:32643"
    # Delhi / Nagpur ~78-79°E -> UTM Zone 44N -> EPSG:32644
    assert IndianSubsurfaceSynthesizer.get_utm_epsg(78.5) == "EPSG:32644"
    # Kolkata / Howrah ~88.3°E -> UTM Zone 45N -> EPSG:32645
    assert IndianSubsurfaceSynthesizer.get_utm_epsg(88.3) == "EPSG:32645"


# ---------------------------------------------------------------------------
# 2. COUPLED MARKOV CHAIN (CMC) MODEL TESTS
# ---------------------------------------------------------------------------

def test_coupled_markov_row_normalization():
    """Verify stochastic matrix properties (row sums == 1.0)."""
    cmc = CoupledMarkovModel(num_states=4)
    freq = np.array([
        [10.0, 5.0, 0.0, 0.0],
        [0.0, 8.0, 4.0, 0.0],
        [0.0, 0.0, 12.0, 2.0],
        [0.0, 0.0, 0.0, 0.0],  # Zero row test
    ])
    prob = cmc.row_normalize(freq)

    # All rows must sum to exactly 1.0
    for r in range(4):
        assert pytest.approx(prob[r].sum(), 1e-6) == 1.0
    # Zero row should have probability 1.0 on diagonal
    assert prob[3, 3] == 1.0


def test_coupled_markov_sequence_fitting_and_simulation():
    """Verify transition fitting and 1D stochastic sequence generation."""
    cmc = CoupledMarkovModel(num_states=3, k_values=[10.0, 15.0, 20.0])
    sequences = [
        [0, 0, 0, 1, 1, 2, 2],
        [0, 0, 1, 1, 1, 2, 2],
        [0, 1, 1, 2, 2, 2, 2],
    ]
    cmc.fit_from_sequences(sequences)

    # Check vertical transition probabilities
    assert cmc.vertical_prob.shape == (3, 3)
    for r in range(3):
        assert pytest.approx(cmc.vertical_prob[r].sum(), 1e-6) == 1.0

    # Simulate 1D sequence
    rng = np.random.default_rng(42)
    sim_seq = cmc.simulate_1d_sequence(num_steps=15, initial_state=0, rng=rng)
    assert len(sim_seq) == 15
    assert sim_seq[0] == 0
    assert all(0 <= s < 3 for s in sim_seq)


def test_coupled_markov_2d_profile_conditioning():
    """Verify that 2D Coupled Markov simulation preserves conditioning borehole layers."""
    cmc = CoupledMarkovModel(num_states=4)
    # Uniform transition setup
    cmc.vertical_prob = np.eye(4) * 0.7 + 0.1
    cmc.vertical_prob = cmc.row_normalize(cmc.vertical_prob)
    cmc.horizontal_prob_1step = np.eye(4) * 0.8 + 0.05
    cmc.horizontal_prob_1step = cmc.row_normalize(cmc.horizontal_prob_1step)

    num_rows, num_cols = 20, 30
    cond_cols = [0, 14, 29]
    cond_layers = np.zeros((num_rows, 3), dtype=np.int32)
    cond_layers[:, 0] = 0  # Column 0 is all stratum 0
    cond_layers[:, 1] = 1  # Column 14 is all stratum 1
    cond_layers[:, 2] = 2  # Column 29 is all stratum 2

    rng = np.random.default_rng(101)
    profile = cmc.simulate_2d_profile(
        conditioning_cols=cond_cols,
        conditioning_layers=cond_layers,
        num_cols=num_cols,
        num_rows=num_rows,
        rng=rng
    )

    assert profile.shape == (num_rows, num_cols)
    # Check strict preservation at conditioning columns
    assert np.all(profile[:, 0] == 0)
    assert np.all(profile[:, 14] == 1)
    assert np.all(profile[:, 29] == 2)


def test_coupled_markov_information_entropy():
    """Verify Shannon information entropy computation and zero-uncertainty at boreholes."""
    r1 = np.array([[0, 1], [0, 1]])
    r2 = np.array([[0, 1], [0, 1]])
    prob_3d, entropy = CoupledMarkovModel.compute_information_entropy([r1, r2], num_states=2)

    assert entropy.shape == (2, 2)
    # Both realizations are identical, so probabilities are 1.0, entropy must be 0.0
    assert np.allclose(entropy, 0.0, atol=1e-5)

    # Divergent realizations
    r3 = np.array([[0, 0], [0, 0]])
    r4 = np.array([[1, 1], [1, 1]])
    _, entropy_max = CoupledMarkovModel.compute_information_entropy([r3, r4], num_states=2)
    # Equal 50/50 probabilities -> Entropy should equal log2(2) = 1.0 bit
    assert np.allclose(entropy_max, 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# 3. SPATIAL FIELD & DEM TOPOGRAPHY TESTS
# ---------------------------------------------------------------------------

def test_spatial_field_generator():
    """Verify Gaussian random field statistical properties."""
    rng = np.random.default_rng(42)
    field = SpatialFieldSynthesizer.generate_gaussian_field(nx=80, ny=80, correlation_length_cells=15.0, rng=rng)
    assert field.shape == (80, 80)
    assert pytest.approx(field.mean(), abs=0.1) == 0.0
    assert pytest.approx(field.std(), abs=0.1) == 1.0


def test_synthesize_terrain_dem_elevation_bounds():
    """Verify synthetic DEM elevations remain strictly within regional geological bounds."""
    for prov in IndianGeologicalProvince:
        meta = PROVINCE_REGISTRY[prov]
        dem = SpatialFieldSynthesizer.synthesize_terrain_dem(prov, nx=50, ny=50, resolution=10.0)
        assert dem.shape == (50, 50)
        assert dem.min() >= meta.elevation_range[0] - 1.0
        assert dem.max() <= meta.elevation_range[1] + 1.0


# ---------------------------------------------------------------------------
# 4. BOREHOLE SYNTHESIS & SCHEMA TESTS
# ---------------------------------------------------------------------------

def test_synthesize_boreholes_schema_and_physics(tmp_path):
    """Verify synthetic boreholes conform strictly to schema and physical rules."""
    synth = IndianSubsurfaceSynthesizer(calibrate_on_defaults=True)

    # 1. Synthesize small DEM
    dem_file = tmp_path / "test_site_dem.tif"
    dem_arr, transform, crs_str, _ = synth.synthesize_site_dem(
        output_path=dem_file,
        province=IndianGeologicalProvince.DECCAN_BASALT_TRAPS,
        extent_m=800.0,
        resolution=10.0,
        random_seed=42
    )

    # 2. Synthesize boreholes
    num_bhs = 8
    bh_df = synth.synthesize_boreholes(
        province=IndianGeologicalProvince.DECCAN_BASALT_TRAPS,
        num_boreholes=num_bhs,
        dem_data=dem_arr,
        transform=transform,
        random_seed=42
    )

    # Required columns
    expected_cols = [
        "Borehole_ID", "Easting_m", "Northing_m", "Surface_RL_m", "Layer_Index", "Layer_Name",
        "Depth_From_m", "Depth_To_m", "Thickness_m", "Layer_Bottom_RL_m", "Field_N", "Soil_Type",
        "Cohesion_kPa", "Friction_Angle_deg", "Unit_Weight_kN_m3", "Water_Table_Depth_m",
        "Refusal_Reached", "Is_Pinchout"
    ]
    for col in expected_cols:
        assert col in bh_df.columns

    assert bh_df["Borehole_ID"].nunique() == num_bhs

    # Verify physical consistency per borehole
    for bh_id, grp in bh_df.groupby("Borehole_ID"):
        # Depths non-decreasing
        assert np.all(grp["Depth_To_m"] >= grp["Depth_From_m"])
        # Thicknesses non-negative
        assert np.all(grp["Thickness_m"] >= 0.0)
        # Reduced levels monotonically non-increasing
        assert np.all(np.diff(grp["Layer_Bottom_RL_m"]) <= 0.001)
        # Surface RL matches Layer 1 top
        first_row = grp.iloc[0]
        assert pytest.approx(first_row["Surface_RL_m"] - first_row["Depth_From_m"], 0.01) == first_row["Surface_RL_m"]
        # Water table depth positive
        assert first_row["Water_Table_Depth_m"] > 0.0

    # Bedrock refusal check
    bedrock_rows = bh_df[bh_df["Layer_Name"] == "Hard Basalt (Bedrock)"]
    assert np.all(bedrock_rows["Refusal_Reached"] == True)
    assert np.all(bedrock_rows["Field_N"] >= 50)


# ---------------------------------------------------------------------------
# 5. REAL DATA CALIBRATION TESTS
# ---------------------------------------------------------------------------

def test_calibrator_on_howrah_dataset():
    """Verify calibration against real Howrah Shalimar borehole records."""
    howrah_path = PROJECT_ROOT / "data/raw/howrah_boreholes_parsed.csv"
    if not howrah_path.exists():
        pytest.skip("Howrah dataset not found.")

    df = pd.read_csv(howrah_path)
    calib = GeotechnicalCalibrator.calibrate_from_dataframe(df)

    assert len(calib["layer_names"]) == 5
    assert "Firm Brown Silty Clay" in calib["strata_stats"]
    assert "Dense Silty Sand" in calib["strata_stats"]

    # Verify Howrah water table calibration (~1.02m)
    assert pytest.approx(calib["water_table_mean"], 0.2) == 1.02

    # Check peaty clay N-value calibration (~2.8)
    peat_stats = calib["strata_stats"]["Soft Peaty Silty Clay"]
    assert pytest.approx(peat_stats["field_n_mean"], 0.5) == 2.8


def test_calibrator_on_deccan_benchmark():
    """Verify calibration against Deccan basalt benchmark dataset."""
    deccan_path = PROJECT_ROOT / "data/benchmark/boreholes_benchmark.csv"
    if not deccan_path.exists():
        pytest.skip("Deccan benchmark dataset not found.")

    df = pd.read_csv(deccan_path)
    calib = GeotechnicalCalibrator.calibrate_from_dataframe(df)

    assert len(calib["layer_names"]) == 5
    assert "Weathered Basalt" in calib["strata_stats"]
    assert "Hard Basalt (Bedrock)" in calib["strata_stats"]

    # Verify murrum pinch-out rate detection (2 pinch-outs out of 20 = 10%)
    murrum_stats = calib["strata_stats"]["Stiff Sandy Silt / Murrum"]
    assert pytest.approx(murrum_stats["pinchout_prob"], 0.05) == 0.10


# ---------------------------------------------------------------------------
# 6. END-TO-END INTEGRATION TEST
# ---------------------------------------------------------------------------

def test_generative_pipeline_end_to_end(tmp_path):
    """
    Executes the full end-to-end generative workflow:
    Synthesize DEM & Boreholes -> BoreholeProcessor -> SpatialInterpolator ->
    Stratigraphic Stacking -> GeotechEngine -> Coupled Markov Simulation.
    """
    synth = IndianSubsurfaceSynthesizer()
    dem_path = tmp_path / "site_e2e_dem.tif"

    # 1. Synthesize DEM for Kolkata / Bengal Delta
    dem_arr, transform, crs_str, _ = synth.synthesize_site_dem(
        output_path=dem_path,
        province=IndianGeologicalProvince.COASTAL_DELTAIC,
        center_lat=22.5726,
        center_lon=88.3639,
        extent_m=1000.0,
        resolution=10.0,
        random_seed=123
    )
    dem_handler = DEMHandler(dem_path)
    assert dem_handler.width == 100
    assert dem_handler.height == 100

    # 2. Synthesize Boreholes
    bh_df = synth.synthesize_boreholes(
        province=IndianGeologicalProvince.COASTAL_DELTAIC,
        num_boreholes=10,
        dem_data=dem_arr,
        transform=transform,
        random_seed=123
    )
    assert len(bh_df) == 50  # 10 bhs * 5 strata

    # 3. Borehole Processor
    bp = BoreholeProcessor(bh_df, dem_handler=dem_handler)
    summary_df = bp.borehole_summary
    assert len(summary_df) == 10

    # 4. Spatial Interpolation & Stacking
    interpolator = SpatialInterpolator(dem_handler.mesh_x, dem_handler.mesh_y, boundary_buffer_m=40.0)
    interpolator.fit_survey_boundary(summary_df["Easting_m"].values, summary_df["Northing_m"].values)

    strata_names = [s.name for s in PROVINCE_REGISTRY[IndianGeologicalProvince.COASTAL_DELTAIC].strata]
    raw_surfaces = []
    for name in strata_names:
        pts = bp.get_layer_points(name)
        valid = pts[pts["Is_Present"] & pts["Layer_Bottom_RL_m"].notnull()]
        grid_z = interpolator.interpolate_idw(valid["Easting_m"].values, valid["Northing_m"].values, valid["Layer_Bottom_RL_m"].values)
        raw_surfaces.append(grid_z)

    corr_surfaces, thicknesses = interpolator.enforce_stratigraphic_stacking(dem_handler.data, raw_surfaces)
    assert len(corr_surfaces) == 5
    assert len(thicknesses) == 5
    # Strict non-crossing: thicknesses >= 0
    for t_grid in thicknesses:
        valid_t = t_grid[~np.isnan(t_grid)]
        assert np.all(valid_t >= -1e-4)

    # 5. Geotechnical Safe Bearing Capacity (IS:6403)
    engine = GeotechEngine(GeotechConfig(footing_width_b=2.0, footing_depth_df=1.5, factor_of_safety=3.0))
    pts_l2 = bp.get_layer_points(strata_names[1])
    n_pts = pts_l2[pts_l2["Is_Present"] & (pts_l2["Field_N"] > 0)]
    interp_n = interpolator.interpolate_idw(n_pts["Easting_m"].values, n_pts["Northing_m"].values, n_pts["Field_N"].values)
    sbc_grid = engine.evaluate_grid_sbc(interp_n, summary_df["Water_Table_Depth_m"].mean(), df_m=1.5, b_m=2.0)

    valid_sbc = sbc_grid[~np.isnan(sbc_grid)]
    assert len(valid_sbc) > 0
    # Soft deltaic clay typical SBC should be in range 40 - 200 kPa
    assert valid_sbc.min() > 30.0
    assert valid_sbc.max() < 300.0

    # 6. Coupled Markov Cross Section Simulation
    markov_res = synth.synthesize_markov_cross_section(bh_df, strata_names, num_cols=50, num_rows=25, num_simulations=4)
    assert len(markov_res["realizations"]) == 4
    assert markov_res["entropy"].shape == (25, 50)
    assert markov_res["entropy"].max() >= 0.0


def test_calibrator_on_cmc_boreholedata():
    """Verify calibration against CoupledMarkov example benchmark dataset."""
    cmc_dir = PROJECT_ROOT / "data/raw/CoupledMarkov/examples/boreholedata"
    if not cmc_dir.exists():
        pytest.skip("CoupledMarkov boreholedata directory not found.")

    calib = GeotechnicalCalibrator.calibrate_from_cmc_boreholedata(cmc_dir)
    assert len(calib["soil_types"]) == 4
    assert len(calib["k_values"]) == 4
    assert calib["k_values"][0] == 12.4
    assert len(calib["discretized_sequences"]) == 12
    assert "Layer 1" in calib["strata_stats"]
    assert calib["strata_stats"]["Layer 1"]["thickness_mean"] > 0.0


def test_calibrated_synthesis_applies_parameters():
    """Verify that synthesizer applies empirical calibrated statistics to synthetic models."""
    synth = IndianSubsurfaceSynthesizer(calibrate_on_defaults=True)

    # 1. Coastal Deltaic should be calibrated on Howrah dataset
    delta_meta = synth.province_metadata[IndianGeologicalProvince.COASTAL_DELTAIC]
    assert pytest.approx(delta_meta.water_table_depth_mean, 0.2) == 1.02

    # 2. Deccan Basalt should have murrum pinchout rate ~0.10
    deccan_meta = synth.province_metadata[IndianGeologicalProvince.DECCAN_BASALT_TRAPS]
    murrum_stratum = next(s for s in deccan_meta.strata if "Murrum" in s.name)
    assert pytest.approx(murrum_stratum.pinchout_prob, 0.05) == 0.10

    # 3. Synthesized boreholes reflect calibrated water table
    bh_df = synth.synthesize_boreholes(IndianGeologicalProvince.COASTAL_DELTAIC, num_boreholes=8, random_seed=42)
    assert bh_df["Water_Table_Depth_m"].mean() < 2.0


def test_coupled_markov_discretized_persistence():
    """Verify that vertical depth discretization produces diagonal-dominant transition matrices."""
    howrah_path = PROJECT_ROOT / "data/raw/howrah_boreholes_parsed.csv"
    if not howrah_path.exists():
        pytest.skip("Howrah dataset not found.")

    df = pd.read_csv(howrah_path)
    synth = IndianSubsurfaceSynthesizer()
    strata_names = [
        "Topsoil / Fill",
        "Firm Brown Silty Clay",
        "Soft Peaty Silty Clay",
        "Stiff Bluish Grey Clay",
        "Dense Silty Sand"
    ]
    res = synth.synthesize_markov_cross_section(
        borehole_df=df,
        strata_names=strata_names,
        num_cols=40,
        num_rows=30,
        num_simulations=2
    )

    vert_prob = res["vertical_prob"]
    horiz_prob = res["horizontal_prob"]

    # Vertical self-transition should be positive and diagonal-dominant (not 0.0!)
    for s in range(len(strata_names)):
        assert vert_prob[s, s] >= 0.5, f"Vertical self-transition for stratum {s} is too low: {vert_prob[s, s]}"

    # Horizontal self-transition should be highly persistent (> 0.95)
    for s in range(len(strata_names)):
        assert horiz_prob[s, s] >= 0.95, f"Horizontal persistence for stratum {s} is too low: {horiz_prob[s, s]}"


def test_coupled_markov_directional_coupling():
    """Verify Elfeki & Dekking directional choice rule and discrete sampling."""
    rng = np.random.default_rng(42)
    h_prob = np.eye(3) * 0.9 + 0.05

    # Case 1: Left stable, right unstable -> Direction 1 (left to right)
    d1 = CoupledMarkovModel.choose_direction(
        left=0, left_above=0, right=0, right_above=1, prev_direction=2, h_prob_spacing=h_prob, rng=rng
    )
    assert d1 == 1

    # Case 2: Right stable, left unstable -> Direction 2 (right to left)
    d2 = CoupledMarkovModel.choose_direction(
        left=1, left_above=0, right=1, right_above=1, prev_direction=1, h_prob_spacing=h_prob, rng=rng
    )
    assert d2 == 2

    # Case 3: Both unchanged -> keep prev_direction
    d3 = CoupledMarkovModel.choose_direction(
        left=0, left_above=0, right=0, right_above=0, prev_direction=2, h_prob_spacing=h_prob, rng=rng
    )
    assert d3 == 2

    # Discrete sampling
    w = np.array([0.0, 1.0, 0.0])
    s = CoupledMarkovModel.sample_discrete(w, rng=rng)
    assert s == 1


def test_gis_exporter_crs_object(tmp_path):
    """Verify GISExporter accepts both rasterio CRS object and string."""
    from rasterio.crs import CRS
    from rasterio.transform import Affine
    from src.exporter import GISExporter

    crs_obj = CRS.from_epsg(32644)
    exporter = GISExporter(Affine.identity(), crs_str=crs_obj)
    assert exporter.crs.to_epsg() == 32644

    # String CRS
    exporter_str = GISExporter(Affine.identity(), crs_str="EPSG:32645")
    assert exporter_str.crs.to_epsg() == 32645


def test_run_generative_pipeline_default_cli(tmp_path):
    """Verify that run_generative_pipeline handles default None province without KeyError."""
    from run_pipeline import run_generative_pipeline

    out = run_generative_pipeline(
        province_name=None,
        num_boreholes=4,
        extent_m=300.0,
        output_dir=tmp_path / "cli_test_out"
    )
    assert out["province"] == IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM
    assert (tmp_path / "cli_test_out" / "site_synthesized_dem.tif").exists()
    assert (tmp_path / "cli_test_out" / "synthesized_boreholes.csv").exists()
    assert "mean_sbc" in out
    assert out["mean_sbc"] > 0.0


def test_cmc_top_row_horizontal_coupling():
    """Verify top row (row 0) between conditioning boreholes is horizontally coupled via Markov bridge."""
    cmc = CoupledMarkovModel(num_states=3, k_values=[15.0, 15.0, 15.0])
    cmc.vertical_prob = np.eye(3) * 0.8 + 0.1
    cmc.vertical_prob = cmc.row_normalize(cmc.vertical_prob)
    # Banded horizontal transition
    cmc.horizontal_prob_1step = np.array([
        [0.7, 0.3, 0.0],
        [0.2, 0.6, 0.2],
        [0.0, 0.3, 0.7],
    ])

    num_rows, num_cols = 10, 20
    cond_cols = [0, 19]
    cond_layers = np.zeros((num_rows, 2), dtype=np.int32)
    cond_layers[:, 0] = 0  # Left column is stratum 0
    cond_layers[:, 1] = 2  # Right column is stratum 2

    rng = np.random.default_rng(42)
    profile = cmc.simulate_2d_profile(
        conditioning_cols=cond_cols,
        conditioning_layers=cond_layers,
        num_cols=num_cols,
        num_rows=num_rows,
        rng=rng
    )

    # Left and right endpoints strictly preserved
    assert profile[0, 0] == 0
    assert profile[0, 19] == 2
    # Row 0 intermediate cells should contain transitions and not be flat 0s or 2s
    row0_unique = np.unique(profile[0, :])
    assert len(row0_unique) >= 2


def test_markov_transect_selection_spans_entire_site():
    """Verify that borehole selection for cross-section spans the entire site transect, not just the left edge."""
    synth = IndianSubsurfaceSynthesizer(calibrate_on_defaults=False)
    # 20 boreholes distributed from Easting 100m to 2000m
    eastings = np.linspace(100.0, 2000.0, 20)
    records = []
    for i, e in enumerate(eastings):
        bh_id = f"BH-{i + 1:02d}"
        for l_idx in range(1, 6):
            records.append({
                "Borehole_ID": bh_id,
                "Easting_m": float(e),
                "Northing_m": 500.0,
                "Surface_RL_m": 50.0,
                "Layer_Index": l_idx,
                "Layer_Name": f"Layer_{l_idx}",
                "Depth_From_m": (l_idx - 1) * 4.0,
                "Depth_To_m": l_idx * 4.0,
                "Thickness_m": 4.0,
                "Layer_Bottom_RL_m": 50.0 - l_idx * 4.0,
                "Field_N": 15,
                "Soil_Type": "Clay",
                "Cohesion_kPa": 20.0,
                "Friction_Angle_deg": 15.0,
                "Unit_Weight_kN_m3": 18.0,
                "Water_Table_Depth_m": 3.0,
                "Refusal_Reached": l_idx == 5,
                "Is_Pinchout": False,
            })
    bh_df = pd.DataFrame(records)
    strata_names = [f"Layer_{i}" for i in range(1, 6)]

    res = synth.synthesize_markov_cross_section(
        borehole_df=bh_df,
        strata_names=strata_names,
        num_cols=80,
        num_rows=30,
        num_simulations=2
    )
    cond_cols = res["conditioning_cols"]
    # With 20 boreholes spanning 100m to 2000m, conditioning cols must span from 0 to 79
    assert len(cond_cols) == 5
    assert cond_cols[0] == 0
    assert cond_cols[-1] == 79
    assert cond_cols[2] > 20 and cond_cols[2] < 60


def test_spt_n_non_refusal_high_strength_stratum():
    """Verify that non-refusal strata with high mean N (e.g. Himalayan Foreland sandstone interbed) are not clamped to 49."""
    synth = IndianSubsurfaceSynthesizer(calibrate_on_defaults=False)
    bh_df = synth.synthesize_boreholes(
        province=IndianGeologicalProvince.HIMALAYAN_FORELAND,
        num_boreholes=15,
        random_seed=42
    )

    sandstone_rows = bh_df[bh_df["Layer_Name"] == "Weak Sandstone / Mudstone Interbed"]
    assert len(sandstone_rows) > 0
    # Field N mean for this stratum is 65.0, should comfortably exceed 49
    max_n = sandstone_rows["Field_N"].max()
    mean_n = sandstone_rows["Field_N"].mean()
    assert max_n > 50, f"Expected N > 50, got max N = {max_n}"
    assert mean_n > 55, f"Expected mean N > 55, got mean N = {mean_n}"


def test_simulate_cmc_benchmark():
    """Verify that simulate_cmc_benchmark executes against CoupledMarkov boreholedata and matches AGENTS.md specs."""
    synth = IndianSubsurfaceSynthesizer()
    res = synth.simulate_cmc_benchmark(num_simulations=4, random_seed=42)

    assert len(res["realizations"]) == 4
    for prof in res["realizations"]:
        # Profiles must contain valid integer soil type indices 0..3 (1..4 in 1-based)
        assert np.all(prof >= 0)
        assert np.all(prof < 4)
        assert not np.isnan(prof).any()

    # Probabilities sum to 1.0 per cell
    probs = res["probabilities"]
    prob_sum = probs.sum(axis=0)
    assert np.allclose(prob_sum, 1.0, atol=1e-5)

    # Entropy in [0, 2] bits for 4 soil states
    entropy = res["entropy"]
    assert entropy.min() >= -1e-5
    assert entropy.max() <= 2.01


def test_cli_partial_coordinates_raises_error():
    """Verify CLI raises clear ValueError when only one of --lat or --lon is provided."""
    import subprocess
    cmd = ["/home/nkm6/miniforge3/bin/python", "run_pipeline.py", "--lat", "28.6139"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode != 0
    assert "Both --lat and --lon must be provided together" in result.stderr or "Both --lat and --lon must be provided together" in result.stdout


def test_run_generative_pipeline_summary_metrics(tmp_path):
    """Verify that run_generative_pipeline returns min_sbc, mean_sbc, max_sbc."""
    from run_pipeline import run_generative_pipeline

    out = run_generative_pipeline(
        province_name="Coastal Deltaic / Soft Marine Deposits",
        num_boreholes=5,
        extent_m=400.0,
        output_dir=tmp_path / "delta_test"
    )
    assert "min_sbc" in out
    assert "mean_sbc" in out
    assert "max_sbc" in out
    assert out["min_sbc"] <= out["mean_sbc"] <= out["max_sbc"]
    assert out["mean_sbc"] > 0.0


def test_extreme_dense_boreholes_100(tmp_path):
    """Verify pipeline and Markov cross-section handle extreme 100 dense boreholes without index collision."""
    synth = IndianSubsurfaceSynthesizer()
    bh_df = synth.synthesize_boreholes(
        province=IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM,
        num_boreholes=100,
        extent_bounds=(100000.0, 2000000.0, 100200.0, 2000200.0),
        random_seed=42
    )
    assert bh_df["Borehole_ID"].nunique() == 100

    strata_names = [s.name for s in synth.province_metadata[IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM].strata]
    markov_res = synth.synthesize_markov_cross_section(
        borehole_df=bh_df,
        strata_names=strata_names,
        num_cols=50,
        num_rows=25,
        num_simulations=2
    )

    cond_cols = markov_res["conditioning_cols"]
    # Check strictly increasing and within bounds
    assert all(0 <= c < 50 for c in cond_cols)
    assert all(cond_cols[i] < cond_cols[i + 1] for i in range(len(cond_cols) - 1))
    assert markov_res["entropy"].shape == (25, 50)


