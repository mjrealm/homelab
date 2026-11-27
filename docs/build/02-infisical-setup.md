# Set up Infisical (one time)

Do this once, on a new cluster, after [Install the cluster](01-cluster-install.md).
Infisical starts with an empty database, and this page covers what the repo
cannot create: the admin user, one project and one machine identity per stack,
the identity IDs in the repo, and an admin identity for disaster recovery. It
takes about 45 minutes in the browser, plus one pull request.

This page is only for a new cluster. After a disaster, use
[Recover the cluster](../recover/01-recover-the-cluster.md) instead. To add an
app's secrets later, use [Add an app's secrets](../operate/03-add-app-secrets.md).

Before you start, check in the Terminal:

1. The cluster is installed and Infisical is running:

   ```bash
   kubectl get pods -n infisical
   ```

   Expect every pod `Running`.

2. One service account per stack exists (the `infisical-operator` chart creates
   them):

   ```bash
   kubectl get sa -n infisical-operator | grep infisical-
   ```

   Expect `infisical-ai`, `infisical-apps`, `infisical-platform` and
   `infisical-system`.

3. <https://infisical.mdeleon.dev> loads in the browser. If not, wait five
   minutes for MetalLB and DNS, then retry.

## 1. Create the admin

1. Open <https://infisical.mdeleon.dev>.
2. Sign up with your email address and a strong password. The first account
   becomes the admin, so do this straight away.
3. In Bitwarden, create an item `Infisical admin` in the folder
   `homelab-infisical-bootstrap`, with the email and password.
4. Skip any "invite your team" or onboarding screens.

## 2. Create a project for each stack

Do the steps below once for each of `apps`, `platform`, `system` and `ai`:

1. In the left sidebar choose **Projects**, then **Add New Project**, and pick
   **Secret Management**.
2. Set **Project name** to the stack name (for example `apps`), then **Create
   Project**.
3. Open **Project Settings**, **General**. Infisical generated a random slug such
   as `apps-3-vp6`. Set **Project Slug** to the stack name and click **Save**.
4. Check that the slug now equals the stack name. Every `InfisicalSecret` file in
   the repo uses `projectSlug: <stack>`.
5. In **Project Settings**, open **Environments** and delete `dev` and `staging`.
6. Check that the one remaining environment has the slug `prod`.

A project is the only access boundary. Folder-level permissions are paid, so
never put two stacks in one project.

## 3. Get the cluster CA certificate

1. In the Terminal, run:

   ```bash
   kubectl get cm kube-root-ca.crt -n default -o jsonpath='{.data.ca\.crt}'
   ```

2. Select and copy the whole output, from `-----BEGIN CERTIFICATE-----` to
   `-----END CERTIFICATE-----`. You paste it once for each identity in step 4.

## 4. Create one machine identity per stack

Do the steps below once for each stack (`apps`, `platform`, `system`, `ai`):

1. Go to **Organization** (the building icon at the top of the sidebar), **Access
   Control**, **Machine Identities**, **Create Identity**.
2. Set **Name** to `infisical-<stack>` (for example `infisical-apps`) and **Role**
   to `Member`. Click **Create**.
3. Open the new identity and click **Authentication**.
4. If **Universal Auth** is listed, remove it.
5. Add **Kubernetes Auth** with these values:

   | Field | Value |
   |---|---|
   | Kubernetes Host | `https://kubernetes.default.svc` |
   | Token Reviewer JWT | leave empty |
   | Allowed Service Account Names | `infisical-<stack>` |
   | Allowed Namespaces | `infisical-operator` |
   | Allowed Audience | leave empty |
   | CA Certificate | the PEM from step 3 |
   | Access Token TTL, Max TTL | leave the defaults |

6. Click **Add**. Copy the **Identity ID** from the top of the identity's page and
   keep it for step 5.

With the reviewer JWT empty, Infisical validates the pod's own token. That works
because each service account is bound to `system:auth-delegator`.

## 5. Add each identity to its project

Do this for each stack:

1. Open the project (`apps`, for example).
2. Go to **Access Control**, **Machine Identities**, **Add Machine Identity to
   Project**, **Assign Existing**.
3. Pick `infisical-<stack>` and give it the project role **Viewer**, then **Add**.

Viewer is enough, because the operator only reads secrets.

## 6. Put the new identity IDs in the repo

A new identity has a new ID, and every `InfisicalSecret` in the repo contains its
stack's ID. Replace the old IDs with the new ones.

