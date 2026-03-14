# Ingress Creation Guidelines

## General Rules
- Use the Helm chart's built-in `ingress` configuration instead of writing custom Kubernetes `Ingress` manifests from scratch.
- Almost all apps have an `ingress:` block available in their `values.yaml`.

## Standard Annotations & Configuration
When exposing an application to the network, ensure the following standards are met:

### 1. TLS and Certificates
Always enable TLS. Use `cert-manager` to automatically provision certificates via Let's Encrypt.
- **Annotation**: `cert-manager.io/cluster-issuer: letsencrypt-prod`
- **TLS Block**: Must specify the `secretName` (usually `<appname>-tls-cert`) and the hosts list.

### 2. Homepage Integration
To automatically add the newly exposed app to the Homelab dashboard, use the `gethomepage.dev` annotations.
Follow guide at https://gethomepage.dev/configs/kubernetes/#automatic-service-discovery

Example:
```yaml
    gethomepage.dev/enabled: "true"
    gethomepage.dev/name: <AppName>
    gethomepage.dev/description: <Short description>
    gethomepage.dev/group: <Category>
    gethomepage.dev/icon: <icon.png>
```

#### Icons
Follow icon guidelines at https://gethomepage.dev/configs/services/#icons
- Prefer selfh.st icons at https://selfh.st/icons/
- Without prefix, it uses icons from https://github.com/homarr-labs/dashboard-icons
- Verify the icon is actually available. For example, https://cdn.jsdelivr.net/gh/selfhst/icons@main/png/actual-budget.png for `selfh.sh` icon of Actual Budget. Use `curl` to verify the icon is available.
- Prefer PNG icons over SVG.
- If the icon is not available, suggest a similar app icon.

#### Pod Selection (Optional)
The `gethomepage.dev/pod-selector` annotation is **optional** and is only required if there are multiple apps in the same namespace (e.g., when a database like Postgres is also installed alongside the app).
- If used, the homelab-admin **must** verify the label is actually correct against the deployed pods (e.g., `app.kubernetes.io/name=<my-app>`).
- If there is only one app in the namespace, do not include this annotation.

### 3. Authentication (Optional)
If the application lacks built-in authentication and needs to be secured, use the external OAuth proxy annotations:
```yaml
nginx.ingress.kubernetes.io/auth-signin: https://oauth-proxy.mdeleon.dev/oauth2/start?rd=https://$host$request_uri
nginx.ingress.kubernetes.io/auth-url: https://oauth-proxy.mdeleon.dev/oauth2/auth
```

### 4. YAML Anchors for Hosts
To prevent typos and keep the file DRY, use YAML anchors (`&appname`) to define the hostname once, and reference it (`*appname`) in the TLS hosts array. The standard internal domain is `mdeleon.dev` or a subdomain of it.

## Example: bjw-s App-Template Ingress
Here is the standard way to define an ingress when using the `bjw-s` helm app-template:

```yaml
ingress:
  main: # Or the name of the controller
    enabled: true
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
      gethomepage.dev/enabled: "true"
      gethomepage.dev/name: "My App"
      gethomepage.dev/group: "Media" # See list of groups in apps/homepage/secrets.dec.yaml
      gethomepage.dev/icon: "app-icon.png"
      gethomepage.dev/pod-selector: "app.kubernetes.io/name=myapp" # OPTIONAL: Only use if multiple apps share the namespace. Must be verified.
      gethomepage.dev/weight: "2" # If you want to change the order of the apps in the group
    hosts:
      - host: &myapp myapp.mdeleon.dev
        paths:
          - path: /
            pathType: Prefix
            service:
              identifier: main # Matches controller name
              port: http       # Matches service port name
    tls:
      - secretName: myapp-tls-cert
        hosts:
          - *myapp # References the anchor defined in the hosts section
```
