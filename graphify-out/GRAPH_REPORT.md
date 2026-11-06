# Graph Report - Dem_Btech  (2026-11-06)

## Corpus Check
- Corpus is ~37,869 words - fits in a single context window. You may not need a graph.

## Summary
- 495 nodes · 1158 edges · 30 communities (17 shown, 13 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 147 edges (avg confidence: 0.87)
- Token cost: 1,250 input · 820 output

## Community Hubs (Navigation)
- CLI Pipeline & Core Runner
- QGIS Desktop Loader & Integration
- Spatial Data Processing & Exporter
- Coupled Markov Chain 2D Profile Modeling
- Borehole Data Normalization & Processing
- Automated Academic Literature Scraper
- Unit & Integration Test Suite
- Indian Borehole Studies GIS Map
- Geotechnical PDF Extraction & Parsing
- Indian Subsurface Geological Synthesizer
- Geological Provinces & Geotech Calibration
- Interactive 3D WebGL Visualization
- Vidarbha Geotechnical Literature Ingestion
- 4D Digital Twin & Voxel Multi-Physics
- Open Public Datasets Ingestion
- Howrah Shalimar Field Investigation
- Spatial Random Field Terrain Synthesizer
- Benchmark Verification Suite
- PDF Borehole Tabular Extractor
- Markov Uncertainty & Entropy Mapping
- Coupled Markov Tunnel Alignments
- Site Investigation & Sampling Standards
- IS-Code Bearing Capacity & Settlement
- Stratigraphic Continuity & Pinch-outs
- Geospatial GIS Ecosystem Reference
- ECC Multi-Harness Architecture
- Model Context Protocol Tool Ecosystem
- Indian Landmass Subsurface Synthesis

## God Nodes (most connected - your core abstractions)
1. `run_generative_pipeline()` - 34 edges
2. `DEMHandler` - 31 edges
3. `IndianSubsurfaceSynthesizer` - 27 edges
4. `GeotechEngine` - 26 edges
5. `run_subsurface_pipeline()` - 25 edges
6. `BoreholeProcessor` - 25 edges
7. `IndianGeologicalProvince` - 24 edges
8. `SubsurfaceSpatialDatabase` - 24 edges
9. `CoupledMarkovModel` - 23 edges
10. `SpatialInterpolator` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Coupled Markov Chain 2D Profile Simulation` --semantically_similar_to--> `Coupled Markov Chain Simulation Workflow`  [INFERRED] [semantically similar]
  README.md → data/raw/CoupledMarkov/README.md
- `run_generative_pipeline()` --uses--> `IndianGeologicalProvince`  [INFERRED]
  run_pipeline.py → src/generative_subsurface.py
- `test_auto_detect_province()` --uses--> `IndianGeologicalProvince`  [INFERRED]
  tests/test_generative_model.py → src/generative_subsurface.py
- `test_auto_detect_province_out_of_bounds()` --uses--> `IndianGeologicalProvince`  [INFERRED]
  tests/test_generative_model.py → src/generative_subsurface.py
- `test_calibrated_synthesis_applies_parameters()` --uses--> `IndianGeologicalProvince`  [INFERRED]
  tests/test_generative_model.py → src/generative_subsurface.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **IS-Code Geotechnical Design Chain** — readme_is2131_spt_corrections, readme_is6403_bearing_capacity, readme_settlement_limiting_criterion [INFERRED 0.95]
- **Stochastic Stratigraphy & Uncertainty Modeling** — readme_coupled_markov_chains, readme_shannon_entropy_uncertainty, data_raw_coupledmarkov_readme_entropy_mapping [INFERRED 0.95]

## Communities (30 total, 13 thin omitted)

### Community 0 - "CLI Pipeline & Core Runner"
Cohesion: 0.06
Nodes (15): run_howrah_geotechnical_engine(), run_generative_pipeline(), run_subsurface_pipeline(), GeotechConfig, GISExporter, GeotechEngine, SpatialInterpolator, SubsurfaceVisualizer (+7 more)

### Community 1 - "QGIS Desktop Loader & Integration"
Cohesion: 0.07
Nodes (12): BoreholeProcessor, DEMHandler, sample_processor(), dem_instance(), test_dem_sampling_boundary_clip(), test_dem_sampling_center(), test_bangalore_literature_pipeline(), test_coupled_markov_public_pipeline() (+4 more)

### Community 2 - "Spatial Data Processing & Exporter"
Cohesion: 0.08
Nodes (6): SubsurfaceSpatialDatabase, spatial_db(), test_spatial_database_init(), test_spatial_database_queries(), test_spatial_database_seeding(), test_spatial_geodataframe_export()

### Community 3 - "Coupled Markov Chain 2D Profile Modeling"
Cohesion: 0.10
Nodes (5): CoupledMarkovModel, test_cmc_top_row_horizontal_coupling(), test_coupled_markov_2d_profile_conditioning(), test_coupled_markov_directional_coupling(), test_coupled_markov_information_entropy()

### Community 4 - "Borehole Data Normalization & Processing"
Cohesion: 0.09
Nodes (7): SubsurfaceDigitalTwinEngine, TelemetrySensor, sample_twin_engine(), test_twin_dynamic_bearing_capacity(), test_twin_telemetry_ingestion_and_water_table(), test_twin_volumetric_voxels_generation(), test_twin_vtk_export()

### Community 5 - "Automated Academic Literature Scraper"
Cohesion: 0.12
Nodes (6): BoreholeLiteratureScraper, ScrapedStudyMetadata, test_auto_harvest_and_ingest(), test_borehole_synthesis(), test_column_normalization(), test_scraper()

### Community 6 - "Unit & Integration Test Suite"
Cohesion: 0.10
Nodes (10): test_calibrated_synthesis_applies_parameters(), test_cli_partial_coordinates_raises_error(), test_coupled_markov_discretized_persistence(), test_coupled_markov_row_normalization(), test_coupled_markov_sequence_fitting_and_simulation(), test_gis_exporter_crs_object(), test_markov_transect_selection_spans_entire_site(), test_province_registry_completeness() (+2 more)

### Community 7 - "Indian Borehole Studies GIS Map"
Cohesion: 0.15
Nodes (5): BoreholeStudy, IndianBoreholeMapGenerator, test_map_export_html(), test_map_generator_dataframe(), test_map_generator_folium_build()

### Community 8 - "Geotechnical PDF Extraction & Parsing"
Cohesion: 0.18
Nodes (4): classify_soil_is1498(), generate_bangalore_literature_dataset(), process_vidarbha_mendeley_dataset(), parse_howrah_pdf()

### Community 9 - "Indian Subsurface Geological Synthesizer"
Cohesion: 0.13
Nodes (5): IndianSubsurfaceSynthesizer, test_auto_detect_province(), test_auto_detect_province_out_of_bounds(), test_simulate_cmc_benchmark(), test_utm_epsg_calculation()

### Community 10 - "Geological Provinces & Geotech Calibration"
Cohesion: 0.20
Nodes (4): GeotechnicalCalibrator, IndianGeologicalProvince, ProvinceMetadata, StratumProfile

### Community 12 - "Vidarbha Geotechnical Literature Ingestion"
Cohesion: 0.18
Nodes (4): test_extreme_dense_boreholes_100(), test_spt_n_non_refusal_high_strength_stratum(), test_synthesize_boreholes_schema_and_physics(), get_synthesized_data()

### Community 14 - "Open Public Datasets Ingestion"
Cohesion: 0.23
Nodes (4): ingest_coupled_markov_public_dataset(), ingest_rotterdam_public_dataset(), test_borehole_processing_layers(), test_borehole_summary()

### Community 16 - "Spatial Random Field Terrain Synthesizer"
Cohesion: 0.27
Nodes (3): SpatialFieldSynthesizer, test_spatial_field_generator(), test_synthesize_terrain_dem_elevation_bounds()

### Community 21 - "Markov Uncertainty & Entropy Mapping"
Cohesion: 0.40
Nodes (5): Coupled Markov Chain Simulation Workflow, Cell-wise Spatial Entropy Mapping, Vertical & Horizontal Transition Probability Matrices, Coupled Markov Chain 2D Profile Simulation, Shannon Information Entropy Geological Uncertainty

### Community 23 - "Site Investigation & Sampling Standards"
Cohesion: 0.67
Nodes (3): Shalimar Howrah Soil Investigation, IS:2132 Undisturbed Tube Sampling Procedure, Reduced Level (R.L.) Normalization

### Community 24 - "IS-Code Bearing Capacity & Settlement"
Cohesion: 0.67
Nodes (3): IS:2131 Standard Penetration Test Corrections, IS:6403-1981 Shallow Foundation Bearing Capacity, Bowles/Teng Settlement Limiting Criterion

## Knowledge Gaps
- **13 isolated node(s):** `Reduced Level (R.L.) Normalization`, `IS:2131 Standard Penetration Test Corrections`, `Bowles/Teng Settlement Limiting Criterion`, `Stratigraphic Monotonicity & Pinch-Out Constraints`, `AI Generative Subsurface for Indian Landmass` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 224 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SubsurfaceSpatialDatabase` connect `Spatial Data Processing & Exporter` to `Subsurface Spatial Database Engine (DuckDB)`, `Interactive 3D WebGL Visualization`, `Automated Academic Literature Scraper`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `run_generative_pipeline()` (e.g. with `.get_layer_points()` and `.get_grid_shape()`) actually correct?**
  _`run_generative_pipeline()` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Reduced Level (R.L.) Normalization`, `IS:2131 Standard Penetration Test Corrections`, `Bowles/Teng Settlement Limiting Criterion` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CLI Pipeline & Core Runner` be split into smaller, more focused modules?**
  _Cohesion score 0.055176890619928594 - nodes in this community are weakly interconnected._
- **Why does `SubsurfaceDigitalTwinEngine` connect `Borehole Data Normalization & Processing` to `QGIS Desktop Loader & Integration`, `Interactive 3D WebGL Visualization`, `4D Digital Twin & Voxel Multi-Physics`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `DEMHandler` (e.g. with `BoreholeProcessor` and `sample_processor()`) actually correct?**
  _`DEMHandler` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `QGIS Desktop Loader & Integration` be split into smaller, more focused modules?**
  _Cohesion score 0.06610169491525424 - nodes in this community are weakly interconnected._