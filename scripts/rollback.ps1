# Prefer the recorded revision when one exists. Otherwise pin the
# rolling deployment back to image 3.1.2.
$history = kubectl rollout history deployment/aceest-rolling -n aceest 2>$null
if ($LASTEXITCODE -eq 0 -and $history -match "REVISION") {
    kubectl rollout undo deployment/aceest-rolling -n aceest
} else {
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/rollback/deployment.yaml
}
kubectl rollout status deployment/aceest-rolling -n aceest --timeout=180s
