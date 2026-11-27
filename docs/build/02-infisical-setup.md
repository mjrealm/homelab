# Set up Infisical (one time)

Do this once, on a new cluster, after [Install the cluster](01-cluster-install.md).
Infisical starts with an empty database, and this covers what the repo cannot
create: the admin user, the four projects, and one machine identity per stack.

This page is only for a new cluster. After a disaster, use
[Recover the cluster](../recover/01-recover-the-cluster.md) instead. To add an
app's secrets later, use [Add an app's secrets](../operate/03-add-app-secrets.md).

Before you start:

- The cluster is installed, so Infisical is running.
- `https://infisical.mdeleon.dev` loads.
- The four service accounts exist (created by the `infisical-operator` chart):

  ```bash
  kubectl get sa -n infisical-operator | grep infisical-
  ```

## Steps

### 1. Create the admin

1. Open `https://infisical.mdeleon.dev`.
2. Sign up. The first account becomes the admin, so do this straight away.
3. Save the email and password in Bitwarden as "Infisical admin".

### 2. Create the four projects

Do this for `apps`, `platform`, `system` and `ai`:

1. Create a **Secret Management** project.
2. Set **Project name** to the stack name.
3. Open **Project Settings**, **General**. Infisical generates a random slug
   such as `apps-3-vp6`. Set **Project Slug** to the stack name and save.
4. Check that the slug now equals the stack name. The `InfisicalSecret` files
   use `projectSlug: <stack>`.
5. In **Project Settings**, delete the `dev` and `staging` environments.
6. Check that the remaining environment has the slug `prod`.

A project is the only access boundary. Folder-level permissions are paid, so
never put two stacks in one project.

### 3. Get the cluster CA certificate

1. Run:

   ```bash
   kubectl get cm kube-root-ca.crt -n default -o jsonpath='{.data.ca\.crt}'
   ```

2. Copy the whole output, including the `BEGIN` and `END` lines.

### 4. Create one machine identity per stack

Do this for each stack:

1. Go to **Organization**, **Access Control**, **Machine Identities**,
   **Create**.
2. Set **Name** to `infisical-<stack>` and **Role** to `Member`.
3. Open the new identity and edit **Authentication**.
4. Remove **Universal Auth**.
5. Add **Kubernetes Auth** with these values:

   | Field | Value |
   |---|---|
   | Kubernetes Host | `https://kubernetes.default.svc` |
   | Token Reviewer JWT | leave empty |
   | Allowed Service Account Names | `infisical-<stack>` |
   | Allowed Namespaces | `infisical-operator` |
   | Allowed Audience | leave empty |
   | CA Certificate | the PEM from step 3 |
   | Access Token TTL, Max TTL | defaults |

6. Copy the **Identity ID** from the top of the identity's page, and write it in
   the table below.

With the reviewer JWT empty, Infisical validates the pod's own token. That works
because each service account is bound to `system:auth-delegator`.

Identity IDs are not secrets. Keep them current here. They end up in each app's
`InfisicalSecret`.

| Stack | Identity | Identity ID |
|---|---|---|
| `apps` | `infisical-apps` | `fefa3b53-6b57-4b79-a20a-e7a9db8c00bf` |
| `platform` | `infisical-platform` | `e2ccd552-d832-493d-8ca4-205f4e8c3f08` |
| `system` | `infisical-system` | `b80ad456-f091-4fdc-9477-518d2b3852e8` |
| `ai` | `infisical-ai` | `e884d4d2-4998-4abe-b7fa-813b2b410f69` |

If you recreate an identity, its ID changes. Search the repo for the old ID and
replace it.

### 5. Add each identity to its project

Do this for each stack:

1. Open the project.
2. Go to **Access Control**, **Machine Identities**, **Add Machine Identity to
   Project**, **Assign Existing**.
3. Pick `infisical-<stack>` with the project role **Viewer**.

Viewer is enough, because the operator only reads secrets.

## Check it

1. Open each project and confirm its slug equals the stack name and the only
   environment is `prod`.
2. Confirm each identity is listed under the project's **Access Control**, with
   the **Viewer** role.
3. Keep the four identity IDs from step 4. Every app's `InfisicalSecret` uses them.

Next: add the first app's secrets, in [Add an app's secrets](../operate/03-add-app-secrets.md).
