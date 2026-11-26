# Deployment script for Kubernetes (PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      CYBERRFP MAROC — DÉPLOIEMENT KUBERNETES DPA" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

Write-Host "📦 1. Construction de l'image Docker..." -ForegroundColor Green
docker build -t cyberrfp-maroc:latest .

Write-Host "🚀 2. Application des manifests Kubernetes..." -ForegroundColor Green
kubectl apply -k k8s/

Write-Host "⏳ 3. Vérification du déploiement..." -ForegroundColor Green
kubectl rollout status deployment/cyberrfp-deployment -n cyberrfp --timeout=90s

Write-Host "`n✅ Déploiement terminé avec succès !" -ForegroundColor Green
Write-Host "Pour tester en local sur votre cluster :" -ForegroundColor White
Write-Host "kubectl port-forward svc/cyberrfp-service 8000:80 -n cyberrfp" -ForegroundColor Yellow
