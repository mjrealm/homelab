#!/bin/sh
# Disposable test cluster for the bootstrap and recovery playbooks.
# Nothing here touches your real cluster or ~/.kube/config: the kubeconfig lives in
# .test/kubeconfig and the playbooks are pointed at it.
#
# Usage: test/cluster.sh up | cluster-up | cluster-down | down | status
#   up           network, an S3 stand-in, test keys and the k3d cluster
#   cluster-up   only the k3d cluster (the S3 stand-in and the keys are kept)
#   cluster-down only delete the k3d cluster (the S3 stand-in and the keys are kept)
#   down         delete everything, including the S3 stand-in and .test/

set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
state="$root/.test"
name=homelab-test
net=homelab-test
s3=homelab-test-s3
s3_user=testaccesskey
s3_password=testsecretkey
bucket=infisical-backups
# MinIO no longer publishes images, so SeaweedFS is the S3 stand-in.
s3_image=chrislusf/seaweedfs:4.55

# Same k3s as production: v1.36.6+k3s1 in the metal role becomes the image tag v1.36.6-k3s1.
k3s_version=$(sed -n 's/^k3s_version: *//p' "$root/metal/roles/k3s/defaults/main.yml")
image="rancher/k3s:$(echo "$k3s_version" | tr '+' '-')"

need() { command -v "$1" >/dev/null 2>&1 || { echo "$1 is not installed. Run: make deps" >&2; exit 1; }; }

preflight() {
	need docker
	need k3d
	docker info >/dev/null 2>&1 || { echo "Docker is not running. Open OrbStack and try again." >&2; exit 1; }
}

infra_up() {
	mkdir -p "$state"
	docker network inspect "$net" >/dev/null 2>&1 || docker network create "$net" >/dev/null
	cat >"$state/s3.json" <<JSON
{"identities":[{"name":"test","credentials":[{"accessKey":"$s3_user","secretKey":"$s3_password"}],"actions":["Admin","Read","Write","List","Tagging"]}]}
JSON
	if ! docker inspect "$s3" >/dev/null 2>&1; then
		echo "Starting SeaweedFS (S3 stand-in)"
		docker run -d --name "$s3" --network "$net" -p 127.0.0.1:8333:8333 \
			-v "$s3-data:/data" -v "$state/s3.json:/s3.json:ro" "$s3_image" \
			server -s3 -s3.config=/s3.json -dir=/data -master.volumeSizeLimitMB=200 >/dev/null
	else
		docker start "$s3" >/dev/null 2>&1 || true
	fi
	echo "Creating the bucket $bucket"
	i=0
	until curl -sf -X PUT --aws-sigv4 "aws:amz:us-east-1:s3" --user "$s3_user:$s3_password" \
		"http://127.0.0.1:8333/$bucket" -o /dev/null 2>/dev/null ||
		curl -sf -I --aws-sigv4 "aws:amz:us-east-1:s3" --user "$s3_user:$s3_password" \
			"http://127.0.0.1:8333/$bucket" -o /dev/null 2>/dev/null; do
		i=$((i + 1))
		[ "$i" -lt 45 ] || { echo "The S3 stand-in did not become ready" >&2; exit 1; }
		sleep 2
	done
	# Fixed for the life of .test/: a recovered cluster must see the same keys.
	if [ ! -f "$state/keys.yml" ]; then
		umask 077
		{
			echo "---"
			echo "test_infisical_keys:"
			echo "  ENCRYPTION_KEY: \"$(openssl rand -hex 16)\""
			echo "  AUTH_SECRET: \"$(openssl rand -base64 32)\""
			echo "  REDIS_PASSWORD: \"$(openssl rand -hex 24)\""
		} >"$state/keys.yml"
	fi
}

cluster_up() {
	mkdir -p "$state"
	if k3d cluster list "$name" >/dev/null 2>&1; then
		echo "Cluster $name already exists"
	else
		echo "Creating the k3d cluster ($image)"
		k3d cluster create "$name" --image "$image" --servers 1 --agents 1 \
			--network "$net" --kubeconfig-update-default=false --kubeconfig-switch-context=false \
			--wait --timeout 240s
	fi
	k3d kubeconfig get "$name" >"$state/kubeconfig"
	chmod 600 "$state/kubeconfig"
	echo
	echo "Ready. Context: k3d-$name. Kubeconfig: .test/kubeconfig"
	echo "Use it:  export KUBECONFIG=$state/kubeconfig"
}

cluster_down() {
	k3d cluster list "$name" >/dev/null 2>&1 && k3d cluster delete "$name" || echo "No cluster $name"
	rm -f "$state/kubeconfig"
}

case "${1:-}" in
up) preflight; infra_up; cluster_up ;;
cluster-up) preflight; cluster_up ;;
cluster-down) preflight; cluster_down ;;
down)
	preflight
	cluster_down
	docker rm -f "$s3" >/dev/null 2>&1 || true
	docker volume rm "$s3-data" >/dev/null 2>&1 || true
	docker network rm "$net" >/dev/null 2>&1 || true
	rm -rf "$state"
	echo "Everything removed"
	;;
status)
	preflight
	k3d cluster list "$name" 2>&1 || true
	docker ps --filter "name=$s3" --format 's3: {{.Status}}'
	;;
*) echo "Usage: $0 up | cluster-up | cluster-down | down | status" >&2; exit 2 ;;
esac
