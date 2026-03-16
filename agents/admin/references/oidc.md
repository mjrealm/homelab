# OIDC Configuration Guidelines (Pocket ID)

**Pocket ID** is the OIDC provider for the homelab. It is used to authenticate users and authorize access to applications.
https://github.com/pocket-id/pocket-id


For applications that doesn't support OIDC, use **OAuth2 Proxy** as a reverse proxy to handle authentication. It will handle the OIDC authentication and forward the request to the application.

## The OIDC "Catch-22" Workflow

Configuring OIDC requires credentials (Client ID and Client Secret) from Pocket ID, but Pocket ID requires the application's callback URL (Redirect URI) before it can generate the Client Secret.

### Step-by-Step Integration

1.  **Stage 1: Initial Deployment**:
    *   You must deploy the application first with its standard `ingress` configuration (as defined in `ingress.md`).
    *   This establishes the stable external URL (e.g., `https://myapp.mdeleon.dev`) needed for OIDC.
2.  **Prompt User for Pocket ID Registration**:
    *   You cannot generate the credentials yourself. You MUST stop and notify the user to log in to their Pocket ID instance and create a new **Client**.
    *   Provide the user with the exact **Redirect URI** they need to use. (Consult the specific app's documentation, usually `https://<app-url>/login/oidc/callback` or `https://<app-url>/oauth2/callback`).
    *   Ask the user to provide you with the resulting **Client ID** and **Client Secret**.
3.  **Stage 2: Credential Configuration**:
    *   Once the user provides the credentials, you must add the **Client Secret** to the application's local `secrets.dec.yaml` file.
    *   Update `values.yaml` with the non-sensitive fields (`Client ID` and `Discovery/Issuer URL`).
    *   Encrypt the secrets into a new file: `sops --encrypt secrets.dec.yaml > secrets.yaml` (Ensure you follow `helm-templates.md` and leave `secrets.dec.yaml` intact for local development).
    *   Commit and push the changes.

## Configuration Standards

- **Environment variables**: Use standard naming like `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, and `OIDC_CLIENT_SECRET`.
- **Secret Management**: OIDC secrets **MUST** be stored in `secrets.dec.yaml`, never in `values.yaml`.
- **Nesting**: In `bjw-s` app-template, ensure `env` variables are correctly nested under `containers.<name>.env`.

## Strict Rules to Follow
- Make sure the PR for the initial deployment contains instructions on how to setup OIDC for the application. Clearly highlight in the PR description. Consult Pocket ID's documentation and application documentation for examples. https://pocket-id.org/docs/client-examples
- Ensure OIDC is part of free tier of the application. If not, we will need to find an alternative solution like LDAP or `OAuth2 Proxy`.
- Encrypt secrets. Follow guidelines at `helm-templates.md`.