#!/usr/bin/env bash
# Disaster-recovery test on throwaway clusters. Creates Infisical data through its
# API, backs it up, deletes the cluster, restores into a new one, and checks that
# the data, the admin login and the secret sync all come back.
#
# Usage: test/dr.sh seed | backup | verify | run
#   seed    bootstrap Infisical (admin, project, secret, machine identity) and prove
#           the operator syncs the secret
#   backup  take a database backup to the S3 stand-in and wait for it
#   verify  on the recovered cluster: admin login, data, then the CA fix and sync
#   run     everything: up, bootstrap, seed, backup, delete cluster, recover, verify
#
# Needs: make deps, Docker running, jq, curl.

set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
state="$root/.test"
kc="$state/kubeconfig"
db="$state/dr.json"
port=18081
base="http://127.0.0.1:$port"
ns_app=harness

export KUBECONFIG="$kc"
k() { kubectl --kubeconfig "$kc" "$@"; }
case "$(k config current-context 2>/dev/null || true)" in
k3d-*) ;;
*) [ "${1:-}" = run ] || { echo "FAIL: .test/kubeconfig is not a k3d test cluster" >&2; exit 1; } ;;
esac
say() { printf '\n== %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
ok() { printf 'ok: %s\n' "$*"; }
get() { jq -r ".$1" "$db"; }
put() { # put key value
	tmp=$(mktemp)
	[ -f "$db" ] || echo '{}' >"$db"
	jq --arg k "$1" --arg v "$2" '.[$k]=$v' "$db" >"$tmp" && mv "$tmp" "$db"
}

need() { command -v "$1" >/dev/null 2>&1 || fail "$1 is not installed"; }
need jq; need curl; need kubectl

pf_pid=
pf_start() {
	k -n infisical port-forward --address 127.0.0.1 svc/infisical-infisical-standalone-infisical "$port:8080" >/dev/null 2>&1 &
	pf_pid=$!
	for _ in $(seq 1 30); do
		curl -sf "$base/api/status" >/dev/null 2>&1 && return 0
		sleep 2
	done
	fail "Infisical did not answer on $base"
}
pf_stop() { [ -z "$pf_pid" ] || kill "$pf_pid" 2>/dev/null || true; pf_pid=; }
trap pf_stop EXIT

# api <method> <path> [json]  (uses the admin token in $TOKEN when set)
api() {
	local m=$1 p=$2 d=${3:-}
	if [ -n "$d" ]; then
		curl -s -X "$m" "$base$p" -H "Authorization: Bearer ${TOKEN:-}" -H 'Content-Type: application/json' -d "$d"
	else
		curl -s -X "$m" "$base$p" -H "Authorization: Bearer ${TOKEN:-}"
	fi
}

login() {
	local r
	r=$(curl -s -X POST "$base/api/v1/auth/universal-auth/login" -H 'Content-Type: application/json' \
		-d "{\"clientId\":\"$(get uaClientId)\",\"clientSecret\":\"$(get uaClientSecret)\"}")
	TOKEN=$(echo "$r" | jq -r '.accessToken // empty')
	[ -n "$TOKEN" ] || { echo "$r" | jq -c . >&2; return 1; }
}

cluster_ca() { k get cm kube-root-ca.crt -n default -o 'jsonpath={.data.ca\.crt}'; }

harness_cr() {
	cat <<YAML
apiVersion: secrets.infisical.com/v1alpha1
kind: InfisicalSecret
metadata:
  name: harness
  namespace: $ns_app
spec:
  hostAPI: http://infisical-infisical-standalone-infisical.infisical.svc.cluster.local:8080/api
  syncConfig:
    resyncInterval: 10s
  authentication:
    kubernetesAuth:
      identityId: $(get k8sIdentityId)
      autoCreateServiceAccountToken: true
      serviceAccountRef:
        name: infisical-platform
        namespace: infisical-operator
      secretsScope:
        projectSlug: platform
        envSlug: prod
        secretsPath: /demo
        recursive: false
  managedKubeSecretReferences:
    - secretName: harness-secrets
      secretNamespace: $ns_app
      creationPolicy: Owner
YAML
}

managed_value() { k -n "$ns_app" get secret harness-secrets -o 'jsonpath={.data.DEMO_KEY}' 2>/dev/null | base64 -d 2>/dev/null || true; }

wait_value() { # wait_value <expected> <seconds>
	local i=0
	while [ "$i" -lt "$2" ]; do
		[ "$(managed_value)" = "$1" ] && return 0
		sleep 5; i=$((i + 5))
	done
	return 1
}

cmd_seed() {
	say "Set up Infisical with scripts/infisical-admin.py"
	rm -f "$db" "$state/dr-admin.json"
	local pw proj ident
	pw=$(openssl rand -hex 12)
	if ! python3 "$root/scripts/infisical-admin.py" setup --port-forward --yes \
		--email admin@example.test --password "$pw" --org homelab-test \
		--no-repo-update --credentials-file "$state/dr-admin.json" >"$state/setup.log" 2>&1; then
		cat "$state/setup.log" >&2
		fail "scripts/infisical-admin.py setup failed"
	fi
	grep -E "^ok:|SETUP DONE" "$state/setup.log"
	put adminEmail admin@example.test; put adminPassword "$pw"
	put uaClientId "$(jq -r .clientId "$state/dr-admin.json")"
	put uaClientSecret "$(jq -r .clientSecret "$state/dr-admin.json")"
	pf_start
	login || fail "dr-admin login failed after setup"
	ok "dr-admin Universal Auth login works"

	proj=$(api GET /api/v1/projects | jq -r '.projects[] | select(.slug=="platform") | .id')
	[ -n "$proj" ] || fail "project platform was not created"
	put projectId "$proj"
	ident=$(api POST /api/v1/identities/search '{"search":{"name":{"$eq":"infisical-platform"}},"limit":5,"offset":0}' | jq -r '.identities[0].identityId // empty')
	[ -n "$ident" ] || fail "identity infisical-platform was not created"
	put k8sIdentityId "$ident"
	api POST /api/v2/folders "{\"projectId\":\"$proj\",\"environment\":\"prod\",\"name\":\"demo\",\"path\":\"/\"}" >/dev/null
	api POST /api/v3/secrets/raw/DEMO_KEY "{\"workspaceId\":\"$proj\",\"environment\":\"prod\",\"secretPath\":\"/demo\",\"secretValue\":\"before-disaster-1234\"}" >/dev/null
	put expected before-disaster-1234
	ok "secret /demo/DEMO_KEY in project platform"

	say "Prove the operator syncs the secret on this cluster"
	k create namespace "$ns_app" --dry-run=client -o yaml | k apply -f - >/dev/null
	harness_cr | k apply -f - >/dev/null
	wait_value before-disaster-1234 120 || { k -n "$ns_app" describe infisicalsecret harness | tail -15; fail "the secret did not sync before the disaster"; }
	ok "operator synced DEMO_KEY into harness-secrets"
}

cmd_backup() {
	say "Take a database backup and wait for it"
	k -n infisical delete backup dr-test --ignore-not-found >/dev/null
	k apply -f - >/dev/null <<'YAML'
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: dr-test
  namespace: infisical
spec:
  cluster:
    name: infisical-database
  method: plugin
  pluginConfiguration:
    name: barman-cloud.cloudnative-pg.io
YAML
	local i=0 ph=
	while [ "$i" -lt 900 ]; do
		ph=$(k -n infisical get backup dr-test -o 'jsonpath={.status.phase}' 2>/dev/null || true)
		[ "$ph" = completed ] && { ok "backup completed"; return 0; }
		[ "$ph" = failed ] && fail "backup failed: $(k -n infisical get backup dr-test -o 'jsonpath={.status.error}')"
		sleep 10; i=$((i + 10))
	done
	fail "backup did not finish in 15 minutes"
}

cmd_verify() {
	say "Verify the recovered cluster"
	pf_start
	local wanted
	wanted=$(get expected)

	# 1. Infisical must come back with its data, not empty.
	login || fail "admin universal auth login failed: Infisical did not restore its data"
	ok "admin login with the old client ID and secret works (identities restored)"
	local got
	got=$(api GET "/api/v3/secrets/raw/DEMO_KEY?workspaceId=$(get projectId)&environment=prod&secretPath=/demo" | jq -r '.secret.secretValue // empty')
	[ "$got" = "$wanted" ] || fail "secret value after restore is '$got', expected '$wanted'"
	ok "secret DEMO_KEY restored with its value"

	# 2. The operator must fail until the CA is replaced: the new cluster has a new CA.
	k create namespace "$ns_app" --dry-run=client -o yaml | k apply -f - >/dev/null
	harness_cr | k apply -f - >/dev/null
	sleep 45
	if [ "$(managed_value)" = "$wanted" ]; then
		say "NOTE: the secret synced without fixing the CA"
	else
		ok "as expected, the operator cannot authenticate with the old CA"
		k -n "$ns_app" get infisicalsecret harness -o 'jsonpath={.status.conditions[0].message}' | cut -c1-200; echo
	fi

	# 3. The documented fix: scripts/infisical-admin.py fix-ca.
	if INFISICAL_CLIENT_ID="$(get uaClientId)" INFISICAL_CLIENT_SECRET="$(get uaClientSecret)" \
		python3 "$root/scripts/infisical-admin.py" fix-ca --port-forward --yes >"$state/fixca.log" 2>&1; then
		ok "fix-ca: $(grep -c '^updated' "$state/fixca.log") identities pointed at the new CA"
	else
		cat "$state/fixca.log" >&2
		fail "scripts/infisical-admin.py fix-ca failed"
	fi
	wait_value "$wanted" 180 || { k -n "$ns_app" describe infisicalsecret harness | tail -15; fail "secret did not sync after the CA fix"; }
	ok "operator synced DEMO_KEY after the CA fix"
	say "DR TEST PASSED"
}

cmd_run() {
	"$root/test/cluster.sh" up
	( cd "$root" && make test-bootstrap )
	cmd_seed
	cmd_backup
	pf_stop
	"$root/test/cluster.sh" cluster-down
	"$root/test/cluster.sh" cluster-up
	( cd "$root" && make test-recover )
	cmd_verify
}

case "${1:-}" in
seed) cmd_seed ;;
backup) cmd_backup ;;
verify) cmd_verify ;;
run) cmd_run ;;
*) echo "Usage: $0 seed | backup | verify | run" >&2; exit 2 ;;
esac
