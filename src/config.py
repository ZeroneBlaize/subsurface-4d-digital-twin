"""
Configuration settings for the Subsurface Geospatial Modeling & Bearing Capacity Engine.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List

PROJECT_ROOT = Path("/home/nkm6/25CL06008/Projects_P/Dem_Btech")
DATA_DIR = PROJECT_ROOT / "data"
BENCHMARK_DIR = DATA_DIR / "benchmark"
RAW_DIR = DATA_DIR / "raw"
DEM_DIR = DATA_DIR / "dem"
DB_DIR = DATA_DIR / "db"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
RASTERS_DIR = OUTPUTS_DIR / "rasters"
VECTORS_DIR = OUTPUTS_DIR / "vectors"
REPORTS_DIR = OUTPUTS_DIR / "visual_reports"

# Default Coordinate Reference System: UTM Zone 44N (suitable for Central India / Nagpur)
DEFAULT_CRS = "EPSG:32644"
GEOGRAPHIC_CRS = "EPSG:4326"

# Standard Geological Stratigraphic Sequence (Top to Bottom)
STANDARD_STRATA = [
    "Topsoil / Fill",
    "Soft to Medium Silty Clay",
    "Stiff Sandy Silt / Murrum",
    "Weathered Basalt",
    "Hard Basalt (Bedrock)",
]

# Geotechnical default parameters
@dataclass
class GeotechConfig:
    footing_width_b: float = 2.0         # meters (width of square/strip footing)
    footing_length_l: float = 2.0        # meters (L=B for square footing)
    footing_depth_df: float = 2.0        # meters (depth of foundation)
    factor_of_safety: float = 3.0        # per IS:6403
    permissible_settlement_mm: float = 25.0  # mm per IS:1904
    water_table_depth_m: float = 3.5     # default water table depth if unmeasured
    gamma_bulk: float = 18.5             # kN/m3
    gamma_submerged: float = 9.5         # kN/m3
