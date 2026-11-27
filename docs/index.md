---
slug: /
sidebar_position: 0
---

# Homelab

Runbooks for the GitOps k3s homelab in
[mjrealm/homelab](https://github.com/mjrealm/homelab). Each page covers one task
from start to finish, with its commands on the page. Pick what you are doing.

| I want to | Start here |
|---|---|
| Build the cluster from nothing | [Workstation setup](prepare/01-workstation-setup.md), then the pages under **1. Prepare** and **2. Build**, in order |
| Rebuild after a disaster | [Recover the cluster](recover/01-recover-the-cluster.md) |
| Change a cluster that is running | [Which playbook do I run?](operate/01-overview.md) |
| Add an app's secrets | [Add an app's secrets](operate/03-add-app-secrets.md) |
| Fix an Infisical authentication error | [Fix Infisical authentication errors](operate/04-infisical-auth-errors.md) |

## How the pages are organised

1. **Prepare**: the machine and the cloud accounts you need before touching a node.
2. **Build**: install k3s, bootstrap the platform, set up Infisical (once).
3. **Recover**: rebuild the cluster from backups after a disaster.
4. **Operate**: tasks on a cluster that already exists.

Run every command from the repo root.
