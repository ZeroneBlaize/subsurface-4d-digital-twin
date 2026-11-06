"""
Automated Subsurface Geospatial Modeling & Bearing Capacity Pipeline Runner.
Executes the full end-to-end computational pipeline from raw borehole logs to 3D models and GIS deliverables.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from src.config import (
    DEM_DIR, BENCHMARK_DIR, OUTPUTS_DIR, RASTERS_DIR, VECTORS_DIR, REPORTS_DIR,
    DEFAULT_CRS, STANDARD_STRATA, GeotechConfig
)
from src.dem_handler import DEMHandler
from src.borehole_processor import BoreholeProcessor
from src.spatial_interpolator import SpatialInterpolator
from src.geotech_engine import GeotechEngine
from src.exporter import GISExporter
from src.visualizer import SubsurfaceVisualizer


def run_subsurface_pipeline(
    dem_path: Path = DEM_DIR / "site_dem.tif",
    borehole_path: Path = BENCHMARK_DIR / "boreholes_benchmark.csv",
    interpolation_method: str = "idw",
    footing_depth: float = 2.0,
    footing_width: float = 2.0
):
    print("=" * 80)
    print("🚀 AUTOMATED SUBSURFACE GEOSPATIAL MODELING & BEARING CAPACITY ENGINE")
    print("=" * 80)
    
    # 0. Check data availability, generate benchmark if missing
    if not dem_path.exists() or not borehole_path.exists():
        print("⚠ Benchmark data missing. Generating synthetic benchmark dataset...")
        from data.generate_benchmark_data import generate_synthetic_dem, generate_synthetic_boreholes
        dem, transform = generate_synthetic_dem(dem_path)
        generate_synthetic_boreholes(dem, transform, borehole_path, borehole_path.with_suffix(".xlsx"))

    # 1. Ingest and inspect DEM
    print(f"\n[1/6] Ingesting Digital Elevation Model (DEM)...")
    dem_handler = DEMHandler(dem_path)
    print(f"      DEM Loaded: {dem_handler.width}x{dem_handler.height} cells, Resolution: {dem_handler.transform.a:.1f}m")
    print(f"      Coordinate Reference System (CRS): {dem_handler.crs}")
    print(f"      Elevation Range: {dem_handler.data.min():.2f}m to {dem_handler.data.max():.2f}m R.L.")

    # 2. Ingest and normalize Boreholes
    print(f"\n[2/6] Processing Borehole Logs & Computing Reduced Levels (R.L.)...")
    bh_processor = BoreholeProcessor(borehole_path, dem_handler=dem_handler)
    summary_df = bh_processor.borehole_summary
    print(f"      Processed {len(summary_df)} boreholes across site.")
    if "Elevation_Discrepancy_m" in bh_processor.processed_df.columns:
        mean_disc = bh_processor.processed_df["Elevation_Discrepancy_m"].abs().mean()
        print(f"      Mean Survey vs DEM elevation residual: {mean_disc:.2f} m")

    # 3. Spatial Interpolation Setup
    print(f"\n[3/6] Setting up Spatial Interpolator & Survey Boundary...")
    interpolator = SpatialInterpolator(dem_handler.mesh_x, dem_handler.mesh_y, boundary_buffer_m=50.0)
    interpolator.fit_survey_boundary(summary_df["Easting_m"].values, summary_df["Northing_m"].values)
    print(f"      Convex Hull boundary constructed to prevent unconstrained extrapolation.")

    # 4. Interpolate Stratum Boundaries
    print(f"\n[4/6] Reconstructing 3D Stratum Boundaries ({interpolation_method.upper()})...")
    raw_strata_surfaces = []
    strata_names = STANDARD_STRATA
    
    for layer_name in strata_names:
        pts_df = bh_processor.get_layer_points(layer_name)
        valid_pts = pts_df[pts_df["Is_Present"] & pts_df["Layer_Bottom_RL_m"].notnull()]
        
        if len(valid_pts) > 0:
            if interpolation_method.lower() == "rbf":
                grid_z = interpolator.interpolate_rbf(
                    valid_pts["Easting_m"].values,
                    valid_pts["Northing_m"].values,
                    valid_pts["Layer_Bottom_RL_m"].values
                )
            else:
                grid_z = interpolator.interpolate_idw(
                    valid_pts["Easting_m"].values,
                    valid_pts["Northing_m"].values,
                    valid_pts["Layer_Bottom_RL_m"].values,
                    power=2.0
                )
        else:
            grid_z = np.full(dem_handler.get_grid_shape(), np.nan, dtype=np.float32)
            
        raw_strata_surfaces.append(grid_z)
        print(f"      ✓ Interpolated layer bottom: {layer_name}")

    # Enforce Stacking & Compute Thicknesses
    corr_surfaces, thicknesses = interpolator.enforce_stratigraphic_stacking(
        dem_handler.data,
        raw_strata_surfaces
    )
    print(f"      ✓ Enforced downward monotonic stacking (Z_k <= Z_{{k-1}}) and resolved pinch-outs.")

    # Interpolate groundwater table
    wt_pts = summary_df[["Easting_m", "Northing_m", "Water_Table_RL_m"]].dropna()
    wt_grid = interpolator.interpolate_idw(
        wt_pts["Easting_m"].values,
        wt_pts["Northing_m"].values,
        wt_pts["Water_Table_RL_m"].values
    )

    # 5. Geotechnical Calculations
    print(f"\n[5/6] Executing Geotechnical Bearing Capacity Engine...")
    cfg = GeotechConfig(footing_width_b=footing_width, footing_depth_df=footing_depth)
    engine = GeotechEngine(cfg)
    
    # Extract representative N-values at foundation depth (e.g. Clay/Silt layer)
    layer2_pts = bh_processor.get_layer_points(strata_names[1])
    n_pts = layer2_pts[layer2_pts["Is_Present"] & (layer2_pts["Field_N"] > 0)]
    
    interp_n = interpolator.interpolate_idw(
        n_pts["Easting_m"].values,
        n_pts["Northing_m"].values,
        n_pts["Field_N"].values
    )
    
    avg_wt_depth = summary_df["Water_Table_Depth_m"].mean()
    sbc_grid = engine.evaluate_grid_sbc(
        interpolated_n=interp_n,
        water_table_depth=avg_wt_depth,
        df_m=footing_depth,
        b_m=footing_width
    )
    
    valid_sbc = sbc_grid[~np.isnan(sbc_grid)]
    print(f"      Computed Safe Bearing Capacity (SBC) across site:")
    print(f"      Min SBC: {valid_sbc.min():.1f} kPa | Max SBC: {valid_sbc.max():.1f} kPa | Mean SBC: {valid_sbc.mean():.1f} kPa")

    # 6. Export Deliverables & Visualizations
    print(f"\n[6/6] Exporting GIS Layers & Visual Deliverables...")
    exporter = GISExporter(dem_handler.transform, crs_str=DEFAULT_CRS)
    
    # Export Rasters
    exporter.export_raster(dem_handler.data, "dem_surface_rl.tif")
    for k, name in enumerate(strata_names):
        safe_name = name.lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
        exporter.export_raster(corr_surfaces[k], f"stratum_base_{safe_name}.tif")
        exporter.export_raster(thicknesses[k], f"thickness_{safe_name}.tif")
    exporter.export_raster(sbc_grid, "safe_bearing_capacity_kpa.tif")
    print(f"      ✓ Exported 12 GeoTIFF rasters to: {RASTERS_DIR}")

    # Export Vectors
    gpkg_path = exporter.export_boreholes_geopackage(summary_df)
    exporter.export_contour_vector(sbc_grid, dem_handler.mesh_x, dem_handler.mesh_y, filename="sbc_contours.gpkg")
    print(f"      ✓ Exported GeoPackage layers to: {gpkg_path}")

    # Generate Visual Reports
    visualizer = SubsurfaceVisualizer(REPORTS_DIR)
    
    # 2D Dashboard
    dash_path = visualizer.generate_site_dashboard_figure(
        dem_handler.mesh_x,
        dem_handler.mesh_y,
        dem_handler.data,
        corr_surfaces[-1],  # Bedrock
        thicknesses[1],      # Clay thickness
        sbc_grid,
        summary_df
    )
    print(f"      ✓ 2D Engineering Dashboard saved: {dash_path}")

    # Cross-Section
    p_a = (summary_df["Easting_m"].min() - 50, summary_df["Northing_m"].min() - 50)
    p_b = (summary_df["Easting_m"].max() + 50, summary_df["Northing_m"].max() + 50)
    cs_path = visualizer.generate_transect_cross_section(
        dem_handler.mesh_x,
        dem_handler.mesh_y,
        dem_handler.data,
        corr_surfaces,
        strata_names,
        wt_grid,
        p_a,
        p_b
    )
    print(f"      ✓ Geotechnical Cross-Section saved: {cs_path}")

    # 3D Interactive Plotly HTML
    html_3d = visualizer.build_interactive_3d_plotly(
        dem_handler.mesh_x,
        dem_handler.mesh_y,
        dem_handler.data,
        corr_surfaces,
        strata_names,
        summary_df
    )
    print(f"      ✓ Interactive 3D Subsurface Model saved: {html_3d}")

    print("\n" + "=" * 80)
    print("✅ PIPELINE EXECUTION COMPLETE! ALL DELIVERABLES GENERATED SUCCESSFULLY.")
    valid_sbc = sbc_grid[~np.isnan(sbc_grid)]
    return {
        "dem": dem_handler,
        "borehole_processor": bh_processor,
        "surfaces": corr_surfaces,
        "thicknesses": thicknesses,
        "sbc_grid": sbc_grid,
        "min_sbc": float(valid_sbc.min()) if len(valid_sbc) > 0 else 0.0,
        "mean_sbc": float(valid_sbc.mean()) if len(valid_sbc) > 0 else 0.0,
        "max_sbc": float(valid_sbc.max()) if len(valid_sbc) > 0 else 0.0,
    }


def run_generative_pipeline(
    province_name: Optional[str] = "Indo-Gangetic Deep Alluvium",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    num_boreholes: int = 15,
    extent_m: float = 2000.0,
    resolution: float = 10.0,
    footing_depth: float = 2.0,
    footing_width: float = 2.0,
    interpolation_method: str = "idw",
    output_dir: Optional[Path] = None,
    random_seed: int = 42
):
    """
    Executes the Generative Subsurface Pipeline for any region across the Indian Landmass.
    Synthesizes conditioned site terrain DEM, realistic 3D borehole logs,
    Coupled Markov Chain cross-sections, and IS:6403 bearing capacity models.
    """
    if num_boreholes < 2:
        raise ValueError("At least 2 boreholes are required for spatial interpolation and subsurface modeling.")

    from src.generative_subsurface import (
        IndianGeologicalProvince, PROVINCE_REGISTRY, IndianSubsurfaceSynthesizer
    )

    print("=" * 80)
    print("🇮🇳 AI GENERATIVE SUBSURFACE MODELING ENGINE: INDIAN LANDMASS")
    print("=" * 80)

    synth = IndianSubsurfaceSynthesizer()

    # Determine province
    target_province = None
    if lat is not None and lon is not None:
        target_province = synth.auto_detect_province(lat, lon)
        print(f"      Geographic Coordinates: ({lat:.4f}°N, {lon:.4f}°E)")
        print(f"      Auto-detected Geological Province: {target_province.value}")
    elif province_name:
        for p in IndianGeologicalProvince:
            if province_name.lower() in p.value.lower() or p.name.lower() in province_name.lower():
                target_province = p
                break

    if target_province is None:
        target_province = IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM

    meta = synth.province_metadata[target_province]
    if lat is None or lon is None:
        _, lat, lon = meta.typical_cities[0]

    safe_prov_slug = target_province.name.lower()
    base_out = output_dir if output_dir is not None else OUTPUTS_DIR / f"generated_{safe_prov_slug}"
    rasters_dir = base_out / "rasters"
    vectors_dir = base_out / "vectors"
    reports_dir = base_out / "visual_reports"
    for d in [rasters_dir, vectors_dir, reports_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/7] Province Selected: {target_province.value}")
    print(f"      Description: {meta.description}")
    print(f"      Target Site Center: ({lat:.4f}°N, {lon:.4f}°E), Extent: {extent_m:.0f}m x {extent_m:.0f}m")

    # 1. Synthesize Site DEM
    dem_tif_path = base_out / "site_synthesized_dem.tif"
    dem_data, transform, crs_str, _ = synth.synthesize_site_dem(
        output_path=dem_tif_path,
        province=target_province,
        center_lat=lat,
        center_lon=lon,
        extent_m=extent_m,
        resolution=resolution,
        random_seed=random_seed
    )
    dem_handler = DEMHandler(dem_tif_path)
    print(f"\n[2/7] Synthesized Geomorphic DEM Raster ({dem_handler.width}x{dem_handler.height} cells):")
    print(f"      Projected CRS: {crs_str}")
    print(f"      Surface Elevation: {dem_handler.data.min():.2f}m to {dem_handler.data.max():.2f}m R.L.")

    # 2. Synthesize Conditioned 3D Boreholes
    bh_df = synth.synthesize_boreholes(
        province=target_province,
        num_boreholes=num_boreholes,
        dem_data=dem_data,
        transform=transform,
        random_seed=random_seed
    )
    bh_csv_path = base_out / "synthesized_boreholes.csv"
    bh_df.to_csv(bh_csv_path, index=False)
    bh_df.to_excel(bh_csv_path.with_suffix(".xlsx"), index=False)
    print(f"\n[3/7] Synthesized {num_boreholes} 3D Geotechnical Boreholes ({len(bh_df)} stratum records):")
    print(f"      Saved: {bh_csv_path}")

    # 3. Borehole Processor
    bh_processor = BoreholeProcessor(bh_df, dem_handler=dem_handler)
    summary_df = bh_processor.borehole_summary
    strata_names = [s.name for s in meta.strata]

    # 4. Spatial Interpolation Setup
    print(f"\n[4/7] Reconstructing 3D Continuous Stratigraphic Architecture ({interpolation_method.upper()})...")
    interpolator = SpatialInterpolator(dem_handler.mesh_x, dem_handler.mesh_y, boundary_buffer_m=50.0)
    interpolator.fit_survey_boundary(summary_df["Easting_m"].values, summary_df["Northing_m"].values)

    raw_surfaces = []
    for layer_name in strata_names:
        pts_df = bh_processor.get_layer_points(layer_name)
        valid_pts = pts_df[pts_df["Is_Present"] & pts_df["Layer_Bottom_RL_m"].notnull()]
        if len(valid_pts) > 0:
            if interpolation_method.lower() == "rbf":
                grid_z = interpolator.interpolate_rbf(
                    valid_pts["Easting_m"].values, valid_pts["Northing_m"].values, valid_pts["Layer_Bottom_RL_m"].values
                )
            else:
                grid_z = interpolator.interpolate_idw(
                    valid_pts["Easting_m"].values, valid_pts["Northing_m"].values, valid_pts["Layer_Bottom_RL_m"].values, power=2.0
                )
        else:
            grid_z = np.full(dem_handler.get_grid_shape(), np.nan, dtype=np.float32)
        raw_surfaces.append(grid_z)

    corr_surfaces, thicknesses = interpolator.enforce_stratigraphic_stacking(dem_handler.data, raw_surfaces)
    print(f"      ✓ Monotonic downward stacking enforced across all {len(strata_names)} strata.")

    # Water table grid
    wt_pts = summary_df[["Easting_m", "Northing_m", "Water_Table_RL_m"]].dropna()
    wt_grid = interpolator.interpolate_idw(
        wt_pts["Easting_m"].values, wt_pts["Northing_m"].values, wt_pts["Water_Table_RL_m"].values
    )

    # 5. Geotechnical Safe Bearing Capacity Calculation (IS:6403 & IS:2131)
    print(f"\n[5/7] Executing Geotechnical Bearing Capacity Engine (Df={footing_depth}m, B={footing_width}m)...")
    cfg = GeotechConfig(footing_width_b=footing_width, footing_depth_df=footing_depth)
    engine = GeotechEngine(cfg)

    # Representative N-value layer (e.g. upper bearing layer)
    bearing_layer_idx = min(1, len(strata_names) - 1)
    pts_bearing = bh_processor.get_layer_points(strata_names[bearing_layer_idx])
    n_pts = pts_bearing[pts_bearing["Is_Present"] & (pts_bearing["Field_N"] > 0)]
    interp_n = interpolator.interpolate_idw(
        n_pts["Easting_m"].values, n_pts["Northing_m"].values, n_pts["Field_N"].values
    )

    avg_wt_depth = summary_df["Water_Table_Depth_m"].mean()
    sbc_grid = engine.evaluate_grid_sbc(
        interpolated_n=interp_n,
        water_table_depth=avg_wt_depth,
        df_m=footing_depth,
        b_m=footing_width
    )
    valid_sbc = sbc_grid[~np.isnan(sbc_grid)]
    print(f"      Continuous Safe Bearing Capacity (SBC) across site:")
    print(f"      Min SBC: {valid_sbc.min():.1f} kPa | Mean SBC: {valid_sbc.mean():.1f} kPa | Max SBC: {valid_sbc.max():.1f} kPa")

    # 6. Coupled Markov Chain 2D Profile & Uncertainty Simulation
    print(f"\n[6/7] Simulating Coupled Markov Chain Cross-Section & Information Entropy...")
    markov_res = synth.synthesize_markov_cross_section(
        borehole_df=bh_df,
        strata_names=strata_names,
        num_cols=80,
        num_rows=40,
        num_simulations=8,
        k_values=meta.horizontal_k_values,
        random_seed=random_seed
    )
    print(f"      ✓ Generated {len(markov_res['realizations'])} Coupled Markov stochastic realizations.")
    print(f"      ✓ Computed Shannon Information Entropy Map: Max Uncertainty = {markov_res['entropy'].max():.2f} bits.")

    # 7. Deliverables & Cartographic Exports
    print(f"\n[7/7] Exporting Deliverables, Maps, and Interactive 3D Model...")
    exporter = GISExporter(transform, crs_str=crs_str)

    # Rasters
    exporter.export_raster(dem_handler.data, "dem_surface_rl.tif", output_dir=rasters_dir)
    for k, name in enumerate(strata_names):
        safe_name = name.lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
        exporter.export_raster(corr_surfaces[k], f"stratum_base_{safe_name}.tif", output_dir=rasters_dir)
        exporter.export_raster(thicknesses[k], f"thickness_{safe_name}.tif", output_dir=rasters_dir)
    exporter.export_raster(sbc_grid, "safe_bearing_capacity_kpa.tif", output_dir=rasters_dir)

    # Vectors
    gpkg_path = exporter.export_boreholes_geopackage(summary_df, filename="subsurface_geotechnical.gpkg", output_dir=vectors_dir)
    exporter.export_contour_vector(sbc_grid, dem_handler.mesh_x, dem_handler.mesh_y, filename="sbc_contours.gpkg", output_dir=vectors_dir)

    # Visualizer
    visualizer = SubsurfaceVisualizer(reports_dir)
    dash_path = visualizer.generate_site_dashboard_figure(
        dem_handler.mesh_x, dem_handler.mesh_y, dem_handler.data,
        corr_surfaces[-1], thicknesses[bearing_layer_idx], sbc_grid, summary_df,
        bedrock_title=f"{strata_names[-1]} Top Surface R.L. (m)",
        clay_title=f"{strata_names[bearing_layer_idx]} Thickness (m) [Isopach]"
    )
    print(f"      ✓ 2D Engineering Dashboard saved: {dash_path}")

    # Cross section
    p_a = (summary_df["Easting_m"].min() - 30, summary_df["Northing_m"].min() - 30)
    p_b = (summary_df["Easting_m"].max() + 30, summary_df["Northing_m"].max() + 30)
    cs_path = visualizer.generate_transect_cross_section(
        dem_handler.mesh_x, dem_handler.mesh_y, dem_handler.data,
        corr_surfaces, strata_names, wt_grid, p_a, p_b
    )
    print(f"      ✓ Geotechnical Cross-Section saved: {cs_path}")

    # Coupled Markov Entropy Profile
    entropy_fig_path = visualizer.generate_markov_entropy_figure(markov_res)
    print(f"      ✓ Coupled Markov Entropy Profile saved: {entropy_fig_path}")

    # 3D Interactive Plotly HTML
    html_3d = visualizer.build_interactive_3d_plotly(
        dem_handler.mesh_x, dem_handler.mesh_y, dem_handler.data,
        corr_surfaces, strata_names, summary_df
    )
    print(f"      ✓ Interactive 3D Model saved: {html_3d}")

    print("\n" + "=" * 80)
    print(f"✅ GENERATIVE SUBSURFACE PIPELINE COMPLETE FOR: {target_province.value.upper()}")
    print(f"   Outputs available in: {base_out}")
    print("=" * 80)

    valid_sbc = sbc_grid[~np.isnan(sbc_grid)]
    return {
        "province": target_province,
        "dem": dem_handler,
        "boreholes": bh_df,
        "summary": summary_df,
        "surfaces": corr_surfaces,
        "thicknesses": thicknesses,
        "sbc_grid": sbc_grid,
        "min_sbc": float(valid_sbc.min()) if len(valid_sbc) > 0 else 0.0,
        "mean_sbc": float(valid_sbc.mean()) if len(valid_sbc) > 0 else 0.0,
        "max_sbc": float(valid_sbc.max()) if len(valid_sbc) > 0 else 0.0,
        "markov": markov_res,
        "output_dir": base_out
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Subsurface Geospatial & Bearing Capacity Pipeline Runner")
    parser.add_argument("--generate", action="store_true", help="Run the Indian landmass generative engine")
    parser.add_argument("--province", type=str, default=None, help="Target Indian geological province name")
    parser.add_argument("--lat", type=float, default=None, help="Site latitude in WGS84")
    parser.add_argument("--lon", type=float, default=None, help="Site longitude in WGS84")
    parser.add_argument("--num-boreholes", type=int, default=15, help="Number of boreholes to synthesize")
    parser.add_argument("--extent", type=float, default=2000.0, help="Site survey extent in meters")
    parser.add_argument("--b", type=float, default=2.0, help="Footing width B (m)")
    parser.add_argument("--df", type=float, default=2.0, help="Footing depth Df (m)")
    parser.add_argument("--method", type=str, default="idw", choices=["idw", "rbf"], help="Interpolation algorithm")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom output directory")
    args = parser.parse_args()

    if (args.lat is not None) ^ (args.lon is not None):
        raise ValueError("Both --lat and --lon must be provided together.")

    if args.generate or args.province is not None or (args.lat is not None and args.lon is not None):
        out_d = Path(args.output_dir) if args.output_dir else None
        run_generative_pipeline(
            province_name=args.province,
            lat=args.lat,
            lon=args.lon,
            num_boreholes=args.num_boreholes,
            extent_m=args.extent,
            footing_depth=args.df,
            footing_width=args.b,
            interpolation_method=args.method,
            output_dir=out_d
        )
    else:
        run_subsurface_pipeline(
            interpolation_method=args.method,
            footing_depth=args.df,
            footing_width=args.b
        )

