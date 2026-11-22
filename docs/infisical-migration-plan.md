# Migration plan: age+sops to Infisical

Replace sops+age with Infisical as the cluster's secret store. External Secrets
(ESO) is used only to give Infisical its own bootstrap secrets.

Each phase is its own PR, branched from the latest `main`. Nothing is removed
until Phase 6.

## Decisions

| Topic | Decision |
|---|---|
| Primary secret store | Infisical, a bootstrap app installed by Ansible before Argo CD |
| ESO | Only for Infisical's own secrets, read from AWS SSM Parameter Store |
| Bootstrap secrets | SecureString params under `/homelab/infisical/` (`ENCRYPTION_KEY`, `AUTH_SECRET`, `REDIS_PASSWORD`), copy in Bitwarden |
| App secret delivery | Infisical Operator (`InfisicalSecret`) creates one Kubernetes Secret per app |
| Operator auth | Kubernetes Auth machine identities, one per stack project. Client JWT as reviewer with short-lived tokens (free). The Gateway reviewer option is paid. |
| Infisical layout | 4 projects (`apps`, `platform`, `system`, `ai`), one folder per app |
| CNPG | Stays in `k8s/platform/cnpg`. An Ansible role installs it from there. |
| Infisical login | Local admin user. OIDC SSO is a paid feature, so no Pocket ID login. Google or GitHub SSO is free if wanted. |
| Infisical DB backups | CNPG Barman Cloud to AWS S3, plus a daily `pg_dump` to Cloudflare R2 |
| Disaster recovery | Infisical restores from S3 before Argo CD and Velero. Velero restores app data afterwards. |

## Phase 0: prerequisites (manual)

See [infisical-phase-0-prerequisites.md](infisical-phase-0-prerequisites.md).

Done when: SSM parameters, S3 bucket, scoped IAM user, R2 bucket and token
exist, and everything is in Bitwarden.

## Phase 1: bootstrap stack

Branch `feat/bootstrap-infisical`. New charts and Ansible roles. No impact on
existing apps.

- `k8s/bootstrap/charts/external-secrets/` and a role. The role creates the AWS
  credentials Secret from env or the Bitwarden CLI. Nothing is committed.
- A `cnpg` role that installs `../platform/cnpg` (release `cnpg`, namespace
  `cnpg`). Skipped on the live cluster, where the operator already runs.
- `k8s/bootstrap/charts/infisical/`:
  - the official `infisical-standalone` chart, pinned;
  - a CNPG `Cluster` for Postgres, and Redis;
  - an `ExternalSecret` and `ClusterSecretStore` for AWS SSM;
  - a Traefik ingress with TLS (hostname defined once with a YAML anchor);
  - Barman Cloud backups to S3 with a `ScheduledBackup`;
  - a `recovery` toggle that bootstraps the Cluster from the S3 backup.
- `k8s/bootstrap/charts/infisical-operator/` and a role (Infisical `secrets-operator`).
- Playbook order: `cilium`, `prometheus-crds`, `cert-manager`, `longhorn`,
  `external-secrets`, `cnpg`, `infisical`, `infisical-operator`, `argocd`.
- Add the new charts to the `bootstrap:` list in `charts/root/values.yaml` so
  Argo can monitor them.
- Check whether anything else in the bootstrap Ansible uses helm-secrets.

Chart versions seen on 2026-11-21 (verify and pin when implementing):

| Chart | Version |
|---|---|
| `external-secrets` | 2.15.0 |
| `infisical-standalone` | 1.12.4 (app v0.167.14) |
| `secrets-operator` | 0.11.18 |
| `cloudnative-pg` | 0.29.2 (repo currently pins 0.29.1) |
| `plugin-barman-cloud` | 0.9.0 |

Done when:

- The ExternalSecret shows `SecretSynced`.
- The Infisical UI loads and the admin user exists.
- A base backup is in S3.
- All 5 existing CNPG clusters are still `Cluster in healthy state`.

## Phase 2: backups and the second copy

- CronJob: daily `pg_dump` of Infisical's database to R2, credentials from ESO.
- Alert (VictoriaMetrics) if the last backup in S3 or R2 is older than 36 hours.

