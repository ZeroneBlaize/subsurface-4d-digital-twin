"""
Synthetic Benchmark Generator: High-Resolution DEM Raster and 20-Borehole Geotechnical Dataset.
"""

import math
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.config import DEM_DIR, BENCHMARK_DIR, DEFAULT_CRS, STANDARD_STRATA


def generate_synthetic_dem(
    output_path: Path,
    nx: int = 200,
    ny: int = 200,
    resolution: float = 10.0,
    x_origin: float = 310000.0,
    y_origin: float = 2337000.0,
) -> tuple[np.ndarray, rasterio.Affine]:
    """
    Generate an undulating terrain DEM raster (2km x 2km at 10m resolution) in UTM Zone 44N.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Coordinates in meters
    x = np.linspace(0, (nx - 1) * resolution, nx)
    y = np.linspace(0, (ny - 1) * resolution, ny)
    X, Y = np.meshgrid(x, y)
    
    # Realistic topography: undulating terrain with main valley and flanking ridges (285m - 318m)
    base_elevation = 295.0
    ridge = 12.0 * np.sin(2 * np.pi * X / 2500.0) * np.cos(2 * np.pi * Y / 2000.0)
    slope = 0.004 * (Y - X)
    undulations = 4.0 * np.sin(2 * np.pi * (X + Y) / 800.0) + 2.0 * np.cos(2 * np.pi * X / 400.0)
    
    dem_data = (base_elevation + ridge + slope + undulations).astype(np.float32)
    
    # Affine transform: upper left corner
    transform = from_origin(x_origin, y_origin, resolution, resolution)
    crs = CRS.from_string(DEFAULT_CRS)
    
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=ny,
        width=nx,
        count=1,
        dtype=dem_data.dtype,
        crs=crs,
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(dem_data, 1)
        
    print(f"✓ Synthetic DEM raster created: {output_path} ({nx}x{ny}, range {dem_data.min():.2f}m - {dem_data.max():.2f}m R.L.)")
    return dem_data, transform


def generate_synthetic_boreholes(
    dem_data: np.ndarray,
    transform: rasterio.Affine,
    output_csv: Path,
    output_xlsx: Path,
    num_boreholes: int = 20,
) -> pd.DataFrame:
    """
    Generate 20 geotechnical borehole drilling logs distributed across the DEM extent.
    Includes pinch-outs, variable N-values, and groundwater measurements.
    """
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(42)
    
    ny, nx = dem_data.shape
    res_x, res_y = transform.a, -transform.e
    x0, y0 = transform.c, transform.f
    
    # Distribute boreholes across the survey site (avoiding the exact outer perimeter)
    margin_x = nx * 0.15
    margin_y = ny * 0.15
    
    col_coords = np.random.uniform(margin_x, nx - margin_x, num_boreholes)
    row_coords = np.random.uniform(margin_y, ny - margin_y, num_boreholes)
    
    records = []
    
    for i in range(num_boreholes):
        bh_id = f"BH-{i+1:02d}"
        col_idx = int(round(col_coords[i]))
        row_idx = int(round(row_coords[i]))
        
        # Real-world UTM coordinates
        easting = x0 + col_idx * res_x
        northing = y0 - row_idx * res_y
        surface_rl = float(dem_data[row_idx, col_idx])
        
        # Groundwater table (2.5m to 5.5m depth below ground)
        water_table_depth = round(float(np.random.uniform(2.5, 5.5)), 2)
        
        # Geological layer thickness modeling with spatial correlation
        # Layer 1: Topsoil / Fill (0.8m - 1.8m)
        t1 = round(float(np.random.uniform(0.8, 1.8)), 2)
        # Layer 2: Soft to Medium Silty Clay (2.5m - 4.5m)
        t2 = round(float(np.random.uniform(2.5, 4.5)), 2)
        # Layer 3: Stiff Sandy Silt / Murrum (Pinch-out at BH-07 and BH-14 for stress-testing)
        if i in [6, 13]:
            t3 = 0.0  # Stratigraphic pinch-out
        else:
            t3 = round(float(np.random.uniform(2.0, 5.0)), 2)
        # Layer 4: Weathered Basalt (3.0m - 5.5m)
        t4 = round(float(np.random.uniform(3.0, 5.5)), 2)
        # Layer 5: Hard Basalt Bedrock (drilled 2.0m to 3.5m into rock to confirm refusal)
        t5 = round(float(np.random.uniform(2.0, 3.5)), 2)
        
        depth_cursor = 0.0
        layers_data = [
            ("Topsoil / Fill", t1, int(np.random.randint(4, 9)), "Clayey Silt", 15.0, 10.0, 17.5, False),
            ("Soft to Medium Silty Clay", t2, int(np.random.randint(6, 15)), "Inorganic Clay (CI)", 35.0, 12.0, 18.0, False),
            ("Stiff Sandy Silt / Murrum", t3, int(np.random.randint(16, 32)), "Sandy Silt (ML)", 10.0, 28.0, 19.0, False),
            ("Weathered Basalt", t4, int(np.random.randint(35, 50)), "Weathered Rock", 50.0, 34.0, 21.0, False),
            ("Hard Basalt (Bedrock)", t5, int(np.random.randint(60, 100)), "Hard Rock (Basalt)", 150.0, 42.0, 24.0, True),
        ]
        
        layer_idx = 1
        for name, thick, n_val, soil_type, c_val, phi_val, gamma, is_refusal in layers_data:
            if thick <= 0.0:
                # Still record zero-thickness stratum or skip? We record it to test pinch-out handling
                records.append({
                    "Borehole_ID": bh_id,
                    "Easting_m": round(easting, 2),
                    "Northing_m": round(northing, 2),
                    "Surface_RL_m": round(surface_rl, 2),
                    "Layer_Index": layer_idx,
                    "Layer_Name": name,
                    "Depth_From_m": round(depth_cursor, 2),
                    "Depth_To_m": round(depth_cursor, 2),
                    "Thickness_m": 0.0,
                    "Layer_Bottom_RL_m": round(surface_rl - depth_cursor, 2),
                    "Field_N": 0,
                    "Soil_Type": soil_type,
                    "Cohesion_kPa": c_val,
                    "Friction_Angle_deg": phi_val,
                    "Unit_Weight_kN_m3": gamma,
                    "Water_Table_Depth_m": water_table_depth,
                    "Refusal_Reached": False,
                    "Is_Pinchout": True
                })
            else:
                depth_to = depth_cursor + thick
                bottom_rl = surface_rl - depth_to
                records.append({
                    "Borehole_ID": bh_id,
                    "Easting_m": round(easting, 2),
                    "Northing_m": round(northing, 2),
                    "Surface_RL_m": round(surface_rl, 2),
                    "Layer_Index": layer_idx,
                    "Layer_Name": name,
                    "Depth_From_m": round(depth_cursor, 2),
                    "Depth_To_m": round(depth_to, 2),
                    "Thickness_m": round(thick, 2),
                    "Layer_Bottom_RL_m": round(bottom_rl, 2),
                    "Field_N": n_val,
                    "Soil_Type": soil_type,
                    "Cohesion_kPa": c_val,
                    "Friction_Angle_deg": phi_val,
                    "Unit_Weight_kN_m3": gamma,
                    "Water_Table_Depth_m": water_table_depth,
                    "Refusal_Reached": is_refusal,
                    "Is_Pinchout": False
                })
                depth_cursor = depth_to
            layer_idx += 1
            
    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    df.to_excel(output_xlsx, index=False)
    
    print(f"✓ Synthetic borehole dataset generated: {output_csv} & {output_xlsx}")
    print(f"  Total records: {len(df)} across {num_boreholes} boreholes")
    return df


if __name__ == "__main__":
    dem_file = DEM_DIR / "site_dem.tif"
    csv_file = BENCHMARK_DIR / "boreholes_benchmark.csv"
    xlsx_file = BENCHMARK_DIR / "boreholes_benchmark.xlsx"
    
    dem, transform = generate_synthetic_dem(dem_file)
    generate_synthetic_boreholes(dem, transform, csv_file, xlsx_file)
