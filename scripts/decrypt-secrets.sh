#!/bin/sh
# Decrypt every k8s/**/secrets.yaml (sops + age) into a sibling secrets.dec.yaml.
#
# sops finds the age private key via one of:
#   SOPS_AGE_KEY       the key itself (AGE-SECRET-KEY-1...)
#   SOPS_AGE_KEY_FILE  path to a keys.txt file
#   default file       ~/.config/sops/age/keys.txt (Linux) or
#                      ~/Library/Application Support/sops/age/keys.txt (macOS)

set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
dir=${1:-"$root/k8s"}

command -v sops >/dev/null 2>&1 || { echo "sops not found in PATH" >&2; exit 1; }

# Prompt for the key when sops has no other way to find it
if [ -z "${SOPS_AGE_KEY:-}" ] && [ -z "${SOPS_AGE_KEY_FILE:-}" ] \
	&& [ ! -f "${XDG_CONFIG_HOME:-$HOME/.config}/sops/age/keys.txt" ] \
	&& [ ! -f "$HOME/Library/Application Support/sops/age/keys.txt" ]; then
	printf "Enter age private key: " >/dev/tty
	stty -echo </dev/tty
	trap 'stty echo </dev/tty' EXIT INT TERM
	read -r SOPS_AGE_KEY </dev/tty
	stty echo </dev/tty
	printf "\n" >/dev/tty
	[ -n "$SOPS_AGE_KEY" ] || { echo "no key entered" >&2; exit 1; }
	export SOPS_AGE_KEY
fi

failed=0
count=0
for f in $(find "$dir" -type f -name secrets.yaml | sort); do
	out="${f%.yaml}.dec.yaml"
	if sops --decrypt "$f" > "$out.tmp" 2>"$out.err"; then
		mv "$out.tmp" "$out"
		rm -f "$out.err"
		echo "decrypted ${f#"$root"/}"
		count=$((count + 1))
	else
		echo "FAILED    ${f#"$root"/}: $(cat "$out.err")" >&2
		rm -f "$out.tmp" "$out.err"
		failed=$((failed + 1))
	fi
done

echo "$count decrypted, $failed failed"
[ "$failed" -eq 0 ]
