---
slug: /
sidebar_position: 0
---

# Homelab

Runbooks for the GitOps k3s homelab in
[mjrealm/homelab](https://github.com/mjrealm/homelab). Pick what you are doing.

| I want to | Start here |
|---|---|
| Build the cluster from nothing | [Workstation setup](prepare/01-workstation-setup.md), then follow the pages in order under **1. Prepare** and **2. Build** |
| Change a cluster that is running | [Which playbook do I run?](operate/01-overview.md), then [Upgrade or extend a live cluster](operate/02-upgrade.md) |
| Rebuild after a disaster | [Which playbook do I run?](operate/01-overview.md) (the recovery guide is coming) |

## How the pages are organised

1. **Prepare**: the machine and the cloud accounts you need before touching a node.
2. **Build**: install k3s, bootstrap the platform, set up Infisical.
3. **Operate**: day-to-day changes and recovery on a cluster that already exists.

Run every command from the repo root.
