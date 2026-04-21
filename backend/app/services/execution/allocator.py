import numpy as np


def equal_weight_strategies(strategies):
    w = 1.0 / len(strategies)
    return {s: w for s in strategies}


def sharpe_weighted(metrics):
    total = sum(max(m.get("sharpe", 0), 0) for m in metrics.values())
    if total == 0:
        return equal_weight_strategies(list(metrics.keys()))
    return {k: max(v.get("sharpe", 0), 0) / total for k, v in metrics.items()}


def correlation_adjusted_weights(returns_dict):
    keys = list(returns_dict.keys())
    returns = np.array([returns_dict[k] for k in keys])

    if len(keys) <= 1:
        return {keys[0]: 1.0}

    corr = np.corrcoef(returns)
    penalty = np.mean(corr, axis=1)
    scores = 1 - penalty

    total = scores.sum()
    if total == 0:
        return equal_weight_strategies(keys)

    weights = scores / total
    return dict(zip(keys, weights, strict=False))


def blended_allocator(metrics, returns):
    w1 = sharpe_weighted(metrics)
    w3 = correlation_adjusted_weights(returns)

    final = {}
    for k in metrics.keys():
        # Using two strategies for now
        final[k] = (w1[k] + w3[k]) / 2

    total = sum(final.values())
    return {k: v / total for k, v in final.items()}


def allocate_to_strategies(weights, total_capital):
    return {strategy: weight * total_capital for strategy, weight in weights.items()}


def combine_strategy_results(results, weights):
    total = 0
    for k, pnl in results.items():
        total += pnl * weights[k]
    return total
