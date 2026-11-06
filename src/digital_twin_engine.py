"""
Subsurface Geotechnical Digital Twin Engine
===========================================
Transitions static 2.5D DTM + 1D Borehole models into a dynamic, 4D
Cyber-Physical Subsurface Digital Twin.

Capabilities:
1. 3D Volumetric Voxelization (True 3D grid with stress, pore pressure, stiffness).
2. Dynamic IoT Sensor Telemetry Ingestion (Piezometers, dewatering pumps, InSAR).
3. Transient Effective Stress & Dynamic Bearing Capacity Tracking (IS:6403 / Terzaghi).
4. Pure-Python VTK Image Data (.vti) and GeoJSON-3D Exporters for ParaView / Cesium.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


@dataclass
class GeotechnicalVoxel:
    """Attributes of an individual 3D subsurface voxel."""
    x: float
    y: float
    z: float
    stratum_name: str
    stratum_id: int
    total_unit_weight_kn_m3: float
    total_stress_kpa: float
    pore_pressure_kpa: float
    effective_stress_kpa: float
    elastic_modulus_mpa: float
    spt_n: float


@dataclass
class TelemetrySensor:
    """IoT Geotechnical Telemetry Sensor (e.g. vibrating wire piezometer or settlement cell)."""
    sensor_id: str
    sensor_type: str  # 'piezometer', 'extensometer', 'settlement_cell', 'insar_point'
    easting_m: float
    northing_m: float
    tip_elevation_m: float
    current_reading: float  # e.g., Water Table RL (m) or Settlement (mm)
    baseline_reading: float
    unit: str
    status: str = "ONLINE"


class SubsurfaceDigitalTwinEngine:
    """
    Core computational kernel of the Subsurface Geotechnical Digital Twin.
    """

    def __init__(
        self,
        grid_x: np.ndarray,
        grid_y: np.ndarray,
        surface_dem: np.ndarray,
        strata_bottom_surfaces: Any,
        strata_names: Optional[List[str]] = None,
        strata_properties: Optional[Dict[str, Dict[str, float]]] = None,
        water_unit_weight_kn_m3: float = 9.81
    ):
        """
        Initialize the Digital Twin with spatial grid bounds, surface DTM,
        and layer boundary surfaces (dict of name->surface or list of surfaces).
        """
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.surface_dem = surface_dem
        self.gamma_w = water_unit_weight_kn_m3
        
        if isinstance(strata_bottom_surfaces, list):
            if strata_names is None:
                strata_names = [f"Stratum_{i+1}" for i in range(len(strata_bottom_surfaces))]
            self.strata_bottoms = {name: surf for name, surf in zip(strata_names, strata_bottom_surfaces)}
            self.strata_names = strata_names
        else:
            self.strata_bottoms = strata_bottom_surfaces
            self.strata_names = list(self.strata_bottoms.keys())
        
        # Default strata geotechnical properties if not provided
        self.strata_props = strata_properties or {
            "Topsoil / Fill": {"gamma": 17.5, "e0": 0.85, "E0": 12.0, "spt": 6.0},
            "Soft Silty Clay": {"gamma": 16.5, "e0": 1.10, "E0": 8.0, "spt": 4.0},
            "Fine Sand": {"gamma": 18.5, "e0": 0.65, "E0": 25.0, "spt": 18.0},
            "Stiff Silty Clay": {"gamma": 19.0, "e0": 0.70, "E0": 35.0, "spt": 24.0},
            "Dense Grey Sand": {"gamma": 20.0, "e0": 0.55, "E0": 60.0, "spt": 38.0},
            "Weathered Rock / Murrum": {"gamma": 21.0, "e0": 0.40, "E0": 90.0, "spt": 65.0},
            "Bedrock": {"gamma": 24.0, "e0": 0.20, "E0": 250.0, "spt": 100.0}
        }
        
        self.sensors: Dict[str, TelemetrySensor] = {}
        self._init_default_sensors()

    def _init_default_sensors(self):
        """Deploys a default array of virtual IoT telemetry sensors across the site."""
        mid_x = float(np.mean(self.grid_x))
        mid_y = float(np.mean(self.grid_y))
        span_x = float(np.max(self.grid_x) - np.min(self.grid_x)) * 0.3
        span_y = float(np.max(self.grid_y) - np.min(self.grid_y)) * 0.3
        
        # Piezometer 1 (Center)
        self.add_sensor(TelemetrySensor(
            sensor_id="PZ-01",
            sensor_type="piezometer",
            easting_m=mid_x,
            northing_m=mid_y,
            tip_elevation_m=float(np.mean(self.surface_dem) - 15.0),
            current_reading=float(np.mean(self.surface_dem) - 2.5),
            baseline_reading=float(np.mean(self.surface_dem) - 2.5),
            unit="m RL"
        ))
        
        # Piezometer 2 (East)
        self.add_sensor(TelemetrySensor(
            sensor_id="PZ-02",
            sensor_type="piezometer",
            easting_m=mid_x + span_x,
            northing_m=mid_y,
            tip_elevation_m=float(np.mean(self.surface_dem) - 18.0),
            current_reading=float(np.mean(self.surface_dem) - 2.8),
            baseline_reading=float(np.mean(self.surface_dem) - 2.8),
            unit="m RL"
        ))
        
        # Settlement Cell 1 (North)
        self.add_sensor(TelemetrySensor(
            sensor_id="SC-01",
            sensor_type="settlement_cell",
            easting_m=mid_x,
            northing_m=mid_y + span_y,
            tip_elevation_m=float(np.mean(self.surface_dem) - 1.5),
            current_reading=0.0,
            baseline_reading=0.0,
            unit="mm"
        ))

    def add_sensor(self, sensor: TelemetrySensor):
        """Registers an IoT telemetry sensor in the twin."""
        self.sensors[sensor.sensor_id] = sensor

    def ingest_sensor_telemetry(self, telemetry_updates: Dict[str, float]):
        """
        Updates live readings from streaming telemetry (e.g. MQTT/REST).
        telemetry_updates = {"PZ-01": 18.2, "SC-01": 4.5}
        """
        for s_id, val in telemetry_updates.items():
            if s_id in self.sensors:
                self.sensors[s_id].current_reading = val

    def get_dynamic_water_table_surface(self) -> np.ndarray:
        """
        Assimilates piezometer telemetry to construct the live 2D groundwater surface.
        """
        piezo_sensors = [s for s in self.sensors.values() if s.sensor_type == "piezometer"]
        if not piezo_sensors:
            # Fallback: uniform water table 3m below surface
            return self.surface_dem - 3.0
            
        pts_x = [s.easting_m for s in piezo_sensors]
        pts_y = [s.northing_m for s in piezo_sensors]
        vals = [s.current_reading for s in piezo_sensors]
        
        if len(piezo_sensors) == 1:
            # Offset surface by reading depth
            delta = float(self.surface_dem.mean() - vals[0])
            return self.surface_dem - delta
            
        # Inverse Distance Weighting interpolation for multiple sensors
        ny, nx = self.surface_dem.shape
        wt_grid = np.zeros_like(self.surface_dem)
        
        for i in range(ny):
            for j in range(nx):
                x_ij = self.grid_x[i, j]
                y_ij = self.grid_y[i, j]
                dists = np.hypot(x_ij - np.array(pts_x), y_ij - np.array(pts_y))
                if np.min(dists) < 1e-3:
                    wt_grid[i, j] = vals[np.argmin(dists)]
                else:
                    weights = 1.0 / (dists ** 2)
                    wt_grid[i, j] = np.sum(weights * np.array(vals)) / np.sum(weights)
                    
        # Ensure groundwater does not exceed ground surface DEM
        return np.minimum(wt_grid, self.surface_dem)

    def generate_volumetric_voxels(
        self,
        nx: int = 40,
        ny: int = 40,
        nz: int = 25,
        depth_extent_m: float = 35.0
    ) -> Dict[str, Any]:
        """
        Constructs a full 3D volumetric multi-physics voxel mesh of the subsurface.
        Computes total stress, pore water pressure, effective stress, and dynamic stiffness.
        """
        # Downsample grid bounds for volumetric speed
        x_lin = np.linspace(self.grid_x.min(), self.grid_x.max(), nx)
        y_lin = np.linspace(self.grid_y.min(), self.grid_y.max(), ny)
        X, Y = np.meshgrid(x_lin, y_lin)
        
        # Sample DTM and water table on this mesh
        from scipy.interpolate import RegularGridInterpolator
        orig_y = self.grid_y[:, 0] if self.grid_y[0, 0] < self.grid_y[-1, 0] else self.grid_y[::-1, 0]
        orig_x = self.grid_x[0, :]
        
        # Surface DTM interpolator
        rgi_dem = RegularGridInterpolator(
            (self.grid_y[:, 0], self.grid_x[0, :]),
            self.surface_dem,
            bounds_error=False,
            fill_value=None
        )
        Z_surf = rgi_dem((Y, X))
        
        # Dynamic Water Table
        live_wt = self.get_dynamic_water_table_surface()
        rgi_wt = RegularGridInterpolator(
            (self.grid_y[:, 0], self.grid_x[0, :]),
            live_wt,
            bounds_error=False,
            fill_value=None
        )
        Z_wt = rgi_wt((Y, X))
        
        # Layer surfaces interpolators
        layer_bottom_grids = {}
        for s_name, s_grid in self.strata_bottoms.items():
            rgi_layer = RegularGridInterpolator(
                (self.grid_y[:, 0], self.grid_x[0, :]),
                s_grid,
                bounds_error=False,
                fill_value=None
            )
            layer_bottom_grids[s_name] = rgi_layer((Y, X))
            
        # Z elevations from max ground surface down to depth_extent_m
        z_max = float(np.max(Z_surf))
        z_min = float(np.min(Z_surf) - depth_extent_m)
        z_lin = np.linspace(z_max, z_min, nz)
        
        # 3D Arrays: shape (ny, nx, nz)
        stratum_id_grid = np.zeros((ny, nx, nz), dtype=np.int32)
        total_stress = np.zeros((ny, nx, nz), dtype=np.float32)
        pore_pressure = np.zeros((ny, nx, nz), dtype=np.float32)
        effective_stress = np.zeros((ny, nx, nz), dtype=np.float32)
        elastic_modulus = np.zeros((ny, nx, nz), dtype=np.float32)
        
        # Atmospheric pressure in kPa for Janbu stress scaling
        p_atm = 101.325
        
        # March down vertically to compute overburden integration
        dz = abs(z_lin[0] - z_lin[1]) if nz > 1 else 1.0
        
        for j in range(ny):
            for i in range(nx):
                surf_z = Z_surf[j, i]
                wt_z = Z_wt[j, i]
                current_sigma = 0.0
                
                for k in range(nz):
                    z_k = z_lin[k]
                    
                    if z_k > surf_z:
                        # Air / Above ground
                        stratum_id_grid[j, i, k] = -1  # Air
                        total_stress[j, i, k] = 0.0
                        pore_pressure[j, i, k] = 0.0
                        effective_stress[j, i, k] = 0.0
                        elastic_modulus[j, i, k] = 0.0
                        continue
                        
                    # Identify Stratum
                    chosen_layer_id = len(self.strata_names) - 1
                    chosen_layer_name = self.strata_names[-1]
                    
                    for idx, s_name in enumerate(self.strata_names):
                        b_z = layer_bottom_grids[s_name][j, i]
                        if z_k >= b_z:
                            chosen_layer_id = idx
                            chosen_layer_name = s_name
                            break
                            
                    props = self.strata_props.get(chosen_layer_name, {"gamma": 18.0, "E0": 20.0, "spt": 15.0})
                    gamma = props["gamma"]
                    e0 = props.get("e0", 0.7)
                    E0 = props["E0"]
                    
                    # Overburden Stress Integration
                    current_sigma += gamma * dz
                    total_stress[j, i, k] = current_sigma
                    
                    # Hydrostatic Pore Pressure
                    if z_k < wt_z:
                        u = (wt_z - z_k) * self.gamma_w
                    else:
                        u = 0.0
                        
                    pore_pressure[j, i, k] = u
                    
                    # Terzaghi Effective Stress: sigma' = sigma - u
                    sigma_prime = max(1.0, current_sigma - u)
                    effective_stress[j, i, k] = sigma_prime
                    
                    # Non-linear stress-dependent stiffness (Janbu / Hardening Soil law)
                    # E = E0 * (sigma' / p_atm) ** 0.5
                    stiffness = E0 * ((sigma_prime / p_atm) ** 0.5)
                    elastic_modulus[j, i, k] = stiffness
                    stratum_id_grid[j, i, k] = chosen_layer_id

        return {
            "x_coords": x_lin,
            "y_coords": y_lin,
            "z_coords": z_lin,
            "stratum_id": stratum_id_grid,
            "total_stress_kpa": total_stress,
            "pore_pressure_kpa": pore_pressure,
            "effective_stress_kpa": effective_stress,
            "elastic_modulus_mpa": elastic_modulus,
            "surface_dem": Z_surf,
            "water_table": Z_wt,
            "strata_names": self.strata_names
        }

    def get_voxel_dataframe(self, nx: int = 30, ny: int = 30, nz: int = 20) -> pd.DataFrame:
        """Flattens non-air subsurface voxels into a pandas DataFrame for 3D visualization."""
        voxels = self.generate_volumetric_voxels(nx=nx, ny=ny, nz=nz)
        x_lin = voxels["x_coords"]
        y_lin = voxels["y_coords"]
        z_lin = voxels["z_coords"]
        s_id = voxels["stratum_id"]
        tot_s = voxels["total_stress_kpa"]
        u = voxels["pore_pressure_kpa"]
        eff_s = voxels["effective_stress_kpa"]
        mod_e = voxels["elastic_modulus_mpa"]
        strata_names = voxels["strata_names"]
        
        records = []
        ny_cnt, nx_cnt, nz_cnt = s_id.shape
        for j in range(ny_cnt):
            for i in range(nx_cnt):
                for k in range(nz_cnt):
                    layer_idx = s_id[j, i, k]
                    if layer_idx < 0:
                        continue  # Air / Above ground
                    s_name = strata_names[layer_idx] if layer_idx < len(strata_names) else "Substratum"
                    records.append({
                        "x": float(x_lin[i]),
                        "y": float(y_lin[j]),
                        "z": float(z_lin[k]),
                        "stratum_name": s_name,
                        "stratum_id": int(layer_idx),
                        "total_stress_kpa": float(tot_s[j, i, k]),
                        "pore_pressure_kpa": float(u[j, i, k]),
                        "effective_stress_kpa": float(eff_s[j, i, k]),
                        "elastic_modulus_mpa": float(mod_e[j, i, k])
                    })
        return pd.DataFrame(records)

    def export_vtk_image_data(self, voxel_data: Dict[str, Any], filepath: str) -> str:
        """
        Exports the 3D subsurface voxel volume into pure-Python VTK XML (.vti) format.
        Directly readable by ParaView, OpenGeoSys, and 3D web graphics pipelines.
        """
        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        nx = len(voxel_data["x_coords"])
        ny = len(voxel_data["y_coords"])
        nz = len(voxel_data["z_coords"])
        
        dx = float(voxel_data["x_coords"][1] - voxel_data["x_coords"][0]) if nx > 1 else 1.0
        dy = float(voxel_data["y_coords"][1] - voxel_data["y_coords"][0]) if ny > 1 else 1.0
        dz = float(abs(voxel_data["z_coords"][1] - voxel_data["z_coords"][0])) if nz > 1 else 1.0
        
        origin_x = float(voxel_data["x_coords"][0])
        origin_y = float(voxel_data["y_coords"][0])
        origin_z = float(voxel_data["z_coords"][-1])  # bottom
        
        # Flatten arrays in Fortran order for VTK
        eff_stress = voxel_data["effective_stress_kpa"].flatten(order='F')
        pore_p = voxel_data["pore_pressure_kpa"].flatten(order='F')
        e_mod = voxel_data["elastic_modulus_mpa"].flatten(order='F')
        strat_id = voxel_data["stratum_id"].flatten(order='F')
        
        def array_to_vtk_str(arr):
            return " ".join(f"{v:.2f}" for v in arr)

        vtk_xml = f"""<?xml version="1.0"?>
