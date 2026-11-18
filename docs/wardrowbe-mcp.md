# Wardrowbe MCP server (MCPhub)

Wardrowbe's API only accepts a user's OIDC identity, so the Wardrowbe MCP server needs one interactive sign-in before it can run headless. That sign-in happens once on a laptop with a browser, and the resulting refresh token is handed to the server. The refresh token is reused until it is revoked.

Package: `@mdeleon23/wardrowbe-mcp` (source: `~/src/wardrowbe-mcp`).

## 1. Pocket ID client

The Wardrowbe client in Pocket ID is confidential, so the login and the server both need its client secret.

- Allowed scopes include `openid profile email offline_access`.
- Redirect URI `http://localhost:8765/callback` is registered. The login step listens on that address on the laptop.

The client ID is in `k8s/apps/wardrowbe/values.yaml` and `k8s/apps/wardrowbe/secrets.dec.yaml` (`OIDC_CLIENT_ID`). The secret is `OIDC_CLIENT_SECRET` in `secrets.dec.yaml`. Do not paste it into chat, a shell history, or a PR.

## 2. One-time sign-in (laptop)

If an earlier login is still holding port 8765, stop it first: `pkill -f "cli.js login"`.

From the homelab repo, with `secrets.dec.yaml` decrypted:

```bash
make wardrowbe-mcp-login
```

The script reads `OIDC_CLIENT_ID` and `OIDC_CLIENT_SECRET` from `k8s/apps/wardrowbe/secrets.dec.yaml`, so the secret never appears on the command line. Complete the sign-in in the browser. The refresh token is written to `~/.config/wardrowbe-mcp/refresh-token.txt` with owner-only permissions, and the script does not print it. Use `OUT=<path>` to pick a different file.

The script runs the local build at `~/src/wardrowbe-mcp/dist/cli.js` if it exists (override with `WARDROWBE_MCP_DIR`). Otherwise it falls back to `npx -y @mdeleon23/wardrowbe-mcp`. The npx path is not verified: it failed with `wardrowbe-mcp: command not found` on a machine where the local build worked.

## 3. Give the token to MCPhub

Set these on the Wardrowbe server in MCPhub:

| Variable | Value |
| --- | --- |
| `WARDROWBE_URL` | `https://wardrowbe.mdeleon.dev` |
| `OIDC_ISSUER_URL` | `https://pocket.mdeleon.dev` |
| `OIDC_CLIENT_ID` | the client ID above |
| `OIDC_CLIENT_SECRET` | the client secret above |
| `OIDC_REFRESH_TOKEN` | the contents of `~/refresh-token.txt` |
| `MCP_TRANSPORT` | `http` |
| `MCP_BIND_HOST` | `0.0.0.0` |
| `MCP_API_KEY` | a bearer key for MCPhub to send to `/mcp` |

MCPhub's server definitions are not tracked in this repo, so set these in MCPhub's UI or in its config. Keep the secret and refresh token out of `values.yaml`.

Then delete the local token file: `rm ~/.config/wardrowbe-mcp/refresh-token.txt`.

## 4. Check

Restart the server in MCPhub, then call `list_items`. A signed-in response means the refresh token works. A `401` or `invalid_grant` means the token was revoked or the client secret is wrong. Rerun step 2.

## Notes

- The refresh token is tied to the Pocket ID user who signed in. If that user's access is removed, the server stops working.
- Rotating the token means rerunning step 2 and replacing `OIDC_REFRESH_TOKEN` in MCPhub.
