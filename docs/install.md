# Installation Guide

Current Cluster Version: **v1.35.3+k3s1**

The cluster is bootstrapped using Ansible. The playbooks located in the `metal/` directory configure the bare-metal nodes and install K3s.

## 1. Prerequisites
- Target nodes with a fresh OS installed.
- SSH access to the nodes configured.
- `ansible` installed on your control machine.

## 2. Configuration Variables

Before running the playbook, you must update the following files to match your environment:

### `metal/inventory/main.yml`
This file defines your nodes. Update the IP addresses and node names:
```yaml
master:
  hosts:
    metal0:
      ansible_host: 192.168.10.14
agent:
  hosts:
    metal1:
      ansible_host: 192.168.10.10
    ...
```

### `metal/group_vars/all.yml`
Update the `ansible_user` to the SSH user you use to connect to your nodes:
```yaml
ansible_user: your_username
```

### `metal/roles/k3s/defaults/main.yml`
This file contains the core configuration for your K3s installation. Key variables to review:
- `k3s_version`: The version of Kubernetes to install.
- `k3s_server_flags`: The flags passed to the K3s server on startup. This is where you disable default components like Traefik or ServiceLB if you intend to use custom ingress/load balancers (e.g., MetalLB, Cilium).

## 3. Running the Playbook

Once your variables are set, run the cluster playbook from the `metal/` directory:

```bash
cd metal
ansible-playbook -i inventory/main.yml cluster-playbook.yml
```

Once the playbook finishes, grab your `kubeconfig` (located at `~/.kube/config.k3s` as defined by `k3s_kube_config_file`) and verify the nodes are ready:

```bash
kubectl get nodes
```
