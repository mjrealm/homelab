# Recover the cluster (disaster recovery)

Use this when the cluster is gone or unusable and you are rebuilding it from
backups: lost nodes, wiped disks, a failed upgrade you cannot roll back. It is the
whole procedure from the first command to the last check. Follow it top to bottom
and do not skip steps. You do not need to know how the cluster works.

Do not use it on a cluster that still works. To change a running cluster, use
[Which playbook do I run?](../operate/01-overview.md).

:::danger Read this first: what is tested
- **Tested:** steps 3 and 4 (`make recover` restores Infisical from its backup, then
  `make recover-ca` points it at the new cluster) run end to end on a throwaway
  cluster with `make test-dr`. That test does not cover real nodes, Longhorn, the NAS,
  Velero or Argo CD.
- **Untested:** steps 5, 6 and 7 are written from the repository's configuration.
  Read each step's expected result, and stop when reality differs from the page.

Volume data (step 6) needs the NAS to be on and reachable from the nodes.
:::

## What you need

Collect these before you start. All are in Bitwarden, folder
`homelab-infisical-bootstrap`.

| Item | Bitwarden item |
|---|---|
| Sudo password for the nodes | `Node sudo password` |
| Cloudflare DNS token | `Cloudflare DNS API token (cert-manager)` |
| AWS access key ID and secret | `AWS IAM homelab-infisical-bootstrap` |
| Infisical admin login | `Infisical admin` |
| Infisical `dr-admin` client ID and secret (`make recover-ca`, step 4) | `Infisical dr-admin` |

You also need:

- A Mac set up as in [Set up your workstation](../prepare/01-workstation-setup.md),
  with the repo cloned.
- The nodes powered on, reachable by SSH, running Ubuntu or Debian, with
  the admin user set as `ansible_user` in `metal/group_vars/all.yml`, with sudo. The nodes are listed in `metal/inventory/main.yml`.

