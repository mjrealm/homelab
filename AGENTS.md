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
| `k8s/platform/` | Shared base layers other apps depend on: identity, messaging, databases, management hubs. | pocket-id, lldap, tinyauth, emqx, cnpg |
| `k8s/system/` | Components that keep the cluster itself running and observable. | velero, metallb, reloader, kured, cloudflared |
| `k8s/ai/` | AI agents, model UIs and AI tooling. | hermes, open-webui, mcphub |
| `k8s/bootstrap/` | Prerequisites installed before Argo CD can deploy anything else. | argocd, cert-manager, cilium |

Check the existing stacks for a similar app before choosing one, and don't create duplicates.

Each app directory has:

```
<app>/
├── Chart.yaml        # wrapper chart; real apps are listed under `dependencies`
├── values.yaml       # one top-level key per dependency name
└── templates/        # optional extra manifests
```

## AI-consuming apps

These apps call an LLM, embedding, reranker, or vision model. When changing model config, check every app here. Keep this list up to date when an app is added, removed, or switched.

Target endpoint: LiteLLM, OpenAI-compatible at `http://litellm.litellm.svc:4000/v1` (in-cluster). Models and keys are managed in LiteLLM. Keys go in Infisical (an `InfisicalSecret` per app), never in `values.yaml`.

| App | Stack | Where the AI config lives | What it uses |
|---|---|---|---|
| hermes | `k8s/ai/` | `values.yaml` (`postStart` script: `providers.litellm.*`), Infisical `ai`/`prod` `/hermes` (`LITELLM_API_KEY`, `LITELLM_DEFAULT_MODEL`) | LiteLLM provider (chat) |
| hindsight | `k8s/ai/` | `values.yaml` (providers, LiteLLM base URLs), Infisical `ai`/`prod` `/hindsight` (`HINDSIGHT_API_*_MODEL`, keys, reranker URL) | LLM, embeddings, reranker (Cohere-compatible) |
| litellm | `k8s/ai/` | `values.yaml` (`proxy_config`, `envVars`), Infisical `ai`/`prod` `/litellm` (master and salt keys, SSO client) | The gateway itself. Models are stored in Postgres. |
| wardrowbe | `k8s/apps/` | `values.yaml` (`AI_BASE_URL`, `AI_TEXT_MODEL`, `AI_VISION_MODEL`), Infisical `apps`/`prod`/`wardrowbe` (`AI_API_KEY`) | Text and vision chat |
| sure | `k8s/apps/` | `values.yaml` (`ASSISTANT_TYPE`, `OPENAI_URI_BASE`, `OPENAI_MODEL`), Infisical `apps`/`prod` `/sure` (`OPENAI_ACCESS_TOKEN`, `EXTERNAL_ASSISTANT_URL`, `EXTERNAL_ASSISTANT_TOKEN`, `MCP_API_TOKEN`, `MCP_USER_EMAIL`) | Chat is delegated to a Hermes profile (external agent, calls back via `/mcp`). LiteLLM handles categorization. |
| karakeep | `k8s/apps/` | `values.yaml` (`OPENAI_BASE_URL`, `INFERENCE_*_MODEL`), Infisical `/karakeep` (`OPENAI_API_KEY`) | Text and image inference |
| mealie | `k8s/apps/` | `values.yaml` (`OPENAI_BASE_URL`, `OPENAI_MODEL`), Infisical `/mealie` (`OPENAI_API_KEY`) | Chat |
| paperless-gpt | `k8s/apps/` | `values.yaml` (`OPENAI_BASE_URL`, `LLM_MODEL`, `VISION_LLM_MODEL`), Infisical `/paperless-gpt` (`OPENAI_API_KEY`) | Chat and vision OCR |
| paperless-ngx | `k8s/apps/` | `PAPERLESS_AI_ENABLED` is `false` in `values.yaml`; no `PAPERLESS_AI_*` settings exist | Inactive. Enable only if AI is re-enabled. |
| paperless-starfruit | `k8s/apps/` | Configured in the app's web UI, not env vars. Nothing in the repo. Set the OpenAI-compatible base URL and model in the UI. | Metadata and OCR |
| trek | `k8s/apps/` | Configured in the app's admin UI (Admin > Addons > AI Parsing), not env vars. Nothing in the repo. Set the OpenAI provider, base URL, and key in the UI. | AI Parsing (fallback for booking imports) |

