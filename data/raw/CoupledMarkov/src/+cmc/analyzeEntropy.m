function outputs = analyzeEntropy(profiles, caseData, entropyDir)
%ANALYZEENTROPY Calculate layer probabilities and information entropy.

numSoilTypes = caseData.config.num_soil_types;
numSimulations = size(profiles, 3);
probabilities = zeros(size(profiles, 1), size(profiles, 2), numSoilTypes);

for layerId = 1:numSoilTypes
    probabilities(:, :, layerId) = sum(profiles == layerId, 3) ./ numSimulations;
end

entropy = zeros(size(profiles, 1), size(profiles, 2));
for layerId = 1:numSoilTypes
    probability = probabilities(:, :, layerId);
    mask = probability > 0;
    entropy(mask) = entropy(mask) - probability(mask) .* log2(probability(mask));
end

probabilityFiles = strings(numSoilTypes, 1);
for layerId = 1:numSoilTypes
    probabilityPath = fullfile(entropyDir, sprintf('probability_layer_%03d.csv', layerId));
    writematrix(probabilities(:, :, layerId), probabilityPath);
    probabilityFiles(layerId) = string(probabilityPath);
    fprintf('Saved %s\n', probabilityPath);
end

entropyCsv = fullfile(entropyDir, 'entropy.csv');
entropyPng = fullfile(entropyDir, 'entropy.png');
writematrix(entropy, entropyCsv);
cmc.plot.writeEntropy(entropy, caseData, entropyPng);

fprintf('Saved %s\n', entropyCsv);
fprintf('Saved %s\n', entropyPng);

outputs = struct();
outputs.probability_files = probabilityFiles;
outputs.entropy_csv = string(entropyCsv);
outputs.entropy_png = string(entropyPng);
end
