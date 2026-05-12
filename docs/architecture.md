# Architecture & Design

This homelab is divided into two primary logical components: **Bare Metal Provisioning** and **Kubernetes Configuration**.

## Directory Structure

```text
.
├── metal/             # Bare metal provisioning and OS configuration via Ansible
│   ├── inventory/     # Ansible inventory defining the nodes
│   ├── group_vars/    # Global variables for the cluster
│   └── roles/         # Ansible roles (e.g., setting up K3s)
│
├── k8s/               # Kubernetes manifests and Helm charts
│   ├── apps/          # User-facing applications and services
│   ├── bootstrap/     # GitOps controllers and initial cluster setup
│   ├── platform/      # Core platform services (Ingress, storage, cert-manager)
│   └── system/        # System-level configurations (monitoring, logs, CRDs)
```

## Explanation

### 1. The `metal` Directory
The `metal` directory contains all the Ansible playbooks required to transform a fresh OS installation into a fully functional Kubernetes node. It handles:
- System updates and package installations.
- Network configuration.
- Installing the K3s server and agent binaries.
- Configuring node roles and labels.

### 2. The `k8s` Directory
The `k8s` directory contains the desired state of the Kubernetes cluster. It is structured to separate different layers of the stack:

- **bootstrap**: Contains the initial manifests needed to start the GitOps engine.
- **platform**: Fundamental services that other applications rely on. This includes things like the ingress controller, CSI drivers for storage, and certificate management.
- **system**: Observability, monitoring, logging, and cluster-wide CRDs.
- **apps**: The actual workloads, dashboards, and services deployed in the homelab. Each app typically has its own directory with a `Chart.yaml` and `values.yaml`.
