"""
Geotechnical Calculation Engine: IS:2131 SPT N-Corrections, IS:6403 Bearing Capacity, and Settlement Analysis.
"""

from typing import Union, Tuple, Dict, Optional
import numpy as np

from src.config import GeotechConfig


class GeotechEngine:
    """
    Implements Indian Standard formulations for:
    - SPT N-value corrections (IS:2131)
    - Ultimate and Safe Bearing Capacity (IS:6403-1981)
    - Allowable Bearing Pressure limited by 25mm settlement (IS:1904 / Bowles)
    """
    def __init__(self, config: Optional[GeotechConfig] = None):
        self.config = config if config is not None else GeotechConfig()

    @staticmethod
    def correct_spt_n(
        field_n: float,
        depth_m: float,
        water_table_depth_m: float,
        gamma_bulk: float = 18.5,
        is_cohesive: bool = False
    ) -> Tuple[float, float, float]:
        """
        Applies IS:2131 corrections to raw SPT N-value:
        1. Overburden pressure correction (C_N)
        2. Dilatancy correction (for saturated silts/fine sands below groundwater table)
        
        Returns:
            (C_N, n_overburden, n_corrected)
        """
        if field_n <= 0:
            return 1.0, 0.0, 0.0
            
        # 1. Effective overburden pressure sigma_v' (kPa)
        if depth_m <= water_table_depth_m:
            sigma_v = gamma_bulk * depth_m
        else:
            h_dry = water_table_depth_m
            h_sub = depth_m - water_table_depth_m
            sigma_v = (gamma_bulk * h_dry) + (9.81 * h_sub)  # effective submerged unit weight approx
            
        # Standardize sigma_v: minimum 20 kPa, maximum 280 kPa
        sigma_v_eff = max(20.0, min(280.0, sigma_v))
        
        # Overburden correction factor C_N (Liao & Whitman / IS:2131)
        # C_N = sqrt(100 / sigma_v') clamped between 0.45 and 2.0
        c_n = float(np.clip(np.sqrt(100.0 / sigma_v_eff), 0.45, 2.0))
        n_overburden = c_n * field_n
        
        # 2. Dilatancy correction (IS:2131 Clause 3.2)
        # Applied to fine sand and silt below water table where N' > 15
        if not is_cohesive and depth_m > water_table_depth_m and n_overburden > 15.0:
            n_corrected = 15.0 + 0.5 * (n_overburden - 15.0)
        else:
            n_corrected = n_overburden
            
        return c_n, round(n_overburden, 2), round(n_corrected, 2)

    @staticmethod
    def estimate_shear_parameters(
        n_corrected: float,
        soil_type: str = "Cohesionless"
    ) -> Tuple[float, float]:
        """
        Estimates effective friction angle phi (degrees) and cohesion c (kPa)
        from corrected SPT N-value.
        """
        if "clay" in soil_type.lower():
            # Cohesive soil: c dominates, phi is low
            c_val = float(np.clip(6.5 * n_corrected, 15.0, 150.0))
            phi_val = float(np.clip(8.0 + 0.2 * n_corrected, 0.0, 18.0))
        elif "rock" in soil_type.lower() or "basalt" in soil_type.lower():
            c_val = float(np.clip(25.0 + 2.0 * n_corrected, 50.0, 300.0))
            phi_val = float(np.clip(32.0 + 0.15 * n_corrected, 32.0, 45.0))
        else:
            # Silt / Sand / Murrum
            c_val = float(np.clip(1.5 * n_corrected, 5.0, 35.0))
            phi_val = float(np.clip(27.0 + 0.35 * n_corrected, 24.0, 42.0))
            
        return round(c_val, 2), round(phi_val, 2)

    @staticmethod
    def compute_water_table_factor(
        df_m: float,
        b_m: float,
        dw_m: float
    ) -> float:
        """
        Water Table Correction Factor W' per IS:6403-1981 Clause 5.1.2:
        - If water table is above foundation base (0 <= Dw <= Df):
            W' = 0.5 + 0.5 * (Dw / Df)
        - If water table is between base and base + B (Df < Dw < Df + B):
            W' = 0.5 + 0.5 * ((Dw - Df) / B)
        - If water table is below Df + B:
            W' = 1.0
        """
        if df_m <= 0:
            return 1.0
        if dw_m <= df_m:
            w_prime = 0.5 + 0.5 * (max(0.0, dw_m) / df_m)
        elif df_m < dw_m < (df_m + b_m):
            w_prime = 0.5 + 0.5 * ((dw_m - df_m) / b_m)
        else:
            w_prime = 1.0
            
        return float(np.clip(w_prime, 0.5, 1.0))

    def compute_is6403_capacity(
        self,
        c_kpa: float,
        phi_deg: float,
        df_m: float,
        b_m: float,
        l_m: float,
        dw_m: float,
        gamma_bulk: float = 18.5,
        footing_shape: str = "square"
    ) -> Dict[str, float]:
        """
        Computes Ultimate Bearing Capacity (q_u) and Net Safe Bearing Capacity (q_ns)
        strictly per IS:6403-1981.
        """
        # Local shear failure adjustment (IS:6403 Clause 5.2) if phi < 28 degrees
        is_local_shear = phi_deg < 28.0
        if is_local_shear:
            phi_rad = np.arctan((2.0 / 3.0) * np.tan(np.radians(phi_deg)))
            phi_effective = np.degrees(phi_rad)
            c_effective = (2.0 / 3.0) * c_kpa
        else:
            phi_effective = phi_deg
            phi_rad = np.radians(phi_deg)
            c_effective = c_kpa
            
        # 1. Bearing Capacity Factors (Vesic / IS:6403 Appendix B)
        if phi_effective <= 0.01:
            n_q = 1.0
            n_c = 5.14
            n_gamma = 0.0
        else:
            n_q = np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.radians(45.0 + phi_effective / 2.0)) ** 2)
            n_c = (n_q - 1.0) / np.tan(phi_rad)
            n_gamma = 2.0 * (n_q + 1.0) * np.tan(phi_rad)
            
        # 2. Shape Factors (IS:6403 Clause 5.1.2)
        if footing_shape.lower() == "square" or abs(b_m - l_m) < 1e-4:
            s_c = 1.0 + (n_q / max(n_c, 1e-4))
            s_q = 1.0 + np.tan(phi_rad)
            s_gamma = 0.6  # 1 - 0.4 * (B/L)
        elif footing_shape.lower() == "strip":
            s_c = 1.0
            s_q = 1.0
            s_gamma = 1.0
        else:
            s_c = 1.0 + 0.2 * (b_m / l_m)
            s_q = 1.0 + 0.2 * (b_m / l_m)
            s_gamma = 1.0 - 0.4 * (b_m / l_m)
            
        # 3. Depth Factors (IS:6403 Clause 5.1.2)
        ratio_df_b = df_m / max(b_m, 0.1)
        if phi_effective > 0.01:
            d_q = 1.0 + 2.0 * np.tan(phi_rad) * ((1.0 - np.sin(phi_rad)) ** 2) * min(ratio_df_b, 1.0)
            d_c = 1.0 + (d_q - 1.0) / (n_c * np.tan(phi_rad))
        else:
            d_q = 1.0
            d_c = 1.0 + 0.4 * min(ratio_df_b, 1.0)
        d_gamma = 1.0
        
        # 4. Water Table Correction Factor W'
        w_prime = self.compute_water_table_factor(df_m, b_m, dw_m)
        
        # 5. Overburden at foundation base q = gamma * Df
        q_overburden = gamma_bulk * df_m
        
        # 6. Net Ultimate Bearing Capacity (q_nu)
        term_cohesion = c_effective * n_c * s_c * d_c
        term_surcharge = q_overburden * (n_q - 1.0) * s_q * d_q * w_prime
        term_wedge = 0.5 * gamma_bulk * b_m * n_gamma * s_gamma * d_gamma * w_prime
        
        q_nu = term_cohesion + term_surcharge + term_wedge
        
        # 7. Safe Bearing Capacity
        fs = self.config.factor_of_safety
        q_ns = q_nu / fs
        q_safe_gross = q_ns + q_overburden
        
        return {
            "phi_effective_deg": round(float(phi_effective), 2),
            "c_effective_kpa": round(float(c_effective), 2),
            "is_local_shear": is_local_shear,
            "Nc": round(float(n_c), 2),
            "Nq": round(float(n_q), 2),
            "Ngamma": round(float(n_gamma), 2),
            "sc": round(float(s_c), 2),
            "sq": round(float(s_q), 2),
            "sgamma": round(float(s_gamma), 2),
            "dc": round(float(d_c), 2),
            "dq": round(float(d_q), 2),
            "W_prime": round(float(w_prime), 2),
            "q_nu_kpa": round(float(q_nu), 2),
            "q_ns_kpa": round(float(q_ns), 2),
            "q_safe_gross_kpa": round(float(q_safe_gross), 2)
        }

    def compute_settlement_allowable_pressure(
        self,
        n_corrected: float,
        b_m: float,
        df_m: float,
        dw_m: float,
        permissible_settlement_mm: float = 25.0
    ) -> float:
        """
        Allowable bearing pressure limited by 25mm maximum permissible settlement
        (Teng / Bowles formulation based on corrected SPT N-value).
        Returns pressure in kPa.
        """
        if n_corrected <= 0:
            return 50.0
            
        w_prime = self.compute_water_table_factor(df_m, b_m, dw_m)
        depth_factor = 1.0 + 0.33 * (df_m / b_m)
        depth_factor = min(1.33, depth_factor)
        
        # Teng's formulation for isolated footings in metric units (yields t/m2, multiply by 9.81 for kPa)
        # qa (t/m2) = 1.4 * (N - 3) * [(B+0.3)/(2B)]^2 * W' * Df_factor for 25mm settlement
        if b_m <= 1.2:
            qa_tm2 = 1.4 * max(1.0, n_corrected - 3.0) * w_prime * depth_factor
        else:
            size_factor = ((b_m + 0.3) / (2.0 * b_m)) ** 2
            qa_tm2 = 1.4 * max(1.0, n_corrected - 3.0) * size_factor * w_prime * depth_factor
            
        qa_kpa = qa_tm2 * 9.81 * (permissible_settlement_mm / 25.0)
        return round(float(qa_kpa), 2)

    def evaluate_grid_sbc(
        self,
        interpolated_n: np.ndarray,
        water_table_depth: float,
        df_m: float = 2.0,
        b_m: float = 2.0,
        soil_type: str = "Silty Sand"
    ) -> np.ndarray:
        """
        Calculates governing Safe Bearing Capacity (SBC) across a 2D interpolated raster grid.
        Governing SBC = min(q_safe_shear, q_allowable_settlement).
        """
        ny, nx = interpolated_n.shape
        sbc_grid = np.full((ny, nx), np.nan, dtype=np.float32)
        
        flat_n = interpolated_n.ravel()
        valid_indices = np.where(~np.isnan(flat_n))[0]
        
        for idx in valid_indices:
            n_val = flat_n[idx]
            # 1. Correct N for depth and water table
            _, _, n_cor = self.correct_spt_n(n_val, df_m, water_table_depth)
            
            # 2. Shear parameters
            c_val, phi_val = self.estimate_shear_parameters(n_cor, soil_type)
            
            # 3. Shear capacity (IS:6403)
            res_is6403 = self.compute_is6403_capacity(
                c_kpa=c_val,
                phi_deg=phi_val,
                df_m=df_m,
                b_m=b_m,
                l_m=b_m,
                dw_m=water_table_depth
            )
            q_safe_shear = res_is6403["q_safe_gross_kpa"]
            
            # 4. Settlement limit
            q_settle = self.compute_settlement_allowable_pressure(
                n_corrected=n_cor,
                b_m=b_m,
                df_m=df_m,
                dw_m=water_table_depth
            )
            
            # Governing SBC (minimum of shear safety and settlement criterion)
            sbc_gov = min(q_safe_shear, q_settle)
            # Geological sanity bounds: min 75 kPa, max 800 kPa for soil
            sbc_gov = np.clip(sbc_gov, 75.0, 800.0)
            
            sbc_grid.ravel()[idx] = sbc_gov
            
        return sbc_grid
