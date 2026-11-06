"""
Borehole Processor: Tabular Ingestion, R.L. Normalization, Discrepancy Auditing, and Pinch-Out Reconciliation.
"""

from pathlib import Path
from typing import Union, List, Dict, Optional, Tuple
import numpy as np
import pandas as pd

from src.dem_handler import DEMHandler
from src.config import STANDARD_STRATA


class BoreholeProcessor:
    """
    Ingests, validates, standardizes, and calculates true Reduced Levels (R.L.)
    for raw borehole geotechnical logs.
    """
    REQUIRED_COLUMNS = ["Borehole_ID", "Easting_m", "Northing_m", "Layer_Name", "Depth_To_m"]

    COLUMN_ALIASES = {
        "bh_id": "Borehole_ID",
        "borehole": "Borehole_ID",
        "hole_id": "Borehole_ID",
        "x": "Easting_m",
        "easting": "Easting_m",
        "longitude": "Easting_m",
        "y": "Northing_m",
        "northing": "Northing_m",
        "latitude": "Northing_m",
        "layer": "Layer_Name",
        "stratum": "Layer_Name",
        "soil_layer": "Layer_Name",
        "depth": "Depth_To_m",
        "depth_to": "Depth_To_m",
        "bottom_depth": "Depth_To_m",
        "depth_from": "Depth_From_m",
        "top_depth": "Depth_From_m",
        "spt": "Field_N",
        "spt_n": "Field_N",
        "n_value": "Field_N",
        "water_table": "Water_Table_Depth_m",
        "gw_table": "Water_Table_Depth_m",
        "water_depth": "Water_Table_Depth_m",
        "surface_rl": "Surface_RL_m",
        "ground_elevation": "Surface_RL_m",
        "elevation": "Surface_RL_m",
    }

    def __init__(self, data_path: Optional[Union[str, Path, pd.DataFrame]] = None, dem_handler: Optional[DEMHandler] = None):
        self.dem_handler = dem_handler
        self.raw_df: Optional[pd.DataFrame] = None
        self.processed_df: Optional[pd.DataFrame] = None
        self.borehole_summary: Optional[pd.DataFrame] = None
        
        if data_path is not None:
            self.load_data(data_path)

    def load_data(self, data_input: Union[str, Path, pd.DataFrame]) -> pd.DataFrame:
        """
        Loads borehole data from CSV, Excel, or an existing Pandas DataFrame.
        """
        if isinstance(data_input, (str, Path)):
            p = Path(data_input)
            if not p.exists():
                raise FileNotFoundError(f"Borehole data file not found: {p}")
            if p.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(p)
            else:
                df = pd.read_csv(p)
        elif isinstance(data_input, pd.DataFrame):
            df = data_input.copy()
        else:
            raise TypeError("data_input must be a file path or pandas DataFrame")
            
        # Standardize column naming
        df.columns = [c.strip() for c in df.columns]
        rename_map = {}
        for col in df.columns:
            clean_name = col.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(".", "")
            if clean_name in self.COLUMN_ALIASES:
                rename_map[col] = self.COLUMN_ALIASES[clean_name]
        df = df.rename(columns=rename_map)
        
        self.raw_df = df
        return self.process_boreholes()

    def process_boreholes(self) -> pd.DataFrame:
        """
        Standardizes drilling depths with actual Reduced Levels (R.L.) of the terrain
        and resolves discrepancies against the high-resolution DEM.
        """
        if self.raw_df is None:
            raise ValueError("No data loaded. Call load_data() first.")
            
        df = self.raw_df.copy()
        
        # Verify required coordinates
        if "Easting_m" not in df.columns or "Northing_m" not in df.columns:
            raise KeyError("Borehole dataset must contain Easting and Northing coordinates.")
            
        # 1. Surface Ground Elevation Normalization
        # If surface elevation is missing or needs validation, sample from DEM
        dem_elevations = []
        if self.dem_handler is not None:
            for _, row in df.iterrows():
                dem_z = self.dem_handler.sample_elevation(row["Easting_m"], row["Northing_m"])
                dem_elevations.append(dem_z)
            df["DEM_Surface_RL_m"] = dem_elevations
            
            if "Surface_RL_m" not in df.columns or df["Surface_RL_m"].isnull().all():
                df["Surface_RL_m"] = df["DEM_Surface_RL_m"]
            else:
                # Check survey elevation vs DEM elevation residual
                df["Elevation_Discrepancy_m"] = np.round(df["Surface_RL_m"] - df["DEM_Surface_RL_m"], 2)
        else:
            if "Surface_RL_m" not in df.columns:
                df["Surface_RL_m"] = 300.0  # fallback arbitrary baseline
                
        # 2. Fill Depth_From_m if missing
        if "Depth_From_m" not in df.columns:
            df["Depth_From_m"] = 0.0
            for bh_id, group in df.groupby("Borehole_ID"):
                prev_depth = 0.0
                for idx in group.index:
                    df.loc[idx, "Depth_From_m"] = prev_depth
                    prev_depth = df.loc[idx, "Depth_To_m"]
                    
        # 3. Thickness calculation
        df["Thickness_m"] = np.maximum(0.0, df["Depth_To_m"] - df["Depth_From_m"])
        
        # 4. Reduced Level (R.L.) Normalization
        # Absolute Layer R.L. = Surface Elevation (from DEM) - Borehole Log Depth
        df["Layer_Top_RL_m"] = np.round(df["Surface_RL_m"] - df["Depth_From_m"], 2)
        df["Layer_Bottom_RL_m"] = np.round(df["Surface_RL_m"] - df["Depth_To_m"], 2)
        
        # 5. Water Table R.L.
        if "Water_Table_Depth_m" in df.columns:
            df["Water_Table_RL_m"] = np.round(df["Surface_RL_m"] - df["Water_Table_Depth_m"], 2)
        else:
            df["Water_Table_Depth_m"] = 3.0
            df["Water_Table_RL_m"] = np.round(df["Surface_RL_m"] - 3.0, 2)
            
        # 6. Default N-values if missing
        if "Field_N" not in df.columns:
            df["Field_N"] = 15
            
        self.processed_df = df
        self._build_summary()
        return df

    def _build_summary(self):
        """
        Creates a clean one-row-per-borehole summary table with location, ground R.L.,
        groundwater level, and termination depth.
        """
        if self.processed_df is None:
            return
            
        summary_rows = []
        for bh_id, grp in self.processed_df.groupby("Borehole_ID"):
            first_row = grp.iloc[0]
            max_depth = grp["Depth_To_m"].max()
            termination_rl = grp["Layer_Bottom_RL_m"].min()
            wt_depth = grp["Water_Table_Depth_m"].mean()
            wt_rl = first_row["Surface_RL_m"] - wt_depth
            
            summary_rows.append({
                "Borehole_ID": bh_id,
                "Easting_m": first_row["Easting_m"],
                "Northing_m": first_row["Northing_m"],
                "Surface_RL_m": first_row["Surface_RL_m"],
                "Max_Drill_Depth_m": max_depth,
                "Termination_RL_m": termination_rl,
                "Water_Table_Depth_m": wt_depth,
                "Water_Table_RL_m": wt_rl,
                "Num_Layers": len(grp)
            })
        self.borehole_summary = pd.DataFrame(summary_rows)

    def get_layer_points(self, layer_name: str) -> pd.DataFrame:
        """
        Extracts coordinate and bottom R.L. points for a specific stratum boundary across all boreholes.
        Handles pinch-outs where a borehole does not contain the stratum.
        """
        if self.processed_df is None:
            raise ValueError("Processed dataframe is empty.")
            
        pts = []
        all_bhs = self.borehole_summary["Borehole_ID"].unique()
        
        for bh_id in all_bhs:
            bh_rows = self.processed_df[self.processed_df["Borehole_ID"] == bh_id]
            matched = bh_rows[bh_rows["Layer_Name"].str.lower().str.strip() == layer_name.lower().strip()]
            
            bh_meta = self.borehole_summary[self.borehole_summary["Borehole_ID"] == bh_id].iloc[0]
            easting = bh_meta["Easting_m"]
            northing = bh_meta["Northing_m"]
            surface_rl = bh_meta["Surface_RL_m"]
            
            if len(matched) > 0 and matched.iloc[0]["Thickness_m"] > 0:
                row = matched.iloc[0]
                pts.append({
                    "Borehole_ID": bh_id,
                    "Easting_m": easting,
                    "Northing_m": northing,
                    "Surface_RL_m": surface_rl,
                    "Layer_Bottom_RL_m": row["Layer_Bottom_RL_m"],
                    "Thickness_m": row["Thickness_m"],
                    "Field_N": row.get("Field_N", 0),
                    "Is_Present": True
                })
            else:
                # Stratigraphic pinch-out: find where this layer should sit in the sequence
                # Set thickness = 0 and clamp elevation to next lower boundary or termination
                # If layer is not present, find previous layer bottom RL
                pts.append({
                    "Borehole_ID": bh_id,
                    "Easting_m": easting,
                    "Northing_m": northing,
                    "Surface_RL_m": surface_rl,
                    "Layer_Bottom_RL_m": np.nan,  # Will be resolved during multi-layer stacking
                    "Thickness_m": 0.0,
                    "Field_N": 0,
                    "Is_Present": False
                })
                
        return pd.DataFrame(pts)
