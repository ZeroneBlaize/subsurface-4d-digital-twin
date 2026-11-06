function colors = layerColors(numSoilTypes)
%LAYERCOLORS Return stable discrete colors for layer IDs.

baseColors = [
    0.1216 0.4667 0.7059
    0.8510 0.3255 0.0980
    0.9294 0.6941 0.1255
    0.4941 0.1843 0.5569
    0.4667 0.6745 0.1882
    0.3020 0.7451 0.9333
    0.6353 0.0784 0.1843
];

if numSoilTypes <= size(baseColors, 1)
    colors = baseColors(1:numSoilTypes, :);
else
    colors = lines(numSoilTypes);
end
end
