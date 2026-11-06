function profile = simulateProfile(caseData)
%SIMULATEPROFILE Generate one conditioned geological profile realization.

cfg = caseData.config;
conditioningCols = caseData.conditioning_cols;
conditioningLayers = caseData.conditioning_layers;
trainingLayers = caseData.training_layers;

[numRows, numConditioning] = size(conditioningLayers);
numCols = cfg.num_cols;
profile = zeros(numRows, numCols);
profile(1, :) = mode(conditioningLayers(1, :));

for i = 1:numConditioning
    profile(:, conditioningCols(i)) = conditioningLayers(:, i);
end

if conditioningCols(1) > 1
    profile(:, 1:conditioningCols(1)-1) = repmat(conditioningLayers(:, 1), 1, conditioningCols(1)-1);
end
if conditioningCols(end) < numCols
    profile(:, conditioningCols(end)+1:numCols) = repmat(conditioningLayers(:, end), 1, numCols-conditioningCols(end));
end

spacing = diff(conditioningCols);
[verticalFrequency, horizontalFrequency] = cmc.model.transferFrequency(cfg.num_soil_types, trainingLayers, cfg.k_values);
[verticalProb, horizontalProb] = cmc.model.transferProbability( ...
    verticalFrequency, horizontalFrequency, cfg.num_soil_types, max(spacing));

for intervalIndex = 1:numConditioning-1
    leftCol = conditioningCols(intervalIndex);
    rightCol = conditioningCols(intervalIndex + 1);
    direction = cmc.model.sampleDiscrete([ ...
        horizontalProb(profile(1, leftCol), profile(1, rightCol), 1), ...
        horizontalProb(profile(1, rightCol), profile(1, leftCol), 1)]);

    for row = 2:numRows
        direction = cmc.model.chooseDirection( ...
            profile(row, leftCol), profile(row-1, leftCol), ...
            profile(row, rightCol), profile(row-1, rightCol), ...
            direction, horizontalProb, spacing(intervalIndex));

        interval = profile(row-1:row, leftCol:rightCol);
        if direction == 1
            profile(row, leftCol:rightCol) = cmc.model.simulateLeftToRight( ...
                interval, cfg.num_soil_types, horizontalProb, verticalProb);
        else
            profile(row, leftCol:rightCol) = cmc.model.simulateRightToLeft( ...
                interval, cfg.num_soil_types, horizontalProb, verticalProb);
        end
    end
end
end
