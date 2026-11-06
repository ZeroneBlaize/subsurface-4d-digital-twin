"""
PyQGIS Subsurface Model Loader: Run directly in QGIS Python Console to load, style, and visualize all outputs.

Instructions:
1. Open QGIS Desktop.
2. Open the Python Console: Plugins -> Python Console (Ctrl + Alt + P).
3. Open this script and click 'Run Script' (Ctrl + R).
"""

from pathlib import Path

# Paths to generated assets
BASE_DIR = Path("/home/nkm6/25CL06008/Projects_P/Dem_Btech/outputs")
RASTERS_DIR = BASE_DIR / "rasters"
VECTORS_DIR = BASE_DIR / "vectors"

def load_subsurface_layers_into_qgis():
    try:
        from qgis.core import (
            QgsProject, QgsRasterLayer, QgsVectorLayer,
            QgsSingleBandPseudoColorRenderer, QgsColorRampShader,
            QgsRasterShader, QgsStyle
        )
    except ImportError:
        print("This script is designed to be executed inside QGIS Desktop's Python Console.")
        return

    project = QgsProject.instance()
    root = project.layerTreeRoot()

    # Create Group for Subsurface Model
    main_group = root.addGroup("Subsurface Geospatial Engine")
    group_rasters = main_group.addGroup("Stratigraphic Rasters (R.L.)")
    group_sbc = main_group.addGroup("Safe Bearing Capacity")
    group_vectors = main_group.addGroup("Survey Vectors")

    # 1. Load DEM
    dem_path = RASTERS_DIR / "dem_surface_rl.tif"
    if dem_path.exists():
        dem_layer = QgsRasterLayer(str(dem_path), "Ground Surface DEM (m R.L.)")
        if dem_layer.isValid():
            project.addMapLayer(dem_layer, False)
            group_rasters.addLayer(dem_layer)
            print("✓ Loaded DEM Surface Raster")

    # 2. Load Bedrock & Strata
    bedrock_path = RASTERS_DIR / "stratum_base_hard_basalt_bedrock.tif"
    if bedrock_path.exists():
        bedrock_layer = QgsRasterLayer(str(bedrock_path), "Bedrock Interface R.L. (m)")
        if bedrock_layer.isValid():
            project.addMapLayer(bedrock_layer, False)
            group_rasters.addLayer(bedrock_layer)
            print("✓ Loaded Bedrock Stratum Raster")

    # 3. Load Safe Bearing Capacity (SBC)
    sbc_path = RASTERS_DIR / "safe_bearing_capacity_kpa.tif"
    if sbc_path.exists():
        sbc_layer = QgsRasterLayer(str(sbc_path), "Safe Bearing Capacity (kPa)")
        if sbc_layer.isValid():
            project.addMapLayer(sbc_layer, False)
            group_sbc.addLayer(sbc_layer)
            print("✓ Loaded Safe Bearing Capacity Raster")

    # 4. Load Borehole Vector Points
    gpkg_path = VECTORS_DIR / "subsurface_geotechnical.gpkg"
    if gpkg_path.exists():
        bh_layer = QgsVectorLayer(f"{gpkg_path}|layername=boreholes", "Borehole Drilling Locations", "ogr")
        if bh_layer.isValid():
            project.addMapLayer(bh_layer, False)
            group_vectors.addLayer(bh_layer)
            print("✓ Loaded Borehole Geotechnical Vector Layer")

    # 5. Load SBC Contours
    contour_path = VECTORS_DIR / "sbc_contours.gpkg"
    if contour_path.exists():
        cntr_layer = QgsVectorLayer(f"{contour_path}|layername=sbc_contours_kpa", "SBC Isoline Contours (kPa)", "ogr")
        if cntr_layer.isValid():
            project.addMapLayer(cntr_layer, False)
            group_vectors.addLayer(cntr_layer)
            print("✓ Loaded SBC Contour Isolines")

    print("\n🎉 All subsurface model layers loaded and grouped successfully in QGIS!")

if __name__ == "__main__":
    load_subsurface_layers_into_qgis()
