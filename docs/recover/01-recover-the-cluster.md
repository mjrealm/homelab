# Recover the cluster (disaster recovery)

Use this when the cluster is gone or unusable and you are rebuilding it from
backups: lost nodes, a wiped disk, a failed upgrade you cannot roll back. This
page is the whole procedure, from the first command to the last check. Follow it
top to bottom.

Do not use it on a cluster that still works. To change a running cluster, use
[Which playbook do I run?](../operate/01-overview.md).

:::caution Work in progress
The automated `make recover` playbook is not built yet. Steps 3, 5 and 6 are
marked **Not available yet**. Steps 1, 2, 4 and 7 work today. This page is
updated as each part is built and tested on a throwaway cluster, so do not treat
it as a tested procedure until this notice is gone.
:::

## What you need

Collect these before you start. Nothing else is typed during recovery.

| Item | Where it is |
|---|---|
| The nodes, powered on, reachable by SSH and listed in `metal/inventory/main.yml` | Your network |
| Sudo password for the nodes | Bitwarden |
| Cloudflare API token that can edit DNS | Bitwarden |
| AWS access key ID and secret (`homelab-infisical-bootstrap`) | Bitwarden, folder `homelab-infisical-bootstrap` |
| Infisical admin login | Bitwarden, "Infisical admin" |
| Infisical `dr-admin` client ID and secret | Bitwarden, folder `homelab-infisical-bootstrap` |

These come back on their own, so you do not need them: Infisical's
`ENCRYPTION_KEY`, `AUTH_SECRET` and `REDIS_PASSWORD` (read from AWS Systems
Manager), and every app secret (restored with Infisical's database from the S3
backup).

## 1. Rebuild the nodes and k3s

1. Run from the repo root:

   ```bash
   make metal
   ```

2. Enter the sudo password, and the Cloudflare API token when asked.
3. Fetch the new kubeconfig and check the context:

   ```bash
   make kubeconfig
   kubectl config current-context   # k3s-ansible
   kubectl get nodes
   ```

All nodes must be `Ready` before you continue.

## 2. Check that the cluster is empty

```bash
kubectl get ns
```

Expect only the k3s defaults and `cert-manager`. If you see `argocd` or
`infisical`, this is not a fresh cluster. Stop and use
[Which playbook do I run?](../operate/01-overview.md).

## 3. Restore the platform and Infisical

:::caution Not available yet
This is `make recover`, stage 1: install cert-manager, Longhorn, CNPG and
Infisical, restore Infisical's database from the S3 backup, and apply only the
`system` stack to Argo CD. Until it exists, do not try to do this by hand.
:::

## 4. Point Infisical at the new cluster

A rebuilt cluster has a new certificate authority, so Infisical must learn it.
The database already holds the admin, projects, identities and secrets.

1. Log in to `https://infisical.mdeleon.dev` with the admin from Bitwarden.
2. Get the new CA:

   ```bash
   kubectl get cm kube-root-ca.crt -n default -o jsonpath='{.data.ca\.crt}'
   ```

3. For each of the four identities (`infisical-apps`, `infisical-platform`,
   `infisical-system`, `infisical-ai`), open **Organization**, **Access
   Control**, **Machine Identities**, the identity, **Authentication**,
   **Kubernetes Auth**, and replace the **CA Certificate** with the output. The
   host and names stay the same.
4. Check that secrets sync with no authentication errors:

   ```bash
   kubectl get infisicalsecret -A
   ```

## 5. Restore the volumes

:::caution Not available yet
This is the Velero restore of the app volumes from R2. It runs after step 4,
because Velero's credentials come from Infisical. The commands are added once
tested.
:::

## 6. Bring the apps up in stages

:::caution Not available yet
`make recover` adds the `platform` stack, waits until it is healthy, then adds
`apps` and `ai`. Platform comes first because apps such as MCPHub read Pocket
ID's configuration at startup.
:::

## 7. Final checks

```bash
kubectl get nodes
kubectl -n argocd get app
kubectl get infisicalsecret -A
```

Expect every app `Synced` and `Healthy`, and no authentication errors.

## After recovery

- **Argo CD MCP token:** the rebuilt Argo CD has a new server key, so the old MCP
  token no longer works. Generate a new one, store it in Infisical under
  `platform`, `prod`, `/argocd`, key `ARGOCD_API_TOKEN`, and the MCP server
  reloads on its own.
- **Backup archive name:** if Infisical's database was restored into a new
  Cluster, set `backup.serverName` in `k8s/bootstrap/charts/infisical/values.yaml`
  to a fresh value, so the old archive is not overwritten. This step is
  confirmed when `make recover` is tested.
