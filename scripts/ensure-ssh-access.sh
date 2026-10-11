#!/bin/sh
# Make sure our SSH key is accepted by every host in an inventory group,
# offering to run ssh-copy-id (password prompt) for hosts that reject it.
#
# Usage: ensure-ssh-access.sh <inventory> <group> [playbook-dir]

set -eu

inventory=${1:?inventory required}
group=${2:?group required}
playbook_dir=${3:-.}

hosts=$(ansible-inventory -i "$inventory" --playbook-dir "$playbook_dir" --list </dev/null | python3 -c '
import json, sys
inv = json.load(sys.stdin)
hostvars = inv.get("_meta", {}).get("hostvars", {})
seen = []
def walk(g):
    for h in inv.get(g, {}).get("hosts", []):
        if h not in seen:
            seen.append(h)
    for c in inv.get(g, {}).get("children", []):
        walk(c)
walk(sys.argv[1])
for h in seen:
    v = hostvars.get(h, {})
    print(h, v.get("ansible_host", h), v.get("ansible_user", ""), v.get("ansible_port", 22))
' "$group")

[ -n "$hosts" ] || { echo "no hosts found in group '$group'" >&2; exit 1; }

echo "$hosts" | while read -r name addr user port; do
	target=${user:+$user@}$addr
	if ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new \
		-p "$port" "$target" true </dev/null >/dev/null 2>&1; then
		echo "ssh ok    $name ($target)"
		continue
	fi
	printf "SSH key not accepted by %s (%s). Copy it with ssh-copy-id? [y/N] " "$name" "$target" >/dev/tty
	read -r answer </dev/tty || answer=
	case $answer in
	[yY]*) ssh-copy-id -o StrictHostKeyChecking=accept-new -p "$port" "$target" </dev/tty ;;
	*) echo "skipping $name; ansible will likely fail to connect" >&2 ;;
	esac
done
