# Homelab Directory Structure

## Overview
```
homelab/k8s/
├── apps/
│   ├── <app-name>/
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   ├── secrets.dec.yaml
│   │   └── templates/
│   │       ├── *.yaml
│   └── <app-name>/
├── platform/
│   ├── <app-name>/
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   ├── secrets.dec.yaml
│   │   └── templates/
│   │       ├── *.yaml
│   └── <app-name>/
├── system/
│   ├── <app-name>/
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   ├── secrets.dec.yaml
│   │   └── templates/
│   │       ├── *.yaml
│   └── <app-name>/
├── system/
│   ├── <app-name>/
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   ├── secrets.dec.yaml
│   │   └── templates/
│   │       ├── *.yaml
│   └── <app-name>/
├── system/
│   ├── <app-name>/
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   ├── secrets.dec.yaml
│   │   └── templates/
│   │       ├── *.yaml
│   └── <app-name>/
├── bootstrap/
│   ├── charts/
│   │   ├── <app-name>/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   ├── secrets.dec.yaml
│   │   │   └── templates/
│   │   │       ├── *.yaml
│   │   └── root/
│   │       ├── templates/
│   │       │   ├── app-project.yaml
│   │       │   ├── application-set-git.yaml
│   │       │   ├── application-set-list.yaml
│   │       ├── Chart.yaml
│   │       ├── values.yaml
```

## Application Categories

### apps
- Applications here are usually specialized tools that do one thing well
- An **app** is typically a standalone, end-user service (like a media server, a recipe manager, or a document editor).
- This is the category where most apps fall into
- Unlike platforms, apps do not orchestrate other system components. They often *consume* services provided by platforms (e.g., using Pocket-ID for login or EMQX for device telemetry).

### platform
- A **platform** acts as a base layer, central hub, or management interface that aggregates or orchestrates other systems.
- Examples include n8n, portainer, pocket-id, homeassistant, emqx, etc.
- **Why these are "platforms" vs "apps"**:
  - **n8n / emqx**: They act as the glue or message bus connecting standalone applications to each other.
    - **homeassistant**: Instead of being a single isolated app, it is a hub that integrates hundreds of disparate IoT devices and subsystems into a unified control plane.
    - **portainer**: It is the foundational layer used to manage the deployment of other services.
    - **pocket-id**: Provides the core SSO and identity layer that multiple end-user apps rely on for authentication.

### system
- Applications here are the core infrastructural components that make Kubernetes run and keep it healthy.
- While platforms orchestrate *other apps*, system components manage the *cluster itself*.
- Examples include Longhorn (storage), Grafana (monitoring), operators, reloaders, etc.
- **Why these are "system" components**:
  - **Longhorn / Storage Provisioners**: They provide the fundamental distributed block storage capabilities that Kubernetes PersistentVolumes rely on. Without them, no stateful applications can run.
  - **Grafana / Prometheus**: These form the observability stack that monitors the health, metrics, and logs of the Kubernetes cluster nodes and workloads themselves.
  - **Operators & Reloaders**: Components like `stakater/reloader` rely on deep integration with the Kubernetes API to automate cluster-level state.

### bootstrap
- Applications in this directory are the absolute prerequisites required to bring the cluster to a functional, automatable state. They must be installed before *any* other applications.
- While these apps could technically be categorized as `system` or `platform`, they are placed in `bootstrap` to ensure a strict order of operations during a fresh cluster build.
- **Why these apps are in bootstrap**:
  - **ingress-nginx**: Provides the core networking ingress controller. Without it, no other applications in the cluster can be exposed to the network or receive incoming traffic.
  - **ArgoCD / FluxCD**: Provides the GitOps deployment engine. This must be installed first so that it can take over and automatically deploy the rest of the applications from the Git repository.
  - **sealed-secrets / external-secrets**: Provides the decryption and secret-management layer. Applications will fail to start if they cannot access their passwords, certificates, or tokens, so the secret manager must exist before any other app is deployed.
- Installed by `bootstrap/charts/root/Chart.yaml`

## Special Cases

### bootstrap/charts/root
- This directory contains ArgoCD-specific manifests like AppProjects, ApplicationSets, and Workflows.
- These manifests are mapped to the git repository structure and create the ArgoCD applications that subsequently deploy everything else to the cluster.
- This directory does not get modified often. It is only modified when there are changes to the core ArgoCD application definitions or the overarching git repository structure.
