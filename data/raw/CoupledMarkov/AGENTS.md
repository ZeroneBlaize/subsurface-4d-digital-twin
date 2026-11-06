# Repository Guidelines

## Project Structure & Module Organization

This MATLAB project simulates conditioned geological profiles with a Coupled Markov Chain model. The root entry point is `main.m`, which adds `src/` to the MATLAB path and calls `cmc.runCase`. Core code is organized as a MATLAB package under `src/+cmc/`: CSV loading lives in `+io`, transition and simulation logic in `+model`, and figure writing in `+plot`.

The only bundled case is `examples/boreholedata/`. It contains `case_config.csv`, `boreholes.csv`, `borehole_layers.csv`, `soil_types.csv`, and one cleaned reference output in `examples/boreholedata/reference/`. Default generated examples are kept in `outputs/profile/` and `outputs/entropy/` so README images render on GitHub.

## Build, Test, and Development Commands

Run the default example:

```powershell
matlab -batch "run('main.m')"
```

Run a custom case from MATLAB:

```matlab
addpath('src')
cmc.runCase('examples/boreholedata', 'outputs')
```

There is no build step; MATLAB reads the package files directly.

## Coding Style & Naming Conventions

Use MATLAB package-qualified functions for new code, for example `cmc.model.sampleDiscrete`. Keep functions small and single-purpose. Use lower camel case for new function names and descriptive variable names, while preserving conventional model names such as `VTPM`, `HTPM`, `dx`, and `dz` when they clarify equations. Use 4-space indentation.

## Testing Guidelines

No formal unit test framework is configured. After changes, run `main.m` and verify that `outputs/profile/profile_*.csv` contains only integer layer IDs `1..4`, has no `0` or `NaN` values, and matches the effective refined grid size. The bundled case uses `grid_refinement=2`, producing a `136 x 171` profile grid. Check that layer probability grids sum to 1 per cell and `outputs/entropy/entropy.csv` is within `0..2` bits.

## Commit & Pull Request Guidelines

Use concise imperative commits such as `Refactor CMC model package` or `Update borehole CSV case`. Pull requests should describe changed simulation inputs, parameter changes, validation performed, and include the generated profile image when plotting or model behavior changes.

## Data & Output Handling

Do not reintroduce Excel as a runtime input. Treat CSV files under `examples/boreholedata/` as the source of truth. Keep generated profile and entropy artifacts under `outputs/profile/` and `outputs/entropy/`.
