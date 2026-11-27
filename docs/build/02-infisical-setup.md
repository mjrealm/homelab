# Infisical setup: projects, identities and the operator

Use this on a new cluster, or after a rebuild where Infisical started with an
empty database. It covers what the repo cannot create: the admin user, the
projects, and one machine identity per stack.

After a rebuild that restored Infisical from a backup, skip to
[After a restore](#after-a-restore).

Before you start:

- The cluster is installed ([Install the cluster](01-cluster-install.md)), so
  Infisical is running.
- `https://infisical.mdeleon.dev` loads.
- The four service accounts exist (created by the `infisical-operator` chart):

  ```bash
  kubectl get sa -n infisical-operator | grep infisical-
  ```

## One-time setup

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

## Adding an app's secrets

Repeat this for each app. The worked example is `convertx` (stack `apps`, secret
`JWT_SECRET`).

### 6. Put the secrets in Infisical

1. Open the stack's project, then **Secrets**.
2. Select the `prod` environment.
3. Create a folder named after the app: `convertx`.
4. Open the folder and add each key and value: `JWT_SECRET`.

### 7. Add the InfisicalSecret to the app

1. Create `k8s/<stack>/<app>/templates/infisicalsecret.yaml`.
2. Fill in the app, the stack and its identity ID from the table above.

   Example, `k8s/apps/convertx/templates/infisicalsecret.yaml`:

   ```yaml
   apiVersion: secrets.infisical.com/v1alpha1
   kind: InfisicalSecret
   metadata:
     name: convertx
   spec:
     hostAPI: http://infisical-infisical-standalone-infisical.infisical.svc.cluster.local:8080/api
     syncConfig:
       resyncInterval: 60s
     authentication:
       kubernetesAuth:
         identityId: fefa3b53-6b57-4b79-a20a-e7a9db8c00bf
         autoCreateServiceAccountToken: true
         serviceAccountRef:
           name: infisical-apps
           namespace: infisical-operator
         secretsScope:
           projectSlug: apps
           envSlug: prod
           secretsPath: /convertx
           recursive: false
     managedKubeSecretReferences:
       - secretName: convertx-secrets
         secretNamespace: {{ .Release.Namespace }}
         creationPolicy: Owner
   ```

   What to change per app:

   - `metadata.name` and `secretsPath`: the app name.
   - `identityId`, `serviceAccountRef.name` and `projectSlug`: the stack's row.
   - `secretName`: `<app>-secrets`.

### 8. Point the app at the Secret

1. In `values.yaml`, load the Secret into the container with `envFrom`, and add
   the auto-reload annotation to the controller.

   Example, `k8s/apps/convertx/values.yaml`:

   ```yaml
   app-template:
     controllers:
       convertx:
         annotations:
           secrets.infisical.com/auto-reload: "true"
         containers:
           convertx:
             envFrom:
               - secretRef:
                   name: convertx-secrets
   ```

2. Keep the ingress and other non-secret values in `values.yaml`.

### 9. Check it

1. Merge the PR, after the keys exist in Infisical. Otherwise the pod waits in
   `CreateContainerConfigError`.
2. Check the sync:

   ```bash
   kubectl get infisicalsecret,secret -n convertx
   kubectl get pods -n convertx
   ```

3. Expect the `InfisicalSecret` to be healthy, `convertx-secrets` to exist, and
   the pod to be Running.
4. To test a reload, change a value in Infisical and wait for the resync
   interval (60s). The pod restarts.

Instant updates is an Enterprise feature, so a changed value reaches the pod
after the resync interval, not at once.

## After a restore

The database already holds the admin, projects, identities and secrets. Only the
cluster CA changes.

1. Log in with the admin from Bitwarden.
2. Get the new CA, because a rebuilt k3s cluster has a new one:

   ```bash
   kubectl get cm kube-root-ca.crt -n default -o jsonpath='{.data.ca\.crt}'
   ```

3. For each of the four identities, edit **Kubernetes Auth** and replace the
   **CA Certificate**. The host and names stay the same.
4. Check that secrets sync with no authentication errors:

   ```bash
   kubectl get infisicalsecret -A
   ```

## If authentication fails

1. Check the `infisical-operator` pod logs.
2. Check the status of the resource:

   ```bash
   kubectl describe infisicalsecret <app> -n <app>
   ```

3. After fixing the cause, wait 1-2 minutes. The operator backs off between
   retries, so the old error stays visible until the next one.
4. Match the symptom:

   | Symptom | Cause |
   |---|---|
   | Authentication or `403` error | The CA certificate is stale, or the allowed service account name or namespace does not match `infisical-<stack>` and `infisical-operator`. |
   | A token review error | The service account is missing its `system:auth-delegator` binding. |
   | `Project with slug '<stack>' not found` | The project still has its generated slug (step 2), or the identity is not added to the project (step 5). |
   | Other project or secret not found | Wrong `envSlug` or `secretsPath`, or the key is missing in Infisical. |
   | The Secret is empty | The folder name does not match `secretsPath`. |

If an empty Token Reviewer JWT does not work, use a dedicated reviewer service
account with a long-lived token. Follow the "Manual long-lived service account
tokens" steps in Infisical's `InfisicalSecret` documentation, and paste that
token into **Token Reviewer JWT**.