Model names for hermes and hindsight are Infisical keys, so you can change them without a commit; the pod restarts for hermes and needs a manual restart for hindsight. When changing a model name, check that the name exists in LiteLLM. Names are case-sensitive, so `qwen3.8:fast` and `Qwen3.8:fast` are different.

## Setup commands

```bash
make deps              # brew tools, pyenv Python venv (ansible, pre-commit), pre-commit hook
make infisicalsecret  # create k8s/<stack>/<app>/templates/infisicalsecret.yaml from prompts (ARGS="-e stack=apps -e app=x" skips them)
make test-up / test-bootstrap / test-down  # disposable k3d cluster to try the bootstrap (own kubeconfig in .test/; never the real cluster)
make infisical-setup  # new Infisical: admin, dr-admin, projects and stack identities through the API; rewrites the identity IDs in the repo
make recover           # NEW rebuilt clusters only: restore Infisical from its backup, system stack only (checks the restore settings are on main)
make recover-ca        # after make recover: point the stack identities at the new cluster's CA
make recover-stage STAGE=platform|all  # after the volumes are restored: add the platform stack, then every stack
make check-backups   # fail when a database backup could overlap Velero's Longhorn CSI snapshots (also runs in CI)
make kubeconfig        # fetch kubeconfig from the control plane and merge it into ~/.kube/config
make metal             # provision nodes with Ansible (checks SSH access first)
make bootstrap         # NEW clusters only: refuses on a live cluster (cert-manager, longhorn, Infisical stack, Argo CD, ...)
make upgrade TAGS=root # re-run on a live cluster by tag: root, argocd, aws-credentials
make docs              # preview the Docusaurus docs site at http://localhost:3000/homelab/
```

Run Ansible through `make`, not `ansible-playbook` directly: the Makefile puts the project's `.venv` on `PATH`.

Before running `kubectl` or `helm`, confirm the context is `k3s-ansible`:

```bash
kubectl config current-context
```

## Secrets

Secrets live in **Infisical**, not in Git. The Infisical operator syncs them into Kubernetes Secrets. There is no sops, age or helm-secrets any more, and no `secrets.yaml` or `secrets.dec.yaml` files.

- One Infisical project and machine identity per stack (`apps`, `platform`, `system`, `ai`); see `docs/operate/03-add-app-secrets.md` for the project slugs and identity IDs. Keys go in environment `prod`, in a folder named after the app (`/<app>`).
- Each app has `templates/infisicalsecret.yaml` (an `InfisicalSecret`) that creates a Secret named `<app>-secrets`. Create it with `make infisicalsecret` (it asks for the stack, app and keys, fills in the project, identity and service account, and prints the `values.yaml` lines), or copy a recent one, for example `k8s/platform/lldap/templates/infisicalsecret.yaml`. Identity IDs live in `scripts/infisicalsecret/stacks.yml`.
- Reference the Secret from `values.yaml` with `envFrom`, `secretKeyRef` or `existingSecret`. Add `secrets.infisical.com/auto-reload: "true"` to the controller's annotations so pods restart when a key changes.
- To build a value from several keys (a database URL, for example), use `template.data` in the `InfisicalSecret`, with Go templates escaped for Helm.
- Hostnames, ports and other non-secret settings stay in `values.yaml`. LAN IPs, personal emails, client IDs and client secrets go in Infisical.
- You can't add keys yourself. In the PR description, list every key the user has to add in Infisical (project, path, key name), and say the keys must exist before the merge, or the pod waits in `CreateContainerConfigError`.
- A gitleaks pre-commit hook and CI workflow scan for secrets. Don't bypass them (`--no-verify`).

## Conventions

