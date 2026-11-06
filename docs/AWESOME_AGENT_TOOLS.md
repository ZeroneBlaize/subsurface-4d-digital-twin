# Curated Ecosystem: Awesome Agent Repositories, ECC Multi-Harness & Geotechnical AI

## 1. Executive Summary & Status

This document catalogs the top curated agent, harness, and geospatial meta-repositories across GitHub, cross-referenced with the reinstated **ECC (Everything Claude Code / Agent Harness Performance Optimization System)**.

### Current System Status
| Component | Status | Location / Harness | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **Hermes Agent** | ❌ Completely Removed | Cleaned (`~/.hermes`, `/tools/hermes-agent`, `~/.local/bin/hermes`) | Purged per user directive |
| **ECC (Everything Claude Code)** | ✅ Installed (Full Profile) | `~/.claude/`, `~/.codex/`, `./.agents/` | 71 agents, 304+ skills, hooks runtime, SQLite state database |
| **Subsurface Digital Twin Engine** | ✅ Active & Running | `src/digital_twin_engine.py`, `ui/app.py` (Tab 8) | 3D Voxelization, IoT Piezometer Ingestion, Terzaghi Effective Stress, VTK Export |
| **Nationwide Borehole Database** | ✅ Active & Ingested | `src/indian_borehole_map.py`, `ui/app.py` (Tab 7) | 12 regional clusters (3,800+ boreholes), interactive Folium GIS map |
| **Streamlit Interactive UI** | ✅ Active (Port 8501) | `http://localhost:8501` (8 tabs, 6 dataset profiles) | Real-time multi-strata bearing capacity & digital twin dashboard |

---

## 2. Meta-Repositories & Curated Directories ("Awesome" Repos)

The following GitHub repositories curate leading AI agent frameworks, harness systems, and developer toolkits:

### A. AI Agent Frameworks & Architectures
1. **[e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents)**
   - *Description*: The industry-standard directory for autonomous AI agents, maintained by E2B (AI Agent Cloud & Sandboxed Execution).
   - *Key Categories*:
     - **Autonomous Coding Agents**: AutoGPT, SWE-agent, OpenDevin/OpenHands, Claude Code, Aider, Mentat.
     - **Multi-Agent Orchestration**: AutoGen, CrewAI, LangGraph, ChatDev, MetaGPT.
     - **Research & Scientific Agents**: GPT-Researcher, ChemCrow, PaperQA.
     - **Browser & Computer-Use Agents**: Browser-Use, OSWorld, UFO.

2. **[Wamphyre/awesome-ai-agents](https://github.com/Wamphyre/awesome-ai-agents)**
   - *Description*: Community-ranked repository of production-ready agents, agent memory systems, and evaluation benchmarks.

### B. Claude Code & Agent Harness Optimizations
1. **[affaan-m/ECC](https://github.com/affaan-m/ECC)** *(Reinstated in Current System)*
   - *Description*: Everything Claude Code — The comprehensive multi-harness operating system for agent performance optimization.
   - *Features*:
     - 71 specialized subagents (architect, code-reviewer, test-engineer, security-auditor, etc.).
     - 304 modular skills spanning machine learning, code generation, verification loops, and documentation governance.
     - Universal Multi-Harness Sync (`claude`, `codex`, `antigravity`, `cursor`, `zed`).
     - Automatic hook runtime with persistent state tracking in SQLite (`state.db`).

2. **[rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit)**
   - *Description*: Extensive toolkit containing curated prompts, custom slash commands, subagent definitions, and workflow scripts tailored for CLI-driven AI workflows.

3. **[subinium/awesome-claude-code](https://github.com/subinium/awesome-claude-code)** & **[jqueryscript/awesome-claude-code](https://github.com/jqueryscript/awesome-claude-code)**
   - *Description*: Curated lists focused on agentic team-based development, automated test verification loops, and cross-IDE integrations.

4. **[VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)**
   - *Description*: High-specialization subagent templates covering microservice refactoring, database migrations, and performance profiling.

### C. Model Context Protocol (MCP) Ecosystem
1. **[punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)**
   - *Description*: The definitive curated index of MCP servers conforming to Anthropic's open Model Context Protocol.
   - *High-Value Servers for Geotechnical & Data Science*:
     - **PostGIS / PostgreSQL MCP**: Direct spatial SQL querying (`ST_Intersects`, `ST_Buffer`, `ST_DWithin`).
     - **DuckDB / SQLite Spatial MCP**: In-memory spatial parquet and borehole log analysis without heavy database overhead.
     - **Filesystem / Cloud Storage (GCS/S3) MCP**: Streaming access to nationwide GIS geotiffs, LiDAR point clouds, and borehole CSVs.
     - **OpenRouter MCP**: Flagship multi-model delegation (`nvidia/nemotron-3-ultra`, `google/gemma-4-31b`, `cohere/north-mini-code`).

2. **[tolkonepiu/best-of-mcp-servers](https://github.com/tolkonepiu/best-of-mcp-servers)** & **[mcpservers.org](https://mcpservers.org/)**
   - *Description*: Automated quality-ranked directories scoring MCP servers by GitHub stars, active maintenance, and package downloads.

### D. Geospatial, Subsurface & Earth Observation
1. **[sacridini/Awesome-Geospatial](https://github.com/sacridini/Awesome-Geospatial)**
   - *Description*: The gold standard curated index of geospatial tools, libraries, and open-source packages.
   - *Key Python Packages in our Stack*:
     - **Rasters & Terrain**: `rasterio`, `rioxarray`, `richdem`, `whitebox-tools`.
     - **Vector & Geometry**: `geopandas`, `shapely`, `pyproj`, `fiona`.
     - **3D Visualization & Meshing**: `pyvista`, `vtk`, `trimesh`, `open3d`.
     - **Subsurface & Geophysics**: `gempy` (implicit geological modeling), `simpeg` (geophysical inversions), `pygimli` (geotechnical resistivity/ERT).

---

## 3. ECC Installed Capabilities in this Project

With ECC installed across `~/.claude/`, `~/.codex/`, and `./.agents/`, the following agent capabilities are active:

| Category | Available Skills & Agents | Project Application |
| :--- | :--- | :--- |
| **Machine Learning & Geotech ML** | `mle-workflow`, `pytorch-patterns`, `eval-harness` | Calibration of generative borehole synthesizers, conditional Markov chains, and Bayesian neural networks |
| **Software Verification** | `verification-loop`, `tdd-workflow`, `e2e-testing` | Automated regression testing for IS:6403 bearing capacity, DEM clipping, and digital twin stress updates |
| **Documentation & Governance** | `docs-governance`, `context-and-decisions` | Maintenance of architectural decision records (ADRs) for digital twin schemas and borehole databases |
| **Search & Discovery** | `search-first`, `deep-research`, `documentation-lookup` | Sourcing open-access Indian geotechnical papers, Mendeley Data repositories, and academic datasets |

---

## 4. Recommendations for Next-Phase Expansion

1. **Deploy PostGIS or DuckDB Spatial MCP**:
   - Store nationwide borehole logs in a spatial database to query by bounding box or radial distance directly from any agent.
2. **PyVista / WebGL 3D Viewer in Streamlit**:
   - Embed real-time 3D voxel rendering directly in the browser using Three.js/PyVista HTML exports, visualizing 3D shear-wave velocity $V_s$ and effective stress isosurfaces.
3. **Automated Continuous Paper Scraper**:
   - An agent pipeline combining Europe PMC / arXiv with automated PDF table extraction for Indian geotechnical investigations.
