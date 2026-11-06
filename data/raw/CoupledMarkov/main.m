clear
clc

projectRoot = fileparts(mfilename('fullpath'));
addpath(fullfile(projectRoot, 'src'));

caseDir = fullfile(projectRoot, 'examples', 'boreholedata');
outputDir = fullfile(projectRoot, 'outputs');

cmc.runCase(caseDir, outputDir);
