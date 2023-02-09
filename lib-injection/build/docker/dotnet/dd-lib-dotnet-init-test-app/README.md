# Running your local changes

## Update sources
The following files are involved in the lib-injection process:
- `lib-injection/Dockerfile`: This is a minimal Dockerfile that will generate the init container. Its purpose is to hold all of the .NET Tracer deployment assets that will later be copied into a shared location that the application container can access.
- `lib-injection/copy-lib.sh`: This file will stored in the init container and invoked by the cluster agent. It must copy the relevant .NET Tracer deployment files to a shared location (passed as argument `$1`) that will be accessible to the application container.
- `.github/workflows/lib-injection.yml`: The GitHub action that will generate the container that will be run as an init container during the library injection process.

## Running the lib-injection GitHub action
After pushing all updates to your branch, you can invoke the lib-injection GitHub action with the following CLI command:

```
gh workflow run "Lib Injection Test" --ref <BRANCH_NAME> -f sha=<SHA> -f version=<MAJOR.MINOR.PATCH>
```

We currently pass in a SHA and version so we can pull the matching Azure blob storage assets, but we may be able to infer all of this information later.

## Deploying the Datadog Agent
To deploy to a GKE linux cluster, run the following command:
```
helm install --set datadog.apiKey=<DATADOG_APP_KEY> --set targetSystem=linux datadog-agent datadog/datadog
```

To deploy to a GKE ARM64 linux cluster, you may need to add the local `helm/helm_agent_arm64_chart_values.yaml` which adds some "tolerations" to match the requirements of the ARM64 nodes, like the following command:
```
helm install -f helm/helm_agent_arm64_chart_values.yaml --set datadog.apiKey=<DATADOG_APP_KEY> --set targetSystem=linux datadog-agent datadog/datadog
```

## Deploying a developer build of the Datadog Agent
To deploy to a GKE linux cluster, run the following command:
```
helm install -f helm/helm_agent_dev_chart_values.yaml --set datadog.apiKey=<DATADOG_APP_KEY> --set targetSystem=linux datadog-agent datadog/datadog
```

To deploy to a GKE ARM64 linux cluster, you may need to add the local `helm/helm_agent_arm64_chart_values.yaml` which adds some "tolerations" to match the requirements of the ARM64 nodes, like the following command:
```
helm install -f helm/helm_agent_arm64_chart_values.yaml -f helm/helm_agent_dev_chart_values.yaml --set datadog.apiKey=<DATADOG_APP_KEY> --set targetSystem=linux datadog-agent datadog/datadog
```

## Uninstalling the Datadog Agent
If you need to uninstall the Datadog Agent helm chart, run the following command:
```
helm uninstall datadog-agent
```

## Deploying the web application

### Debian
First, build a multi-arch debian example, run the following command:

```
docker buildx build --build-arg RUNTIME=bullseye-slim --push --platform linux/arm64/v8,linux/amd64 --tag ddzachmontoya/minimal-web-app:debian .
```

If necessary, you may need to run the following command to initialize the builder:

```
docker buildx create --use
```

Next, run the appliction in the current Kubernetes cluster with the following command:

```
kubectl apply -f k8s/minimal-web-app-debian.yaml
```

### Alpine
To build a multi-arch alpine example, run the following command:

```
docker buildx build --build-arg RUNTIME=alpine --push --platform linux/arm64/v8,linux/amd64 --tag ddzachmontoya/minimal-web-app:alpine .
```

If necessary, you may need to run the following command to initialize the builder:

```
docker buildx create --use
```

Next, run the appliction in the current Kubernetes cluster with the following command:

```
kubectl apply -f k8s/minimal-web-app-alpine.yaml
```

### Windows
First, build a multi-arch debian example, run the following command:

```
docker buildx build --push --platform windows/amd64 --tag ddzachmontoya/minimal-web-app:windows --file Dockerfile.windows .
```

If necessary, you may need to run the following command to initialize the builder:

```
docker buildx create --use
```

Next, run the appliction in the current Kubernetes cluster with the following command:

```
kubectl apply -f k8s/minimal-web-app-windows.yaml
```

## Tips
You can switch between GKE clusters by running the following command:
```
gcloud container clusters get-credentials <CLUSTER> --zone <ZONE> --project <PROJECT>
```

The following commands may be useful for understanding what is going on inside the cluster:
- `kubectl get nodes` - Gets all the nodes (hosts) in the current cluster
- `kubectl describe node <NODE_NAME>` - Gets a bunch of information for the specified node
- `kubectl get pods` - Gets all the pods (applications) in the current cluster
- `kubectl describe pod <POD_NAME>` - Gets a bunch of information for the specified running pod
- `kubectl delete pod <POD_NAME>` - Deletes the specified running pod
- `kubectl exec --stdin --tty <POD_NAME> -- /bin/bash` - Opens a terminal in the specified running pod