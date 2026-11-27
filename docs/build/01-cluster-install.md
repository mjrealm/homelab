# Install the cluster

Build the nodes, install k3s, and bootstrap everything up to Argo CD. It takes
about 45 minutes, most of it waiting. Run every command from the repo root of
the `homelab` folder, in the Terminal.

Finish [Set up your workstation](../prepare/01-workstation-setup.md) and
[Cloud prerequisites](../prepare/02-cloud-prerequisites.md) first.

Have these ready (all in Bitwarden, folder `homelab-infisical-bootstrap`):

| What | Bitwarden item |
|---|---|
| Sudo password for the nodes | `Node sudo password` |
| Cloudflare DNS token | `Cloudflare DNS API token (cert-manager)` |
| AWS access key ID and secret | `AWS IAM homelab-infisical-bootstrap` |

And on the network: all nodes are powered on, reachable by SSH, and listed in
`metal/inventory/main.yml` (one `master`, the rest `agent`).

## 1. Install k3s on the nodes

1. Run:

   ```bash
   make metal
   ```

2. If a node rejects your SSH key, the script asks
   `SSH key not accepted by <node>. Copy it with ssh-copy-id? [y/N]`. Type `y`
   and enter that node's login password.
3. When Ansible shows `BECOME password:`, enter the sudo password.
4. Wait about 10 minutes. The play updates each node, installs k3s on the
   `master` node first, then joins the `agent` nodes, then writes your kubeconfig
   (context name `k3s-ansible`).
5. At the end it asks `Enter Cloudflare API Key (sensitive)`. Paste the
   Cloudflare DNS token and press Enter. It is stored in the Secret
   `cloudflare-api-token-secret` in the `cert-manager` namespace.
6. Expect the final `PLAY RECAP` to show `failed=0` for every host.

If the play stops at one node, fix that node (power, network, SSH) and run
`make metal` again. It is safe to repeat.

## 2. Check the cluster

1. Run:

   ```bash
   kubectl config current-context
   kubectl get nodes
   ```

2. Expect the context `k3s-ansible`, and four nodes all `Ready`, one with the
   roles `control-plane,etcd`. If the context is something else, run
   `kubectl config use-context k3s-ansible` before going on. If you see
   `NotReady`, wait two minutes and run `kubectl get nodes` again.

If your kubeconfig is ever lost, `make kubeconfig` fetches it again.

## 3. Bootstrap the platform

1. Run:

   ```bash
   make bootstrap
   ```

2. The playbook prints a box that starts `=== BOOTSTRAP, new cluster only ===`,
   then the `context:` and `server:` of the cluster it will change. Check them,
   then type `y` and press Enter at
   `Continue on the cluster above? Type y to continue, anything else stops`.

   If it stops with `This cluster already has: ...`, this is not a new cluster.
   Do not continue. Use [Recover the cluster](../recover/01-recover-the-cluster.md)
   if you are rebuilding after a disaster.
3. When asked for the AWS values, copy them from Bitwarden:

   - `AWS access key ID`: the access key ID.
   - `AWS secret access key`: the secret. It is hidden as you type.
   - `AWS region, press Enter for us-east-2`: press Enter.
4. Wait about 30 minutes. The playbook installs these, in order, and prints
   `PLAY RECAP` at the end:

   - `prometheus-crds`, `cert-manager`, `longhorn`.
   - The two Secrets that hold the AWS key, then `external-secrets`.
   - `cnpg` and `barman-cloud`.
   - `infisical` with its database. This is the slowest step, up to 15 minutes.
   - `infisical-operator`.
   - `argocd`, then the root ApplicationSets.

5. The last task prints `Admin Initial Password` and the password. Copy it into a
   new Bitwarden item named `Argo CD admin (initial)`. You use it to log in to
   Argo CD, with the username `admin`.

If the playbook fails halfway, read the red error, fix the cause, and do not run
`make bootstrap` again: it stops on a half-built cluster. Run
`make upgrade TAGS=<tag>` for the part that failed, using
[Upgrade or extend a live cluster](../operate/02-upgrade.md).

## 4. Check it

1. Check the Infisical pieces:

   ```bash
   kubectl get clustersecretstore,externalsecret -A
   kubectl get cluster -n infisical
   kubectl get pods -n infisical
   ```

2. Expect:

   - The ClusterSecretStore `aws-ssm` with status `Valid`, and the ExternalSecret
     `infisical-secrets` with status `SecretSynced`.
   - The `Cluster` `infisical-database` with `Cluster in healthy state`.
   - All Infisical pods `Running`.

3. Check Argo CD:

   ```bash
   kubectl -n argocd get app
   ```

   Expect a list of apps appearing over the next minutes. Many apps will show
   `Progressing` or `Degraded` until you finish the next page, because their
   secrets do not exist in Infisical yet. That is normal.

4. Open <https://argo.mdeleon.dev> in the browser and log in with `admin` and the
   password from step 3. If the page does not load yet, it needs MetalLB and
   DNS, which Argo CD installs in the first few minutes. Retry after five
   minutes. To read the password again:

   ```bash
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
   ```

Next: [Set up Infisical](02-infisical-setup.md).
