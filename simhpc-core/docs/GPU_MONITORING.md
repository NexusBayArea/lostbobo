# GPU Monitoring Setup

## Install NVIDIA DCGM Exporter

```bash
helm repo add nvidia https://helm.nvidia.com/stable
helm repo update

helm install --namespace monitoring nvidia-dcgm-exporter nvidia/dcgm-exporter \
  --set serviceMonitor.enabled=true \
  --set prometheus.enabled=false \
  --create-namespace
```

## Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: 'nvidia-dcgm-exporter'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app_kubernetes_io_name]
        action: keep
        regex: nvidia-dcgm-exporter
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        action: keep
        regex: 9400
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'DCGM_.*'
        action: keep

  - job_name: 'simhpc-core-gpu'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: simhpc-core
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        action: keep
        regex: 8000
```

## Grafana Dashboard

Import Dashboard ID: 12239 (NVIDIA DCGM Exporter)

## Verification

```bash
kubectl get pods -n monitoring -l app=nvidia-dcgm-exporter

# Check metrics
kubectl port-forward -n monitoring svc/prometheus 9090
# Query: DCGM_FI_DEV_GPU_UTIL
```