You do **not** need to type or find: Infisical's `ENCRYPTION_KEY`, `AUTH_SECRET`
and `REDIS_PASSWORD` (read from AWS Systems Manager automatically), and every app
secret (restored with Infisical's database from the S3 backup).

## The steps

| # | Step | Time | Status |
|---|---|---|---|
| 1 | Get the repo ready | 2 min | works |
| 2 | Rebuild the nodes and k3s | 15 min | works |
| 3 | Restore Infisical and the platform | 45 min | tested on a throwaway cluster; not with Argo CD |
| 4 | Point Infisical at the new cluster | 20 min | tested on a throwaway cluster |
| 5 | Check the platform | 10 min | untested |
| 6 | Restore the volumes | 1 to 3 hours | untested |
| 7 | Bring the apps up | 30 min | untested |
| 8 | Regenerate the Argo CD MCP token | 10 min | web UI steps written, not yet run on a rebuilt cluster |
| 9 | Final checks | 5 min | works |

## 1. Get the repo ready

1. In the Terminal, in the `homelab` folder, run:

   ```bash
   git checkout main
   git pull
   git status --short
   ```

2. Expect no output from `git status --short`. If it lists files, you have local
   changes. Stash them with `git stash` unless you know why they are there.

## 2. Rebuild the nodes and k3s

1. Run:

   ```bash
   make metal
   ```

2. If a node rejects your SSH key, type `y` at the `ssh-copy-id` question and
   enter that node's login password.
3. At `BECOME password:`, enter the sudo password.
4. Wait about 10 minutes. The play also installs `open-iscsi` and `nfs-common` on
   every node, which Longhorn needs. At the end it asks `Enter Cloudflare API
   Key (sensitive)`. Paste the Cloudflare DNS token and press Enter.
5. Expect `PLAY RECAP` with `failed=0` for every host. Then check:

   ```bash
   kubectl config current-context
   kubectl get nodes
   ```

6. Expect the context `k3s-ansible` and every node in `metal/inventory/main.yml`
   listed and `Ready`, with one node having the roles `control-plane,etcd`. If a node is `NotReady`, wait two minutes and
   check again.

## 3. Restore Infisical and the platform

Infisical's database is restored from the daily backup in S3. Argo CD manages the
Infisical chart from Git, so the restore settings must be merged to `main` **before**
you run `make recover`. Otherwise Argo CD would later undo the restore. `make
recover` checks this and stops if `main` does not have them.

1. Create a branch:

   ```bash
   git checkout -b fix/disaster-recovery
   ```

2. Open `k8s/bootstrap/charts/infisical/values.yaml`. Find the `backup:` and
   `recovery:` blocks. Make exactly these two edits:

   - In `backup:`, change `serverName: infisical-database` to
     `serverName: infisical-database-r1`. This is the name the new cluster writes
     its backups under, so the old archive is never overwritten. If
     `infisical-database-r1` was used by an earlier recovery, use `-r2`, `-r3`.
   - In `recovery:`, change `enabled: false` to `enabled: true`. Leave
     `sourceServerName: infisical-database` as it is: it is the archive to
     restore from.

3. Commit, push and open the pull request. **Merge it on GitHub**, then update
   your copy:

   ```bash
   git add k8s/bootstrap/charts/infisical/values.yaml
   git commit -m "fix(infisical): restore from backup after disaster"
   git push -u origin HEAD
   gh pr create --fill
   # merge the pull request on GitHub, then:
   git checkout main
   git pull
   ```

4. Run:

   ```bash
   make recover
   ```

5. It prints a box starting `=== RECOVER, rebuilt cluster only ===` and the
   `context:` and `server:` of the cluster. Check them, then type `y`. It stops
   before any prompt if the cluster already has Argo CD, Infisical or cert-manager.
6. Enter the AWS values from Bitwarden when asked: the key ID, the secret, and press
   Enter for `us-east-2`. Wait about 30 minutes. It installs the platform, restores
   Infisical, installs Argo CD, and starts **only the `system` stack**, so apps do not
   start before their data is restored. It ends with `PLAY RECAP` and `failed=0`.
7. Check that Infisical restored from the backup, not from scratch:

   ```bash
   kubectl -n infisical get cluster
   kubectl -n infisical get pods
   ```

   Expect `Cluster in healthy state` and all pods `Running`. Then check which
   database Infisical uses:

   ```bash
   kubectl -n infisical get secret infisical-database-app -o jsonpath='{.data.dbname}' | base64 -d; echo
   ```

   Expect `infisical`. If it prints `app`, the restored data is in a different
   database than the one Infisical reads, and Infisical will start empty. **Stop
   here.** The `recovery` block in
   `k8s/bootstrap/charts/infisical/templates/database.yaml` must name
   `database: infisical`.

   Then open <https://infisical.mdeleon.dev> (it works once Argo CD has installed
   MetalLB, about five minutes after the playbook ends) and log in with
   `Infisical admin`. Expect to see one project for each stack, with its secrets.

   If the page asks you to create a new admin account, the restore did not
   happen and Infisical started empty. **Stop here. Do not create an account.**
   Run these two commands and keep the output for the owner:

   ```bash
   kubectl -n infisical describe cluster infisical-database | tail -40
   kubectl -n infisical get pods
   ```

## 4. Point Infisical at the new cluster

A rebuilt cluster has a new certificate authority. Infisical must learn it, or
every `InfisicalSecret` fails with an authentication error. The database already
holds the admin, projects, identities and secrets.

1. In the Terminal, run:

   ```bash
   make recover-ca
   ```

2. It prints the `kubectl context` and `API server`. Check them, then type `y`. When
   asked, enter the `dr-admin client ID`, then the `dr-admin client secret` (hidden),
   from Bitwarden item `Infisical dr-admin`.
3. It waits for <https://infisical.mdeleon.dev> to answer, up to 15 minutes (it needs
   MetalLB and Traefik from the `system` stack). Then it prints one line for each
   stack and ends with `CA FIXED`:

   ```text
   updated apps (<identity id>)
   updated platform (<identity id>)
   updated system (<identity id>)
   updated ai (<identity id>)
   ```

   A `FAILED` line names the stack and the reason. A `login failed` line means the
   client ID or secret is wrong.
4. Check that secrets sync. Wait two minutes, then run:

   ```bash
   kubectl get infisicalsecret -A -o 'custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,READY:.status.conditions[0].status,REASON:.status.conditions[0].reason'
   ```

   Expect `READY` `True` and `REASON` `OK` for every row of the `system` stack
   (for example `velero`). Rows of other stacks do not exist yet.

