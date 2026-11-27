# Fix Infisical authentication errors

Use this when an `InfisicalSecret` does not sync, or a pod waits in
`CreateContainerConfigError` because its Secret is missing.

## 1. Read the error

```bash
kubectl get infisicalsecret -A
kubectl describe infisicalsecret <app> -n <app>
kubectl logs -n infisical-operator deploy/infisical-opera-controller-manager --tail=50
```

After fixing a cause, wait 1-2 minutes. The operator backs off between retries,
so the old error stays visible until the next attempt.

## 2. Match the symptom

| Symptom | Cause | Fix |
|---|---|---|
| Authentication or `403` error | The CA certificate is stale, or the allowed service account name or namespace does not match `infisical-<stack>` and `infisical-operator`. | In Infisical, open **Organization**, **Access Control**, **Machine Identities**, the identity, **Authentication**, **Kubernetes Auth**. Fix the **CA Certificate** (get it below) and the **Allowed Service Account Names** and **Allowed Namespaces**. |
| A token review error | The service account is missing its `system:auth-delegator` binding. | Reinstall or sync the `infisical-operator` chart, which creates the binding. |
| `Project with slug '<stack>' not found` | The project still has its generated slug, or the identity is not added to the project. | Open the project, **Project Settings**, **General**, set **Project Slug** to the stack name. Then **Access Control**, **Machine Identities**, **Add Machine Identity to Project**, **Assign Existing**, pick `infisical-<stack>` with the **Viewer** role. |
| Another project or secret not found | Wrong `envSlug` or `secretsPath`, or the key is missing in Infisical. | Check that the environment is `prod`, the folder is named after the app, and the key exists. |
| The Secret is empty | The folder name does not match `secretsPath`. | Rename the folder or fix `secretsPath` in the app's `InfisicalSecret`. |

## Get the cluster CA certificate

```bash
kubectl get cm kube-root-ca.crt -n default -o jsonpath='{.data.ca\.crt}'
```

Copy the whole output, including the `BEGIN` and `END` lines, into **CA
Certificate**.

## If an empty Token Reviewer JWT does not work

Use a dedicated reviewer service account with a long-lived token. Follow the
"Manual long-lived service account tokens" steps in Infisical's `InfisicalSecret`
documentation, and paste that token into **Token Reviewer JWT**.
