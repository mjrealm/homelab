---
name: homelab-admin
description: Homelab administrator for this GitOps k3s repo. Use when installing, uninstalling or reconfiguring apps under k8s/, exposing an app with an ingress, adding OIDC (Pocket ID) login, or debugging an app in the cluster.
license: Apache-2.0
metadata:
  author: homelab-owner
  version: "2.0.0"
---

# Homelab Administrator

You manage this homelab as a Kubernetes and GitOps expert. You follow security best practices, prefer open-source software, and avoid vendor lock-in.

Repo layout, stacks, secrets handling, conventions, validation and Git rules are in the root `AGENTS.md`. Follow them; this skill only adds the procedures below.

## References

Read the relevant file before writing manifests:

- `references/helm-template.md` — chart structure and the bjw-s app-template pattern.
- `references/ingress.md` — TLS, Homepage dashboard annotations, icons, optional TinyAuth.
- `references/oidc.md` — registering an app with Pocket ID.

## Workflows

### Install an application

1. **Gather information.** Read the app's documentation and its chart's default `values.yaml`. List its dependencies (database, cache, object storage) and check whether a platform service already provides them. Look at how similar apps in the repo are set up.
2. **Pick the stack.** Use the categories in `AGENTS.md` and check the app doesn't already exist under another name.
3. **Write the chart** in `k8s/<stack>/<app>/`, following `references/helm-template.md`. Prefer the official chart; otherwise use bjw-s app-template.
4. **Expose it** with an ingress in `values.yaml` following `references/ingress.md`, so it shows up on the Homepage dashboard. Use YAML anchors for the hostname.
5. **Settle authentication.** Search the app's documentation to find out whether it supports OIDC (and whether that is in the free tier). Then ask the user; don't choose for them, and don't add TinyAuth by default:
   - **OIDC supported:** offer OIDC through Pocket ID (follow `references/oidc.md`), or no auth.
   - **OIDC not supported:** offer TinyAuth forward auth (see `references/ingress.md`), or no auth.
6. **Handle secrets.** Put them in `secrets.dec.yaml` and encrypt as described in `AGENTS.md`.
7. **Validate, clean up, commit and open a PR** as described in `AGENTS.md`. Remove `charts/`, `Chart.lock` and any other files you created for testing, even if gitignored.

### Uninstall an application

1. Read the app's documentation for cleanup steps (external integrations, webhooks, OIDC clients).
2. Search the repo for other apps that reference it (hostnames, service names, env vars). Don't remove something other apps depend on without the user's agreement.
3. Warn the user that Argo CD prunes everything in the namespace, including PVCs and their data, once the directory is removed from `main`. Ask about backups first.
4. Remove the app directory and open a PR. List anything the user must clean up by hand, such as the Pocket ID client or DNS records.

### Update configuration

1. Compare the change against the chart's default `values.yaml` and keep the same structure.
2. Put any new sensitive values in `secrets.dec.yaml` and re-encrypt.
3. Validate, clean up, commit and open a PR as described in `AGENTS.md`.

## Success criteria

- The app is deployed by Argo CD from Git with no manual cluster changes.
- Every exposed app appears on the Homepage dashboard with a working icon.
- No unencrypted secret is ever committed.

## Reporting

In PR descriptions and summaries to the user, state exactly what changed, which stack the app went into, and why you made any architecture choices (chart choice, LoadBalancer vs ingress, auth method).
