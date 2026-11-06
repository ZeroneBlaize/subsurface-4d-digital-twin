"""
Unit tests for the Spatial Interpolator and Monotonic Stacking Constraints.
"""

import pytest
import numpy as np
from src.spatial_interpolator import SpatialInterpolator


def test_idw_exact_interpolation():
    # 2x2 grid
    x = np.array([0.0, 10.0])
    y = np.array([0.0, 10.0])
    X, Y = np.meshgrid(x, y)
    
    interp = SpatialInterpolator(X, Y, boundary_buffer_m=100.0)
    
    # 3 known points
    x_obs = np.array([0.0, 10.0, 5.0])
    y_obs = np.array([0.0, 10.0, 5.0])
    z_obs = np.array([100.0, 200.0, 150.0])
    
    res = interp.interpolate_idw(x_obs, y_obs, z_obs)
    # Check exact match at co-located points
    assert abs(res[0, 0] - 100.0) < 1e-3
    assert abs(res[1, 1] - 200.0) < 1e-3


def test_monotonic_stacking_enforcement():
    # Ground DEM
    dem = np.full((10, 10), 300.0, dtype=np.float32)
    
    # Stratum 1: intended 295m, but with bad interpolation artifact at [0,0] where elevation = 305m (above ground!)
    s1 = np.full((10, 10), 295.0, dtype=np.float32)
    s1[0, 0] = 305.0
    
    # Stratum 2: intended 288m, with pinch-out (absent) at [5,5]
    s2 = np.full((10, 10), 288.0, dtype=np.float32)
    s2[5, 5] = 296.0  # Would cross above s1!
    
    X, Y = np.meshgrid(np.arange(10)*10.0, np.arange(10)*10.0)
    interp = SpatialInterpolator(X, Y)
    
    corr_surfaces, thicknesses = interp.enforce_stratigraphic_stacking(dem, [s1, s2])
    
    c_s1, c_s2 = corr_surfaces
    t1, t2 = thicknesses
    
    # Check non-crossing
    assert np.all(dem >= c_s1)
    assert np.all(c_s1 >= c_s2)
    
    # Check non-negative thickness
    assert np.all(t1 >= 0.0)
    assert np.all(t2 >= 0.0)
    
    # At [0,0], s1 must have been clamped down to ground level (300.0)
    assert c_s1[0, 0] == 300.0
    assert t1[0, 0] == 0.0
