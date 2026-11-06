function rowValues = simulateLeftToRight(previousAndCurrentRows, numSoilTypes, horizontalProb, verticalProb)
%SIMULATELEFTTORIGHT Simulate one interval row from left to right.

numCols = size(previousAndCurrentRows, 2);
rowValues = zeros(1, numCols);
rowValues(1) = previousAndCurrentRows(2, 1);
rowValues(numCols) = previousAndCurrentRows(2, numCols);

for col = 2:numCols-1
    weights = zeros(1, numSoilTypes);
    for soilType = 1:numSoilTypes
        weights(soilType) = verticalProb(previousAndCurrentRows(1, col), soilType) ...
            * horizontalProb(rowValues(col - 1), soilType, 1) ...
            * horizontalProb(soilType, rowValues(numCols), numCols - col);
    end
    rowValues(col) = cmc.model.sampleDiscrete(weights);
end
end
