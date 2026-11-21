# Infisical setup: projects, identities and the operator

Follow this on a new cluster, or after a rebuild where Infisical started with an
empty database. It sets up everything inside Infisical that the repo cannot
create: the admin user, the projects, and one machine identity per stack.

After a rebuild that restored Infisical from a backup, the admin, projects,
identities and secrets are already there. Skip to
[After a restore](#after-a-restore).

Prerequisite: the bootstrap stack is installed (`make bootstrap-infisical`) and
`https://infisical.mdeleon.dev` loads.

The service accounts `infisical-apps`, `infisical-platform`, `infisical-system`
and `infisical-ai` are created by the `infisical-operator` chart in the
`infisical-operator` namespace. Check they exist:

```bash
kubectl get sa -n infisical-operator | grep infisical-
```

## 1. Create the admin

Open `https://infisical.mdeleon.dev` and sign up. The first account becomes the
admin, so do this straight away. Save the email and password in Bitwarden under
"Infisical admin".

## 2. Create the four projects

For each of `apps`, `platform`, `system` and `ai`, create a **Secret
Management** project:

- **Project name:** the stack name.
- Keep the project slug equal to the name. The operator uses the slug.
- Keep the **Production** environment with slug `prod`. Delete or ignore the
  others.

A project is the only access boundary. Folder-level permissions are paid, so
never put two stacks in one project.

## 3. Get the cluster CA certificate

```bash
kubectl get cm kube-root-ca.crt -n default -o jsonpath='{.data.ca\.crt}'
```

Copy the whole output, including the `BEGIN` and `END` lines.

## 4. Create one machine identity per stack

Go to **Organization**, **Access Control**, **Machine Identities**, **Create**.
Do this four times:

- **Name:** `infisical-apps`, `infisical-platform`, `infisical-system`,
  `infisical-ai`.
- **Role:** Member. It only covers organization-level resources. Project access
  is set in step 5.

Each new identity starts with Universal Auth. Edit **Authentication**, remove
Universal Auth, and add **Kubernetes Auth**:

| Field | Value |
|---|---|
| Kubernetes Host / Base Kubernetes API URL | `https://kubernetes.default.svc` |
| Token Reviewer JWT | leave empty |
| Allowed Service Account Names | `infisical-apps` (match the identity) |
| Allowed Namespaces | `infisical-operator` |
| Allowed Audience | leave empty |
| CA Certificate | the PEM from step 3 (this turns on TLS verification) |
| Access Token TTL, Max TTL | defaults |

With the reviewer JWT empty, Infisical validates the pod's own token. That works
because each service account is bound to `system:auth-delegator`. Infisical runs
inside the cluster, so the in-cluster API address is correct.

Copy each **Identity ID**. They are not secrets. You need them in step 7.

## 5. Add each identity to its project

For each stack, open the project, then **Access Control**, **Machine
Identities**, **Add Machine Identity to Project**, **Assign Existing**:

| Project | Identity | Project role |
|---|---|---|
| `apps` | `infisical-apps` | Viewer |
| `platform` | `infisical-platform` | Viewer |
| `system` | `infisical-system` | Viewer |
| `ai` | `infisical-ai` | Viewer |

Viewer is enough: the operator only reads secrets.

## 6. Create a folder per app and add the secrets

In a project, open **Secrets**, choose the `prod` environment, and create a
folder named after the app (for example `upsnap`). Add the app's secrets inside
it as key and value pairs. Folder path in the CRD is `/<app>`.

## 7. Per app: the InfisicalSecret

Each app's chart gets a `templates/infisicalsecret.yaml`. Replace the angle
brackets. The service address below is the in-cluster Infisical backend.

```yaml
apiVersion: secrets.infisical.com/v1alpha1
kind: InfisicalSecret
metadata:
  name: <app>
spec:
  hostAPI: http://infisical-infisical-standalone-infisical.infisical.svc.cluster.local:8080/api
  syncConfig:
    resyncInterval: 60s
  authentication:
    kubernetesAuth:
      identityId: <identity id of the stack>
      autoCreateServiceAccountToken: true
      serviceAccountRef:
        name: infisical-<stack>
        namespace: infisical-operator
      secretsScope:
        projectSlug: <stack>
        envSlug: prod
        secretsPath: /<app>
        recursive: false
  managedKubeSecretReferences:
    - secretName: <app>-secrets
      secretNamespace: <app>
      creationPolicy: Owner
```

Then point the app at `<app>-secrets` with `envFrom` or `existingSecret`, and add
the annotation `secrets.infisical.com/auto-reload: "true"` to the Deployment so a
changed secret restarts the pod.

Instant updates is an Enterprise feature, so a changed value reaches the pod
after the resync interval, not at once.

## After a restore

The database already holds the admin, projects, identities and secrets. Only
what depends on the new cluster needs fixing:

1. Log in with the admin from Bitwarden.
2. Run `kubectl get cm kube-root-ca.crt -n default -o jsonpath='{.data.ca\.crt}'`.
   A rebuilt k3s cluster has a new CA.
3. For each of the four identities, edit **Kubernetes Auth** and replace the **CA
   Certificate**. The host and service account names stay the same.
4. Check one app: `kubectl get infisicalsecret -A` should show the secrets
   syncing, with no authentication errors.

## If authentication fails

Check the `infisical-operator` pod logs, and the status on an `InfisicalSecret`
(`kubectl describe infisicalsecret <app> -n <app>`). Typical causes:

| Symptom | Cause |
|---|---|
| Authentication or `403` error | The CA certificate is stale, or Allowed Service Account Names or Namespaces does not match `infisical-<stack>` and `infisical-operator`. |
| A token review error | The service account is missing its `system:auth-delegator` binding. |
| Project or secret not found | Wrong `projectSlug`, `envSlug` or `secretsPath`, or the identity is not added to the project. |
| The Secret is empty | The folder name does not match `secretsPath`. |

If validating with an empty Token Reviewer JWT does not work, the fallback is a
dedicated reviewer service account with a long-lived token. Use the "Manual
long-lived service account tokens" steps in Infisical's `InfisicalSecret`
documentation, and paste that token into **Token Reviewer JWT**.