If a row shows an authentication error after five minutes, use
[Fix Infisical authentication errors](../operate/04-infisical-auth-errors.md).

### By hand in the browser (fallback)

Use this if `make recover-ca` cannot run. Log in to <https://infisical.mdeleon.dev>
with `Infisical admin`, then:

1. In the Terminal, print the new CA and copy the whole output, from
   `-----BEGIN CERTIFICATE-----` to `-----END CERTIFICATE-----`:

   ```bash
   kubectl get cm kube-root-ca.crt -n default -o 'jsonpath={.data.ca\.crt}'
   ```

2. For each stack identity (`infisical-apps`, `infisical-platform`,
   `infisical-system`, `infisical-ai`):

   1. Click **Organization** (the building icon at the top of the sidebar), then
      **Access Control**, then **Machine Identities**.
   2. Click the identity.
   3. Click **Authentication**, then the pencil icon next to **Kubernetes Auth**.
   4. Delete the text in **CA Certificate** and paste the new CA.
   5. Click **Save**. Leave every other field as it is.

## 5. Check the platform

```bash
kubectl -n argocd get app
kubectl get pods -A | grep -v -E 'Running|Completed'
```

Expect the `system` apps `Synced` and `Healthy`, including `velero`, `metallb`
and `longhorn-system`. The second command lists pods that are not running. Wait
five minutes and run it again; it should print only the header line.

## 6. Restore the volumes

Two backups work together here, so know which holds what:

- **Velero** (Cloudflare R2 bucket `homelab-backups`) holds the Kubernetes
  objects and a reference to each volume's backup. It holds no volume data.
- **Longhorn** backups on the NAS hold the volume data. The NAS is the long-term
  copy, kept under its own 3-2-1 backup.

A Velero restore creates each volume from its Longhorn backup, so the NAS must be
reachable first.

1. Check that Longhorn can see the NAS backup target:

   ```bash
   kubectl -n longhorn-system get backuptargets.longhorn.io
   ```

   Expect one row, `default`, with a URL that starts with `nfs://` and
   `AVAILABLE` `true`. The URL comes from
   `defaultBackupStore.backupTarget` in
   `k8s/bootstrap/charts/longhorn-system/values.yaml`.

   If `AVAILABLE` is `false` or empty, check, in this order: the NAS is powered
   on and on the network; the nodes can reach it; each node has the packages
   `nfs-common` and `open-iscsi` (`make metal` installs them):

   ```bash
   ssh <ansible_user>@<node> 'dpkg -s nfs-common open-iscsi | grep -E "Package|Status"'
   ```

   Do not continue until `AVAILABLE` is `true`.

2. Wait until Longhorn has read the backups from the NAS:

   ```bash
   kubectl -n longhorn-system get backupvolumes.longhorn.io --no-headers | wc -l
   ```

   Expect a number above zero. If it is `0`,
   wait two minutes and run it again.

3. List the available backups. Velero reads them from the Cloudflare R2 bucket
   `homelab-backups`:

   ```bash
   velero backup get
   ```

   Expect a list such as `velero-daily-backup-20261126030154  Completed`. The
   `velero-biweekly-backup-*` backups include every namespace. The
   `velero-daily-backup-*` backups include only `paperless-ngx`, `immich`,
   `mealie`, `hermes`, `hindsight`, `outline` and `infisical`. If the list is
   empty, wait two minutes for Velero to sync the bucket and run it again.

4. Pick the newest `Completed` backup with the namespaces you need, and restore
   it. Replace `<backup-name>`:

   ```bash
   velero restore create --from-backup <backup-name> --include-namespaces paperless-ngx,immich,mealie,hermes,hindsight,outline
   ```

   Do not include `infisical` (it was already restored in step 3), `argocd`, or
   any `system` namespace.

5. Watch the restore until the phase is `Completed`:

   ```bash
   velero restore get
   ```

6. Check the volumes are bound. Large volumes take time to restore from the NAS,
   so this can take an hour:

   ```bash
   kubectl get pvc -A | grep -v Bound
   ```

   Expect only the header line. Also check that Longhorn reports the volumes
   healthy:

   ```bash
   kubectl -n longhorn-system get volumes.longhorn.io
   ```

   Expect the `ROBUSTNESS` column to say `healthy` for attached volumes.

