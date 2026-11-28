# OIDC Configuration Guidelines (Pocket ID)

**Pocket ID** is the OIDC provider for the homelab. It is used to authenticate users and authorize access to applications.
https://github.com/pocket-id/pocket-id


Search the app's documentation to confirm it supports OIDC before offering this. If it does, offer OIDC (or no auth); if not, offer TinyAuth (or no auth). See `ingress.md`.

## The OIDC "Catch-22" Workflow

Configuring OIDC requires credentials (Client ID and Client Secret) from Pocket ID, but Pocket ID requires the application's callback URL (Redirect URI) before it can generate the Client Secret.

### Step-by-Step Integration

1.  **Prompt User for Pocket ID Registration**:
    *   You cannot generate the credentials yourself. You MUST stop and notify the user to log in to their Pocket ID instance and create a new **Client**.
    *   Provide the user with the exact **Redirect URI** they need to use. (Consult the specific app's documentation, usually `https://<app-url>/login/oidc/callback` or `https://<app-url>/oauth2/callback`).
    *   Tell the user to copy the resulting **Client ID** and **Client Secret** straight into Infisical (next step). Don't ask them to paste either into the chat.
    *   Consult Pocket ID's documentation for examples. https://pocket-id.org/docs/client-examples
2.  **Credential Configuration and Deployment**:
    *   Tell the user to add the **Client ID** and **Client Secret** to Infisical (project of the app's stack, environment `prod`, path `/<app>`) under key names you choose and list in the PR, and reference them from the app's `<app>-secrets` Secret (see "Secrets" in `helm-template.md`). They must exist before the merge.
    *   Update `values.yaml` with the non-sensitive fields (the `Discovery/Issuer URL`).
    *   List the Infisical keys in the PR, as described in "Secrets" in `AGENTS.md`.

## Strict Rules to Follow
- OIDC client IDs and secrets **MUST** be stored in Infisical, never in `values.yaml`. Refer to `helm-template.md` for more information.
- Make sure the PR clearly highlights the OIDC setup in the PR description.
- Ensure OIDC is part of free tier of the application. If not, find an alternative such as LDAP (lldap) or TinyAuth.