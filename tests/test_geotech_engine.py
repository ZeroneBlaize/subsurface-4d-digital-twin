"""
Unit tests for the Geotechnical Calculation Engine (IS:2131, IS:6403, and Bowles Settlement).
"""

import math
import pytest
import numpy as np
from src.geotech_engine import GeotechEngine
from src.config import GeotechConfig


def test_is2131_overburden_correction():
    # At standard effective overburden of 100 kPa (approx 5.4m depth at gamma=18.5)
    depth = 100.0 / 18.5
    cn, n_ob, n_cor = GeotechEngine.correct_spt_n(field_n=20, depth_m=depth, water_table_depth_m=10.0)
    assert abs(cn - 1.0) < 0.05
    assert abs(n_ob - 20.0) < 1.0


def test_is2131_dilatancy_correction():
    # For fine sand/silt below water table with N_ob = 25 > 15
    # Corrected N = 15 + 0.5*(25 - 15) = 20
    # Setup depth where cn is approx 1.0
    depth = 100.0 / 18.5
    cn, n_ob, n_cor = GeotechEngine.correct_spt_n(
        field_n=20,
        depth_m=depth,
        water_table_depth_m=2.0,  # Below water table
        is_cohesive=False
    )
    expected_n_cor = 15.0 + 0.5 * (n_ob - 15.0)
    assert abs(n_cor - expected_n_cor) < 0.1


def test_water_table_factor_w_prime():
    # 1. Water table at surface (Dw = 0) -> W' = 0.5
    w1 = GeotechEngine.compute_water_table_factor(df_m=2.0, b_m=2.0, dw_m=0.0)
    assert abs(w1 - 0.5) < 1e-4

    # 2. Water table at base (Dw = Df = 2.0) -> W' = 1.0 / 0.5+0.5 = 1.0 or 0.5+0.5*(2/2) = 1.0
    w2 = GeotechEngine.compute_water_table_factor(df_m=2.0, b_m=2.0, dw_m=2.0)
    assert abs(w2 - 1.0) < 1e-4

    # 3. Water table deep below Df + B (Dw = 6.0) -> W' = 1.0
    w3 = GeotechEngine.compute_water_table_factor(df_m=2.0, b_m=2.0, dw_m=6.0)
    assert abs(w3 - 1.0) < 1e-4


def test_is6403_bearing_capacity_factors():
    cfg = GeotechConfig(factor_of_safety=3.0)
    engine = GeotechEngine(cfg)
    
    # Purely cohesive soil (phi = 0)
    res_phi0 = engine.compute_is6403_capacity(c_kpa=50.0, phi_deg=0.0, df_m=1.5, b_m=2.0, l_m=2.0, dw_m=5.0)
    assert res_phi0["Nc"] == 5.14
    assert res_phi0["Nq"] == 1.0
    assert res_phi0["Ngamma"] == 0.0
    assert res_phi0["q_nu_kpa"] > 0

    # Mixed soil (phi = 30)
    res_phi30 = engine.compute_is6403_capacity(c_kpa=10.0, phi_deg=30.0, df_m=2.0, b_m=2.0, l_m=2.0, dw_m=5.0)
    assert res_phi30["Nq"] > 18.0
    assert res_phi30["Nc"] > 30.0
    assert res_phi30["Ngamma"] > 20.0
    assert res_phi30["q_safe_gross_kpa"] > res_phi30["q_ns_kpa"]
