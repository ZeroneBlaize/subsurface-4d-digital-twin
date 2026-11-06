function config = readConfig(configPath)
%READCONFIG Read key/value simulation settings from case_config.csv.

rawData = readcell(configPath, 'Delimiter', ',');
config = struct();

for row = 2:size(rawData, 1)
    key = matlab.lang.makeValidName(char(rawData{row, 1}));
    valueCell = rawData{row, 2};
    if isnumeric(valueCell)
        rawValue = num2str(valueCell);
    else
        rawValue = strtrim(char(valueCell));
    end
    numericValue = str2num(rawValue); %#ok<ST2NM>
    if ~isempty(numericValue)
        config.(key) = numericValue;
    else
        config.(key) = rawValue;
    end
end

requiredFields = {'num_soil_types', 'dx_m', 'dz_m', 'num_cols', 'num_rows', ...
    'num_simulations', 'random_seed', 'k_values', 'x_min_m', 'x_max_m', ...
    'depth_min_m', 'depth_max_m'};
for i = 1:numel(requiredFields)
    if ~isfield(config, requiredFields{i})
        error('Missing required config parameter: %s.', requiredFields{i});
    end
end

if numel(config.k_values) ~= config.num_soil_types
    error('k_values must contain one value per soil type.');
end
end