Done when: a dump file is in R2, and the alert fires when the CronJob is
suspended.

## Phase 3: operator, projects and pilot app

- In Infisical, create the 4 projects, a Kubernetes Auth identity per stack, and
  a folder per app. Folder-level permissions are paid, so keep one project per
  stack: it is the access boundary.
- Per stack, create a service account for the operator and bind it to
  `system:auth-delegator`. Set `autoCreateServiceAccountToken: true` on each
  `InfisicalSecret`. Set `syncConfig.resyncInterval` (for example 60s). Instant
  updates is an Enterprise feature, so changes arrive by polling.
- Pilot one low-risk app (`myspeed` or `upsnap`):
  1. Load its values into Infisical.
  2. Add `templates/infisicalsecret.yaml`, producing `<app>-secrets` with the
     auto-reload annotation.
  3. Switch the app to `envFrom` or `existingSecret`.
  4. Delete its `secrets.yaml` and `secrets.dec.yaml`.
- Write down the recipe for the remaining apps.

Done when: the pilot syncs with no `secrets://` file, `helm template` shows no
secret literals, and changing the value in Infisical restarts the pod within the resync interval.

## Phase 4: Argo CD and bootstrap-chart secrets

- List the keys in Argo CD's `secrets.yaml` (not the values), then move them to
  `InfisicalSecret` resources in the `argocd` chart.
- Do the same for other bootstrap charts that have a `secrets.yaml`.
- Ansible creates the namespaces before the operator, so Secrets can be written
  before Argo exists.

Done when: `argocd` is Healthy and Synced with its secrets from Infisical.

## Phase 5: migrate the apps

Order: `apps` (36, batches of about 6), `ai`, `system`, then `platform` last.

Special cases, one at a time:

- hermes `postStart` script: use the operator's secret templating.
- Homepage widget keys in ingress annotations: annotations cannot read Secrets.
  Drop the key, move the widget to homepage's own config, or accept it. Decide
  before the first affected app.
- Charts with no `existingSecret`: a small template Secret plus `extraEnvFrom`.
- Keep the AI-apps table in `AGENTS.md` current.

Done when: no `secrets.yaml` is left under `k8s/` and every app is Synced and
Healthy.

## Phase 6: remove sops

- Remove `secrets://secrets.yaml` from both ApplicationSets in
  `k8s/bootstrap/charts/root/templates/`.
- Remove the sops/age init container and the `helm-secrets-private-keys` mount
  and Secret from the Argo values.
- Delete `.sops.yaml`, `scripts/decrypt-secrets.sh`, and the `decrypt-secrets`
  and `clean-secrets` Makefile targets. Drop `sops`, `age` and helm-secrets from
  `make deps`.
- Update `.gitignore`, pre-commit (keep gitleaks), `AGENTS.md` and the
  `homelab-admin` skill.

Done when: a fresh clone needs no sops tooling and CI is green.

## Phase 7: cleanup

- Retire the age key, and rotate high-value secrets (Cloudflare, AWS, API
  keys), because the old encrypted files stay in git history.
- Write a short runbook: add a secret, rotate a secret, run DR.

Done when: the age key is retired and the runbook is merged.

## Disaster recovery order

1. `make metal`, then `make kubeconfig`.
2. Provide the AWS IAM key from Bitwarden. Ansible creates the Secret.
3. Bootstrap playbook: cilium, cert-manager, longhorn, ESO, CNPG operator,
   Infisical with `recovery: true` (restores from S3), Infisical operator.
4. Install Argo CD. It syncs everything, and the operator fills in the secrets.
5. Velero is now healthy. Run `velero restore` for app data.

If S3 is unusable, restore from the R2 `pg_dump`. `ENCRYPTION_KEY` comes from
Bitwarden.

## Risks

- **Startup race.** An app's first sync can sit in `CreateContainerConfigError`
  for a minute until the operator creates its Secret.
- **No drift view.** Argo no longer diffs secret values.
- **Single point of failure.** The AWS account plus `ENCRYPTION_KEY` replace the
  age key. The R2 copy and Bitwarden are the mitigation.
- **Argo CD in a rebuild.** Whether other bootstrap Ansible uses helm-secrets is
  unchecked.
