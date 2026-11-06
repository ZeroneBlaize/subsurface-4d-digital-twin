function rowValues = simulateRightToLeft(previousAndCurrentRows, numSoilTypes, horizontalProb, verticalProb)
%SIMULATERIGHTTOLEFT Simulate one interval row from right to left.

numCols = size(previousAndCurrentRows, 2);
rowValues = zeros(1, numCols);
rowValues(1) = previousAndCurrentRows(2, 1);
rowValues(numCols) = previousAndCurrentRows(2, numCols);

for col = numCols-1:-1:2
    weights = zeros(1, numSoilTypes);
    for soilType = 1:numSoilTypes
        weights(soilType) = verticalProb(previousAndCurrentRows(1, col), soilType) ...
            * horizontalProb(rowValues(col + 1), soilType, 1) ...
            * horizontalProb(soilType, rowValues(1), col - 1);
    end
    rowValues(col) = cmc.model.sampleDiscrete(weights);
end
end
