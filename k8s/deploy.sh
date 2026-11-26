#!/bin/bash
set -e

echo "=========================================================="
echo "      CYBERRFP MAROC — DÉPLOIEMENT KUBERNETES DPA"
echo "=========================================================="

# 1. Build Docker image
echo "📦 Construction de l'image Docker cyberrfp-maroc:latest..."
docker build -t cyberrfp-maroc:latest .

# 2. Deploy to Kubernetes
echo "🚀 Application des manifests Kubernetes..."
kubectl apply -k k8s/

echo "⏳ Attente du démarrage du pod CyberRFP..."
kubectl rollout status deployment/cyberrfp-deployment -n cyberrfp --timeout=90s

echo "✅ Déploiement terminé avec succès !"
echo "🌐 URL du Service : kubectl port-forward svc/cyberrfp-service 8000:80 -n cyberrfp"