1. In the Terminal, in the repo folder, create a branch:

   ```bash
   git checkout main && git pull
   git checkout -b chore/infisical-identity-ids
   ```

2. For each stack, run the block below with that stack's old and new ID. The
   current old IDs are:

   | Stack | Old identity ID |
   |---|---|
   | `apps` | `fefa3b53-6b57-4b79-a20a-e7a9db8c00bf` |
   | `platform` | `e2ccd552-d832-493d-8ca4-205f4e8c3f08` |
   | `system` | `b80ad456-f091-4fdc-9477-518d2b3852e8` |
   | `ai` | `e884d4d2-4998-4abe-b7fa-813b2b410f69` |

   ```bash
   OLD=fefa3b53-6b57-4b79-a20a-e7a9db8c00bf
   NEW=<paste the new identity ID>
   grep -rl "$OLD" k8s docs scripts | xargs sed -i '' "s/$OLD/$NEW/g"
   ```

   Repeat with the next stack's `OLD` and `NEW`.

3. For each stack, check that its old ID is gone. Set `OLD` to that stack's old
   ID again and run:

   ```bash
   grep -rn "$OLD" k8s docs scripts
   ```

   Expect no output. Then commit, push and open a pull request:

   ```bash
   git add -A
   git commit -m "chore(infisical): new machine identity IDs"
   git push -u origin HEAD
   gh pr create --fill
   ```

   Merge the pull request on GitHub. The replacement also updates the ID tables
   in these docs and the list in `scripts/infisicalsecret/stacks.yml`, so the
   `make infisicalsecret` command and the docs stay correct.

4. After Argo CD syncs (about five minutes), the secrets show as synced. They
   stay empty or failing until you add each app's keys
   ([Add an app's secrets](../operate/03-add-app-secrets.md)).

## 7. Create the disaster-recovery admin identity

This identity lets a person who is rebuilding the cluster fix Infisical without
the browser login. It lives in Infisical's database, so the backups cover it.

1. In the browser, go to **Organization**, **Access Control**, **Machine
   Identities**, **Create Identity**.
2. Set **Name** to `dr-admin` and **Role** to `Admin`. Click **Create**.
3. Open it, click **Authentication**, **Add Auth Method**, and choose **Universal
   Auth**.
4. Set **Access Token TTL** and **Max TTL** to `3600`, **Access Token Max Number
   of Uses** to `0`, leave the trusted IPs at `0.0.0.0/0`, and click **Add**.
5. Copy the **Client ID** from the identity page.
6. Under **Client Secrets**, click **Create**. Set **TTL** to `0` (never expires)
   and **Number of uses** to `0` (unlimited). Copy the **Client Secret** now. It
   is shown once.
7. In Bitwarden, create an item `Infisical dr-admin` in the folder
   `homelab-infisical-bootstrap` with the client ID and the client secret.
8. Test it. This prints `ok` and no secret:

   ```bash
   read -r "CID?Client ID: "; read -rs "CSEC?Client secret: "; echo
   curl -s -X POST https://infisical.mdeleon.dev/api/v1/auth/universal-auth/login \
     -H 'Content-Type: application/json' \
     -d "{\"clientId\":\"$CID\",\"clientSecret\":\"$CSEC\"}" \
     | python3 -c "import json,sys;d=json.load(sys.stdin);print('ok' if 'accessToken' in d else d)"
   unset CID CSEC
   ```

   Paste the client ID, press Enter, paste the secret, press Enter. Expect `ok`.

## 8. Check it

1. Every `InfisicalSecret` is ready:

   ```bash
   kubectl get infisicalsecret -A -o 'custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,READY:.status.conditions[0].status,REASON:.status.conditions[0].reason'
   ```

   Expect `READY` to be `True` and `REASON` `OK` once an app's keys exist. A row
   with an authentication error means that stack's identity is wrong. See
   [Fix Infisical authentication errors](../operate/04-infisical-auth-errors.md).

2. Infisical's database backs up daily to S3. Check the schedule and the latest
   backup:

   ```bash
   kubectl -n infisical get scheduledbackup
   kubectl -n infisical get backups.postgresql.cnpg.io
   ```

   Expect the `infisical-daily` schedule, and after 03:00 UTC the next day a
   backup with the phase `completed`. A new cluster has no backup until then.

3. Bitwarden has `Infisical admin` and `Infisical dr-admin` in the folder
   `homelab-infisical-bootstrap`.

Next: add the first app's secrets, in [Add an app's secrets](../operate/03-add-app-secrets.md).
