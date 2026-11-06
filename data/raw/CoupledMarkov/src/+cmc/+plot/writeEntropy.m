function writeEntropy(entropy, caseData, pngPath)
%WRITEENTROPY Save an information entropy cloud map.

cfg = caseData.config;
axesInfo = cmc.plot.profileAxes(caseData);
maxEntropy = log2(cfg.num_soil_types);

fig = figure('visible', 'off', 'Color', 'w', 'Position', [100 100 1200 520]);
imagesc(axesInfo.x_data, axesInfo.y_data, entropy);
set(gca, 'YDir', 'reverse', 'FontName', 'Times New Roman', 'FontSize', 16, 'Layer', 'top');
xlim(axesInfo.x_limits);
ylim(axesInfo.y_limits);
colormap(parula(256));
caxis([0 maxEntropy]);

colorbarHandle = colorbar;
colorbarHandle.Label.String = 'Entropy (bits)';
colorbarHandle.Label.FontName = 'Times New Roman';
colorbarHandle.Label.FontSize = 16;
colorbarHandle.FontName = 'Times New Roman';
colorbarHandle.FontSize = 15;

xlabel('x (m)', 'FontName', 'Times New Roman', 'FontSize', 17);
ylabel('Depth (m)', 'FontName', 'Times New Roman', 'FontSize', 17);
title('Information Entropy Map', 'FontName', 'Times New Roman', 'FontSize', 18);

hold on
for i = 1:numel(axesInfo.borehole_x)
    xLine = axesInfo.borehole_x(i);
    plot([xLine xLine], axesInfo.y_limits, 'r-', 'LineWidth', 1.2);
end
hold off

print(fig, pngPath, '-dpng', '-r300');
close(fig);
end
