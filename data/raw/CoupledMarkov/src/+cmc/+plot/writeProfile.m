function writeProfile(profile, caseData, pngPath, simNumber)
%WRITEPROFILE Save a PNG preview of a simulated profile.

cfg = caseData.config;
axesInfo = cmc.plot.profileAxes(caseData);
colors = cmc.plot.layerColors(cfg.num_soil_types);

fig = figure('visible', 'off', 'Color', 'w', 'Position', [100 100 1200 520]);
imagesc(axesInfo.x_data, axesInfo.y_data, profile);
set(gca, 'YDir', 'reverse', 'FontName', 'Times New Roman', 'FontSize', 16, 'Layer', 'top');
xlim(axesInfo.x_limits);
ylim(axesInfo.y_limits);

colormap(colors);
caxis([1 cfg.num_soil_types]);

xlabel('x (m)', 'FontName', 'Times New Roman', 'FontSize', 17);
ylabel('Depth (m)', 'FontName', 'Times New Roman', 'FontSize', 17);
title(sprintf('Coupled Markov Chain Profile %03d', simNumber), 'FontName', 'Times New Roman', 'FontSize', 18);

hold on
for i = 1:numel(axesInfo.borehole_x)
    xLine = axesInfo.borehole_x(i);
    plot([xLine xLine], axesInfo.y_limits, 'r-', 'LineWidth', 1.2);
end

legendHandles = gobjects(cfg.num_soil_types, 1);
for layerId = 1:cfg.num_soil_types
    legendHandles(layerId) = plot(nan, nan, 's', ...
        'MarkerFaceColor', colors(layerId, :), ...
        'MarkerEdgeColor', colors(layerId, :), ...
        'MarkerSize', 10);
end
legendLabels = caseData.soil_types.soil_name;
legend(legendHandles, legendLabels, 'Location', 'eastoutside', ...
    'FontName', 'Times New Roman', 'FontSize', 15, 'Box', 'off');
hold off

print(fig, pngPath, '-dpng', '-r300');
close(fig);
end
