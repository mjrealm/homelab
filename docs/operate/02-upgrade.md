# Upgrade or extend a live cluster

Use `make upgrade` to change a cluster that is already running. It is safe to
re-run. Nothing runs unless you choose a tag, so a typo cannot touch the whole
platform.

```bash
make upgrade TAGS=<tag>
```

| Tag | What it does | When |
|---|---|---|
| `root` | Re-applies the Argo CD AppProjects and ApplicationSets from `k8s/bootstrap/charts/root`. | You changed the root chart: a new stack, a new bootstrap app, or a changed sync option. |
| `argocd` | Re-applies the Argo CD chart with server-side apply. | An Argo CD change did not reach the cluster, or the repo-server is missing. |
| `aws-credentials` | Prompts for the AWS key and replaces the two Secrets that hold it. | You rotated the `homelab-infisical-bootstrap` IAM key. |

Every run ends with `PLAY RECAP`. Expect `failed=0`. `changed=0` means nothing
needed changing, which is fine.

`make apply-root` is the same as `make upgrade TAGS=root`.

## Add a new bootstrap app

1. Create the chart in `k8s/bootstrap/charts/<app>/`.
2. Add the app under `bootstrap:` in `k8s/bootstrap/charts/root/values.yaml`
   (name, namespace, project).
3. Merge the pull request.
4. Run:

   ```bash
   make upgrade TAGS=root
   ```

Argo CD then installs the chart. A new app that must exist before Argo CD can run
is different: it needs a role in `k8s/bootstrap/roles/` and a line in
`bootstrap.yml`, so a new cluster gets it too.

## Rotate the AWS bootstrap key

1. In AWS IAM, create a new access key for `homelab-infisical-bootstrap` and save
   it in Bitwarden.
2. Run:

   ```bash
   make upgrade TAGS=aws-credentials
   ```

3. Enter the new access key ID and secret from Bitwarden (`AWS IAM
   homelab-infisical-bootstrap`). Press Enter for `us-east-2`.
4. Check that both Secrets synced:

   ```bash
   kubectl get clustersecretstore,externalsecret -A
   kubectl -n infisical get cluster
   ```

   Expect the ClusterSecretStore `Valid`, the ExternalSecret `SecretSynced`, and
   the Cluster `Cluster in healthy state`.

5. Delete the old access key in AWS IAM.

## Repair Argo CD

If a change to Argo CD's own chart (`k8s/bootstrap/charts/argocd`) does not apply,
or the `argocd-repo-server` Deployment is missing, Argo CD cannot render
anything, so it cannot fix itself. Re-apply it from outside:

```bash
make upgrade TAGS=argocd
kubectl -n argocd get pods
```

Do not use `helm upgrade` for Argo CD. It fails on resources that Argo CD
now owns.

## Change k3s

k3s version and flags (for example OIDC settings) are not here. Edit them in
`metal/` and run:

```bash
make metal
```
