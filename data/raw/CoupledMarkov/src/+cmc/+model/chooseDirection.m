function direction = chooseDirection(left, leftAbove, right, rightAbove, previousDirection, horizontalProb, spacing)
%CHOOSEDIRECTION Determine row simulation direction between two boreholes.

if left == right && left == leftAbove && right ~= rightAbove
    direction = 1;
elseif left == right && left ~= leftAbove && right == rightAbove
    direction = 2;
elseif left ~= leftAbove && right == rightAbove
    direction = 1;
elseif left == leftAbove && right ~= rightAbove
    direction = 2;
elseif left == leftAbove && right == rightAbove
    direction = previousDirection;
else
    direction = cmc.model.sampleDiscrete([ ...
        horizontalProb(left, right, spacing), ...
        horizontalProb(right, left, spacing)]);
end
end
