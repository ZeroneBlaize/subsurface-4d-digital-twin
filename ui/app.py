"""
Interactive Streamlit Application: Subsurface Geospatial Modeling & Bearing Capacity Engine.
Features AI Generative Subsurface Modeling across the Indian Landmass (Coupled Markov Chains & IS:6403).
Run with: streamlit run ui/app.py
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

# Setup path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import (
    DEM_DIR, BENCHMARK_DIR, RASTERS_DIR, VECTORS_DIR, REPORTS_DIR,
    DEFAULT_CRS, STANDARD_STRATA, GeotechConfig
)
from src.dem_handler import DEMHandler
from src.borehole_processor import BoreholeProcessor
from src.spatial_interpolator import SpatialInterpolator
from src.geotech_engine import GeotechEngine
from src.exporter import GISExporter
from src.visualizer import SubsurfaceVisualizer
from src.generative_subsurface import (
    IndianGeologicalProvince, PROVINCE_REGISTRY, IndianSubsurfaceSynthesizer
)
from src.indian_borehole_map import IndianBoreholeMapGenerator
from src.digital_twin_engine import SubsurfaceDigitalTwinEngine
from src.visualizer_3d import build_interactive_3d_digital_twin_scene, build_interactive_3d_borehole_scene
from src.spatial_database import SubsurfaceSpatialDatabase
from src.borehole_scraper import BoreholeLiteratureScraper
from src.landing_counter import get_landing_counter
import streamlit.components.v1 as components


st.set_page_config(
    page_title="Subsurface 4D · Geotechnical Digital Twin",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System (UI/UX Pro Max & Tasteskill 2.5)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif;
}

code, pre, .stCodeBlock {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Header & Title Banner */
.custom-app-header {
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
    border: 1px solid rgba(59, 130, 246, 0.25);
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.custom-title {
    font-size: 1.85rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.custom-subtitle {
    font-size: 0.95rem;
    color: #94a3b8;
    margin: 0 0 0.75rem 0;
    line-height: 1.5;
}

.custom-author-strip {
    display: inline-flex;
    align-items: center;
    gap: 0.625rem;
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    padding: 0.35rem 0.85rem;
    font-size: 0.8125rem;
    color: #cbd5e1;
}

.author-pill {
    font-weight: 600;
    color: #60a5fa;
}

/* Styled Streamlit Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background-color: rgba(15, 23, 42, 0.5);
    border-radius: 10px;
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 0.875rem;
    color: #94a3b8;
    transition: all 150ms ease;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(59, 130, 246, 0.2) !important;
    color: #ffffff !important;
    border: 1px solid rgba(59, 130, 246, 0.4) !important;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: rgba(17, 24, 39, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Buttons */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
    transition: all 150ms ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}
</style>

<div class="custom-app-header">
    <div class="custom-title">
        <span>🏗️ Subsurface Geospatial Modeling & Bearing Capacity Engine</span>
    </div>
    <div class="custom-subtitle">
        4D Cyber-Physical Subsurface Digital Twin, Coupled Markov Chain Transitions, and Automated IS:6403 & IS:2131 Safe Bearing Capacity.
    </div>
    <div class="custom-author-strip">
        <span class="author-pill">Lead Investigator: Sahil Deshpande</span>
        <span>·</span>
        <span>Geotechnical & Computational Engineering</span>
        <span>·</span>
        <span style="color: #34d399;">Computers & Geotechnics Target</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
st.sidebar.header("⚙️ Configuration & Data Source")

data_source = st.sidebar.radio(
    "Select Borehole Data Source:",
    [
        "🇮🇳 AI Generative Subsurface (Indian Landmass)",
        "Real Indian Soil Investigation (14 Boreholes, Howrah WB)",
        "Real Literature Dataset: Maharashtra Vidarbha (IndiaNGMMSM Mendeley Data)",
        "Real Literature Dataset: Bengaluru Urban Microzonation (IISc Bangalore)",
        "Public Benchmark: Rotterdam Deltaic Subsurface (DINOloket / TNO)",
        "Public Benchmark: Coupled Markov Tunnel Alignment (Elfeki Benchmark)",
        "Synthetic Benchmark Dataset (20 Boreholes, Deccan Basalt)",
        "Upload Custom Borehole CSV / Excel"
    ]
)

# Landing & Telemetry Counter
landing_counter = get_landing_counter()
if "visited" not in st.session_state:
    landing_counter.increment_visit()
    st.session_state["visited"] = True
landing_counts = landing_counter.get_counts()

st.sidebar.markdown(f"""
<div style="background: rgba(15,23,42,0.85); border: 1px solid rgba(59,130,246,0.25); border-radius: 8px; padding: 12px; margin-bottom: 16px;">
    <div style="font-size: 10px; color: #94a3b8; font-family: monospace; text-transform: uppercase; letter-spacing: 0.05em;">⚡ Live Landing Counter</div>
    <div style="font-size: 19px; font-weight: 700; color: #38bdf8; font-family: monospace; line-height: 1.2;">{landing_counts['total_visits']:,} Visits</div>
    <div style="font-size: 11px; color: #cbd5e1; margin-top: 4px;">{landing_counts['total_simulations']:,} Simulations · {landing_counts['total_boreholes_processed']:,} Boreholes</div>
