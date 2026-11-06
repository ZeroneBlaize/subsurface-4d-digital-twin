"""
Visualizer: Publication-Quality 2D Strata Maps, Geotechnical Cross-Sections, and Interactive 3D Plotly Subsurface Models.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import plotly.graph_objects as go
import pandas as pd

from src.config import REPORTS_DIR, STANDARD_STRATA


class SubsurfaceVisualizer:
    """
    Renders 2D engineering cartography, geotechnical cross-sections,
    and interactive 3D multi-stratum models.
    """
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir if output_dir is not None else REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Color mapping for strata
        self.strata_colors = {
            "Topsoil / Fill": "#8D6E63",
            "Soft to Medium Silty Clay": "#4E342E",
            "Stiff Sandy Silt / Murrum": "#FFA726",
            "Weathered Basalt": "#78909C",
            "Hard Basalt (Bedrock)": "#37474F",
            "Water Table": "#0288D1"
        }

    def generate_site_dashboard_figure(
        self,
        mesh_x: np.ndarray,
        mesh_y: np.ndarray,
        ground_dem: np.ndarray,
        bedrock_rl: np.ndarray,
        clay_thickness: np.ndarray,
        sbc_grid: np.ndarray,
        borehole_df: pd.DataFrame,
        filename: str = "site_geotechnical_dashboard.png",
        bedrock_title: str = "Bedrock / Basal Stratum Top Surface R.L. (m)",
        clay_title: str = "Bearing Stratum Thickness (m) [Isopach Map]"
    ) -> Path:
        """
        Generates a 4-panel publication-ready engineering summary figure.
        """
        fig, axes = plt.subplots(2, 2, figsize=(18, 14), dpi=150)
        
        # Panel 1: DEM Elevation & Boreholes
        ax1 = axes[0, 0]
        im1 = ax1.pcolormesh(mesh_x, mesh_y, ground_dem, cmap="terrain", shading="auto")
        sc1 = ax1.scatter(borehole_df["Easting_m"], borehole_df["Northing_m"], color="black", s=40, edgecolors="white", label="Boreholes", zorder=5)
        for _, r in borehole_df.iterrows():
            ax1.text(r["Easting_m"] + 15, r["Northing_m"] + 15, r["Borehole_ID"], fontsize=8, weight="bold", color="black", zorder=6)
        ax1.set_title("Ground Surface Digital Elevation Model (DEM) & Borehole Locations", fontsize=12, pad=10, weight="bold")
        ax1.set_xlabel("Easting (m)", fontsize=10)
        ax1.set_ylabel("Northing (m)", fontsize=10)
        plt.colorbar(im1, ax=ax1, label="Surface Reduced Level (m)")
        ax1.legend(loc="upper right")
        ax1.grid(True, linestyle="--", alpha=0.4)
        
        # Panel 2: Bedrock Elevation
        ax2 = axes[0, 1]
        im2 = ax2.pcolormesh(mesh_x, mesh_y, bedrock_rl, cmap="viridis", shading="auto")
        if np.nanmax(bedrock_rl) - np.nanmin(bedrock_rl) > 0.05:
            cs2 = ax2.contour(mesh_x, mesh_y, bedrock_rl, levels=8, colors="white", alpha=0.6, linewidths=1.0)
            ax2.clabel(cs2, inline=True, fontsize=8, fmt="%.1f m")
        ax2.scatter(borehole_df["Easting_m"], borehole_df["Northing_m"], color="red", s=25, zorder=5)
        ax2.set_title(bedrock_title, fontsize=12, pad=10, weight="bold")
        ax2.set_xlabel("Easting (m)", fontsize=10)
        ax2.set_ylabel("Northing (m)", fontsize=10)
        plt.colorbar(im2, ax=ax2, label="Elevation (m R.L.)")
        ax2.grid(True, linestyle="--", alpha=0.4)
        
        # Panel 3: Stratum Thickness Isopach
        ax3 = axes[1, 0]
        im3 = ax3.pcolormesh(mesh_x, mesh_y, clay_thickness, cmap="YlOrBr", shading="auto")
        if np.nanmax(clay_thickness) - np.nanmin(clay_thickness) > 0.05:
            cs3 = ax3.contour(mesh_x, mesh_y, clay_thickness, levels=6, colors="black", alpha=0.4, linewidths=0.8)
            ax3.clabel(cs3, inline=True, fontsize=8, fmt="%.1f m")
        ax3.scatter(borehole_df["Easting_m"], borehole_df["Northing_m"], color="black", s=25, zorder=5)
        ax3.set_title(clay_title, fontsize=12, pad=10, weight="bold")
        ax3.set_xlabel("Easting (m)", fontsize=10)
        ax3.set_ylabel("Northing (m)", fontsize=10)
        plt.colorbar(im3, ax=ax3, label="Stratum Thickness (m)")
        ax3.grid(True, linestyle="--", alpha=0.4)
        
        # Panel 4: Safe Bearing Capacity (SBC)
        ax4 = axes[1, 1]
        im4 = ax4.pcolormesh(mesh_x, mesh_y, sbc_grid, cmap="RdYlGn", shading="auto")
        if np.nanmax(sbc_grid) - np.nanmin(sbc_grid) > 0.05:
            cs4 = ax4.contour(mesh_x, mesh_y, sbc_grid, levels=10, colors="black", alpha=0.6, linewidths=1.2)
            ax4.clabel(cs4, inline=True, fontsize=9, fmt="%d kPa")
        ax4.scatter(borehole_df["Easting_m"], borehole_df["Northing_m"], color="blue", s=30, edgecolors="white", zorder=5)
        ax4.set_title("Preliminary Safe Bearing Capacity (SBC in kPa) [IS:6403 & IS:2131]", fontsize=12, pad=10, weight="bold")
        ax4.set_xlabel("Easting (m)", fontsize=10)
        ax4.set_ylabel("Northing (m)", fontsize=10)
        plt.colorbar(im4, ax=ax4, label="Safe Bearing Capacity (kPa)")
        ax4.grid(True, linestyle="--", alpha=0.4)
        
        plt.tight_layout()
        out_path = self.output_dir / filename
        plt.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def generate_transect_cross_section(
        self,
        mesh_x: np.ndarray,
        mesh_y: np.ndarray,
        ground_dem: np.ndarray,
        strata_surfaces: List[np.ndarray],
        strata_names: List[str],
        water_table_rl: np.ndarray,
        p_start: Tuple[float, float],
        p_end: Tuple[float, float],
        filename: str = "geotechnical_cross_section.png",
        num_pts: int = 250
    ) -> Path:
        """
        Draws a geotechnical stratigraphic cross-section profile along transect A-A'.
        """
        from scipy.interpolate import RegularGridInterpolator
        
        y_vec = mesh_y[:, 0]
        x_vec = mesh_x[0, :]
        
        # Build transect coordinate line
        x_line = np.linspace(p_start[0], p_end[0], num_pts)
        y_line = np.linspace(p_start[1], p_end[1], num_pts)
        dists = np.sqrt((x_line - p_start[0])**2 + (y_line - p_start[1])**2)
        
        eval_coords = np.column_stack([y_line, x_line])
        
        # Sample ground elevation
        interp_dem = RegularGridInterpolator((y_vec, x_vec), ground_dem, bounds_error=False, fill_value=np.nan)
        z_ground = interp_dem(eval_coords)
        
        # Sample strata bottom elevations
        z_strata = []
        for s in strata_surfaces:
            fn = RegularGridInterpolator((y_vec, x_vec), s, bounds_error=False, fill_value=np.nan)
            z_strata.append(fn(eval_coords))
            
        # Sample water table
        interp_wt = RegularGridInterpolator((y_vec, x_vec), water_table_rl, bounds_error=False, fill_value=np.nan)
        z_wt = interp_wt(eval_coords)
        
        fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
        
        # Plot filled strata between successive interfaces
        ceiling = z_ground
        colors = ["#D7CCC8", "#8D6E63", "#FFCC80", "#B0BEC5", "#546E7A"]
        
        for k, (z_floor, name) in enumerate(zip(z_strata, strata_names)):
            col = colors[k % len(colors)]
            ax.fill_between(dists, z_floor, ceiling, color=col, alpha=0.85, label=name)
            ceiling = z_floor
            
        # Ground surface outline
        ax.plot(dists, z_ground, color="black", linewidth=2.0, label="Ground Surface (DEM)")
        # Water table line
        ax.plot(dists, z_wt, color="#0288D1", linestyle="--", linewidth=1.8, label="Groundwater Table")
        
        ax.set_title(f"Subsurface Geological Cross-Section Transect A-A' ({dists[-1]:.0f} m Length)", fontsize=13, weight="bold", pad=12)
        ax.set_xlabel("Distance along Transect (m)", fontsize=11)
        ax.set_ylabel("Reduced Level R.L. (m)", fontsize=11)
        ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, borderaxespad=0, frameon=True)
        ax.grid(True, linestyle=":", alpha=0.6)
        
        plt.tight_layout()
        out_path = self.output_dir / filename
        plt.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def build_interactive_3d_plotly(
        self,
        mesh_x: np.ndarray,
        mesh_y: np.ndarray,
        ground_dem: np.ndarray,
        strata_surfaces: List[np.ndarray],
        strata_names: List[str],
        borehole_df: pd.DataFrame,
        filename: str = "interactive_3d_strata.html",
        downsample_factor: int = 4
    ) -> Path:
        """
        Creates an interactive 3D multi-layered subsurface geological model with Plotly.
        Allows rotating, zooming, and toggling visibility of ground surface, strata interfaces, and boreholes.
        """
        # Downsample for smooth browser rendering
        step = max(1, downsample_factor)
        ds_x = mesh_x[::step, ::step]
        ds_y = mesh_y[::step, ::step]
        ds_dem = ground_dem[::step, ::step]
        
        fig = go.Figure()
        
        # 1. Ground Surface (DEM)
        fig.add_trace(go.Surface(
            x=ds_x,
            y=ds_y,
            z=ds_dem,
            name="Ground Surface (DEM)",
            colorscale="Earth",
            opacity=0.85,
            showscale=False
        ))
        
        # 2. Subsurface Strata Surfaces
        surface_colorscales = ["YlOrBr", "Blues", "Tealgrn", "Greys"]
        for k, (s_grid, name) in enumerate(zip(strata_surfaces, strata_names)):
            ds_s = s_grid[::step, ::step]
            cs = surface_colorscales[k % len(surface_colorscales)]
            fig.add_trace(go.Surface(
                x=ds_x,
                y=ds_y,
                z=ds_s,
                name=f"Base: {name}",
                colorscale=cs,
                opacity=0.75,
                showscale=False,
                visible=True
            ))
            
        # 3. 3D Borehole Cylinders / Lines
        for _, bh in borehole_df.iterrows():
            bx = bh["Easting_m"]
            by = bh["Northing_m"]
            top_z = bh["Surface_RL_m"]
            bot_z = bh["Termination_RL_m"]
            
            fig.add_trace(go.Scatter3d(
                x=[bx, bx],
                y=[by, by],
                z=[top_z, bot_z],
                mode="lines+markers",
                line=dict(color="black", width=7),
                marker=dict(size=4, color="red"),
                name=f"{bh['Borehole_ID']} (Depth: {bh['Max_Drill_Depth_m']}m)",
                hoverinfo="text",
                hovertext=f"{bh['Borehole_ID']}<br>Surface: {top_z:.1f}m R.L.<br>Bedrock: {bot_z:.1f}m R.L."
            ))
            
        # Layout tuning
        fig.update_layout(
            title="Interactive 3D Subsurface Strata & Geotechnical Borehole Model",
            scene=dict(
                xaxis_title="Easting (m)",
                yaxis_title="Northing (m)",
                zaxis_title="Elevation R.L. (m)",
                aspectratio=dict(x=1, y=1, z=0.45)
            ),
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        out_path = self.output_dir / filename
        fig.write_html(str(out_path))
        return out_path

    def generate_markov_entropy_figure(
        self,
        markov_results: Dict,
        filename: str = "coupled_markov_entropy_profile.png"
    ) -> Path:
        """
        Visualizes Coupled Markov Chain stochastic realizations and Shannon Information Entropy map.
        Shows simulated 2D geological cross-sections and spatial uncertainty across un-drilled zones.
        """
        realizations = markov_results.get("realizations", [])
        entropy = markov_results.get("entropy", None)
        cond_cols = markov_results.get("conditioning_cols", [])
        strata_names = markov_results.get("strata_names", [])
        num_states = len(strata_names)

        fig, axes = plt.subplots(3, 1, figsize=(14, 12), dpi=150)

        # Discrete colormap for strata
        cmap_strata = plt.get_cmap("tab10", num_states)

        # Panel 1: Stochastic Realization 1
        ax1 = axes[0]
        if len(realizations) > 0:
            im1 = ax1.imshow(realizations[0], cmap=cmap_strata, aspect="auto", vmin=-0.5, vmax=num_states - 0.5)
            for c in cond_cols:
                ax1.axvline(c, color="black", linestyle="--", linewidth=1.2, alpha=0.7)
            cbar1 = plt.colorbar(im1, ax=ax1, ticks=range(num_states), label="Stratum Layer")
            cbar1.ax.set_yticklabels(strata_names, fontsize=8)
        ax1.set_title("Coupled Markov Chain: Stochastic Realization #1 (Conditioned Cross-Section)", fontsize=11, weight="bold")
        ax1.set_ylabel("Depth Cells", fontsize=10)

        # Panel 2: Stochastic Realization 2
        ax2 = axes[1]
        if len(realizations) > 1:
            im2 = ax2.imshow(realizations[1], cmap=cmap_strata, aspect="auto", vmin=-0.5, vmax=num_states - 0.5)
            for c in cond_cols:
                ax2.axvline(c, color="black", linestyle="--", linewidth=1.2, alpha=0.7)
            cbar2 = plt.colorbar(im2, ax=ax2, ticks=range(num_states), label="Stratum Layer")
            cbar2.ax.set_yticklabels(strata_names, fontsize=8)
        ax2.set_title("Coupled Markov Chain: Stochastic Realization #2 (Alternative Profile)", fontsize=11, weight="bold")
        ax2.set_ylabel("Depth Cells", fontsize=10)

        # Panel 3: Shannon Information Entropy (Uncertainty Map)
        ax3 = axes[2]
        if entropy is not None:
            im3 = ax3.imshow(entropy, cmap="inferno", aspect="auto")
            for c in cond_cols:
                ax3.axvline(c, color="cyan", linestyle="-", linewidth=1.5, alpha=0.9, label="Conditioning Borehole" if c == cond_cols[0] else "")
            cbar3 = plt.colorbar(im3, ax=ax3, label="Information Entropy (bits)")
            ax3.legend(loc="upper right", framealpha=0.8)
        ax3.set_title("Lithological Information Entropy Map $H(x, z) = -\\sum p_i \\log_2(p_i)$ [Spatial Uncertainty]", fontsize=11, weight="bold")
        ax3.set_xlabel("Horizontal Profile Distance (Grid Columns)", fontsize=10)
        ax3.set_ylabel("Depth Cells", fontsize=10)

        plt.tight_layout()
        out_path = self.output_dir / filename
        plt.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return out_path

