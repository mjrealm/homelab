---
slug: /
sidebar_position: 0
---

# Homelab runbooks

Guides for the GitOps k3s homelab in
[mjrealm/homelab](https://github.com/mjrealm/homelab).

## New cluster

Follow these in order to build the cluster from scratch:

1. [Workstation setup](new-cluster/01-workstation-setup.md): clone the repo and
   install the tools.
2. [Cloud prerequisites](new-cluster/02-cloud-prerequisites.md): AWS, R2 and
   Bitwarden.
3. [Install the cluster](new-cluster/03-cluster-install.md): k3s, the bootstrap
   stack and Argo CD.
4. [Infisical setup](new-cluster/04-infisical-setup.md): projects, identities and
   the operator.

## Playbooks

How to change the cluster after it exists:

1. [Which playbook do I run?](playbooks/01-overview.md): bootstrap, upgrade or
   recover.
2. [Upgrade or extend a live cluster](playbooks/02-upgrade.md): re-apply the root
   chart, add a bootstrap app, rotate the AWS key, repair Argo CD.
