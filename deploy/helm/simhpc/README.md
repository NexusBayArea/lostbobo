# SimHPC Helm Chart

Production-ready Helm chart for SimHPC World Brain - Simulation Intelligence Platform.

## Usage

```bash
# Install with Minikube
helm install simhpc ./simhpc --namespace simhpc --create-namespace

# Upgrade after changes
helm upgrade simhpc ./simhpc --namespace simhpc

# Uninstall
helm uninstall simhpc --namespace simhpc

# For development (hot reload)
helm install simhpc ./simhpc --namespace simhpc --set image.tag=latest --set replicaCount=1
```

## Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `2` |
| `image.repository` | Docker image | `simhpc/backend` |
| `image.tag` | Image tag | `latest` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8000` |
| `ingress.enabled` | Enable Ingress | `true` |
| `ingress.host` | Ingress host | `simhpc.local` |
| `resources.requests.cpu` | CPU request | `500m` |
| `resources.requests.memory` | Memory request | `512Mi` |
| `resources.limits.cpu` | CPU limit | `2000m` |
| `resources.limits.memory` | Memory limit | `2Gi` |
| `env.RUNTIME_MODE` | Runtime mode | `production` |
| `redis.enabled` | Enable Redis | `true` |
| `redis.host` | Redis host | `redis-master` |
| `redis.port` | Redis port | `6379` |

## Minikube

```bash
minikube dashboard
minikube tunnel
```

## Development

For local development with hot reload:

```bash
helm install simhpc ./simhpc --namespace simhpc --set image.tag=latest --set replicaCount=1
```