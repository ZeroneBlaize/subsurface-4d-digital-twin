function axesInfo = profileAxes(caseData)
%PROFILEAXES Build relative plotting coordinates from conditioning boreholes.

cfg = caseData.config;
leftCol = min(caseData.conditioning_cols);
rightCol = max(caseData.conditioning_cols);
profileWidth = (rightCol - leftCol) * cfg.dx_m;
depthHeight = cfg.depth_max_m - cfg.depth_min_m;
xMargin = max(cfg.dx_m * 2, profileWidth * 0.025);

axesInfo = struct();
axesInfo.left_col = leftCol;
axesInfo.right_col = rightCol;
axesInfo.x_data = [0 profileWidth];
axesInfo.y_data = [0 depthHeight];
axesInfo.x_limits = [-xMargin profileWidth + xMargin];
axesInfo.y_limits = [0 depthHeight];
axesInfo.borehole_x = (caseData.conditioning_cols - leftCol) * cfg.dx_m;
end
