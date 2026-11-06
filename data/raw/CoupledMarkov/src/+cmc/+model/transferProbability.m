function [verticalProb, horizontalProb] = transferProbability(verticalFrequency, horizontalFrequency, numSoilTypes, maxDistance)
%TRANSFERPROBABILITY Convert frequency matrices into transition probabilities.

verticalProb = rowNormalize(verticalFrequency);
horizontalOneStep = rowNormalize(horizontalFrequency);

horizontalProb = zeros(numSoilTypes, numSoilTypes, maxDistance);
horizontalProb(:, :, 1) = horizontalOneStep;
for distance = 2:maxDistance
    horizontalProb(:, :, distance) = horizontalProb(:, :, distance - 1) * horizontalOneStep;
end
end

function probability = rowNormalize(frequency)
numStates = size(frequency, 1);
probability = zeros(size(frequency));
rowSums = sum(frequency, 2);
for row = 1:numStates
    if rowSums(row) > 0
        probability(row, :) = frequency(row, :) ./ rowSums(row);
    else
        probability(row, row) = 1;
    end
end
end
