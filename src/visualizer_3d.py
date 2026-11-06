"""
Interactive 3D Subsurface & Digital Twin Visualizer
===================================================
Generates rotatable, GPU-accelerated WebGL 3D interactive scenes for Streamlit
and web deployment using Plotly 3D.

Visualizations:
1. 3D Cyber-Physical Digital Twin Scene:
   - 3D Terrain DTM Surface
   - 3D Subsurface Strata Boundaries
   - 3D Volumetric Voxels (Effective Stress, Pore Pressure, Janbu Modulus)
   - 3D Live IoT Piezometers (Sensor tip, casing, and dynamic groundwater surface)
2. 3D Borehole Stratigraphy Scene:
   - 3D Vertical borehole logs positioned at geospatial coordinates
   - Lithological layer intervals and SPT N-value heatmaps
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def build_interactive_3d_digital_twin_scene(
    twin_engine,
    stress_metric: str = "effective_stress_kpa",
    show_voxels: bool = True,
    show_sensors: bool = True,
    show_water_table: bool = True,
    downsample_factor: int = 2
) -> go.Figure:
    """
    Constructs an interactive 3D WebGL Digital Twin scene from a SubsurfaceDigitalTwinEngine.
    """
    fig = go.Figure()
    
    # 1. Surface DTM
    dem = twin_engine.surface_dem[::downsample_factor, ::downsample_factor]
    gx = twin_engine.grid_x[::downsample_factor, ::downsample_factor]
    gy = twin_engine.grid_y[::downsample_factor, ::downsample_factor]
    
    fig.add_trace(go.Surface(
        x=gx,
        y=gy,
        z=dem,
        colorscale="Earth",
        opacity=0.75,
        name="Ground Surface (DTM)",
        showscale=False,
        hoverinfo="x+y+z",
        contours_z=dict(show=True, usecolormap=True, highlightcolor="limegreen", project_z=True)
    ))
    
    # 2. Dynamic Groundwater Surface (if sensors available)
    if show_water_table and twin_engine.sensors:
        pz_levels = [s.current_reading for s in twin_engine.sensors.values() if s.sensor_type == "piezometer"]
        if pz_levels:
            mean_wt = float(np.mean(pz_levels))
            wt_plane = np.full_like(dem, mean_wt)
            fig.add_trace(go.Surface(
                x=gx,
                y=gy,
                z=wt_plane,
                colorscale=[[0, "rgba(0, 150, 255, 0.5)"], [1, "rgba(0, 100, 230, 0.6)"]],
                opacity=0.55,
                name=f"Dynamic Water Table ({mean_wt:.2f} m RL)",
                showscale=False,
                hoverinfo="x+y+z"
            ))

    # 3. Strata Boundary Interfaces
    colors = ["#c2b280", "#a08260", "#c29b38", "#708090", "#36454f", "#2f4f4f"]
    for idx, (s_name, s_surf) in enumerate(twin_engine.strata_bottoms.items()):
        down_surf = s_surf[::downsample_factor, ::downsample_factor]
        color = colors[idx % len(colors)]
        fig.add_trace(go.Surface(
            x=gx,
            y=gy,
            z=down_surf,
            colorscale=[[0, color], [1, color]],
            opacity=0.35,
            name=f"Base: {s_name}",
            showscale=False,
            hoverinfo="x+y+z"
        ))

    # 4. Volumetric Subsurface Voxels
    if show_voxels:
        v_df = twin_engine.get_voxel_dataframe()
        if not v_df.empty:
            # Subsample voxels for smooth 60fps WebGL rendering
            step = max(1, len(v_df) // 3000)
            sample_voxels = v_df.iloc[::step]
            
            metric_col = stress_metric if stress_metric in sample_voxels.columns else "effective_stress_kpa"
            metric_label = {
                "effective_stress_kpa": "Effective Stress (kPa)",
                "total_stress_kpa": "Total Overburden Stress (kPa)",
                "pore_pressure_kpa": "Hydrostatic Pore Pressure (kPa)",
                "elastic_modulus_mpa": "Janbu Modulus E' (MPa)",
                "spt_n": "Synthesized SPT N-value"
            }.get(metric_col, metric_col)
            
            customdata = np.stack((
                sample_voxels["stratum_name"],
                sample_voxels["total_stress_kpa"],
                sample_voxels["pore_pressure_kpa"],
                sample_voxels["effective_stress_kpa"],
                sample_voxels["elastic_modulus_mpa"]
            ), axis=-1)

            fig.add_trace(go.Scatter3d(
                x=sample_voxels["x"],
                y=sample_voxels["y"],
                z=sample_voxels["z"],
                mode="markers",
                marker=dict(
                    size=4.5,
                    color=sample_voxels[metric_col],
                    colorscale="Turbo",
                    colorbar=dict(
                        title=dict(text=metric_label, side="right"),
                        thickness=16,
                        len=0.75,
                        x=1.05
                    ),
                    opacity=0.85
                ),
                name="Subsurface 3D Voxels",
                customdata=customdata,
                hovertemplate=(
                    "<b>X:</b> %{x:.1f} m<br>"
                    "<b>Y:</b> %{y:.1f} m<br>"
                    "<b>Elevation:</b> %{z:.2f} m RL<br>"
                    "<b>Stratum:</b> %{customdata[0]}<br>"
                    "<b>Total Stress:</b> %{customdata[1]:.1f} kPa<br>"
                    "<b>Pore Pressure:</b> %{customdata[2]:.1f} kPa<br>"
                    "<b>Effective Stress:</b> %{customdata[3]:.1f} kPa<br>"
                    "<b>Modulus E':</b> %{customdata[4]:.1f} MPa<br>"
                    "<extra></extra>"
                )
            ))

    # 5. IoT Telemetry Sensors (Piezometers)
    if show_sensors and twin_engine.sensors:
        for s_id, s in twin_engine.sensors.items():
            surf_z = float(np.mean(dem))
            # Casing tube line
            fig.add_trace(go.Scatter3d(
                x=[s.easting_m, s.easting_m],
                y=[s.northing_m, s.northing_m],
                z=[s.tip_elevation_m, surf_z + 1.5],
                mode="lines",
                line=dict(color="cyan", width=6),
                name=f"Well Casing: {s_id}",
                showlegend=False
            ))
            # Sensor tip marker
            fig.add_trace(go.Scatter3d(
                x=[s.easting_m],
                y=[s.northing_m],
                z=[s.tip_elevation_m],
                mode="markers+text",
                marker=dict(size=8, color="red", symbol="diamond"),
                text=[s_id],
                textposition="bottom center",
                name=f"Piezometer {s_id}",
                hovertemplate=(
                    f"<b>Sensor:</b> {s_id}<br>"
                    f"<b>Type:</b> {s.sensor_type}<br>"
                    f"<b>Tip Elevation:</b> {s.tip_elevation_m:.2f} m RL<br>"
                    f"<b>Water Level:</b> {s.current_reading:.2f} m RL<br>"
                    f"<b>Status:</b> {s.status}<extra></extra>"
                )
            ))

    # 3D Layout formatting
    fig.update_layout(
        title=dict(
            text="⚡ Interactive 3D Geotechnical Digital Twin (WebGL)",
            x=0.05,
            y=0.95,
            font=dict(size=18, color="white")
        ),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        scene=dict(
            xaxis=dict(title="Easting (m)", gridcolor="#333333", backgroundcolor="#161b22"),
            yaxis=dict(title="Northing (m)", gridcolor="#333333", backgroundcolor="#161b22"),
            zaxis=dict(title="Elevation (m RL)", gridcolor="#333333", backgroundcolor="#161b22"),
            aspectmode="manual",
            aspectratio=dict(x=1.2, y=1.2, z=0.6),
            camera=dict(
                eye=dict(x=1.6, y=-1.6, z=1.1)
            )
        ),
        legend=dict(
            bgcolor="rgba(22, 27, 34, 0.8)",
            font=dict(color="white"),
            x=0.01,
            y=0.99
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    
    return fig


def build_interactive_3d_borehole_scene(
    dem_handler,
    borehole_df: pd.DataFrame,
    strata_names: Optional[List[str]] = None
) -> go.Figure:
    """
    Constructs an interactive 3D WebGL scene displaying terrain and vertical borehole cylinders.
    """
    fig = go.Figure()

    # DTM Surface
    gx = dem_handler.mesh_x
    gy = dem_handler.mesh_y
    dem = dem_handler.data
    
    # Subsample if large
    step = max(1, dem.shape[0] // 50)
    fig.add_trace(go.Surface(
        x=gx[::step, ::step],
        y=gy[::step, ::step],
        z=dem[::step, ::step],
        colorscale="Earth",
        opacity=0.65,
        name="Terrain DTM",
        showscale=False
    ))

    # Unique boreholes
    bh_groups = borehole_df.groupby("Borehole_ID")
    strata_palette = {
        "Topsoil": "#8B5A2B",
        "Fill": "#A0522D",
        "Soft": "#CD853F",
        "Clay": "#D2691E",
        "Sand": "#DAA520",
        "Silt": "#BDB76B",
        "Murrum": "#CD5C5C",
        "Weathered": "#708090",
        "Basalt": "#2F4F4F",
        "Gneiss": "#4682B4",
        "Rock": "#1C1C1C"
    }

    def get_color(layer_name: str) -> str:
        for k, col in strata_palette.items():
            if k.lower() in str(layer_name).lower():
                return col
        return "#808080"

    for bh_id, group in bh_groups:
        first = group.iloc[0]
        easting = float(first.get("Easting_m", 0.0))
        northing = float(first.get("Northing_m", 0.0))
        ground_rl = float(first.get("Ground_RL_m", first.get("Ground_Elevation_m", 0.0)))
        
        # Ground marker
        fig.add_trace(go.Scatter3d(
            x=[easting],
            y=[northing],
            z=[ground_rl + 0.5],
            mode="markers+text",
            marker=dict(size=5, color="yellow", symbol="circle"),
            text=[str(bh_id)],
            textposition="top center",
            name=f"Borehole {bh_id}",
            showlegend=False
        ))

        # Stratum segments
        for _, row in group.iterrows():
            d_top = float(row.get("Depth_Top_m", 0.0))
            d_bot = float(row.get("Depth_Bottom_m", row.get("Depth_m", d_top + 2.0)))
            z_top = float(row.get("Layer_Top_RL_m", ground_rl - d_top))
            z_bot = float(row.get("Layer_Bottom_RL_m", ground_rl - d_bot))
            s_name = str(row.get("Layer_Name", "Strata"))
            n_val = float(row.get("Field_N", row.get("Corrected_N", 0.0)))
            
            fig.add_trace(go.Scatter3d(
                x=[easting, easting],
                y=[northing, northing],
                z=[z_bot, z_top],
                mode="lines",
                line=dict(color=get_color(s_name), width=10),
                name=s_name,
                showlegend=False,
                hovertemplate=(
                    f"<b>Borehole:</b> {bh_id}<br>"
                    f"<b>Strata:</b> {s_name}<br>"
                    f"<b>Depth:</b> {d_top:.1f} - {d_bot:.1f} m<br>"
                    f"<b>RL:</b> {z_bot:.2f} to {z_top:.2f} m<br>"
                    f"<b>SPT N:</b> {n_val:.0f}<extra></extra>"
                )
            ))

    fig.update_layout(
        title="📍 3D Borehole Lithological Columns & Surface DTM",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        scene=dict(
            xaxis=dict(title="Easting (m)", gridcolor="#333"),
            yaxis=dict(title="Northing (m)", gridcolor="#333"),
            zaxis=dict(title="Elevation (m RL)", gridcolor="#333"),
            aspectratio=dict(x=1.2, y=1.2, z=0.7)
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    return fig
