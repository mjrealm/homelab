import os
import yaml
from pathlib import Path

# Dictionary of known apps to provide nice descriptions and URLs
KNOWN_APPS = {
    "adguard-home": {"desc": "Network-wide ad and tracker blocking", "url": "https://adguard.com/"},
    "argocd": {"desc": "Declarative continuous deployment for Kubernetes", "url": "https://argoproj.github.io/cd/"},
    "cert-manager": {"desc": "Cloud native certificate management", "url": "https://cert-manager.io/"},
    "cilium": {"desc": "eBPF-based Networking, Observability, Security", "url": "https://cilium.io/"},
    "clickhouse": {"desc": "Fast open-source OLAP database", "url": "https://clickhouse.com/"},
    "cloudflared": {"desc": "Cloudflare Tunnel client", "url": "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/"},
    "convertx": {"desc": "File converter", "url": "https://github.com/c4illin/ConvertX"},
    "databasus": {"desc": "Database management dashboard", "url": "https://github.com/BeryJu/databasus"},
    "docuseal": {"desc": "Open source document signing", "url": "https://www.docuseal.co/"},
    "docuseal-mc": {"desc": "Open source document signing (Memcached)", "url": "https://www.docuseal.co/"},
    "emqx": {"desc": "Highly scalable MQTT broker", "url": "https://www.emqx.io/"},
    "garage": {"desc": "S3-compatible distributed object storage", "url": "https://garagehq.deuxfleurs.fr/"},
    "headlamp": {"desc": "Easy-to-use extensible Kubernetes UI", "url": "https://headlamp.dev/"},
    "homebridge": {"desc": "Apple HomeKit integration bridge", "url": "https://homebridge.io/"},
    "homepage": {"desc": "Modern, fully static, fast dashboard", "url": "https://gethomepage.dev/"},
    "karakeep": {"desc": "Karaoke management system", "url": "https://karakeep.com/"},
    "karma": {"desc": "Alertmanager dashboard", "url": "https://github.com/prymitive/karma"},
    "lldap": {"desc": "Lightweight LDAP server", "url": "https://github.com/lldap/lldap"},
    "longhorn-system": {"desc": "Cloud native distributed block storage", "url": "https://longhorn.io/"},
    "mealie": {"desc": "Self-hosted recipe manager", "url": "https://mealie.io/"},
    "metallb-system": {"desc": "Network load-balancer for Kubernetes", "url": "https://metallb.universe.tf/"},
    "mongodb": {"desc": "NoSQL Database", "url": "https://www.mongodb.com/"},
    "myspeed": {"desc": "Speedtest tracking dashboard", "url": "https://myspeed.dev/"},
    "n8n": {"desc": "Workflow automation tool", "url": "https://n8n.io/"},
    "nfs-csi": {"desc": "NFS CSI driver for Kubernetes", "url": "https://github.com/kubernetes-csi/csi-driver-nfs"},
    "outline": {"desc": "Team knowledge base & wiki", "url": "https://www.getoutline.com/"},
    "paperless-ngx": {"desc": "Document management system", "url": "https://docs.paperless-ngx.com/"},
    "pgadmin": {"desc": "PostgreSQL administration tool", "url": "https://www.pgadmin.org/"},
    "pgo": {"desc": "CrunchyData Postgres Operator", "url": "https://access.crunchydata.com/documentation/postgres-operator/"},
    "plex": {"desc": "Media server", "url": "https://www.plex.tv/"},
    "pocket-id": {"desc": "OIDC Identity Provider", "url": "https://github.com/pocket-id/pocket-id"},
    "portabase": {"desc": "Database management", "url": "https://github.com/BeryJu/portabase"},
    "portainer": {"desc": "Container management UI", "url": "https://www.portainer.io/"},
    "prometheus-operator-crds": {"desc": "Prometheus Operator CRDs", "url": "https://prometheus-operator.dev/"},
    "redpanda": {"desc": "Kafka compatible streaming platform", "url": "https://redpanda.com/"},
    "reloader": {"desc": "Restarts pods on ConfigMap/Secret changes", "url": "https://github.com/stakater/Reloader"},
    "romm": {"desc": "Retro games manager", "url": "https://github.com/rommapp/romm"},
    "root": {"desc": "Root ArgoCD Application", "url": "https://argoproj.github.io/cd/"},
    "seerr": {"desc": "Media request manager", "url": "https://overseerr.dev/"},
    "servarr": {"desc": "Media management suite (Sonarr, Radarr, etc.)", "url": "https://wiki.servarr.com/"},
    "stirling-pdf": {"desc": "Robust, locally hosted web-based PDF manipulation tool", "url": "https://github.com/Stirling-Tools/Stirling-PDF"},
    "system-upgrade": {"desc": "System Upgrade Controller", "url": "https://github.com/rancher/system-upgrade-controller"},
    "upsnap": {"desc": "Wake on LAN dashboard", "url": "https://upsnap.io/"},
    "uptime-kuma": {"desc": "Self-hosted monitoring tool", "url": "https://uptime.kuma.pet/"},
    "velero": {"desc": "Backup and migrate Kubernetes resources", "url": "https://velero.io/"},
    "velero-ui": {"desc": "UI for Velero", "url": "https://github.com/kubernetes-sigs/velero-ui"},
    "without-bg": {"desc": "Background removal tool", "url": "https://github.com/withoutbg/withoutbg"},
}

def process_chart(chart_path):
    with open(chart_path, 'r') as f:
        content = f.read()

    # Skip if already has annotations
    if "annotations:" in content and "homelab/description:" in content:
        return

    # Parse yaml to get the name safely
    try:
        data = yaml.safe_load(content)
        name = data.get('name', '')
    except Exception:
        return

    # Get info or default
    info = KNOWN_APPS.get(name, {"desc": f"{name} service", "url": ""})
    desc = info["desc"].replace('"', '\\"')
    url = info["url"]

    # Insert annotations right after version: or name:
    lines = content.split('\n')
    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)
        if not inserted and line.startswith('version:'):
            new_lines.append('annotations:')
            new_lines.append(f'  homelab/description: "{desc}"')
            new_lines.append(f'  homelab/url: "{url}"')
            inserted = True

    if inserted:
        with open(chart_path, 'w') as f:
            f.write('\n'.join(new_lines))
        print(f"Updated {chart_path} for {name}")
    else:
        print(f"Could not insert into {chart_path}")

def main():
    repo_root = Path(__file__).parent.parent
    k8s_dir = repo_root / "k8s"
    
    for chart_file in k8s_dir.rglob("Chart.yaml"):
        process_chart(str(chart_file))

if __name__ == "__main__":
    main()
