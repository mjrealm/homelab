# OIDC Configuration Guidelines (Pocket ID)

**Pocket ID** is the OIDC provider for the homelab. It is used to authenticate users and authorize access to applications.
https://github.com/pocket-id/pocket-id


For applications that don't support OIDC, put them behind **TinyAuth** forward authentication (see `ingress.md`).

## The OIDC "Catch-22" Workflow

Configuring OIDC requires credentials (Client ID and Client Secret) from Pocket ID, but Pocket ID requires the application's callback URL (Redirect URI) before it can generate the Client Secret.

### Step-by-Step Integration

1.  **Prompt User for Pocket ID Registration**:
    *   You cannot generate the credentials yourself. You MUST stop and notify the user to log in to their Pocket ID instance and create a new **Client**.
    *   Provide the user with the exact **Redirect URI** they need to use. (Consult the specific app's documentation, usually `https://<app-url>/login/oidc/callback` or `https://<app-url>/oauth2/callback`).
    *   Ask the user to provide you with the resulting **Client ID** and **Client Secret**.
    *   Consult Pocket ID's documentation for examples. https://pocket-id.org/docs/client-examples
2.  **Credential Configuration and Deployment**:
    *   Once the user provides the credentials, you must add the **Client Secret** to the application's local `secrets.dec.yaml` file.
    *   Update `values.yaml` with the non-sensitive fields (`Client ID` and `Discovery/Issuer URL`).
    *   Encrypt the secrets as described in `AGENTS.md`, and leave `secrets.dec.yaml` in place for local development.

## Strict Rules to Follow
- OIDC secrets **MUST** be stored in `secrets.dec.yaml`, never in `values.yaml`. Refer to `helm-template.md` for more information.
- Make sure the PR clearly highlights the OIDC setup in the PR description.
- Ensure OIDC is part of free tier of the application. If not, find an alternative such as LDAP (lldap) or TinyAuth.