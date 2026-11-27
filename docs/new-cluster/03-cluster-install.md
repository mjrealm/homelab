# Install the cluster

Build the nodes, install k3s, and bootstrap everything up to Argo CD. Run all
commands from the repo root, after [Workstation setup](01-workstation-setup.md)
and [Cloud prerequisites](02-cloud-prerequisites.md).

Have these ready:

- The nodes are powered on, reachable by SSH, and listed in
  `metal/inventory/main.yml`.
- The sudo password for the nodes (the `ansible_user` in `metal/group_vars`).
- A Cloudflare API token that can edit DNS. cert-manager uses it for certificates.
- The AWS access key and secret of `homelab-infisical-bootstrap` (from
  Bitwarden).

## 1. Install k3s

1. Run:

   ```bash
   make metal
   ```

2. If a node rejects your SSH key, accept the offer to run `ssh-copy-id`. It asks
   for that node's password.
3. Enter the sudo password when Ansible asks (`-K`).
4. When the play reaches the localhost part, paste the Cloudflare API token. It is stored
   as a Secret in the `cert-manager` namespace.

## 2. Get the kubeconfig

1. Run:

   ```bash
   make kubeconfig
   ```

2. Check that the context is the right one and the nodes are Ready:

   ```bash
   kubectl config current-context   # k3s-ansible
   kubectl get nodes
   ```

## 3. Bootstrap

1. Run:

   ```bash
   make bootstrap
   ```

2. The playbook shows which cluster it will change and stops if the cluster is
   already in use. Check the context and API server, then type `y`.
3. At the prompts, enter the AWS access key ID and secret access key. Press Enter
   to accept the default region `us-east-2`.
4. Wait. The playbook installs these, in order:

   - `prometheus-crds`, `cert-manager`, `longhorn`.
   - The Secrets that hold the AWS key, then `external-secrets`.
   - `cnpg` and `barman-cloud`.
   - `infisical`, with its database. This takes several minutes.
   - `infisical-operator`.
   - `argocd`, then it applies the root ApplicationSets.

5. The last task prints the initial Argo CD admin password. Save it.

Do not run `make bootstrap` again on this cluster. To change it later, see
[Upgrade or extend a live cluster](../playbooks/02-upgrade.md).

## 4. Check

1. Check the Infisical pieces:

   ```bash
   kubectl get clustersecretstore,externalsecret -A
   kubectl get cluster -n infisical
   kubectl get pods -n infisical
   ```

2. Expect the ExternalSecret `SecretSynced`, the database cluster
   `Cluster in healthy state`, and the pods Running.
3. Open Argo CD and wait for the apps to appear and sync.

Next: [Infisical setup](04-infisical-setup.md).
