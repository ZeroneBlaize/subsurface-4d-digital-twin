function caseData = loadCase(caseDir)
%LOADCASE Read and validate a CSV-based CMC case directory.

config = cmc.io.readConfig(fullfile(caseDir, 'case_config.csv'));
boreholes = readtable(fullfile(caseDir, 'boreholes.csv'), 'TextType', 'string');
layers = readtable(fullfile(caseDir, 'borehole_layers.csv'), 'TextType', 'string');
soilTypes = readtable(fullfile(caseDir, 'soil_types.csv'), 'TextType', 'string');

boreholes = sortrows(boreholes, 'order');
trainingBoreholes = boreholes(boreholes.is_training ~= 0, :);
conditioningBoreholes = boreholes(boreholes.is_conditioning ~= 0, :);

depths = unique(layers.depth_m);
depths = sort(depths);
trainingLayers = buildLayerMatrix(layers, trainingBoreholes.borehole_id, depths);
conditioningLayers = buildLayerMatrix(layers, conditioningBoreholes.borehole_id, depths);
conditioningCols = conditioningBoreholes.grid_col';

caseData = struct();
caseData.base_config = config;
caseData.depths = depths;

[config, trainingLayers, conditioningLayers, conditioningCols] = applyGridRefinement( ...
    config, trainingLayers, conditioningLayers, conditioningCols);

validateattributes(trainingLayers, {'numeric'}, {'integer', '>=', 1, '<=', config.num_soil_types});
validateattributes(conditioningLayers, {'numeric'}, {'integer', '>=', 1, '<=', config.num_soil_types});
validateattributes(conditioningCols, {'numeric'}, {'integer', '>=', 1, '<=', config.num_cols});

if height(soilTypes) ~= config.num_soil_types
    error('soil_types.csv must contain %d soil types.', config.num_soil_types);
end
if numel(conditioningCols) < 2
    error('At least two conditioning boreholes are required.');
end

caseData.config = config;
caseData.boreholes = boreholes;
caseData.soil_types = soilTypes;
caseData.training_layers = trainingLayers;
caseData.conditioning_layers = conditioningLayers;
caseData.conditioning_cols = conditioningCols;
end

function matrix = buildLayerMatrix(layers, boreholeIds, depths)
matrix = zeros(numel(depths), numel(boreholeIds));
for col = 1:numel(boreholeIds)
    rows = layers(layers.borehole_id == boreholeIds(col), :);
    rows = sortrows(rows, 'depth_m');
    if height(rows) ~= numel(depths)
        error('Borehole %s has %d layer rows, expected %d.', boreholeIds(col), height(rows), numel(depths));
    end
    if any(rows.depth_m ~= depths)
        error('Borehole %s depth grid does not match the case depth grid.', boreholeIds(col));
    end
    matrix(:, col) = round(rows.layer_id);
end
end

function [config, trainingLayers, conditioningLayers, conditioningCols] = applyGridRefinement( ...
    config, trainingLayers, conditioningLayers, conditioningCols)
if isfield(config, 'grid_refinement')
    refinement = config.grid_refinement;
else
    refinement = 1;
end

if refinement < 1 || refinement ~= round(refinement)
    error('grid_refinement must be a positive integer.');
end

if refinement == 1
    return
end

trainingLayers = repelem(trainingLayers, refinement, 1);
conditioningLayers = repelem(conditioningLayers, refinement, 1);
conditioningCols = (conditioningCols - 1) * refinement + 1;

config.dx_m = config.dx_m / refinement;
config.dz_m = config.dz_m / refinement;
config.num_rows = size(conditioningLayers, 1);
config.num_cols = (config.num_cols - 1) * refinement + 1;
end
