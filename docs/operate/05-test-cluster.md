# Try a change on a throwaway cluster

Use this to test the bootstrap playbook, the Infisical chart or the recovery
steps without touching the real cluster. It creates a small cluster inside Docker
on your Mac, runs the playbook against it, and deletes it. Nothing here can reach
the real cluster: the test uses its own kubeconfig file, and the test run refuses
any kubectl context that does not start with `k3d-`.

## What you need

- OrbStack running (`docker info` prints a version) and `k3d` installed. Both come
  from `make deps`. See [Set up your workstation](../prepare/01-workstation-setup.md).
- About 6 GB of free memory and 10 minutes.

## 1. Create the test cluster

1. In the Terminal, in the repo folder, run:

   ```bash
   make test-up
   ```

2. Expect about 30 seconds of output ending with
   `Ready. Context: k3d-homelab-test. Kubeconfig: .test/kubeconfig`. It creates a
   k3s cluster with the same version as production, a small S3 server that stands
   in for the AWS bucket, and random test keys in `.test/keys.yml`.

3. Your normal context is unchanged. Check:

   ```bash
   kubectl config current-context
   ```

   Expect `k3s-ansible`, not `k3d-homelab-test`.

## 2. Run the bootstrap on it

1. Run:

   ```bash
   make test-bootstrap
   ```

2. Wait about 5 minutes. It installs the same roles as `make bootstrap`, except
   Longhorn, Argo CD and the Let's Encrypt issuer, and with a fake store instead of
   AWS. It ends with `PLAY RECAP` and `failed=0`.

## 3. Look at the result

Point `kubectl` at the test cluster for this Terminal window only:

```bash
export KUBECONFIG="$PWD/.test/kubeconfig"
kubectl config current-context
```

Expect `k3d-homelab-test`. Then:

```bash
kubectl get clustersecretstore,externalsecret -A
kubectl -n infisical get cluster,pods
```

Expect the store `Valid`, the ExternalSecret `SecretSynced`, the Cluster
`Cluster in healthy state`, and all pods `Running`.

To check that backups reach the S3 server, take one and wait for it (about five
minutes):

```bash
kubectl apply -f - <<'YAML'
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: harness-check
  namespace: infisical
spec:
  cluster:
    name: infisical-database
  method: plugin
  pluginConfiguration:
    name: barman-cloud.cloudnative-pg.io
YAML
kubectl -n infisical get backup harness-check
```

Expect the phase to go from `started` to `completed`.

When you are done, switch this window back:

```bash
unset KUBECONFIG
kubectl config current-context
```

Expect `k3s-ansible`.

## 4. Delete everything

```bash
make test-down
```

Expect `Everything removed`. This deletes the test cluster, the S3 server and its
data, and `.test/`. To delete only the cluster and keep the S3 data and keys (for
a recovery test), run `test/cluster.sh cluster-down`.

## What the test does not cover

- Longhorn and the NAS backup target, and Velero volume restores. They need real
  nodes.
- Argo CD and the app stacks.
- Real Let's Encrypt certificates, AWS Systems Manager and the AWS S3 bucket.
- The browser steps in the recovery guide.

## If it fails

| Symptom | Fix |
|---|---|
| `Docker is not running` | Open OrbStack, wait for it to start, run the command again. |
| `Cluster homelab-test already exists` | Fine. It is reused. To start clean, run `make test-down` first. |
| `This run needs a kubectl context that starts with "k3d-"` | The test refused to run against the wrong cluster. Run `make test-up` and use `make test-bootstrap`, not a manual command. |
| `make test-bootstrap` fails and you re-run it | Run `make test-down`, then `make test-up`, then `make test-bootstrap`. The bootstrap is for a clean cluster. |
