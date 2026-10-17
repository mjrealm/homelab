# AGENTS.md

## Project overview

GitOps-managed homelab running k3s. Changes reach the cluster only through Git:

- `metal/` — Ansible playbooks that provision the nodes and install k3s.
- `k8s/bootstrap/` — Ansible playbook and charts installed before Argo CD takes over (argocd, cert-manager, cilium, longhorn, CRDs). `bootstrap/charts/root` holds the Argo CD AppProjects and ApplicationSets; change it only when the repo layout or stacks change.
- `k8s/<stack>/<app>/` — one Helm chart per app. An ApplicationSet per stack turns every directory into an Argo CD Application named after the directory, deployed to a namespace of the same name, with automated sync, **prune** and self-heal.

Removing an app directory deletes the app (and its PVCs) from the cluster.

## Repo layout and categories

Each app lives in exactly one stack:

| Stack | What belongs there | Examples |
|---|---|---|
| `k8s/apps/` | Standalone end-user services that do one thing well. Most apps go here. They consume platform services (SSO, messaging) but don't orchestrate other apps. | immich, mealie, paperless-ngx, n8n |
| `k8s/platform/` | Shared base layers other apps depend on: identity, messaging, databases, management hubs. | pocket-id, lldap, tinyauth, emqx, cnpg, portainer |
| `k8s/system/` | Components that keep the cluster itself running and observable. | velero, metallb, reloader, kured, cloudflared |
| `k8s/ai/` | AI agents, model UIs and AI tooling. | hermes, open-webui, mcphub |
| `k8s/bootstrap/` | Prerequisites installed before Argo CD can deploy anything else. | argocd, cert-manager, cilium |

Check the existing stacks for a similar app before choosing one, and don't create duplicates.

Each app directory has:

```
<app>/
├── Chart.yaml        # wrapper chart; real apps are listed under `dependencies`
├── values.yaml       # one top-level key per dependency name
├── secrets.yaml      # sops-encrypted values (committed)
├── secrets.dec.yaml  # decrypted copy for local editing (gitignored, never commit)
└── templates/        # optional extra manifests
```

## Setup commands

```bash
make deps              # brew tools, pyenv Python venv (ansible, pre-commit), helm-secrets plugins, pre-commit hook
make decrypt-secrets   # decrypt every k8s/**/secrets.yaml to secrets.dec.yaml (prompts for the age key)
make clean-secrets     # delete all secrets.dec.yaml files
make kubeconfig        # fetch kubeconfig from the control plane and merge it into ~/.kube/config
make metal             # provision nodes with Ansible (checks SSH access first)
```

Before running `kubectl` or `helm`, confirm the context is `k3s-ansible`:

```bash
kubectl config current-context
```

## Secrets

Secrets are encrypted with **sops + age** and decrypted by Argo CD through the **helm-secrets** plugin (`secrets://secrets.yaml`). The age public key is in `.sops.yaml`.

- Put passwords, tokens, API keys and OIDC client secrets in `secrets.dec.yaml`, never in `values.yaml`. It uses the same structure as `values.yaml`.
- Encrypt to `secrets.yaml` without risking an empty file if encryption fails:

  ```bash
  helm secrets encrypt secrets.dec.yaml > secrets.yaml.tmp && mv secrets.yaml.tmp secrets.yaml
  ```

- Never commit `secrets.dec.yaml`, and don't delete it locally; it is the working copy.
- A gitleaks pre-commit hook and CI workflow scan for secrets. Don't bypass them (`--no-verify`).

## Conventions

- Prefer the app's official Helm chart. Otherwise use the [bjw-s app-template](https://bjw-s-labs.github.io/helm-charts/docs/app-template/) chart (currently `5.3.0` across the repo).
- Pin image tags and expose them in `values.yaml` so Renovate can update them. Never use `:latest`.
- Use persistent volumes for app data, not temporary storage.
- Expose apps with an Ingress (`ingressClassName: traefik`). Use a LoadBalancer only when an Ingress can't work, and call it out in the PR. Never use NodePort.
- Define each hostname once with a YAML anchor and reference it in the TLS hosts list.

## Validation

Before opening a PR:

```bash
yamllint -c .yamllint.yaml <changed files>
helm dependency build k8s/<stack>/<app> && helm template k8s/<stack>/<app>
gitleaks git --staged .
```

Check that every changed `secrets.yaml` has a `sops:` block.

## Git and pull requests

- Never commit to `main`. Start from the latest `main` (`git checkout main && git pull`) and work on a new branch.
- Before adding a fix to an existing branch, check whether its PR was already merged. If so, start a new branch and PR.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`, e.g. `feat(apps): add actual-budget`, `fix(outline): ingress host`. Types: `feat`, `fix`, `chore`, `docs`, `refactor`.
- PR descriptions cover what changed, why, which stack an app went into, chart and image versions, and how it was verified.
- Don't merge PRs unless asked.

## Safety

- Make all cluster changes through Git. Don't run `kubectl delete`, `helm uninstall`, or `kubectl apply` against Argo CD-managed resources; self-heal will revert them anyway.
- Read-only `kubectl` (get, describe, logs) is fine for verifying and debugging.