<VTKFile type="ImageData" version="0.1" byte_order="LittleEndian">
  <ImageData WholeExtent="0 {nx-1} 0 {ny-1} 0 {nz-1}" Origin="{origin_x:.3f} {origin_y:.3f} {origin_z:.3f}" Spacing="{dx:.3f} {dy:.3f} {dz:.3f}">
    <Piece Extent="0 {nx-1} 0 {ny-1} 0 {nz-1}">
      <PointData Scalars="EffectiveStress_kPa">
        <DataArray type="Float32" Name="EffectiveStress_kPa" NumberOfComponents="1" format="ascii">
          {array_to_vtk_str(eff_stress)}
        </DataArray>
        <DataArray type="Float32" Name="PoreWaterPressure_kPa" NumberOfComponents="1" format="ascii">
          {array_to_vtk_str(pore_p)}
        </DataArray>
        <DataArray type="Float32" Name="ElasticModulus_MPa" NumberOfComponents="1" format="ascii">
          {array_to_vtk_str(e_mod)}
        </DataArray>
        <DataArray type="Int32" Name="StratumID" NumberOfComponents="1" format="ascii">
          {" ".join(str(int(v)) for v in strat_id)}
        </DataArray>
      </PointData>
    </Piece>
  </ImageData>
</VTKFile>
"""
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(vtk_xml)
            
        return str(out_path.resolve())

    def compute_dynamic_bearing_capacity(
        self,
        foundation_depth_m: float = 2.0,
        footing_width_m: float = 2.5,
        spt_n_layer: float = 18.0
    ) -> Dict[str, Any]:
        """
        Dynamically recalculates safe bearing capacity across the site in response
        to live piezometer water table levels (IS:6403 & IS:2131).
        """
        live_wt = self.get_dynamic_water_table_surface()
        wt_depth = np.maximum(0.0, self.surface_dem - live_wt)
        
        # IS:6403 Water Table Factor W'
        # Dw <= Df: W' = 0.5 * (1 + Dw / Df)
        # Df < Dw < Df + B: W' = 0.5 * (1 + (Dw - Df)/B)
        # Dw >= Df + B: W' = 1.0
        w_prime = np.ones_like(wt_depth)
        
        mask_zone1 = wt_depth <= foundation_depth_m
        w_prime[mask_zone1] = 0.5 * (1.0 + wt_depth[mask_zone1] / max(0.1, foundation_depth_m))
        
        mask_zone2 = (wt_depth > foundation_depth_m) & (wt_depth < foundation_depth_m + footing_width_m)
        w_prime[mask_zone2] = 0.5 * (1.0 + (wt_depth[mask_zone2] - foundation_depth_m) / footing_width_m)
        
        w_prime = np.clip(w_prime, 0.5, 1.0)
        
        # Base Bearing Capacity from corrected SPT N
        # Empirical Bowles / Teng equation with continuous water correction
        # q_net_safe = 12.0 * N * W' * (1 + 0.33 * Df / B)
        depth_factor = 1.0 + 0.33 * min(foundation_depth_m / footing_width_m, 1.33)
        q_sbc_kpa = 12.0 * spt_n_layer * w_prime * depth_factor
        
        return {
            "dynamic_sbc_kpa": q_sbc_kpa,
            "water_table_depth_m": wt_depth,
            "water_factor_w_prime": w_prime,
            "mean_sbc_kpa": float(np.mean(q_sbc_kpa)),
            "min_sbc_kpa": float(np.min(q_sbc_kpa)),
            "max_sbc_kpa": float(np.max(q_sbc_kpa))
        }
