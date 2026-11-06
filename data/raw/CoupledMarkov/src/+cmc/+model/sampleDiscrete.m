function value = sampleDiscrete(weights)
%SAMPLEDISCRETE Sample a 1-based index from non-negative weights.

weights = weights(:)';
if any(~isfinite(weights)) || sum(weights) <= 0
    weights = ones(size(weights)) ./ numel(weights);
else
    weights = weights ./ sum(weights);
end

edges = cumsum(weights);
value = find(rand <= edges, 1, 'first');
end
