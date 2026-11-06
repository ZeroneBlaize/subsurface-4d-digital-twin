clear
clc

scriptDir = fileparts(mfilename('fullpath'));
outPath = fullfile(scriptDir, 'cmc_concept.png');

fontName = 'Times New Roman';
fig = figure('visible', 'off', 'Color', 'w', 'Position', [100 100 1500 900]);
ax = axes('Position', [0 0 1 1], 'Visible', 'off');
hold(ax, 'on')
axis(ax, [0 1 0 1])

blue = [0.10 0.35 0.70];
orange = [0.90 0.35 0.12];
green = [0.24 0.60 0.30];
purple = [0.48 0.22 0.62];
gray = [0.94 0.95 0.96];
dark = [0.12 0.13 0.15];
red = [0.85 0.10 0.10];

titleText = 'CoupledMarkov_Chains_DC Concept';
text(0.5, 0.94, titleText, 'FontName', fontName, 'FontSize', 26, ...
    'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Color', dark, 'Interpreter', 'none');
text(0.5, 0.90, 'CSV borehole data condition stochastic geological profile simulation and uncertainty mapping', ...
    'FontName', fontName, 'FontSize', 16, 'HorizontalAlignment', 'center', 'Color', [0.30 0.30 0.30]);

boxY = 0.72;
boxW = 0.17;
boxH = 0.105;
boxX = [0.07 0.30 0.53 0.76];
boxColors = [blue; orange; green; purple];
boxTitles = {'CSV Case Input', 'Transition Model', 'Conditioned Profiles', 'Entropy Analysis'};
boxNotes = {
    'boreholes.csv  |  layers.csv'
    'vertical + horizontal TPM'
    '10 stochastic realizations'
    'cell-wise layer probabilities'
};

