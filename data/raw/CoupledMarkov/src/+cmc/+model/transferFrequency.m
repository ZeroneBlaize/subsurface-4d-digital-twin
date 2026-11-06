function [verticalFrequency, horizontalFrequency] = transferFrequency(numSoilTypes, boreholeLayers, kValues)
%TRANSFERFREQUENCY Calculate vertical and horizontal transition frequencies.

[numRows, numBoreholes] = size(boreholeLayers);
verticalFrequency = zeros(numSoilTypes, numSoilTypes);
bottomToTop = zeros(numSoilTypes, numSoilTypes);

for borehole = 1:numBoreholes
    for row = 1:numRows-1
        from = boreholeLayers(row, borehole);
        to = boreholeLayers(row + 1, borehole);
        verticalFrequency(from, to) = verticalFrequency(from, to) + 1;
    end
end

for borehole = 1:numBoreholes
    for row = numRows:-1:2
        from = boreholeLayers(row, borehole);
        to = boreholeLayers(row - 1, borehole);
        bottomToTop(from, to) = bottomToTop(from, to) + 1;
    end
end

horizontalFrequency = bottomToTop;
for soilType = 1:numSoilTypes
    horizontalFrequency(soilType, soilType) = kValues(soilType) * bottomToTop(soilType, soilType);
end
end
