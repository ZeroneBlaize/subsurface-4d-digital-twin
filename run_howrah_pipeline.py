"""
Pipeline execution on Real Indian Geotechnical Investigation Dataset:
14 Boreholes at Shalimar, Howrah, West Bengal.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from src.dem_handler import DEMHandler
from src.borehole_processor import BoreholeProcessor
from src.spatial_interpolator import SpatialInterpolator
from src.geotech_engine import GeotechEngine
from src.exporter import GISExporter
from src.visualizer import SubsurfaceVisualizer
from src.config import GeotechConfig
import numpy as np

def run_howrah_geotechnical_engine():
    dem_path = PROJECT_ROOT / "data/dem/howrah_dem.tif"
    borehole_path = PROJECT_ROOT / "data/raw/howrah_boreholes_parsed.csv"
    output_dir = PROJECT_ROOT / "outputs/howrah_real"
    
    (output_dir / "rasters").mkdir(parents=True, exist_ok=True)
    (output_dir / "vectors").mkdir(parents=True, exist_ok=True)
    (output_dir / "visual_reports").mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("🇮🇳 PROCESSING REAL INDIAN GEOTECHNICAL BOREHOLE DATASET (HOWRAH, WB)")
    print("=" * 80)
    
    # 1. Ingest DEM
    dem = DEMHandler(dem_path)
    print(f"[1/5] Ingested Howrah Site DEM: {dem.width}x{dem.height} cells, range {dem.data.min():.2f}m - {dem.data.max():.2f}m R.L.")
    
    # 2. Ingest real boreholes
    bp = BoreholeProcessor(borehole_path, dem_handler=dem)
    summary_df = bp.borehole_summary
    print(f"[2/5] Ingested {len(summary_df)} real Indian borehole logs.")
    print(f"      Easting Range: {summary_df['Easting_m'].min():.1f}m to {summary_df['Easting_m'].max():.1f}m")
    print(f"      Northing Range: {summary_df['Northing_m'].min():.1f}m to {summary_df['Northing_m'].max():.1f}m")
    print(f"      Groundwater Table: Mean depth = {summary_df['Water_Table_Depth_m'].mean():.2f}m below ground.")
    
    # 3. Spatial Interpolation
    print(f"[3/5] Interpolating Subsurface Strata Surfaces across the Shalimar parcel...")
    interpolator = SpatialInterpolator(dem.mesh_x, dem.mesh_y, boundary_buffer_m=30.0)
    interpolator.fit_survey_boundary(summary_df["Easting_m"].values, summary_df["Northing_m"].values)
    
    howrah_strata = [
        "Topsoil / Fill",
        "Firm Brown Silty Clay",
        "Soft Peaty Silty Clay",
        "Stiff Bluish Grey Clay",
        "Dense Silty Sand"
    ]
    
    raw_surfaces = []
    for layer in howrah_strata:
        pts = bp.get_layer_points(layer)
        valid = pts[pts["Is_Present"] & pts["Layer_Bottom_RL_m"].notnull()]
        grid_z = interpolator.interpolate_idw(
            valid["Easting_m"].values,
            valid["Northing_m"].values,
            valid["Layer_Bottom_RL_m"].values,
            power=2.0
        )
        raw_surfaces.append(grid_z)
        
    corr_surfaces, thicknesses = interpolator.enforce_stratigraphic_stacking(dem.data, raw_surfaces)
    print("      ✓ Monotonic downward stratum stacking enforced across all 5 layers.")
    
    # 4. Geotechnical Safe Bearing Capacity Calculation (IS:6403 & IS:2131)
    print(f"[4/5] Computing Safe Bearing Capacity for Footing (Df=1.5m, B=2.0m, FS=3.0)...")
    cfg = GeotechConfig(footing_width_b=2.0, footing_depth_df=1.5, factor_of_safety=3.0)
    engine = GeotechEngine(cfg)
    
    # Representative N at footing depth (Firm silty clay layer)
    pts_l2 = bp.get_layer_points(howrah_strata[1])
    n_pts = pts_l2[pts_l2["Is_Present"] & (pts_l2["Field_N"] > 0)]
    interp_n = interpolator.interpolate_idw(n_pts["Easting_m"].values, n_pts["Northing_m"].values, n_pts["Field_N"].values)
    
    sbc_grid = engine.evaluate_grid_sbc(
        interp_n,
        water_table_depth=summary_df["Water_Table_Depth_m"].mean(),
        df_m=1.5,
        b_m=2.0,
        soil_type="Clay"
    )
    
    valid_sbc = sbc_grid[~np.isnan(sbc_grid)]
    print(f"      Safe Bearing Capacity across Howrah site:")
    print(f"      Min SBC: {valid_sbc.min():.1f} kPa | Max SBC: {valid_sbc.max():.1f} kPa | Mean SBC: {valid_sbc.mean():.1f} kPa")
    
    # 5. Visual Reports & Exports
    print(f"[5/5] Exporting Deliverables and 3D Model...")
    exporter = GISExporter(dem.transform, crs_str="EPSG:32645")
    exporter.export_raster(sbc_grid, "howrah_sbc_kpa.tif", output_dir=output_dir / "rasters")
    exporter.export_raster(corr_surfaces[-1], "howrah_dense_sand_base_rl.tif", output_dir=output_dir / "rasters")
    
    viz = SubsurfaceVisualizer(output_dir / "visual_reports")
    
    dash_path = viz.generate_site_dashboard_figure(
        dem.mesh_x, dem.mesh_y, dem.data,
        corr_surfaces[-1], thicknesses[1], sbc_grid, summary_df,
        filename="howrah_site_dashboard.png"
    )
    
    html_3d = viz.build_interactive_3d_plotly(
        dem.mesh_x, dem.mesh_y, dem.data,
        corr_surfaces, howrah_strata, summary_df,
        filename="howrah_3d_strata.html"
    )
    
    print(f"      ✓ Dashboard: {dash_path}")
    print(f"      ✓ Interactive 3D Model: {html_3d}")
    print("\n✅ REAL INDIAN DATASET EVALUATION COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_howrah_geotechnical_engine()
