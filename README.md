# My Homelab

[![license](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue?style=flat-square&logo=github)](https://mjrealm.github.io/homelab/)
[![Lint YAML](https://github.com/mjrealm/homelab/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/mjrealm/homelab/actions/workflows/lint.yml)
[![Gitleaks](https://github.com/mjrealm/homelab/actions/workflows/gitleaks.yml/badge.svg?branch=main)](https://github.com/mjrealm/homelab/actions/workflows/gitleaks.yml)
[![Docs](https://github.com/mjrealm/homelab/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/mjrealm/homelab/actions/workflows/docs.yml)

My personal homelab on [k3s](https://k3s.io), managed with [GitOps](https://codefresh.io/learn/gitops/): every change reaches the cluster through Git, and [Argo CD](https://argo-cd.readthedocs.io) applies it.

- `metal/`: Ansible playbooks that prepare the nodes and install k3s.
- `k8s/bootstrap/`: what runs before Argo CD takes over (cert-manager, Longhorn, the Infisical stack, Argo CD).
- `k8s/<stack>/<app>/`: one Helm chart per app, grouped into the `apps`, `platform`, `system` and `ai` stacks.

Secrets are not stored in this repository. They live in [Infisical](https://infisical.com), and an operator syncs them into the cluster.

This is my own setup, not a framework. Hostnames, networks and accounts are specific to my environment, so use it as a reference and replace them with yours.
