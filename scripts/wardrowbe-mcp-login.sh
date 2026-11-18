#!/usr/bin/env bash
# One-time Wardrowbe OIDC sign-in. Writes a refresh token to a 0600 file (never printed).
# Usage: make wardrowbe-mcp-login [OUT=path]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SECRETS="$ROOT/k8s/apps/wardrowbe/secrets.dec.yaml"
ISSUER="${OIDC_ISSUER_URL:-https://pocket.mdeleon.dev}"
MCP_DIR="${WARDROWBE_MCP_DIR:-$HOME/src/wardrowbe-mcp}"
OUT="${OUT:-$HOME/.config/wardrowbe-mcp/refresh-token.txt}"

if [[ ! -f "$SECRETS" ]]; then
  echo "Missing $SECRETS. Run 'make decrypt-secrets' first." >&2
  exit 1
fi

read_key() {
  sed -n "s/^ *$1: *//p" "$SECRETS" | head -1 | sed -E 's/^"(.*)"$/\1/'
}
CLIENT_ID="$(read_key OIDC_CLIENT_ID)"
CLIENT_SECRET="$(read_key OIDC_CLIENT_SECRET)"
if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
  echo "OIDC_CLIENT_ID or OIDC_CLIENT_SECRET not found in $SECRETS." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
umask 077
TMP="$OUT.tmp"
trap 'rm -f "$TMP"' EXIT

# The secret goes in the environment, not on the command line. The CLI reads OIDC_CLIENT_SECRET.
export OIDC_CLIENT_SECRET="$CLIENT_SECRET"
if [[ -f "$MCP_DIR/dist/cli.js" ]]; then
  node "$MCP_DIR/dist/cli.js" login --issuer "$ISSUER" --client-id "$CLIENT_ID" > "$TMP"
else
  npx -y @mdeleon23/wardrowbe-mcp login --issuer "$ISSUER" --client-id "$CLIENT_ID" > "$TMP"
fi

if [[ ! -s "$TMP" ]]; then
  echo "Login finished without a refresh token." >&2
  exit 1
fi
mv "$TMP" "$OUT"
trap - EXIT
echo "Refresh token written to $OUT (not printed)."
echo "Set OIDC_REFRESH_TOKEN in MCPhub to its contents, then delete the file."
