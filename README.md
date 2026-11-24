# ACEest Fitness CI/CD

Flask service for the ACEest Fitness and Gym assignment. The desktop
versions supplied with the brief are in `versions/`. `ACEest_Fitness.py`
is the web service Jenkins builds and Kubernetes runs.

Student: Chaitanya Reddy, 2025TM93047

## Run the tests

```powershell
py -3.8 -m pip install -r requirements-dev.txt
py -3.8 -m pytest
py -3.8 ACEest_Fitness.py
```

Open http://127.0.0.1:5000/health and http://127.0.0.1:5000/.

## Images

Docker is not installed on the machine where this repository was prepared.
On a machine with Docker, after `docker login`:

```powershell
.\scripts\build-all-versions.ps1 -Image usernamejaya/aceest-fitness
```

That builds and pushes tags 1.0, 1.1, 1.1.2, 2.0.1, 2.1.2, 2.2.1, 2.2.4, 3.0.1, 3.1.2, and 3.2.4. Change the image name if the Docker Hub account is different, and use the same name in the Kubernetes manifests.

## Cluster

kubectl and Minikube are not installed here, so these manifests have not been applied. After `minikube start`:

```powershell
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rolling
kubectl apply -f k8s/blue-green
kubectl apply -f k8s/canary
kubectl apply -f k8s/shadow/primary.yaml
kubectl apply -f k8s/shadow/shadow.yaml
kubectl apply -f k8s/ab
```

`k8s/shadow/virtualservice.yaml` is the Istio mirror. Apply it only when Istio is installed. Without Istio, user traffic stays on `aceest-primary` and the shadow deployment is the comparison copy.

NodePorts, then `minikube ip`:

| Strategy | URL |
| --- | --- |
| Rolling update | http://MINIKUBE_IP:30080 |
| Blue-green live | http://MINIKUBE_IP:30081 |
| Canary (4 stable, 1 new) | http://MINIKUBE_IP:30082 |
| Shadow primary | http://MINIKUBE_IP:30083 |
| A/B router | http://MINIKUBE_IP:30084 |

Blue-green starts on blue (3.1.2). Switch to green with `.\scripts\switch-blue-green.ps1 -Color green`. Switch back with `-Color blue`.

A/B sends the default request to version A. A request with header `X-Variant: B` goes to version B.

Rollback of the rolling deployment:

```powershell
.\scripts\rollback.ps1
```

That runs `kubectl rollout undo` when a previous revision exists. Otherwise it applies `k8s/rollback/deployment.yaml`, which pins the same deployment to image 3.1.2 with `maxUnavailable: 0`.

## Jenkins

`Jenkinsfile` checks out the repository, runs pytest, runs SonarQube with the server named `SonarQube`, waits for the quality gate, builds and pushes the image with the `dockerhub` credential, then applies the strategy chosen in `DEPLOY_STRATEGY`. A failed deploy rolls the rolling deployment back.

SonarQube settings are in `sonar-project.properties`. This PC has no SonarQube server, so the scan runs on the Jenkins agent that has `sonar-scanner` and the SonarQube plugin.
