# Which playbook do I run?

Three Ansible playbooks cover the cluster's life. Pick by situation, not by habit.
Run every command from the repo root, after [Workstation setup](../prepare/01-workstation-setup.md).

| Situation | Command | Playbook |
|---|---|---|
| Brand-new cluster, nothing installed yet | `make bootstrap` | `k8s/bootstrap/bootstrap.yml` |
| Live cluster: rotate the AWS key, re-apply the root chart, repair Argo CD | `make upgrade TAGS=<tag>` | `k8s/bootstrap/upgrade.yml` |
| Cluster rebuilt after a disaster, restoring from backups | `make recover` (coming soon) | See [Recover the cluster](../recover/01-recover-the-cluster.md) |

Operating system and k3s changes (version, flags such as OIDC) are separate. They
live in `metal/` and run with `make metal`. That playbook is safe to re-run.

## Safety checks

`make bootstrap` refuses to run on a cluster that is already in use. Before it
changes anything it:

1. Prints which cluster it will touch (kubectl context and API server address).
2. Stops if the `argocd`, `infisical`, `cert-manager` or `longhorn-system`
   namespace already exists.
3. Asks `y` or anything else. Only `y` or `yes` continues.

Skip the question in scripts with `-e confirm=yes`. Run on a used cluster anyway
with `-e force=true`. You will rarely want that.

## Where each playbook gets its secrets

| Value | Where it comes from |
|---|---|
| AWS access key and secret | Bitwarden item `AWS IAM homelab-infisical-bootstrap`. The playbook prompts. |
| Cloudflare API token | Bitwarden item `Cloudflare DNS API token (cert-manager)`. `make metal` prompts. |
| Infisical `ENCRYPTION_KEY`, `AUTH_SECRET`, `REDIS_PASSWORD` | AWS Systems Manager. Never typed. |

To skip the AWS prompts, export `INFISICAL_AWS_ACCESS_KEY_ID`,
`INFISICAL_AWS_SECRET_ACCESS_KEY` and `INFISICAL_AWS_REGION` first. The playbooks
never read a password manager themselves.
