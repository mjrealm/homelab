# Homelab Documentation

Welcome to my personal homelab documentation! 

This repository follows **GitOps** principles to manage my bare-metal servers and Kubernetes cluster. It is fully automated from OS provisioning to application deployment.

## Features

- **Infrastructure as Code (IaC)**: Ansible playbooks to provision and configure the bare-metal servers (`/metal`).
- **Kubernetes**: Lightweight K3s cluster.
- **GitOps**: Automated deployment of cluster components and applications via ArgoCD or Flux (depending on the setup).
- **Self-Hosted Services**: An extensive list of applications and services managed declaratively (`/k8s`).

## Quick Links
- [Architecture](architecture.md) - Learn how the repository and infrastructure are structured.
- [Installation Guide](install.md) - How to bootstrap the cluster.
### Installed Services
- [Apps](apps.md) - User-facing applications and workloads.
- [System](system.md) - Monitoring, logging, and core system workloads.
- [Platform](platform.md) - Core platform services (ingress, storage).
- [Bootstrap](bootstrap.md) - GitOps controllers.

> :bulb: **What is a homelab?**
>
> "Simply put, a home lab consists of one or more servers (or normal PCs acting as servers), that you have in your home and you use them to experiment and try out stuff." -[techie-show](https://techie-show.com/home-lab-guide-basics/)
