# OIDC Configuration Guidelines (Pocket ID)

OpenID Connect (OIDC) integration via **Pocket ID** follows a specific "Catch-22" workflow where application components depend on each other.

## The OIDC "Catch-22" Workflow

Configuring OIDC requires credentials (Client ID and Client Secret) from Pocket ID, but Pocket ID requires the application's callback URL (Redirect URI) before it can generate the Client Secret.

### Step-by-Step Integration

1.  **Stage 1: Initial Deployment**:
    *   Deploy the application with its standard `ingress` configuration (as defined in `ingress.md`).
    *   This establishes the stable external URL (e.g., `https://myapp.mdeleon.dev`).
2.  **Manual Step: Pocket ID Registration**:
    *   Log in to your Pocket ID instance.
    *   Create a new **Client**.
    *   **Redirect URI**: Typically `https://<app-url>/login/oidc/callback` or `https://<app-url>/oauth2/callback`. Consult the specific app's documentation for the exact path.
    *   Save the Client to generate the **Client ID** and **Client Secret**.
3.  **Stage 2: Credential Configuration**:
    *   Add the **Client Secret** to the application's local `secrets.dec.yaml` file.
    *   Update `values.yaml` with the non-sensitive fields (`Client ID`, `Discovery/Issuer URL`).
    *   Encrypt and deploy: `sops --encrypt --in-place secrets.dec.yaml && mv secrets.dec.yaml secrets.yaml`.

## Configuration Standards

- **Environment variables**: Use standard naming like `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, and `OIDC_CLIENT_SECRET`.
- **Secret Management**: OIDC secrets **MUST** be stored in `secrets.dec.yaml`, never in `values.yaml`.
- **Nesting**: In `bjw-s` app-template, ensure `env` variables are correctly nested under `containers.<name>.env`.
