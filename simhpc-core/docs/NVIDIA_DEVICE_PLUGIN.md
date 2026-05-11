# NVIDIA Device Plugin Setup

## Prerequisites

- Kubernetes cluster (v1.21+)
- NVIDIA GPU drivers installed on all GPU nodes
- Helm 3 installed
- Nodes labeled with nvidia.com/gpu=true

## Install NVIDIA Device Plugin

```bash
helm repo add nvidia https://helm.nvidia.com/stable
helm repo update

helm install --namespace kube-system nvidia-device-plugin nvidia/k8s-device-plugin \
  --set mig.strategy=mixed \
  --set devicePlugin.enabled=true \
  --set devicePlugin.config.default=true
```

## Production Values

Create `nvidia-device-plugin-values.yaml`:

```yaml
devicePlugin:
  enabled: true
  config:
    default: true
    sharing:
      enabled: true
      mps:
        enabled: true
      timeSlicing:
        enabled: false

mig:
  strategy: mixed

nodeSelector:
  nvidia.com/gpu: "true"

tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
```

## Verify Installation

```bash
kubectl get pods -n kube-system -l app=nvidia-device-plugin-daemonset
kubectl describe node <gpu-node-name> | grep nvidia.com/gpu
```

## Enable MIG (Optional)

```bash
kubectl label node <gpu-node> nvidia.com/mig.config=enable-all-1g.5gb
```
