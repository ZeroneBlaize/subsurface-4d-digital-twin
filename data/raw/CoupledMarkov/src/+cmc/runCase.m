function outputs = runCase(caseDir, outputRoot)
%RUNCASE Run a Coupled Markov Chain profile simulation case.

if nargin < 1 || isempty(caseDir)
    caseDir = fullfile(pwd, 'examples', 'boreholedata');
end
if nargin < 2 || isempty(outputRoot)
    outputRoot = fullfile(pwd, 'outputs');
end

profileDir = fullfile(outputRoot, 'profile');
entropyDir = fullfile(outputRoot, 'entropy');
if ~exist(profileDir, 'dir')
    mkdir(profileDir);
end
if ~exist(entropyDir, 'dir')
    mkdir(entropyDir);
end

caseData = cmc.io.loadCase(caseDir);
rng(caseData.config.random_seed);

profiles = zeros(caseData.config.num_rows, caseData.config.num_cols, caseData.config.num_simulations);
profileFiles = strings(caseData.config.num_simulations, 2);
for sim = 1:caseData.config.num_simulations
    profile = cmc.simulateProfile(caseData);
    profiles(:, :, sim) = profile;

    csvPath = fullfile(profileDir, sprintf('profile_%03d.csv', sim));
    pngPath = fullfile(profileDir, sprintf('profile_%03d.png', sim));
    writematrix(profile, csvPath);
    cmc.plot.writeProfile(profile, caseData, pngPath, sim);

    profileFiles(sim, :) = [string(csvPath), string(pngPath)];
    fprintf('Saved %s\n', csvPath);
    fprintf('Saved %s\n', pngPath);
end

entropyOutputs = cmc.analyzeEntropy(profiles, caseData, entropyDir);

outputs = struct();
outputs.profile_files = profileFiles;
outputs.entropy = entropyOutputs;
end
