# Add an app's secrets

Use this when an app needs passwords, tokens or API keys. The secrets live in
Infisical, and the cluster syncs them into a Kubernetes Secret. Repeat these
steps for each app. The worked example is `convertx` (stack `apps`, one secret,
`JWT_SECRET`).

## What you need

- Infisical admin login (Bitwarden, "Infisical admin").
- The app's stack and that stack's row below. Stack, project slug and identity
  are fixed per stack:

  | Stack | Project slug | Identity (service account) | Identity ID |
  |---|---|---|---|
  | `apps` | `apps` | `infisical-apps` | `fefa3b53-6b57-4b79-a20a-e7a9db8c00bf` |
  | `platform` | `platform` | `infisical-platform` | `e2ccd552-d832-493d-8ca4-205f4e8c3f08` |
  | `system` | `system` | `infisical-system` | `b80ad456-f091-4fdc-9477-518d2b3852e8` |
  | `ai` | `ai` | `infisical-ai` | `e884d4d2-4998-4abe-b7fa-813b2b410f69` |

  <!-- Keep in sync with the identity table in docs/build/02-infisical-setup.md -->

## 1. Put the secrets in Infisical

1. Open the stack's project, then **Secrets**.
2. Select the `prod` environment.
3. Create a folder named after the app: `convertx`.
4. Open the folder and add each key and value: `JWT_SECRET`.

Do this before merging the pull request. Otherwise the pod waits in
`CreateContainerConfigError`.

## 2. Add the InfisicalSecret to the app

1. Create `k8s/<stack>/<app>/templates/infisicalsecret.yaml`, filled in from the
   table above.

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

2. What to change per app:

   - `metadata.name` and `secretsPath`: the app name.
   - `identityId`, `serviceAccountRef.name` and `projectSlug`: the stack's row.
   - `secretName`: `<app>-secrets`.

## 3. Point the app at the Secret

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

## 4. Check it

1. Merge the pull request.
2. Check the sync:

   ```bash
   kubectl get infisicalsecret,secret -n convertx
   kubectl get pods -n convertx
   ```

3. Expect the `InfisicalSecret` to be healthy, `convertx-secrets` to exist, and
   the pod to be Running.
4. To test a reload, change a value in Infisical and wait 60 seconds. The pod
   restarts. Instant updates is an Enterprise feature, so a changed value reaches
   the pod after the resync interval, not at once.

If the `InfisicalSecret` reports an error, use the authentication errors guide.