- Prefer the app's official Helm chart. Otherwise use the [bjw-s app-template](https://bjw-s-labs.github.io/helm-charts/docs/app-template/) chart (currently `5.3.0` across the repo).
- Pin image tags and expose them in `values.yaml` so Renovate can update them. Never use `:latest`.
- Use persistent volumes for app data, not temporary storage.
- Expose apps with an Ingress (`ingressClassName: traefik`). Use a LoadBalancer only when an Ingress can't work, and call it out in the PR. Never use NodePort.
- Define each hostname once with a YAML anchor (`&app` / `*app`) and reference it in the TLS hosts list. Keep the ingress in `values.yaml`.

## Docs

The runbooks in `docs/` are published with Docusaurus (`make docs` previews them). The reader is often in the middle of an outage, so:

- Write for a reader who has never seen this cluster. Every step says where to do it (Terminal or which screen), gives the exact command or the exact buttons to click, says what result to expect, and says what to do if the result differs. No "configure X" or "see the docs" without the values.
- Quote shell arguments that contain `[`, `*` or `?` (for example `-o 'custom-columns=...'`): macOS uses zsh, which rejects them unquoted.
- Name Bitwarden items exactly as listed in `docs/prepare/02-cloud-prerequisites.md`.
- Write the docs as a spec, not a snapshot. Say what must be true and how to check it. Do not state counts or versions that change as the cluster changes (how many volumes, apps, nodes, backups, databases; a tool's current version). Keep a number only when it is a requirement or policy a reader acts on (a retention, a schedule, a port, a minimum memory), and say which file defines it.
- One task or scenario per page. A page for a new cluster never also covers a restore; a restore never also covers adding an app.
- A runbook is self-contained: every command and value needed is on the page. Link to other pages only for background, never for a step the reader must do to finish.
- When a fact such as the identity ID table is needed on two pages, keep both copies and say so in a comment, rather than sending the reader away.
- Put new pages in the section for what the reader is doing: `prepare/`, `build/`, `recover/` or `operate/`, and add them to `website/sidebars.js`.

## Validation

Before opening a PR:

```bash
yamllint -c .yamllint.yaml <changed files>
helm dependency build k8s/<stack>/<app> && helm template k8s/<stack>/<app>
gitleaks git --staged .
```

Check that every key the chart reads from a Secret is listed in the PR for the user to add in Infisical.

## Clean up

Remove everything you created only to validate or test, even if it is gitignored, before you commit and when you finish:

```bash
rm -rf k8s/<stack>/<app>/charts k8s/<stack>/<app>/Chart.lock   # created by `helm dependency build`
```

- Also delete rendered output, downloaded or extracted charts and archives, test files, and extra worktrees or branches you made.
- Check with `git status --short --ignored`: only the files you meant to change, plus `.venv`, should remain.

## Git and pull requests

- Never commit to `main`. Always work on a branch created from the latest `main`.
- Before every commit and push, check whether the current branch's PR was already merged:

  ```bash
  gh pr view --json state --jq .state   # MERGED, CLOSED, OPEN, or an error if no PR exists
  ```

  PRs are squash-merged, so `git branch --merged` doesn't detect this; use `gh`. If the PR is `MERGED` or `CLOSED`, don't push to that branch. Switch to `main`, pull the latest, and start a new branch (uncommitted changes carry over):

  ```bash
  git checkout main && git pull
  git checkout -b <type>/<short-description>
  ```

- When starting new work, also switch to `main` and pull first, even if the current branch is unmerged.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`, e.g. `feat(apps): add actual-budget`, `fix(outline): ingress host`. Types: `feat`, `fix`, `chore`, `docs`, `refactor`.
- PR descriptions cover what changed, why, which stack an app went into, chart and image versions, and how it was verified.
- Don't merge PRs unless asked.

## Safety

- Make all cluster changes through Git. Don't run `kubectl delete`, `helm uninstall`, or `kubectl apply` against Argo CD-managed resources; self-heal will revert them anyway.
- Read-only `kubectl` (get, describe, logs) is fine for verifying and debugging.
- Only remove an app directory (and so its PVCs) when the user explicitly asks to remove that app. Don't remove apps on your own initiative, even to clean up or simplify. Removal requires an explicit instruction in the current request.
