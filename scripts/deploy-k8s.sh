#!/bin/bash
# Kubernetes Deployment Script for HRPO-X

set -e

NAMESPACE="${NAMESPACE:-hrpox}"
ENVIRONMENT="${ENVIRONMENT:-production}"
REPLICAS="${REPLICAS:-2}"

echo "[*] Deploying HRPO-X to Kubernetes"
echo "    Namespace: $NAMESPACE"
echo "    Environment: $ENVIRONMENT"
echo "    Replicas: $REPLICAS"

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create ConfigMap from config files
echo "[>] Creating ConfigMap..."
kubectl create configmap hrpox-config \
    --from-file=config/ \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Create Secrets (from environment variables or files)
echo "[>] Creating Secrets..."
kubectl create secret generic hrpox-secrets \
    --from-literal=redis-password=${REDIS_PASSWORD} \
    --from-literal=secret-key=${SECRET_KEY} \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy Redis
echo "[>] Deploying Redis..."
kubectl apply -f k8s/redis-deployment.yaml -n $NAMESPACE

# Deploy HRPO-X Core
echo "[>] Deploying HRPO-X Core..."
kubectl apply -f k8s/hrpox-deployment.yaml -n $NAMESPACE

# Deploy Monitoring Stack
echo "[>] Deploying Monitoring..."
kubectl apply -f k8s/monitoring/ -n $NAMESPACE

# Wait for rollout
echo "[>] Waiting for rollout to complete..."
kubectl rollout status deployment/hrpox-core -n $NAMESPACE

# Display status
echo "[+] Deployment complete!"
kubectl get all -n $NAMESPACE

echo ""
echo "[*] Access the application:"
echo "    kubectl port-forward -n $NAMESPACE svc/hrpox-core 8000:8000"
echo ""
echo "[*] View logs:"
echo "    kubectl logs -f -n $NAMESPACE deployment/hrpox-core"
