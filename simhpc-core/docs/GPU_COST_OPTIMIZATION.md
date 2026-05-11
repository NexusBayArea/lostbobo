# GPU Cost Optimization

## Features

- **Spot-first scheduling** via Karpenter (60-75% savings)
- **Fractional GPU packing** maximizes utilization
- **Demand forecasting** drives proactive provisioning
- **Economic scoring** prefers spot when safe
- **MPS + container isolation** allows high-density sharing
- **Idle node consolidation** via Karpenter

## Karpenter Spot Configuration

Update NodePool to prefer spot instances:

```yaml
spec:
  requirements:
    - key: karpenter.sh/capacity-type
      operator: In
      values: ["spot", "on-demand"]
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s
  weight: 100
```

## Values Configuration

```yaml
costOptimization:
  spotPriority: true
  spotThreshold: 0.4
  minSpotSavings: 0.6
```

## Cost-Aware Scheduling

The ResourceEconomicsRuntime scores capacity based on:

- Margin (45%)
- Utilization (25%)
- Spot savings (20%)
- Demand alignment (10%)

Spot recommendation when savings exceed 40%.