for i = 1:4
    drawRoundBox(ax, boxX(i), boxY, boxW, boxH, boxColors(i, :), gray);
    text(boxX(i) + boxW/2, boxY + 0.068, boxTitles{i}, 'FontName', fontName, ...
        'FontSize', 17, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Color', dark);
    text(boxX(i) + boxW/2, boxY + 0.034, boxNotes{i}, 'FontName', fontName, ...
        'FontSize', 13, 'HorizontalAlignment', 'center', 'Color', [0.25 0.25 0.25]);
    if i < 4
        drawArrow(ax, boxX(i) + boxW + 0.025, boxY + boxH/2, boxX(i + 1) - 0.025, boxY + boxH/2, dark);
    end
end

% Conceptual geological section.
sectionX = 0.08;
sectionY = 0.18;
sectionW = 0.54;
sectionH = 0.42;
drawPanel(ax, sectionX, sectionY, sectionW, sectionH, 'Conditioned Geological Profile', fontName);

layers = [
    1 1 1 1 2 2 2 2 2 2 2 2
    1 1 1 2 2 2 2 2 2 2 2 2
    2 2 2 2 2 3 3 3 3 3 3 3
    2 2 3 3 3 3 3 3 3 3 3 4
    3 3 3 4 4 4 4 4 4 4 4 4
    4 4 4 4 4 4 4 4 4 4 4 4
];
layerColors = [
    0.1216 0.4667 0.7059
    0.8510 0.3255 0.0980
    0.9294 0.6941 0.1255
    0.4941 0.1843 0.5569
];
cellW = sectionW / size(layers, 2);
cellH = (sectionH - 0.08) / size(layers, 1);
for r = 1:size(layers, 1)
    for c = 1:size(layers, 2)
        x = sectionX + (c - 1) * cellW;
        y = sectionY + 0.02 + (size(layers, 1) - r) * cellH;
        rectangle(ax, 'Position', [x y cellW cellH], 'FaceColor', layerColors(layers(r, c), :), ...
            'EdgeColor', 'none');
    end
end

boreholeXs = sectionX + [0.02 0.20 0.52] * sectionW;
for i = 1:numel(boreholeXs)
    plot(ax, [boreholeXs(i) boreholeXs(i)], [sectionY + 0.02 sectionY + sectionH - 0.06], ...
        '-', 'Color', red, 'LineWidth', 2.2);
end
text(sectionX + sectionW/2, sectionY - 0.025, 'x: relative distance from the left boundary borehole', ...
    'FontName', fontName, 'FontSize', 13, 'HorizontalAlignment', 'center', 'Color', [0.30 0.30 0.30]);
text(sectionX - 0.035, sectionY + sectionH/2 - 0.02, 'Depth', ...
    'FontName', fontName, 'FontSize', 14, 'Rotation', 90, 'HorizontalAlignment', 'center', 'Color', [0.30 0.30 0.30]);

% Entropy panel.
entropyX = 0.68;
entropyY = 0.18;
entropyW = 0.24;
entropyH = 0.42;
drawPanel(ax, entropyX, entropyY, entropyW, entropyH, 'Information Entropy', fontName);

[xx, yy] = meshgrid(linspace(-2.5, 2.5, 16), linspace(-2.5, 2.5, 12));
entropyField = exp(-(xx.^2 + yy.^2) / 4) + 0.45 * exp(-((xx - 1.3).^2 + (yy + 0.8).^2) / 0.8);
entropyField = entropyField ./ max(entropyField(:));
entropyColors = parula(128);
for r = 1:size(entropyField, 1)
    for c = 1:size(entropyField, 2)
        idx = max(1, min(128, round(1 + entropyField(r, c) * 127)));
        x = entropyX + (c - 1) * entropyW / size(entropyField, 2);
        y = entropyY + 0.02 + (size(entropyField, 1) - r) * (entropyH - 0.08) / size(entropyField, 1);
        rectangle(ax, 'Position', [x y entropyW / size(entropyField, 2) (entropyH - 0.08) / size(entropyField, 1)], ...
            'FaceColor', entropyColors(idx, :), 'EdgeColor', 'none');
    end
end

text(entropyX + entropyW/2, entropyY - 0.025, 'H = -\Sigma p_i log_2(p_i)', ...
    'FontName', fontName, 'FontSize', 14, 'HorizontalAlignment', 'center', 'Color', [0.30 0.30 0.30], ...
    'Interpreter', 'tex');

% Legend for layer colors.
legendX = 0.10;
legendY = 0.10;
for i = 1:4
    rectangle(ax, 'Position', [legendX + (i-1)*0.12 legendY 0.018 0.018], ...
        'FaceColor', layerColors(i, :), 'EdgeColor', 'none');
    text(legendX + 0.025 + (i-1)*0.12, legendY + 0.009, sprintf('Layer %d', i), ...
        'FontName', fontName, 'FontSize', 13, 'VerticalAlignment', 'middle', 'Color', dark);
end
plot(ax, [0.62 0.65], [legendY + 0.009 legendY + 0.009], '-', 'Color', red, 'LineWidth', 2.2);
text(0.66, legendY + 0.009, 'Conditioning boreholes', 'FontName', fontName, ...
    'FontSize', 13, 'VerticalAlignment', 'middle', 'Color', dark);

print(fig, outPath, '-dpng', '-r300');
close(fig);
fprintf('Saved %s\n', outPath);

function drawRoundBox(ax, x, y, w, h, accent, fillColor)
rectangle(ax, 'Position', [x y w h], 'Curvature', 0.08, 'FaceColor', fillColor, ...
    'EdgeColor', accent, 'LineWidth', 2);
rectangle(ax, 'Position', [x y + h - 0.012 w 0.012], 'FaceColor', accent, 'EdgeColor', accent);
end

function drawArrow(ax, x1, y1, x2, y2, color)
plot(ax, [x1 x2], [y1 y2], '-', 'Color', color, 'LineWidth', 1.5);
head = 0.012;
patch(ax, [x2 x2-head x2-head], [y2 y2+head*0.6 y2-head*0.6], color, 'EdgeColor', color);
end

function drawPanel(ax, x, y, w, h, titleText, fontName)
rectangle(ax, 'Position', [x y w h], 'FaceColor', [0.98 0.98 0.98], ...
    'EdgeColor', [0.30 0.30 0.30], 'LineWidth', 1);
text(x + w/2, y + h - 0.035, titleText, 'FontName', fontName, ...
    'FontSize', 17, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Color', [0.12 0.13 0.15]);
end