## 7. Bring the apps up

Apps start when Argo CD sees their stack. Add the stacks one at a time, and wait for
each to become healthy before adding the next. Platform comes first because apps
such as MCPHub read Pocket ID's configuration when they start.

1. Add the `platform` stack:

   ```bash
   make recover-stage STAGE=platform
   kubectl -n argocd get app
   ```

   Run the `get app` command every few minutes. Continue when every app is
   `Synced` and `Healthy`. This can take 15 minutes.

2. Add every other stack:

   ```bash
   make recover-stage STAGE=all
   kubectl -n argocd get app
   ```

3. Wait until every app is `Synced` and `Healthy`. Some apps stay `Progressing`
   until their keys exist in Infisical. Check with:

   ```bash
   kubectl -n argocd get app | grep -v -E 'Synced +Healthy'
   ```

   Expect only the header line when everything is healthy.

## 8. Regenerate the Argo CD MCP token

The Argo CD MCP server logs in to Argo CD with an API token. The rebuilt Argo CD
has a new signing key, so the old token no longer works. Make a new one and put
it in Infisical. Skip this step if you do not use the MCP server. The pod will
keep failing to authenticate until you do.

### In the web UI

1. Get the Argo CD admin password:

   ```bash
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
   ```

   Copy the output. (It is also in Bitwarden as `Argo CD admin (initial)`, but a
   rebuilt cluster has a new one.)

2. Open <https://argo.mdeleon.dev> and log in with the username `admin` and that
   password.
3. In the left sidebar click the gear icon, **Settings**, then **Accounts**.
4. Click the non-`admin` account that has the **apiKey** capability (the account named under `accounts.` in `k8s/bootstrap/charts/argocd/values.yaml`, which also has the `role:admin` role).
5. Under **Tokens**, click **Generate New**. Leave **Expires in** empty so the
   token never expires, then confirm.
6. Copy the token that appears. It is shown once.
7. Open <https://infisical.mdeleon.dev> and log in with `Infisical admin`.
8. Open the project `platform`, click **Secrets**, select the `prod`
   environment, and open the folder `argocd`.
9. Click the secret `ARGOCD_API_TOKEN`, replace its value with the new token, and
   click **Save**.
10. Wait one minute. The operator syncs the value and restarts the MCP server.
    Check it:

    ```bash
    kubectl -n argocd get pods | grep mcp
    kubectl -n argocd logs deploy/argocd-mcp-server --tail=20
    ```

    Expect a pod with an age of a few minutes and no `401` or `Unauthorized` in
    the log.

### With the command line

The same, without the browser for steps 2 to 6.

1. In one Terminal window, open a tunnel to Argo CD and leave it running:

   ```bash
   kubectl -n argocd port-forward --address 127.0.0.1 svc/argocd-server 8081:80
   ```

2. In a second window, log in with the admin password from step 1 above:

   ```bash
   argocd login 127.0.0.1:8081 --plaintext --grpc-web --username admin
   ```

   Enter the password when asked. Expect `'admin:login' logged in successfully`.
   If you see `connection reset by peer` or `connection refused`, stop the tunnel
   and use the web UI instructions instead.

3. Create the token and copy it. Replace `<account>` with the account named under `accounts.` in `k8s/bootstrap/charts/argocd/values.yaml` (not `admin`):

   ```bash
   argocd account generate-token --account <account> --id mcp --grpc-web
   ```

4. Do steps 7 to 10 of the web UI instructions above to store it in Infisical.
5. Log out and stop the tunnel (Ctrl+C in the first window):

   ```bash
   argocd logout 127.0.0.1:8081
   ```

## 9. Final checks

Run these three commands:

```bash
kubectl get nodes
kubectl -n argocd get app
kubectl get infisicalsecret -A -o 'custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,READY:.status.conditions[0].status,REASON:.status.conditions[0].reason'
```

Expect every node `Ready`, every app `Synced` and `Healthy`, and every
`InfisicalSecret` with `READY` `True`. Then open <https://infisical.mdeleon.dev>
and <https://argo.mdeleon.dev> and log in to confirm.

When everything is healthy, tell the owner which steps behaved differently from
this page. Each difference is a fix to make here.