</div>
""", unsafe_allow_html=True)

# Province / Synthesis Controls
synth_engine = IndianSubsurfaceSynthesizer()
selected_province = IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM
active_prov = selected_province
site_lat = 28.6139
site_lon = 77.2090
num_synth_bh = 15
site_extent_m = 2000.0
synth_seed = 42

if data_source == "🇮🇳 AI Generative Subsurface (Indian Landmass)":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🇮🇳 Indian Landmass Regional Selector")
    
    geo_mode = st.sidebar.selectbox(
        "Location Mode:",
        ["Geological Province Preset", "Major Indian City Preset", "Custom Geographic Coordinates"]
    )
    
    if geo_mode == "Geological Province Preset":
        prov_options = [p.value for p in IndianGeologicalProvince]
        chosen_prov_val = st.sidebar.selectbox("Select Geological Province:", prov_options, index=0)
        for p in IndianGeologicalProvince:
            if p.value == chosen_prov_val:
                selected_province = p
                break
        meta = PROVINCE_REGISTRY[selected_province]
        _, site_lat, site_lon = meta.typical_cities[0]
        st.sidebar.caption(f"📍 Reference Site: {meta.typical_cities[0][0]} ({site_lat:.2f}°N, {site_lon:.2f}°E)")
        
    elif geo_mode == "Major Indian City Preset":
        city_dict = {
            "Delhi (Indo-Gangetic Alluvium)": (28.6139, 77.2090),
            "Mumbai (Deccan Basalt Traps)": (19.0760, 72.8777),
            "Bengaluru (Peninsular Archaean Granite)": (12.9716, 77.5946),
            "Kolkata / Howrah (Coastal Deltaic)": (22.5726, 88.3639),
            "Hyderabad (Peninsular Archaean)": (17.3850, 78.4867),
            "Chennai (Peninsular / Coastal)": (13.0827, 80.2707),
            "Pune (Deccan Basalt Plateau)": (18.5204, 73.8567),
            "Kanpur (Indo-Gangetic Deep Silt)": (26.4499, 80.3319),
            "Dehradun (Himalayan Foreland)": (30.3165, 78.0322),
            "Jammu (Sub-Himalayan Shiwalik)": (32.7266, 74.8570),
            "Guwahati (Brahmaputra Valley)": (26.1445, 91.7362),
        }
        city_choice = st.sidebar.selectbox("Select Indian City:", list(city_dict.keys()), index=0)
        site_lat, site_lon = city_dict[city_choice]
        selected_province = synth_engine.auto_detect_province(site_lat, site_lon)
        st.sidebar.caption(f"🏛️ Auto-classified Domain: **{selected_province.value}** ({site_lat:.4f}°N, {site_lon:.4f}°E)")

    elif geo_mode == "Custom Geographic Coordinates":
        c1, c2 = st.sidebar.columns(2)
        site_lat = c1.number_input("Latitude (°N):", min_value=-90.0, max_value=90.0, value=28.6139, step=0.1)
        site_lon = c2.number_input("Longitude (°E):", min_value=-180.0, max_value=180.0, value=77.2090, step=0.1)
        try:
            selected_province = synth_engine.auto_detect_province(site_lat, site_lon, strict=True)
            st.sidebar.info(f"Detected Geological Province: **{selected_province.value}**")
        except ValueError as err:
            st.sidebar.error(str(err))
            selected_province = IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM
            meta = PROVINCE_REGISTRY[selected_province]
            _, site_lat, site_lon = meta.typical_cities[0]

    num_synth_bh = st.sidebar.slider("Number of Synthesized Boreholes:", 6, 25, 14, 1)
    site_extent_m = st.sidebar.slider("Survey Site Extent (m):", 1000.0, 3000.0, 2000.0, 250.0)
    synth_seed = st.sidebar.number_input("Stochastic Random Seed:", min_value=1, max_value=999, value=42, step=1)

uploaded_file = None
if data_source == "Upload Custom Borehole CSV / Excel":
    uploaded_file = st.sidebar.file_uploader("Upload Borehole File (.csv, .xlsx)", type=["csv", "xlsx"])

st.sidebar.markdown("---")
st.sidebar.subheader("📐 Geotechnical Design Criteria")
b_m = st.sidebar.slider("Footing Width B (m):", 1.0, 5.0, 2.0, 0.5)
df_m = st.sidebar.slider("Foundation Depth Df (m):", 1.0, 4.0, 2.0, 0.5)
fs_val = st.sidebar.slider("Factor of Safety (FS):", 2.0, 3.5, 3.0, 0.1)
permissible_settlement = st.sidebar.selectbox("Permissible Settlement Limit:", [25.0, 40.0], index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Spatial Interpolation Settings")
interp_method = st.sidebar.selectbox("Interpolation Algorithm:", ["IDW (Inverse Distance Weighting)", "RBF (Radial Basis Functions / Splines)"])
idw_power = st.sidebar.slider("IDW Power Parameter (p):", 1.0, 3.0, 2.0, 0.5)
boundary_buffer = st.sidebar.slider("Convex Hull Boundary Buffer (m):", 20.0, 100.0, 50.0, 10.0)

run_button = st.sidebar.button("🚀 Run Full Pipeline", type="primary", use_container_width=True)

# ----------------- PIPELINE EXECUTION -----------------

@st.cache_data
def get_synthesized_data(prov_val: str, lat_val: float, lon_val: float, n_bhs: int, ext_m: float, seed_val: int):
    p_enum = None
    for p in IndianGeologicalProvince:
        if p.value == prov_val:
            p_enum = p
            break
    if p_enum is None:
        p_enum = IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM

    dem_slug = f"{p_enum.name.lower()}_{int(round(lat_val * 100))}_{int(round(lon_val * 100))}_{int(ext_m)}_{seed_val}"
    out_dem = DEM_DIR / f"ui_synth_dem_{dem_slug}.tif"
    dem_arr, transform, crs_str, _ = synth_engine.synthesize_site_dem(
        output_path=out_dem,
        province=p_enum,
        center_lat=lat_val,
        center_lon=lon_val,
        extent_m=ext_m,
        resolution=10.0,
        random_seed=seed_val
    )
    bh_df = synth_engine.synthesize_boreholes(
        province=p_enum,
        num_boreholes=n_bhs,
        dem_data=dem_arr,
        transform=transform,
        random_seed=seed_val
    )
    meta = PROVINCE_REGISTRY[p_enum]
    strata = [s.name for s in meta.strata]
    return out_dem, bh_df, strata, p_enum


# Load or synthesize dataset
if data_source == "🇮🇳 AI Generative Subsurface (Indian Landmass)":
    dem_path, bh_input, active_strata, active_prov = get_synthesized_data(
        selected_province.value, site_lat, site_lon, num_synth_bh, site_extent_m, synth_seed
    )
    dem_handler = DEMHandler(dem_path)
elif "Howrah" in data_source:
    dem_path = DEM_DIR / "howrah_dem.tif"
    dem_handler = DEMHandler(dem_path)
    bh_input = ROOT_DIR / "data/raw/howrah_boreholes_parsed.csv"
    active_strata = [
        "Topsoil / Fill",
        "Firm Brown Silty Clay",
        "Soft Peaty Silty Clay",
        "Stiff Bluish Grey Clay",
        "Dense Silty Sand"
    ]
elif "Vidarbha" in data_source:
    dem_path = DEM_DIR / "vidarbha_dem.tif"
    dem_handler = DEMHandler(dem_path)
    bh_input = ROOT_DIR / "data/raw/vidarbha_boreholes_parsed.csv"
    active_strata = [
        "Topsoil / Clayey Silt",
        "Expansive Black Cotton Clay (CH)",
        "Inorganic Silt of Low Plasticity (ML)",
        "Intermediate Silt (MI)",
        "Stiff Silt with Kankar",
        "Silty Sand (SM)",
        "Dense Basaltic Silt / Murrum"
    ]
elif "Bengaluru" in data_source:
    dem_path = DEM_DIR / "bangalore_dem.tif"
    dem_handler = DEMHandler(dem_path)
    bh_input = ROOT_DIR / "data/raw/bangalore_boreholes_parsed.csv"
    active_strata = [
        "Red Gravelly Sand / Laterite",
        "Silty Clay / Saprolite",
        "Completely Weathered Granite",
        "Hard Granite-Gneiss Bedrock"
    ]
elif "Rotterdam" in data_source:
    dem_path = DEM_DIR / "rotterdam_dem.tif"
    dem_handler = DEMHandler(dem_path)
    bh_input = ROOT_DIR / "data/raw/rotterdam_boreholes_parsed.csv"
    active_strata = [
        "Made Ground / Fill",
        "Soft Clay (Klei)",
        "Peat (Veen)",
        "Silty Sand / Loam",
        "Medium Dense Sand",
        "Gravelly Sand"
    ]
elif "Coupled Markov" in data_source:
    dem_path = DEM_DIR / "coupled_markov_dem.tif"
    dem_handler = DEMHandler(dem_path)
    bh_input = ROOT_DIR / "data/raw/coupled_markov_boreholes_parsed.csv"
    active_strata = [
        "Alluvial Silty Sand",
        "Soft Marine Silt-Clay",
        "Dense Glacial Till / Sand",
        "Bedrock Basement"
    ]
elif "Synthetic Benchmark" in data_source:
    dem_path = DEM_DIR / "site_dem.tif"
    if not dem_path.exists():
        from data.generate_benchmark_data import generate_synthetic_dem
        generate_synthetic_dem(dem_path)
    dem_handler = DEMHandler(dem_path)
    bh_input = BENCHMARK_DIR / "boreholes_benchmark.csv"
    if not bh_input.exists():
        from data.generate_benchmark_data import generate_synthetic_boreholes
        generate_synthetic_boreholes(dem_handler.data, dem_handler.transform, bh_input, bh_input.with_suffix(".xlsx"))
    active_strata = STANDARD_STRATA
else:
    dem_path = DEM_DIR / "site_dem.tif"
    dem_handler = DEMHandler(dem_path)
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".xlsx"):
            bh_input = pd.read_excel(uploaded_file)
        else:
            bh_input = pd.read_csv(uploaded_file)
        active_strata = STANDARD_STRATA
    else:
        bh_input = BENCHMARK_DIR / "boreholes_benchmark.csv"
        active_strata = STANDARD_STRATA

bh_processor = BoreholeProcessor(bh_input, dem_handler=dem_handler)
summary_df = bh_processor.borehole_summary

# Spatial Interpolation
interpolator = SpatialInterpolator(dem_handler.mesh_x, dem_handler.mesh_y, boundary_buffer_m=boundary_buffer)
interpolator.fit_survey_boundary(summary_df["Easting_m"].values, summary_df["Northing_m"].values)

raw_surfaces = []
for layer_name in active_strata:
    pts_df = bh_processor.get_layer_points(layer_name)
    valid_pts = pts_df[pts_df["Is_Present"] & pts_df["Layer_Bottom_RL_m"].notnull()]
    if len(valid_pts) > 0:
        if "RBF" in interp_method:
            grid_z = interpolator.interpolate_rbf(valid_pts["Easting_m"].values, valid_pts["Northing_m"].values, valid_pts["Layer_Bottom_RL_m"].values)
        else:
            grid_z = interpolator.interpolate_idw(valid_pts["Easting_m"].values, valid_pts["Northing_m"].values, valid_pts["Layer_Bottom_RL_m"].values, power=idw_power)
    else:
        grid_z = np.full(dem_handler.get_grid_shape(), np.nan, dtype=np.float32)
    raw_surfaces.append(grid_z)

corr_surfaces, thicknesses = interpolator.enforce_stratigraphic_stacking(dem_handler.data, raw_surfaces)

# Geotechnical calculation
cfg = GeotechConfig(footing_width_b=b_m, footing_depth_df=df_m, factor_of_safety=fs_val, permissible_settlement_mm=permissible_settlement)
engine = GeotechEngine(cfg)

bearing_layer_idx = min(1, len(active_strata) - 1)
layer2_pts = bh_processor.get_layer_points(active_strata[bearing_layer_idx])
n_pts = layer2_pts[layer2_pts["Is_Present"] & (layer2_pts["Field_N"] > 0)]
interp_n = interpolator.interpolate_idw(n_pts["Easting_m"].values, n_pts["Northing_m"].values, n_pts["Field_N"].values)
sbc_grid = engine.evaluate_grid_sbc(interp_n, summary_df["Water_Table_Depth_m"].mean(), df_m=df_m, b_m=b_m)

visualizer = SubsurfaceVisualizer(REPORTS_DIR)

# ----------------- TABS -----------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🌐 Interactive 3D Subsurface",
    "🗺️ Safe Bearing Capacity Heatmap",
    "📊 Cross-Section & Isopach Maps",
    "🎲 Coupled Markov Uncertainty & Entropy",
    "📋 Borehole Database & Discrepancies",
    "💾 Downloads & QGIS Assets",
    "📍 Indian Borehole Studies & Literature Map",
    "⚡ Geotechnical Digital Twin (IoT & 4D)",
    "🗄️ Spatial Database & Academic Scraper"
])

# --- TAB 1: 3D MODEL ---
with tab1:
    st.subheader("Interactive 3D Subsurface Geological & Stratum Model")
    st.caption("Rotate, pan, zoom, and inspect layered strata and borehole drill cylinders.")
    
    slug_key = (
        f"{active_prov.name.lower()}_{int(round(site_lat * 100))}_{int(round(site_lon * 100))}_{synth_seed}"
        if data_source.startswith("🇮🇳")
        else (
            "vidarbha" if "Vidarbha" in data_source
            else ("bangalore" if "Bengaluru" in data_source
            else ("rotterdam" if "Rotterdam" in data_source
            else ("coupled_markov" if "Coupled Markov" in data_source
            else ("howrah" if "Howrah" in data_source else "benchmark"))))
        )
    )
    html_3d = REPORTS_DIR / f"interactive_3d_{slug_key}.html"
    if not html_3d.exists() or run_button:
        html_3d = visualizer.build_interactive_3d_plotly(
            dem_handler.mesh_x, dem_handler.mesh_y, dem_handler.data, corr_surfaces, active_strata, summary_df,
            filename=f"interactive_3d_{slug_key}.html"
        )
    
    with open(html_3d, "r") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=650, scrolling=True)

# --- TAB 2: BEARING CAPACITY ---
with tab2:
    st.subheader("Continuous Safe Bearing Capacity (SBC) Predictive Map")
    colA, colB, colC = st.columns(3)
    valid_sbc = sbc_grid[~np.isnan(sbc_grid)]
    colA.metric("Minimum SBC across Site", f"{valid_sbc.min():.0f} kPa")
    colB.metric("Mean Safe Bearing Capacity", f"{valid_sbc.mean():.0f} kPa")
    colC.metric("Maximum SBC (High Ground)", f"{valid_sbc.max():.0f} kPa")
    
    dash_img = REPORTS_DIR / f"dashboard_{slug_key}.png"
    if not dash_img.exists() or run_button:
        dash_img = visualizer.generate_site_dashboard_figure(
            dem_handler.mesh_x, dem_handler.mesh_y, dem_handler.data,
            corr_surfaces[-1], thicknesses[bearing_layer_idx], sbc_grid, summary_df,
            filename=f"dashboard_{slug_key}.png",
            bedrock_title=f"{active_strata[-1]} Top Surface R.L. (m)",
            clay_title=f"{active_strata[bearing_layer_idx]} Thickness (m) [Isopach]"
        )
    st.image(str(dash_img), use_container_width=True)

# --- TAB 3: CROSS SECTION & ISOPACH ---
with tab3:
    st.subheader("Subsurface Geotechnical Cross-Section (Transect A - A')")
    p_a = (summary_df["Easting_m"].min() - 30, summary_df["Northing_m"].min() - 30)
    p_b = (summary_df["Easting_m"].max() + 30, summary_df["Northing_m"].max() + 30)
    
    wt_pts = summary_df[["Easting_m", "Northing_m", "Water_Table_RL_m"]].dropna()
    wt_grid = interpolator.interpolate_idw(wt_pts["Easting_m"].values, wt_pts["Northing_m"].values, wt_pts["Water_Table_RL_m"].values)
    
    cs_img = REPORTS_DIR / f"cross_section_{slug_key}.png"
    if not cs_img.exists() or run_button:
        cs_img = visualizer.generate_transect_cross_section(
            dem_handler.mesh_x, dem_handler.mesh_y, dem_handler.data, corr_surfaces, active_strata, wt_grid, p_a, p_b,
            filename=f"cross_section_{slug_key}.png"
        )
    st.image(str(cs_img), use_container_width=True)

# --- TAB 4: COUPLED MARKOV UNCERTAINTY ---
with tab4:
    st.subheader("🎲 Coupled Markov Chain 2D Profile Simulation & Shannon Entropy")
    st.markdown("""
    *Elfeki & Dekking (2001, 2005) Coupled Markov Chain formulation: simulates multi-realization 2D cross-sections conditioned on borehole boundaries, and quantifies spatial geological uncertainty via Shannon Information Entropy ($H$).*
    """)
    
    # Run Markov cross section
    k_vals = synth_engine.province_metadata[active_prov].horizontal_k_values if data_source.startswith("🇮🇳") else None
    markov_res = synth_engine.synthesize_markov_cross_section(
        borehole_df=bh_processor.processed_df,
        strata_names=active_strata,
        num_cols=80,
        num_rows=40,
        num_simulations=6,
        k_values=k_vals,
        random_seed=synth_seed
    )
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Stochastic Realizations", len(markov_res["realizations"]))
    m_col2.metric("Conditioned Boreholes", len(markov_res["conditioning_cols"]))
    m_col3.metric("Peak Information Entropy", f"{markov_res['entropy'].max():.2f} bits")
    
    entropy_fig = visualizer.generate_markov_entropy_figure(markov_res, filename=f"coupled_markov_entropy_{slug_key}.png")
    st.image(str(entropy_fig), use_container_width=True)

# --- TAB 5: DATABASE & DISCREPANCIES ---
with tab5:
    st.subheader("Borehole Geotechnical Summary & Elevation Audit")
    st.dataframe(summary_df, use_container_width=True)
    
    st.subheader("Layer-by-Layer Geological Records")
    show_cols = ["Borehole_ID", "Layer_Name", "Depth_From_m", "Depth_To_m", "Thickness_m", "Layer_Bottom_RL_m", "Field_N", "Soil_Type"]
    existing_cols = [c for c in show_cols if c in bh_processor.processed_df.columns]
    st.dataframe(bh_processor.processed_df[existing_cols], use_container_width=True)

# --- TAB 6: DOWNLOADS ---
with tab6:
    st.subheader("Exported GIS Deliverables (QGIS Compatible)")
    st.markdown("""
    All outputs are exported in standard GIS formats:
    - **GeoTIFF Rasters:** Layer R.L. boundaries, thickness isopachs, and continuous SBC maps.
    - **GeoPackage Layers:** Vector points and contour isolines.
    - **PyQGIS Script:** Run `qgis/subsurface_qgis_loader.py` inside QGIS for one-click styling.
    """)
    
    # Run exports with exact DEM CRS
    exporter = GISExporter(dem_handler.transform, crs_str=dem_handler.crs)
    sbc_tif = exporter.export_raster(sbc_grid, "safe_bearing_capacity_kpa.tif")
    gpkg_file = exporter.export_boreholes_geopackage(summary_df)
    
    with open(sbc_tif, "rb") as f:
        st.download_button("📥 Download SBC GeoTIFF Raster", f, file_name="safe_bearing_capacity_kpa.tif", mime="image/tiff")
        
    with open(gpkg_file, "rb") as f:
        st.download_button("📥 Download Boreholes GeoPackage (.gpkg)", f, file_name="subsurface_geotechnical.gpkg", mime="application/octet-stream")

    # CSV / Excel Download
    csv_bytes = bh_processor.processed_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Borehole Dataset (CSV)", csv_bytes, file_name="borehole_dataset.csv", mime="text/csv")

# --- TAB 7: NATIONWIDE INDIAN BOREHOLE STUDIES & LITERATURE MAP ---
with tab7:
    st.subheader("📍 Nationwide Geospatial Database of Indian Borehole Studies & Open Data")
    st.markdown("""
    *Interactive survey of academic papers, technical investigations, and open repositories across India utilizing borehole logs and Standard Penetration Test (SPT) data.*
    """)
    
    map_gen = IndianBoreholeMapGenerator()
    df_studies = map_gen.get_summary_dataframe()
    
    # Overview Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Study Locations", len(df_studies))
    m2.metric("Total Documented Boreholes", f"{df_studies['borehole_count'].sum():,}+")
    open_count = len(df_studies[df_studies["data_access_status"] == "Open Access Repository"])
    m3.metric("Open Access Repositories", f"{open_count} Sites")
    m4.metric("Geological Basins", df_studies["geological_province"].nunique())
    
    # Render Interactive Folium Map
    map_html_file = REPORTS_DIR / "indian_borehole_studies_map.html"
    if not map_html_file.exists():
        map_gen.export_html(str(map_html_file))
    
    with open(map_html_file, "r", encoding="utf-8") as f:
        map_html_str = f.read()
    
    components.html(map_html_str, height=620, scrolling=False)
    
    st.markdown("---")
    st.subheader("📚 Literature Survey & Dataset Accessibility Catalog")
    
    # Filter table
    filter_status = st.multiselect(
        "Filter by Data Accessibility Status:",
        options=list(df_studies["data_access_status"].unique()),
        default=list(df_studies["data_access_status"].unique())
    )
    
    filtered_df = df_studies[df_studies["data_access_status"].isin(filter_status)]
    
    display_cols = [
        "id", "city", "state", "geological_province", "borehole_count",
        "depth_range_m", "spt_n_range", "data_access_status", "authors", "year", "journal_or_agency"
    ]
    st.dataframe(filtered_df[display_cols], use_container_width=True)
    
    # Detailed Card view for selected study
    selected_study_id = st.selectbox("Select Study for Deep Dive & Citation:", options=filtered_df["id"].tolist())
    if selected_study_id:
        study_row = filtered_df[filtered_df["id"] == selected_study_id].iloc[0]
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"### {study_row['city']} ({study_row['state']})")
            st.markdown(f"**Geological Province:** {study_row['geological_province']}")
            st.markdown(f"**Primary Objective:** {study_row['primary_objective']}")
            st.markdown(f"**Key Strata Succession:** {', '.join(study_row['predominant_strata'])}")
            st.markdown(f"**Publication:** *{study_row['paper_title']}*")
            st.markdown(f"**Authors:** {study_row['authors']} ({study_row['year']}) — {study_row['journal_or_agency']}")
            st.markdown(f"**Data Repository:** `{study_row['data_repository']}`")
            st.markdown(f"**Notes:** {study_row['notes']}")
        with c2:
            st.metric("Boreholes", study_row["borehole_count"])
            st.metric("Depth Range", study_row["depth_range_m"])
            st.metric("SPT N Range", study_row["spt_n_range"])
            st.metric("Water Table", study_row["water_table_m"])
            st.markdown(f"[🔗 Open Paper / Dataset URL]({study_row['doi_or_url']})")

# --- TAB 8: GEOTECHNICAL DIGITAL TWIN (IoT & 4D) ---
with tab8:
    st.subheader("⚡ 4D Subsurface Geotechnical Digital Twin (Cyber-Physical System)")
    st.markdown("""
    *Evolving static 2.5D DTM + 1D Borehole models into a live Digital Twin via 3D Volumetric Voxelization, IoT Piezometer Telemetry Assimilation, Transient Terzaghi Effective Stress, and Dynamic IS:6403 Bearing Capacity.*
    """)
    
    twin_engine = SubsurfaceDigitalTwinEngine(
        grid_x=dem_handler.mesh_x,
        grid_y=dem_handler.mesh_y,
        surface_dem=dem_handler.data,
        strata_bottom_surfaces=corr_surfaces,
        strata_names=active_strata
    )
    
    # IoT Telemetry Simulator Controls
    st.markdown("#### 📡 Live IoT Telemetry Simulator & Sensor Ingestion")
    st.caption("Adjust simulated sensor readings to emulate real-time monsoon rainfall recharge or construction site dewatering.")
    
    t_col1, t_col2, t_col3 = st.columns(3)
    mean_surf = float(np.mean(dem_handler.data))
    
    with t_col1:
        sim_pz1 = st.slider(
            "📍 Piezometer PZ-01 Water Level (m RL):",
            min_value=float(mean_surf - 10.0),
            max_value=float(mean_surf),
            value=float(mean_surf - 2.5),
            step=0.25
        )
    with t_col2:
        sim_pz2 = st.slider(
            "📍 Piezometer PZ-02 Water Level (m RL):",
            min_value=float(mean_surf - 10.0),
            max_value=float(mean_surf),
            value=float(mean_surf - 2.8),
            step=0.25
        )
    with t_col3:
        st.info(f"**Ground Surface Mean RL:** `{mean_surf:.2f} m`\n\n**Water Depth at Center:** `{(mean_surf - sim_pz1):.2f} m bgl`")
        
    # Ingest updates into twin
    twin_engine.ingest_sensor_telemetry({"PZ-01": sim_pz1, "PZ-02": sim_pz2})
    
    # Re-evaluate Dynamic Bearing Capacity
    dynamic_sbc = twin_engine.compute_dynamic_bearing_capacity(
        foundation_depth_m=df_m,
        footing_width_m=b_m,
        spt_n_layer=float(summary_df["Corrected_N"].mean() if "Corrected_N" in summary_df else 18.0)
    )
    
    st.markdown("#### 🔄 Dynamic Bearing Capacity & Water Factor Response")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Mean Safe Bearing Capacity", f"{dynamic_sbc['mean_sbc_kpa']:.1f} kPa")
    d2.metric("Min Safe Bearing Capacity", f"{dynamic_sbc['min_sbc_kpa']:.1f} kPa")
    d3.metric("Max Safe Bearing Capacity", f"{dynamic_sbc['max_sbc_kpa']:.1f} kPa")
    mean_w = float(np.mean(dynamic_sbc['water_factor_w_prime']))
    d4.metric("Mean IS:6403 W' Factor", f"{mean_w:.3f}", delta=f"{(mean_w - 1.0)*100:.1f}% reduction" if mean_w < 1.0 else "Full capacity")
    
    # Interactive 3D WebGL Digital Twin Scene
    st.markdown("---")
    st.markdown("#### 🌐 Interactive 3D Digital Twin Viewer (WebGL)")
    st.caption("Inspect live 3D terrain surface, subsurface strata boundaries, piezometer well tubes, and volumetric stress voxels.")
    
    st_metric_col1, st_metric_col2, st_metric_col3 = st.columns(3)
    with st_metric_col1:
        chosen_metric = st.selectbox(
            "Voxel Color Metric:",
            ["effective_stress_kpa", "total_stress_kpa", "pore_pressure_kpa", "elastic_modulus_mpa"],
            format_func=lambda x: {
                "effective_stress_kpa": "Terzaghi Effective Stress σ' (kPa)",
                "total_stress_kpa": "Total Overburden Stress σ (kPa)",
                "pore_pressure_kpa": "Hydrostatic Pore Pressure u (kPa)",
                "elastic_modulus_mpa": "Janbu Elastic Modulus E' (MPa)"
            }.get(x, x)
        )
    with st_metric_col2:
        show_voxels_toggle = st.checkbox("Show Volumetric Stress Voxels", value=True)
    with st_metric_col3:
        show_wt_toggle = st.checkbox("Show Dynamic Groundwater Plane", value=True)

    fig_3d_twin = build_interactive_3d_digital_twin_scene(
        twin_engine,
        stress_metric=chosen_metric,
        show_voxels=show_voxels_toggle,
        show_sensors=True,
        show_water_table=show_wt_toggle
    )
    st.plotly_chart(fig_3d_twin, use_container_width=True)

    # 3D Volumetric Voxelization Generator
    st.markdown("---")
    st.markdown("#### 🧊 3D Volumetric Multi-Physics Voxelization & VTK Export")
    st.caption("Discretizes the subsurface into a structured 3D voxel grid containing Effective Stress (σ'), Hydrostatic Pore Pressure (u), and non-linear Elastic Modulus (E').")
    
    vox_col1, vox_col2 = st.columns([1, 1])
    with vox_col1:
        voxel_res = st.select_slider("Voxel Mesh Resolution:", options=["Coarse (20x20x15)", "Standard (30x30x20)", "High (40x40x25)"], value="Standard (30x30x20)")
        res_map = {"Coarse (20x20x15)": (20, 20, 15), "Standard (30x30x20)": (30, 30, 20), "High (40x40x25)": (40, 40, 25)}
        vx_nx, vx_ny, vx_nz = res_map[voxel_res]
        
    generate_voxels_btn = st.button("🚀 Generate 3D Multi-Physics Voxel Volume & Export VTK")
    
    if generate_voxels_btn:
        with st.spinner("Computing 3D volumetric overburden, hydrostatic pore pressure, and Janbu stress-dependent modulus..."):
            vox_data = twin_engine.generate_volumetric_voxels(nx=vx_nx, ny=vx_ny, nz=vx_nz, depth_extent_m=35.0)
            
            # Export VTK
            vti_file = REPORTS_DIR / "subsurface_digital_twin_volume.vti"
            saved_vti = twin_engine.export_vtk_image_data(vox_data, str(vti_file))
            
            st.success(f"✅ 3D Volumetric Digital Twin generated ({vx_nx * vx_ny * vx_nz:,} active voxels)!")
            
            v1, v2, v3 = st.columns(3)
            v1.metric("Max Effective Stress", f"{np.max(vox_data['effective_stress_kpa']):.1f} kPa")
            v2.metric("Max Pore Water Pressure", f"{np.max(vox_data['pore_pressure_kpa']):.1f} kPa")
            v3.metric("Max Elastic Modulus (E')", f"{np.max(vox_data['elastic_modulus_mpa']):.1f} MPa")
            
            with open(saved_vti, "rb") as f:
                st.download_button(
                    "📥 Download ParaView / OpenGeoSys VTK Volume (.vti)",
                    f,
                    file_name="subsurface_digital_twin_volume.vti",
                    mime="application/octet-stream"
                )

# --- TAB 9: SPATIAL DATABASE & ACADEMIC SCRAPER ---
with tab9:
    st.subheader("🗄️ Subsurface Geospatial Database & Academic Scraper (DuckDB & OpenAlex)")
    st.markdown("""
    *High-performance spatial database storing geotechnical borehole logs, stratigraphic sequences, and regional clusters with sub-millisecond DuckDB columnar querying. Features an automated scholarly scraper querying OpenAlex and CrossRef APIs for live Indian geotechnical investigations.*
    """)
    
    spatial_db = SubsurfaceSpatialDatabase()
    db_stats = spatial_db.get_database_stats()
    if db_stats["total_boreholes"] == 0:
        spatial_db.auto_seed_all_datasets()
        db_stats = spatial_db.get_database_stats()

    # DB Stats Banner
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Indexed Boreholes", f"{db_stats['total_boreholes']:,}")
    s2.metric("Total Strata Records", f"{db_stats['total_strata_layers']:,}")
    s3.metric("Regional Study Clusters", f"{db_stats['total_regional_clusters']}")
    s4.metric("Database Engine", f"{db_stats['backend']} (Columnar)")

    st.markdown("---")
    db_col1, db_col2 = st.columns([1, 1])
    
    with db_col1:
        st.markdown("#### 🎯 Spatial Coordinate & Radius Query")
        st.caption("Search for ground-truth boreholes within a radial distance from any coordinate in India.")
        q_lat = st.number_input("Query Latitude (°N):", min_value=5.0, max_value=38.0, value=float(site_lat), step=0.1)
        q_lon = st.number_input("Query Longitude (°E):", min_value=65.0, max_value=100.0, value=float(site_lon), step=0.1)
        q_rad = st.slider("Search Radius (km):", min_value=5.0, max_value=300.0, value=50.0, step=5.0)
        
        if st.button("🔍 Execute Spatial Radius Query", key="btn_spatial_query"):
            res_df = spatial_db.query_radius(q_lat, q_lon, q_rad)
            if res_df.empty:
                st.warning(f"No boreholes found within {q_rad} km of ({q_lat:.2f}°N, {q_lon:.2f}°E). Try increasing search radius.")
            else:
                st.success(f"Found {len(res_df)} boreholes within {q_rad} km!")
                disp_cols = ["global_id", "borehole_id", "city", "state", "distance_from_center_km", "ground_elevation_rl_m", "termination_depth_m", "geological_province"]
                st.dataframe(res_df[[c for c in disp_cols if c in res_df.columns]], use_container_width=True)
                
                # Strata drill-down
                selected_bh = st.selectbox("Inspect Stratigraphy for Borehole:", res_df["global_id"].tolist())
                if selected_bh:
                    strata_df = spatial_db.get_borehole_stratigraphy(selected_bh)
                    st.dataframe(strata_df[["stratum_order", "layer_name", "is_1498_class", "depth_top_m", "depth_bottom_m", "thickness_m", "field_n", "corrected_n"]], use_container_width=True)

    with db_col2:
        st.markdown("#### 🌐 Automated Academic Literature Harvester")
        active_prov_val = active_prov if ("active_prov" in locals() and active_prov is not None) else selected_province
        prov_meta = PROVINCE_REGISTRY.get(active_prov_val)
        target_city_name = prov_meta.typical_cities[0][0] if prov_meta and prov_meta.typical_cities else "Chennai"
        scraper_query = st.text_input("Academic Search Query:", value=f"geotechnical borehole {target_city_name} India")
        harvest_city = st.text_input("Target City / Site:", value=target_city_name)
        harvest_limit = st.slider("Max Papers to Ingest:", 1, 10, 3)
        
        if st.button("🚀 Harvest Literature & Ingest into Database", key="btn_harvest"):
            with st.spinner("Querying OpenAlex & CrossRef APIs, standardizing stratigraphic tables..."):
                scraper = BoreholeLiteratureScraper(spatial_db=spatial_db)
                harvest_res = scraper.auto_harvest_and_ingest(
                    query=scraper_query,
                    limit=harvest_limit,
                    target_city=harvest_city
                )
                st.success(f"Harvested {harvest_res['boreholes_ingested']} boreholes for {harvest_city}!")
                st.info(f"**Indexed Paper:** *{harvest_res['citation']}*\n\n**DOI:** `{harvest_res['doi']}`")
                
                # Show updated count
                new_stats = spatial_db.get_database_stats()
                st.metric("Total Database Boreholes Now", f"{new_stats['total_boreholes']:,}")
