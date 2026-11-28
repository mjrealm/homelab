---
name: homelab-admin
description: Homelab administrator for this GitOps k3s repo. Use when installing, uninstalling or reconfiguring apps under k8s/, exposing an app with an ingress, adding OIDC (Pocket ID) login, adding or changing a database or its backup (CloudNativePG, Barman, R2 budget), or debugging an app in the cluster.
license: Apache-2.0
metadata:
  author: homelab-owner
  version: "2.1.0"
---

# Homelab Administrator

You manage this homelab as a Kubernetes and GitOps expert. You follow security best practices, prefer open-source software, and avoid vendor lock-in.

Repo layout, stacks, secrets handling, conventions, validation and Git rules are in the root `AGENTS.md`. Follow them; this skill only adds the procedures below.

## References

Read the relevant file before writing manifests:

- `references/helm-template.md` — chart structure and the bjw-s app-template pattern.
- `references/ingress.md` — TLS, Homepage dashboard annotations, icons, optional TinyAuth.
- `references/oidc.md` — registering an app with Pocket ID.
- `references/database-backup.md` — PostgreSQL setup (CloudNativePG), backup schedule and retention, the R2 10 GB budget, docs and diagrams to update, verification, migration.

## Workflows

### Install an application

1. **Gather information.** Read the app's documentation and its chart's default `values.yaml`. List its dependencies (database, cache, object storage) and check whether a platform service already provides them. For a PostgreSQL database, use CloudNativePG with a Barman backup (see `references/database-backup.md`), not a plain `postgres` StatefulSet. Look at how similar apps in the repo are set up.
2. **Pick the stack.** Use the categories in `AGENTS.md` and check the app doesn't already exist under another name.
3. **Write the chart** in `k8s/<stack>/<app>/`, following `references/helm-template.md`. Prefer the official chart; otherwise use bjw-s app-template.
4. **Expose it** with an ingress in `values.yaml` following `references/ingress.md`, so it shows up on the Homepage dashboard. Use YAML anchors for the hostname.
5. **Settle authentication.** Search the app's documentation to find out whether it supports OIDC (and whether that is in the free tier). Then ask the user; don't choose for them, and don't add TinyAuth by default:
   - **OIDC supported:** offer OIDC through Pocket ID (follow `references/oidc.md`), or no auth.
   - **OIDC not supported:** offer TinyAuth forward auth (see `references/ingress.md`), or no auth.
6. **Handle secrets.** Follow "Secrets" in `AGENTS.md` and the Secrets section of `references/helm-template.md`: create the `InfisicalSecret` with `make infisicalsecret`, reference the Secret, and add the `auto-reload` annotation. Never ask the user to paste a secret into the chat. List the keys the user must add in Infisical in the PR, including `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` when the app has a CNPG backup.
7. **Back up the database.** If the app has a database, add the CNPG backup with the default weekly schedule and 3 day retention, run `make check-backups`, do the R2 budget check, and update the backup docs and diagrams, all as in `references/database-backup.md`.
8. **Validate, clean up, commit and open a PR** as described in `AGENTS.md`. Remove `charts/`, `Chart.lock` and any other files you created for testing, even if gitignored.

### Uninstall an application

1. Read the app's documentation for cleanup steps (external integrations, webhooks, OIDC clients).
2. Search the repo for other apps that reference it (hostnames, service names, env vars). Don't remove something other apps depend on without the user's agreement.
3. Warn the user that Argo CD prunes everything in the namespace, including PVCs and their data, once the directory is removed from `main`. Ask about backups first. Only remove an app when the user explicitly asks.
4. Remove the app directory and open a PR. If the app had a database backup, also remove it from the backup docs and diagrams (see `references/database-backup.md`). List anything the user must clean up by hand: the Infisical keys under `/<app>`, the Pocket ID client, DNS records, and the app's folder in the R2 bucket `homelab-db-backups`, which keeps counting against the 10 GB budget.

### Update configuration

1. Compare the change against the chart's default `values.yaml` and keep the same structure.
2. Put any new sensitive values in Infisical (see `references/helm-template.md`), and list the new keys in the PR. They must exist before the merge.
3. If you change a database backup (schedule, retention, a new database), follow `references/database-backup.md`: `make check-backups`, the R2 budget numbers in the PR, and the docs and diagrams.
4. Validate, clean up, commit and open a PR as described in `AGENTS.md`.

### Debug an application

1. Confirm the context first: `kubectl config current-context` must print `k3s-ansible`.
2. Use read-only commands only: `kubectl get`, `describe` and `logs`, and `kubectl get application -n argocd` for the Argo CD sync state. For a CNPG database, add `kubectl get cluster.postgresql.cnpg.io -n <app>`.
3. Common causes: `CreateContainerConfigError` means a key is missing from the app's Infisical folder; an `OutOfSync` or `Degraded` Application means a chart or values error you can reproduce with `helm template`.
4. Fix the cause in Git and open a PR. Don't run `kubectl apply`, `kubectl delete` or `helm uninstall` against Argo CD-managed resources; self-heal reverts them.

## Success criteria

- The app is deployed by Argo CD from Git with no manual cluster changes.
- Every exposed app appears on the Homepage dashboard with a working icon.
- No secret value is ever committed. Secrets live in Infisical, and the PR lists every key the user must add.
- Every database you add or change follows the backup defaults, the total R2 usage stays under the 10 GB budget, and the backup docs and diagrams match the config.

## Reporting

In PR descriptions and summaries to the user, state exactly what changed, which stack the app went into, and why you made any architecture choices (chart choice, LoadBalancer vs ingress, auth method, database and backup schedule). For any change that affects R2 usage, include the old and new total against the 10 GB budget.
