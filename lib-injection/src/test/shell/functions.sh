#!/bin/bash

## HELPERS
function echoerr() {
    echo "$@" 1>&2;
}
## end HELPERS

if [ -z "${BASE_DIR}" ] ; then
    echoerr "MUST define BASE_DIR before sourcing this file"
    exit 1
fi
export SRC_DIR=${BASE_DIR}/src
export BUILD_DIR=${BASE_DIR}/build
export LIBRARY=java
export LIBRARY_DIR=${BASE_DIR}/${LIBRARY}

mkdir -p ${BUILD_DIR}

if [ -z ${CI} ] ; then
    export RUNNING_LOCALLY=1
    if [ -z ${DOCKER_USERNAME} ] ; then
        echoerr "MUST set DOCKER_USERNAME to your dockerhub username"
    fi
    export INIT_DOCKER_IMAGE_REPO=docker.io/${DOCKER_USERNAME}/dd-lib-java-init
    export APP_DOCKER_IMAGE_REPO=docker.io/${DOCKER_USERNAME}/dd-lib-java-init-test-app
    # export DOCKER_IMAGE_TAG=latest
    export DOCKER_IMAGE_TAG=34db2f76715dbbe9168806bac7c89c7ad4d51996
else
    export RUNNING_LOCALLY=0
    export INIT_DOCKER_IMAGE_REPO=ghcr.io/datadog/dd-trace-java/dd-lib-java-init
    export APP_DOCKER_IMAGE_REPO=ghcr.io/datadog/dd-trace-java/dd-lib-java-init-test-app
    export DOCKER_IMAGE_TAG=34db2f76715dbbe9168806bac7c89c7ad4d51996
    # if [[ -n ${GITHUB_SHA} ]] ; then
    #     # export DOCKER_IMAGE_TAG=${GITHUB_SHA}
    #     export DOCKER_IMAGE_TAG=latest
    # fi
    # if [[ -n ${CI_COMMIT_SHA} ]] ; then
    #     # export DOCKER_IMAGE_TAG=${CI_COMMIT_SHA}
    #     export DOCKER_IMAGE_TAG=${CI_COMMIT_SHA}
    # fi
    # if [[ -n ${DOCKER_IMAGE_TAG} ]] ; then
    #     echoerr "Unknown CI provider used, can't determine git commit hash"
    #     exit 1
    # fi
    export DD_API_KEY=apikey
    export DD_APP_KEY=appkey
fi

export USE_ADMISSION_CONTROLLER=0
export USE_UDS=0
echo "Running locally: ${RUNNING_LOCALLY}"
echo "Sample app image: ${APP_DOCKER_IMAGE_REPO}:${DOCKER_IMAGE_TAG}"
echo "Init image: ${INIT_DOCKER_IMAGE_REPO}:${DOCKER_IMAGE_TAG}"

## MODIFIERS
function uds() {
    export USE_UDS=1
}

function network() {
    export USE_UDS=0
}

function use-admission-controller() {
    export USE_ADMISSION_CONTROLLER=1
}

## FUNCTIONS
function reset-cluster() {
    if [[ "$(kind get clusters)" =~ "lib-injection-testing" ]] ;  then
        kind delete cluster --name lib-injection-testing
    fi
}

function reset-buildx() {
    if [[ "$(docker buildx ls)" =~ "lib-injection-testing" ]] ;  then
        echo "deleting docker buildx builder: lib-injection-testing"
        docker buildx rm lib-injection-testing
    fi
}

function reset-deploys() {
    reset-app
    helm uninstall datadog
    kubectl delete daemonset datadog
    kubectl delete pods -l app=datadog
}

function reset-all() {
    reset-cluster
    reset-buildx
}

function ensure-cluster() {
    if ! [[ "$(kind get clusters)" =~ "lib-injection-testing" ]] ;  then
        kind create cluster --image=kindest/node:v1.22.9 --name lib-injection-testing --config "${SRC_DIR}/test/resources/kind-config.yaml" || exit 1
    fi
}

function ensure-buildx() {
    if ! [[ "$(docker buildx ls)" =~ "lib-injection-testing" ]] ;  then
        docker buildx create --name lib-injection-testing || exit 1
    fi
    docker buildx use lib-injection-testing
}

function deploy-operator() {
    operator_file=${BASE_DIR}/java/operator-helm-values.yaml
    if [ ${USE_UDS} -eq 1 ] ; then
      operator_file=${BASE_DIR}/java/operator-helm-values-uds.yaml
    fi

    helm repo add datadog https://helm.datadoghq.com
    helm repo update

    helm install datadog --set datadog.apiKey=${DD_API_KEY} --set datadog.appKey=${DD_APP_KEY} -f "${operator_file}" datadog/datadog
    sleep 5 && kubectl get pods

    pod_name=$(kubectl get pods -l app=datadog-cluster-agent -o name)
    # kubectl wait "${pod_name}" --for condition=ready --timeout=5m
    kubectl wait "${pod_name}" --for condition=ready --timeout=1m
    sleep 5 && kubectl get pods
}

function deploy-test-agent() {
    kubectl apply -f "${SRC_DIR}/test/resources/dd-apm-test-agent-config.yaml"
    kubectl rollout status daemonset/datadog
    sleep 5 && kubectl get pods -l app=datadog

    pod_name=$(kubectl get pods -l app=datadog -o name)
    kubectl wait "${pod_name}" --for condition=ready
    sleep 5 && kubectl get pods -l app=datadog
}

function deploy-agents() {
    if [ ${USE_ADMISSION_CONTROLLER} -eq 1 ] ;  then
        deploy-operator
    fi
    deploy-test-agent   
}

function reset-app() {
    kubectl delete pods my-app
}

function deploy-app() {
    echo "Deploying library $LIBRARY"
    helm template lib-injection/common \
      -f lib-injection/$LIBRARY/values-override.yaml \
      --set use_uds=${USE_UDS} \
      --set use_admission_controller=${USE_ADMISSION_CONTROLLER} | kubectl apply -f -
    # kubectl apply -f "${app_config}"
    # kubectl wait pod/my-app --for condition=ready --timeout=5m
    kubectl wait pod/my-app --for condition=ready --timeout=1m
    sleep 5 && kubectl get pods
}

function test-for-traces() {
    tmpfile=$(mktemp -t traces.XXXXXX)
    wget -O $(readlink -f "${tmpfile}") http://localhost:18126/test/traces || true
    traces=`cat ${tmpfile}`
    if [[ ${#traces} -lt 3 ]] ; then
        echoerr "No traces reported - ${traces}"
        exit 1
    else
        count=`jq '. | length' <<< "${traces}"`
        echo "Received ${count} traces so far"
    fi
}
