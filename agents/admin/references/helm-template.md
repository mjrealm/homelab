## Helm Chart Guide

## Structure
```
<app-name>/
├── Chart.yaml
├── values.yaml
├── secrets.dec.yaml
├── secrets.yaml
└── templates/
    ├── *.yaml
```

## Structure Details
### Chart.yaml
- This file contains the metadata for the Helm chart.
- It is used to identify the chart and its version.
- It follows ArgoCD's App of Apps pattern.
- The dependencies section contains the actual applications to be deployed.
- Always check the latest version of the chart in the official repository.

### values.yaml
- This file contains the custom configuration values for the Helm chart.
- Since it follows the App of Apps pattern, each top level key in this file corresponds to an application to be deployed.
- The key corresponds to the name defined in `Chart.yaml` dependencies section.

### secrets.dec.yaml
- This file contains the decrypted secrets for the Helm chart.
- It is used to specify the secrets of the chart. Example: passwords, api keys, etc.
- It follows the same format as `values.yaml`.
- **CRITICAL**: For `bjw-s` app-template v3, `env` blocks in secrets **must** be nested under `containers.<container_name>.env`. Do not put them directly under the `controllers` root.
- It is *not* pushed to git. This file is explicitly ignored in the `.gitignore` file.

### secrets.yaml
- This file contains the encrypted secrets for the Helm chart.
- It is encrypted using `helm secrets encrypt secrets.dec.yaml > secrets.yaml` command.
- Since it is encrypted, it is safe to push to git.
- Encryption is handled by `helm-secrets` plugin. It uses Mozilla SOPS for encryption with Age. The public key is stored in `.sops.yaml` file.
- Helm secrets plugin is installed by ArgoCD. It automatically decrypts the secrets when rendering the templates.

### templates/
- This directory contains any custom manifests for the chart.

## Chart Creation Guidelines
- Always use official charts if available. Only use the documentation as source of truth.
- If no official chart is available, create a new chart following Helm app template below.
- Prefer using persistent volumes over temporary storage.
- Avoid using NodePort services. Use LoadBalancer instead.
- Prefer using Ingress over LoadBalancer.
- Explicitly define image tags. Do not use :latest.
- Always expose the image tag in `values.yaml` for renovate patching.

## Helm App Template
Use [bjw-s Helm Charts](https://bjw-s-labs.github.io/helm-charts/docs/app-template/) as a template for creating new charts where official charts are not available.

### When to use
- When no official chart is available for an application
- When the official chart is not maintained or updated frequently
- When the container image is available
- When a docker-compose file is available. You can configure multiple containers in one chart.

### Example
#### Chart.yaml
```yaml
---
apiVersion: v2
name: media-stack
version: 1.0.0
dependencies:
  - name: app-template
    repository: https://bjw-s-labs.github.io/helm-charts
    version: 4.6.2

---
```

#### values.yaml
```yaml
---
app-template:
    controllers:
        filebrowser:
            replicas: 1
            strategy: Recreate
            containers:
                filebrowser:
                    image:
                        repository: ghcr.io/gtsteffaniak/filebrowser
                        tag: 1.3.0-beta-slim
        sonarr:
            replicas: 1
            strategy: Recreate
            containers:
                sonarr:
                    image:
                        repository: lscr.io/linuxserver/sonarr
                        tag: 4.0.16
    service:
        filebrowser:
            controller: filebrowser
            ports:
                http:
                    port: 80
        sonarr:
            controller: sonarr
            ports:
                http:
                    port: 8989
    persistence:
        config:
            enabled: true
            type: persistentVolumeClaim
            accessMode: ReadWriteOnce
            size: 4Gi
            advancedMounts:
                sonarr:
                    sonarr:
                        - path: /config # Refer to the volumes of the container
                          subPath: sonarr
                filebrowser:
                    filebrowser:
                        - path: /home/filebrowser/data/config.yaml
                          subPath: config.yaml
                          readOnly: false
```

## Notes
- DO NOT delete `secrets.dec.yaml` file locally. It is used for local development and testing.