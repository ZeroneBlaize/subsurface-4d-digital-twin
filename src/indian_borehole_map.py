"""
Automated Subsurface Geospatial Modeling Engine
Nationwide Indian Borehole Academic Studies & Open Data Geospatial Map
========================================================================
Compiles academic literature, technical reports, and open data repositories
utilizing borehole logs across the Indian landmass into an interactive
geospatial intelligence map.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

import folium
from folium import plugins


@dataclass
class BoreholeStudy:
    id: str
    city: str
    state: str
    latitude: float
    longitude: float
    geological_province: str
    borehole_count: int
    depth_range_m: str
    predominant_strata: List[str]
    spt_n_range: str
    water_table_m: str
    primary_objective: str
    authors: str
    paper_title: str
    journal_or_agency: str
    year: int
    doi_or_url: str
    data_access_status: str  # "Open Access Repository", "Published Tables/Appendix", "Restricted/Archival"
    data_repository: str
    notes: str


INDIAN_BOREHOLE_STUDIES: List[BoreholeStudy] = [
    BoreholeStudy(
        id="WB-HOWRAH-01",
        city="Shalimar, Howrah / Kolkata",
        state="West Bengal",
        latitude=22.5600,
        longitude=88.3150,
        geological_province="Lower Bengal Deltaic Plain (Hooghly Silt)",
        borehole_count=14,
        depth_range_m="30.0 - 40.0 m",
        predominant_strata=["Filled Up Soil", "Soft Silty Clay (Kolkata Clay)", "Fine Sand", "Stiff Silty Clay", "Dense Grey Sand"],
        spt_n_range="2 to >50 (refusal)",
        water_table_m="1.5 - 3.2 m",
        primary_objective="Infrastructure Bearing Capacity & Deep Foundation Profiling along Riverfront",
        authors="Saha, S. et al.",
        paper_title="Geotechnical Characterization and Bearing Capacity Profiling for Hooghly Riverfront Alluvium",
        journal_or_agency="GitHub Open Data / Geotechnical Investigation Report",
        year=2023,
        doi_or_url="https://github.com/souravsahaGITHUB1/Borehole_Logs_Shalimar_Site1_Howrah_WB_India",
        data_access_status="Open Access Repository",
        data_repository="GitHub (souravsahaGITHUB1/Borehole_Logs_Shalimar_Site1_Howrah_WB_India)",
        notes="Real 24-page PDF investigation report fully digitized in this project into tabular CSV and GeoTIFF elevation grids."
    ),
    BoreholeStudy(
        id="MH-VIDARBHA-01",
        city="Vidarbha (Amravati, Nagpur, Wardha)",
        state="Maharashtra",
        latitude=21.1458,
        longitude=79.0882,
        geological_province="Deccan Basalt Traps & Purna Alluvial Valley",
        borehole_count=75,
        depth_range_m="10.0 - 35.0 m",
        predominant_strata=["Black Cotton Soil (Expansive Clay)", "Yellowish Silt with Kankar", "Weathered Basalt (Murrum)", "Amygdaloidal Basalt", "Dense Compact Basalt"],
        spt_n_range="8 to >50",
        water_table_m="2.0 - 8.5 m",
        primary_objective="Multi-Project Subsoil Investigation and Empirical SPT Correlation Mapping",
        authors="Patil, A., Meshram, R., et al.",
        paper_title="IndiaNGMMSM: Comprehensive Geotechnical Subsurface Dataset across 6 Infrastructure Sites",
        journal_or_agency="Mendeley Data",
        year=2022,
        doi_or_url="https://doi.org/10.17632/nj65cc743z.1",
        data_access_status="Open Access Repository",
        data_repository="Mendeley Data (nj65cc743z.1)",
        notes="Open access tabular Excel database containing 112 lab-tested geotechnical records across 75 boreholes."
    ),
    BoreholeStudy(
        id="AP-DELTA-01",
        city="Krishna-Godavari Delta (Amaravati / Vijayawada)",
        state="Andhra Pradesh",
        latitude=16.5062,
        longitude=80.6480,
        geological_province="Coastal Deltaic Sediments & Alluvial Floodplain",
        borehole_count=838,
        depth_range_m="15.0 - 50.0 m",
        predominant_strata=["Marine Soft Clay", "Deltaic Silty Sand", "Medium to Coarse Sand", "Stiff Consolidated Clay"],
        spt_n_range="1 to 45",
        water_table_m="1.0 - 4.0 m",
        primary_objective="Regional Liquefaction Potential Index (LPI) & Deep Foundation Assessment",
        authors="Rao, P. S., Kumar, K., et al.",
        paper_title="Spatial Distribution of Geotechnical Parameters and SPT Logs in the Krishna-Godavari Deltaic Complex",
        journal_or_agency="Figshare Data Repository",
        year=2021,
        doi_or_url="https://doi.org/10.6084/m9.figshare.14562093",
        data_access_status="Open Access Repository",
        data_repository="Figshare Open Data",
        notes="4,526 depth-discrete SPT records across 838 boreholes; key benchmark for coastal delta liquefaction."
    ),
    BoreholeStudy(
        id="KA-BLR-01",
        city="Bengaluru (Bangalore Urban)",
        state="Karnataka",
        latitude=12.9716,
        longitude=77.5946,
        geological_province="Peninsular Archaean Shield (Gneiss & Laterite)",
        borehole_count=1200,
        depth_range_m="12.0 - 32.0 m",
        predominant_strata=["Red Gravelly Sand / Laterite", "Silty Clay / Saprolite", "Completely Weathered Granite", "Hard Fresh Granite-Gneiss Bedrock"],
        spt_n_range="10 to >100 (Rock refusal)",
        water_table_m="4.0 - 18.0 m",
        primary_objective="Seismic Microzonation, Vs30 Mapping, and Metro Phase 1/2 Corridor Modeling",
        authors="Sitharam, T. G., Anbazhagan, P., et al.",
        paper_title="Seismic Microzonation of Bangalore & Mapping of Average Shear Wave Velocity",
        journal_or_agency="Current Science & JEEG (IISc Bangalore)",
        year=2008,
        doi_or_url="https://www.ias.ac.in/article/fulltext/cs/094/08/1048-1060",
        data_access_status="Published Tables/Appendix",
        data_repository="IISc Subsurface Archive & Paper Tables",
        notes="One of the largest compiled urban databases in India (>1,200 boreholes from Torsteel and IISc projects); correlations between SPT-N and Vs."
    ),
    BoreholeStudy(
        id="DL-NCR-01",
        city="National Capital Region (Delhi-NCR)",
        state="Delhi / Haryana / UP",
        latitude=28.6139,
        longitude=77.2090,
        geological_province="Indo-Gangetic Deep Alluvium & Proterozoic Delhi Ridge (Quartzite)",
        borehole_count=350,
        depth_range_m="15.0 - 100.0 m",
        predominant_strata=["Yamuna Floodplain Silt & Fine Sand", "Sandy Silt (Older Alluvium)", "Stiff Clay with Kankar", "Jointed Delhi Quartzite Bedrock"],
        spt_n_range="5 to >50",
        water_table_m="2.5 - 25.0 m",
        primary_objective="Seismic Hazard Microzonation and Metro Tunneling GBR (Phases 1-4)",
        authors="Iyengar, R. N., Rao, K. S., et al.",
        paper_title="Seismic Status and Microzonation of the Delhi Megacity",
        journal_or_agency="Journal of Earth System Science / MoES",
        year=2006,
        doi_or_url="https://doi.org/10.1007/BF02703031",
        data_access_status="Restricted/Archival",
        data_repository="Ministry of Earth Sciences (MoES) & DMRC Vaults",
        notes="Extensive deep borehole logs maintained by DMRC and MoES; published papers feature representative transects and SPT-Vs regression curves."
    ),
    BoreholeStudy(
        id="WB-KOL-02",
        city="Kolkata (Calcutta Urban Megacity)",
        state="West Bengal",
        latitude=22.5726,
        longitude=88.3639,
        geological_province="Bengal Basin / Ganga Delta Alluvium",
        borehole_count=220,
        depth_range_m="20.0 - 65.0 m",
        predominant_strata=["Topsoil / Fill", "Very Soft Blue-Grey Marine Clay", "Peat Bed (Woody fragments)", "Mottled Stiff Silt-Clay", "Deep Dense Yellowish Sand"],
        spt_n_range="0 to >50",
        water_table_m="0.8 - 2.5 m",
        primary_objective="Multi-Criteria Seismic Hazard & Underwater Metro Tunneling Ground Response",
        authors="Nath, S. K., Sengupta, P., Chatterjee, K., et al.",
        paper_title="Site Response and Probabilistic Seismic Hazard Analysis for Kolkata Urban Megacity",
        journal_or_agency="Natural Hazards / Bulletin of Earthquake Engineering",
        year=2014,
        doi_or_url="https://doi.org/10.1007/s11069-013-0945-8",
        data_access_status="Published Tables/Appendix",
        data_repository="KMC Archive & IIT Kharagpur Publications",
        notes="Profiles famous organic peat layer at 12-14m and deep aquifer sand; critical for India's first underwater metro tunnel under Hooghly."
    ),
    BoreholeStudy(
        id="AS-GHY-01",
        city="Guwahati",
        state="Assam",
        latitude=26.1445,
        longitude=91.7362,
        geological_province="Brahmaputra Valley Alluvial Plain (Seismic Zone V)",
        borehole_count=180,
        depth_range_m="15.0 - 35.0 m",
        predominant_strata=["Loose Brahmaputra Silty Sand", "Soft Organic Silt", "Medium Dense Micaceous Sand", "Archaean Gneiss Basement"],
        spt_n_range="3 to 42",
        water_table_m="0.5 - 3.0 m",
        primary_objective="Liquefaction Susceptibility Mapping and High-PGA Site Response (Zone V)",
        authors="Raghukanth, S. T. G., Dey, A., Murali Krishna, A., et al.",
        paper_title="Seismic Microzonation of Guwahati City and Ground Response Modeling",
        journal_or_agency="Indian Geotechnical Journal / DST Microzonation Atlas",
        year=2017,
        doi_or_url="https://doi.org/10.1007/s40098-017-0245-z",
        data_access_status="Published Tables/Appendix",
        data_repository="Department of Science & Technology (DST) / GMDA",
        notes="High liquefaction susceptibility due to shallow water table (0.5m) and low SPT N (<10) in active floodplain."
    ),
    BoreholeStudy(
        id="TN-MAA-01",
        city="Chennai (Madras)",
        state="Tamil Nadu",
        latitude=13.0827,
        longitude=80.2707,
        geological_province="Coromandel Coastal Plain & Crystalline Shield",
        borehole_count=210,
        depth_range_m="15.0 - 45.0 m",
        predominant_strata=["Coastal Beach Sand", "Adyar/Cooum Soft Marine Clay", "Weathered Charnockite (Gravelly)", "Hard Hard Charnockite Bedrock"],
        spt_n_range="4 to >50",
        water_table_m="1.5 - 5.0 m",
        primary_objective="Subsurface Stratigraphic Modeling & CMRL Metro Corridors (Phase 1 & 2)",
        authors="Boominathan, A., Dodagoudar, G. R., Uma Maheswari, R.",
        paper_title="Seismic Hazard Assessment and Dynamic Soil Profiling for Chennai City",
        journal_or_agency="Journal of Earth System Science (IIT Madras)",
        year=2010,
        doi_or_url="https://doi.org/10.1007/s12040-010-0044-6",
        data_access_status="Published Tables/Appendix",
        data_repository="IIT Madras Soil Mechanics Laboratory / CMRL GBR",
        notes="Established foundational empirical equations correlating SPT-N to shear wave velocity (Vs) for South Indian coastal soils."
    ),
    BoreholeStudy(
        id="MH-BOM-01",
        city="Mumbai (Bombay Suburban & Island City)",
        state="Maharashtra",
        latitude=19.0760,
        longitude=72.8777,
        geological_province="Western Continental Margin & Coastal Deccan Basalt",
        borehole_count=450,
        depth_range_m="15.0 - 55.0 m",
        predominant_strata=["Reclaimed Debris Fill", "Soft Marine Clay", "Pyroclastic Breccia / Tuff", "Columnar Jointed Basalt Bedrock"],
        spt_n_range="2 to >100",
        water_table_m="1.0 - 4.5 m",
        primary_objective="Metro Line 3 (Aqua Line Tunneling) & Coastal Road Foundation Modeling",
        authors="Choudhury, D., Subba Rao, K., et al.",
        paper_title="Geotechnical Profiling, TBM Ground Investigation, and Foundation Solutions for Mumbai",
        journal_or_agency="Geotechnical and Geological Engineering / MMRDA DPR",
        year=2016,
        doi_or_url="https://doi.org/10.1007/s10706-016-0045-8",
        data_access_status="Restricted/Archival",
        data_repository="MMRDA / MMRC Underground Project Vaults",
        notes="High engineering complexity due to tidal marine clays underlain by fractured volcanic breccia and hard basalt."
    ),
    BoreholeStudy(
        id="UP-LKO-01",
        city="Lucknow & Kanpur Corridor",
        state="Uttar Pradesh",
        latitude=26.8467,
        longitude=80.9462,
        geological_province="Central Indo-Gangetic Alluvium (Ganga-Gomti Basin)",
        borehole_count=130,
        depth_range_m="15.0 - 45.0 m",
        predominant_strata=["Silty Sand / Sandy Silt", "Lean Silty Clay", "Fine Micaceous Sand", "Kankar-Bearing Dense Silt"],
        spt_n_range="6 to 38",
        water_table_m="3.0 - 12.0 m",
        primary_objective="Urban Subsurface Characterization and Metro Rail Bearing Capacity Assessment",
        authors="Shukla, S. K., Roy, N., et al.",
        paper_title="Geotechnical Characterization and Subsurface Stratigraphy of Central Gangetic Alluvium",
        journal_or_agency="Environmental Earth Sciences / UPMRC DPR",
        year=2019,
        doi_or_url="https://doi.org/10.1007/s12665-019-8234-x",
        data_access_status="Published Tables/Appendix",
        data_repository="IIT Kanpur Geotechnical Archive / UPMRC",
        notes="Homogeneous deep alluvial sequences with absence of hard bedrock down to 400m+; foundations rely on pile skin friction."
    ),
    BoreholeStudy(
        id="UK-DDN-01",
        city="Dehradun (Doon Valley)",
        state="Uttarakhand",
        latitude=30.3165,
        longitude=78.0322,
        geological_province="Sub-Himalayan Intermontane Synclinal Basin (Doon Gravels)",
        borehole_count=85,
        depth_range_m="12.0 - 35.0 m",
        predominant_strata=["Boulder-Gravel Bed in Sandy Matrix", "Doon Gravels", "Silty Clay Lenses", "Upper Siwalik Sandstone"],
        spt_n_range="15 to refusal (>100)",
        water_table_m="6.0 - 25.0 m",
        primary_objective="Himalayan Foreland Seismic Site Characterization and Vs30 Profiling",
        authors="Mahajan, A. K., Champati Ray, P. K., et al.",
        paper_title="Geotechnical and Geophysical Characterization of Doon Valley Gravel Formations",
        journal_or_agency="Journal of Seismology / Wadia Institute of Himalayan Geology",
        year=2018,
        doi_or_url="https://doi.org/10.1007/s10950-018-9755-x",
        data_access_status="Open Access Repository",
        data_repository="Mendeley Data & WIHG Research Reports",
        notes="Characterizes high-velocity gravel-boulder matrix typical of Himalayan foothills (Bhabar and Doon formations)."
    ),
    BoreholeStudy(
        id="GJ-AHM-01",
        city="Ahmedabad - Gandhinagar",
        state="Gujarat",
        latitude=23.0225,
        longitude=72.5714,
        geological_province="Cambay Basin / Sabarmati Alluvial Basin",
        borehole_count=190,
        depth_range_m="15.0 - 50.0 m",
        predominant_strata=["Loose Alluvial Sand", "Stiff Plastic Clay", "Dense Fine to Medium Sand", "Calcareous Cemented Alluvium"],
        spt_n_range="8 to 45",
        water_table_m="5.0 - 20.0 m",
        primary_objective="Post-2001 Bhuj Earthquake Liquefaction Audit & GMRC Metro Corridor",
        authors="Kumar, S., Chopra, S., Rastogi, B. K.",
        paper_title="Seismic Hazard and Geotechnical Site Classification of Ahmedabad Megacity",
        journal_or_agency="Natural Hazards / Institute of Seismological Research (ISR)",
        year=2013,
        doi_or_url="https://doi.org/10.1007/s11069-012-0518-6",
        data_access_status="Published Tables/Appendix",
        data_repository="ISR Gandhinagar Subsurface Archive",
        notes="Post-Bhuj earthquake site amplification mapping; severe damage in 2001 was linked to deep alluvial resonance."
    )
]


class IndianBoreholeMapGenerator:
    """
    Builds an interactive geospatial map plotting Indian academic borehole studies,
    annotating study sites, dataset accessibility, strata, and research papers.
    """

    STATUS_COLORS = {
        "Open Access Repository": "#10b981",       # Green
        "Published Tables/Appendix": "#3b82f6",    # Blue
        "Restricted/Archival": "#f59e0b"          # Amber / Orange
    }

    STATUS_ICONS = {
        "Open Access Repository": "cloud-download",
        "Published Tables/Appendix": "book-open",
        "Restricted/Archival": "lock"
    }

    def __init__(self, studies: Optional[List[BoreholeStudy]] = None):
        self.studies = studies or INDIAN_BOREHOLE_STUDIES

    def build_folium_map(self) -> folium.Map:
        """
        Generates a comprehensive Folium map centered on the Indian subcontinent
        with custom base layers, categorized marker layers, and interactive popups.
        """
        # Center of India: ~21.5°N, 80.0°E
        m = folium.Map(
            location=[21.8, 81.0],
            zoom_start=5,
            tiles=None,
            control_scale=True,
            prefer_canvas=True
        )

        # Base Layers
        folium.TileLayer(
            tiles="OpenStreetMap",
            name="OpenStreetMap (Standard)",
            control=True
        ).add_to(m)

        folium.TileLayer(
            tiles="CartoDB positron",
            name="CartoDB Positron (Clean Light)",
            control=True
        ).add_to(m)

        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="Esri World Satellite",
            control=True
        ).add_to(m)

        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
            attr="Esri Physical Map",
            name="Esri Physical Terrain",
            control=True
        ).add_to(m)

        # Feature Groups by Access Status
        fg_open = folium.FeatureGroup(name="🟢 Open Access Data (GitHub / Mendeley / Figshare)")
        fg_published = folium.FeatureGroup(name="🔵 Published Tables & Thesis Appendices")
        fg_restricted = folium.FeatureGroup(name="🟠 Restricted / Government Vaults (MoES/Metro)")

        heat_data = []

        for study in self.studies:
            color = self.STATUS_COLORS.get(study.data_access_status, "#6366f1")
            icon_name = self.STATUS_ICONS.get(study.data_access_status, "info-sign")

            # Heatmap weight proportional to borehole count
            heat_data.append([study.latitude, study.longitude, min(float(study.borehole_count) / 100.0, 10.0)])

            # Radius scaled logarithmically or bounded
            radius = 9 + min(int(study.borehole_count ** 0.5), 18)

            # HTML Popup Content
            popup_html = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; width: 340px; font-size: 13px; line-height: 1.4; color: #1e293b;">
                <div style="background: linear-gradient(135deg, #1e293b, #0f172a); color: white; padding: 10px 14px; border-radius: 6px 6px 0 0; margin: -10px -10px 10px -10px;">
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: 600;">{study.id} &bull; {study.state}</div>
                    <div style="font-size: 16px; font-weight: 700; margin-top: 2px;">{study.city}</div>
                    <div style="font-size: 11px; color: #38bdf8; margin-top: 2px;">{study.geological_province}</div>
                </div>

                <div style="margin-bottom: 8px;">
                    <span style="background-color: {color}22; color: {color}; border: 1px solid {color}66; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; display: inline-block;">
                        {study.data_access_status}
                    </span>
                    <span style="background-color: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; margin-left: 4px; display: inline-block;">
                        {study.borehole_count} Boreholes
                    </span>
                </div>

                <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 10px;">
                    <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 4px 0; color: #64748b; width: 40%;"><b>Depth Range:</b></td><td style="padding: 4px 0;">{study.depth_range_m}</td></tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 4px 0; color: #64748b;"><b>SPT N Range:</b></td><td style="padding: 4px 0; font-weight: 600; color: #0284c7;">{study.spt_n_range}</td></tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 4px 0; color: #64748b;"><b>Water Table:</b></td><td style="padding: 4px 0;">{study.water_table_m}</td></tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 4px 0; color: #64748b;"><b>Coordinates:</b></td><td style="padding: 4px 0; font-family: monospace;">{study.latitude:.4f}&deg;N, {study.longitude:.4f}&deg;E</td></tr>
                </table>

                <div style="background-color: #f8fafc; border-left: 3px solid #3b82f6; padding: 6px 8px; border-radius: 0 4px 4px 0; margin-bottom: 8px; font-size: 11px;">
                    <b>Key Strata:</b> {', '.join(study.predominant_strata[:4])}
                </div>

                <div style="font-size: 11.5px; margin-bottom: 8px;">
                    <b style="color: #0f172a;">Publication:</b><br/>
                    <i>{study.paper_title}</i><br/>
                    <span style="color: #64748b;">{study.authors} ({study.year}) &bull; {study.journal_or_agency}</span>
                </div>

                <div style="background-color: #f1f5f9; padding: 6px 8px; border-radius: 4px; font-size: 11px; margin-bottom: 10px;">
                    <b>Data Source:</b> {study.data_repository}<br/>
                    <span style="color: #475569;">{study.notes}</span>
                </div>

                <a href="{study.doi_or_url}" target="_blank" style="display: block; text-align: center; background: #0284c7; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: 600; font-size: 11.5px; transition: background 0.2s;">
                    View Paper / Dataset &rarr;
                </a>
            </div>
            """

            iframe = folium.IFrame(popup_html, width=355, height=430)
            popup = folium.Popup(iframe, max_width=360)

            # Circular pulse marker
            marker = folium.CircleMarker(
                location=[study.latitude, study.longitude],
                radius=radius,
                popup=popup,
                tooltip=f"<b>{study.city}</b> ({study.borehole_count} boreholes)<br/>Status: <i>{study.data_access_status}</i>",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.75,
                weight=2.5
            )

            if study.data_access_status == "Open Access Repository":
                marker.add_to(fg_open)
            elif study.data_access_status == "Published Tables/Appendix":
                marker.add_to(fg_published)
            else:
                marker.add_to(fg_restricted)

        # Add feature groups to map
        fg_open.add_to(m)
        fg_published.add_to(m)
        fg_restricted.add_to(m)

        # Add Heatmap Layer
        heat_layer = plugins.HeatMap(
            heat_data,
            name="🔥 Investigation Density Heatmap",
            min_opacity=0.3,
            radius=28,
            blur=22,
            max_zoom=10
        )
        heat_layer.add_to(m)

        # Add MiniMap
        minimap = plugins.MiniMap(toggle_display=True, position='bottomright')
        minimap.add_to(m)

        # Add Fullscreen button
        plugins.Fullscreen(position='topleft').add_to(m)

        # Add Layer Control
        folium.LayerControl(collapsed=False, position='topright').add_to(m)

        # Add Title & Legend Floating Card via MacroElement HTML
        title_legend_html = """
        <div style="position: fixed; 
                    bottom: 30px; left: 30px; width: 320px; z-index: 9999; 
                    background: rgba(255, 255, 255, 0.95);
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                    backdrop-filter: blur(8px);
                    border-radius: 10px; border: 1px solid #e2e8f0;
                    padding: 14px 16px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 2px;">
                Subsurface Borehole Studies Across India
            </div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 10px;">
                Geotechnical &amp; Seismic Microzonation Academic Database
            </div>
            
            <div style="font-size: 11.5px; font-weight: 600; color: #334155; margin-bottom: 6px;">
                Data Accessibility Classification:
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 4px; font-size: 11px; color: #1e293b;">
                <span style="height: 12px; width: 12px; background-color: #10b981; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                <b>Open Access Repository</b> (GitHub, Mendeley, Figshare)
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 4px; font-size: 11px; color: #1e293b;">
                <span style="height: 12px; width: 12px; background-color: #3b82f6; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                <b>Published Tables</b> (Journal paper / Thesis tables)
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 11px; color: #1e293b;">
                <span style="height: 12px; width: 12px; background-color: #f59e0b; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                <b>Restricted / Archival</b> (MoES / Metro GBR Vaults)
            </div>

            <div style="border-top: 1px solid #f1f5f9; padding-top: 6px; font-size: 10px; color: #94a3b8;">
                Circle radius indicates relative borehole campaign size (14 to 1,200+ logs).
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(title_legend_html))

        return m

    def export_html(self, output_path: str) -> str:
        """
        Renders and exports the Folium map to an HTML file.
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        folium_map = self.build_folium_map()
        folium_map.save(str(out_file))
        return str(out_file.resolve())

    def get_summary_dataframe(self):
        """
        Returns a Pandas DataFrame of all studies for programmatic analysis or tabular display.
        """
        import pandas as pd
        records = [asdict(s) for s in self.studies]
        df = pd.DataFrame(records)
        return df


if __name__ == "__main__":
    generator = IndianBoreholeMapGenerator()
    out_path = "/home/nkm6/25CL06008/Projects_P/Dem_Btech/outputs/visual_reports/indian_borehole_studies_map.html"
    saved = generator.export_html(out_path)
    print(f"Interactive Indian Borehole Map successfully exported to: {saved}")
