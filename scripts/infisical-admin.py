#!/usr/bin/env python3
"""Set up Infisical through its API, and repair it after a rebuild.

  setup   On a NEW Infisical: create the admin and organization, the `dr-admin`
          identity, one project and one Kubernetes Auth machine identity per stack,
          and put the new identity IDs into the repo. Safe to re-run with the
          dr-admin login: it only creates what is missing.
  fix-ca  After a cluster rebuild: point every stack identity at the new cluster's
          certificate authority.

Reach Infisical with --url (default: the production address) or --port-forward
(kubectl, for a cluster that has no ingress yet or a test cluster). The kubectl context
decides which cluster's CA is used, so the script shows it and asks first (--yes skips).

The stacks and their current identity IDs come from scripts/infisicalsecret/stacks.yml.
The dr-admin login comes from --client-id and --client-secret, or the environment
variables INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET, or a prompt.
"""
import argparse
import atexit
import getpass
import json
import os
import secrets
import socket
import string
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STACKS_FILE = ROOT / "scripts/infisicalsecret/stacks.yml"
NAMESPACE, SERVICE = "infisical", "infisical-infisical-standalone-infisical"
DEFAULT_URL = "https://infisical.mdeleon.dev"
ID_DIRS = ("k8s", "docs", "scripts")
ID_SUFFIXES = (".yaml", ".yml", ".md", ".j2", ".py", ".txt")


def die(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def say(msg=""):
    print(msg, flush=True)


class ApiError(Exception):
    def __init__(self, code, body):
        self.code, self.body = code, body
        msg = body.get("message") if isinstance(body, dict) else body
        super().__init__(f"HTTP {code}: {msg}")


class Api:
    def __init__(self, base):
        self.base, self.token = base.rstrip("/"), None

    def call(self, method, path, body=None, allow=()):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                code, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            code, raw = e.code, e.read()
        parsed = json.loads(raw) if raw else {}
        if code >= 400 and code not in allow:
            raise ApiError(code, parsed)
        return parsed if code < 400 else None

    def get(self, p, **k):
        return self.call("GET", p, **k)

    def post(self, p, b=None, **k):
        return self.call("POST", p, b if b is not None else {}, **k)

    def patch(self, p, b, **k):
        return self.call("PATCH", p, b, **k)

    def delete(self, p, **k):
        return self.call("DELETE", p, **k)


def kubectl(*args):
    r = subprocess.run(["kubectl", *args], capture_output=True, text=True)
    if r.returncode != 0:
        die(f"kubectl {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def start_port_forward():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen(
        ["kubectl", "-n", NAMESPACE, "port-forward", "--address", "127.0.0.1", f"svc/{SERVICE}", f"{port}:8080"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    atexit.register(proc.terminate)
    return f"http://127.0.0.1:{port}"


def wait_ready(base, seconds=900):
    end = time.time() + seconds
    while time.time() < end:
        try:
            with urllib.request.urlopen(base + "/api/status", timeout=10) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(3)
    die(f"Infisical did not answer at {base} within {seconds // 60} minutes")


def load_stacks():
    return yaml.safe_load(STACKS_FILE.read_text())["infisicalsecret_stacks"]


def confirm_cluster(yes):
    ctx = kubectl("config", "current-context").strip()
    server = kubectl("config", "view", "--minify", "-o", "jsonpath={.clusters[0].cluster.server}").strip()
    say(f"kubectl context: {ctx}\nAPI server:      {server}")
    if yes:
        return
    if input("Use this cluster's certificate authority? Type y to continue, anything else stops: ").strip().lower() not in ("y", "yes"):
        die("Stopped. Nothing was changed.")


def cluster_ca():
    ca = kubectl("get", "cm", "kube-root-ca.crt", "-n", "default", "-o", "jsonpath={.data.ca\\.crt}")
    if "BEGIN CERTIFICATE" not in ca:
        die("could not read the cluster CA from configmap kube-root-ca.crt")
    return ca


def get_login(a):
    cid = a.client_id or os.environ.get("INFISICAL_CLIENT_ID")
    csec = a.client_secret or os.environ.get("INFISICAL_CLIENT_SECRET")
    return cid, csec


def login(api, cid, csec):
    try:
        r = api.post("/api/v1/auth/universal-auth/login", {"clientId": cid, "clientSecret": csec})
    except ApiError as e:
        die(f"dr-admin login failed ({e}). Check the client ID and secret (Bitwarden item 'Infisical dr-admin').")
    api.token = r["accessToken"]


def connect(a):
    base = start_port_forward() if a.port_forward else a.url
    wait_ready(base)
    return Api(base)


# ---------------------------------------------------------------- setup

def random_password():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(28))


def bootstrap(api, a):
    email = a.email or input("Admin email: ").strip()
    org = a.org or "homelab"
    password = a.password or getpass.getpass("Admin password (Enter to generate one): ")
    generated = not password
    password = password or random_password()
    try:
        r = api.post("/api/v1/admin/bootstrap", {"email": email, "password": password, "organization": org})
    except ApiError as e:
        if e.code == 400 and "already" in str(e):
            die("This Infisical already has an admin, so setup cannot create one. "
                "Re-run with the dr-admin login (INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET) "
                "to create only what is missing, or use the browser steps.")
        raise
    api.token = r["identity"]["credentials"]["token"]
    say(f"ok: admin and organization '{org}' created ({email})")
    if generated:
        say(f"    generated admin password: {password}")
        say("    Save it now in Bitwarden, item 'Infisical admin'.")
    return r["organization"]["id"]


def ensure_dr_admin(api, org_id):
    ident = api.post("/api/v1/identities", {"name": "dr-admin", "organizationId": org_id, "role": "admin"})["identity"]
    ua = api.post(f"/api/v1/auth/universal-auth/identities/{ident['id']}", {
        "accessTokenTTL": 3600, "accessTokenMaxTTL": 3600, "accessTokenNumUsesLimit": 0,
        "clientSecretTrustedIps": [{"ipAddress": "0.0.0.0/0"}], "accessTokenTrustedIps": [{"ipAddress": "0.0.0.0/0"}],
    })["identityUniversalAuth"]
    secret = api.post(f"/api/v1/auth/universal-auth/identities/{ident['id']}/client-secrets",
                      {"description": "dr-admin", "ttl": 0, "numUsesLimit": 0})["clientSecret"]
    say("ok: identity 'dr-admin' created with Universal Auth")
    say("")
    say("    dr-admin client ID:     " + ua["clientId"])
    say("    dr-admin client secret: " + secret)
    say("    Save both now in Bitwarden, item 'Infisical dr-admin'. The secret is shown once.")
    say("")
    return ua["clientId"], secret


def org_id_of(api):
    items = api.post("/api/v1/identities/search", {"limit": 1, "offset": 0})["identities"]
    if not items:
        die("could not find the organization")
    return items[0]["orgId"]


def ensure_project(api, stack):
    projects = api.get("/api/v1/projects")["projects"]
    p = next((x for x in projects if x["slug"] == stack), None)
    created = p is None
    if created:
        p = api.post("/api/v2/workspace", {"projectName": stack, "shouldCreateDefaultEnvs": True})["project"]
        try:
            api.patch(f"/api/v1/projects/{p['id']}", {"slug": stack})
        except ApiError as e:
            die(f"could not set the slug of project '{stack}' to '{stack}' ({e}). "
                f"Set it in the browser (Project Settings, General), then re-run.")
    envs = {e["slug"]: e["id"] for e in p.get("environments", [])}
    for slug in ("dev", "staging"):
        if slug in envs:
            api.delete(f"/api/v1/projects/{p['id']}/environments/{envs[slug]}")
    if "prod" not in envs:
        api.post(f"/api/v1/projects/{p['id']}/environments", {"name": "Production", "slug": "prod"})
    say(f"ok: project '{stack}' {'created' if created else 'exists'} (environment prod only)")
    return p["id"]


def ensure_identity(api, org_id, name):
    found = api.post("/api/v1/identities/search", {"search": {"name": {"$eq": name}}, "limit": 5, "offset": 0})["identities"]
    for item in found:
        ident = item.get("identity", item)
        if ident.get("name") == name:
            return item.get("identityId") or ident["id"], False
    return api.post("/api/v1/identities", {"name": name, "organizationId": org_id, "role": "member"})["identity"]["id"], True


def ensure_identity_lookup(api, name):
    found = api.post("/api/v1/identities/search", {"search": {"name": {"$eq": name}}, "limit": 5, "offset": 0})["identities"]
    for item in found:
        ident = item.get("identity", item)
        if ident.get("name") == name:
            return item.get("identityId") or ident["id"], False
    raise KeyError(f"identity '{name}' not found")


def ensure_kubernetes_auth(api, ident_id, stack, svc_account, ca):
    cfg = {"kubernetesHost": "https://kubernetes.default.svc", "allowedNames": svc_account,
           "allowedNamespaces": "infisical-operator", "caCert": ca, "tokenReviewMode": "api"}
    if api.get(f"/api/v1/auth/kubernetes-auth/identities/{ident_id}", allow=(404,)) is None:
        api.post(f"/api/v1/auth/kubernetes-auth/identities/{ident_id}", cfg)
    else:
        api.patch(f"/api/v1/auth/kubernetes-auth/identities/{ident_id}", cfg)


def ensure_viewer(api, project_id, ident_id):
    members = api.get(f"/api/v2/workspace/{project_id}/identity-memberships")["identityMemberships"]
    if any(m["identityId"] == ident_id for m in members):
        return
    api.post(f"/api/v2/workspace/{project_id}/identity-memberships/{ident_id}", {"role": "viewer"})


def skipped(path):
    """Skip tool folders and downloaded dependency charts (a `charts` folder next to a Chart.yaml)."""
    parts = path.relative_to(ROOT).parts
    if any(p in ("node_modules", ".git", ".test") for p in parts):
        return True
    return any(p == "charts" and (ROOT.joinpath(*parts[:i]) / "Chart.yaml").exists() for i, p in enumerate(parts))


def replace_ids(old_to_new):
    changed = []
    for d in ID_DIRS:
        for path in (ROOT / d).rglob("*"):
            if not path.is_file() or path.suffix not in ID_SUFFIXES or skipped(path):
                continue
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            new = text
            for old, nw in old_to_new.items():
                new = new.replace(old, nw)
            if new != text:
                path.write_text(new)
                changed.append(path.relative_to(ROOT))
    return changed


def cmd_setup(a):
    stacks = load_stacks()
    confirm_cluster(a.yes)
    api = connect(a)
    cid, csec = get_login(a)
    if cid and csec:
        login(api, cid, csec)
        org_id = org_id_of(api)
        say("ok: logged in as dr-admin; creating only what is missing")
    else:
        org_id = bootstrap(api, a)
        cid, csec = ensure_dr_admin(api, org_id)
        if a.credentials_file:
            fd = os.open(a.credentials_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump({"clientId": cid, "clientSecret": csec}, f)
        login(api, cid, csec)
    ca = cluster_ca()
    new_ids = {}
    for stack, info in stacks.items():
        project_id = ensure_project(api, stack)
        ident_id, created = ensure_identity(api, org_id, info["service_account"])
        ensure_kubernetes_auth(api, ident_id, stack, info["service_account"], ca)
        ensure_viewer(api, project_id, ident_id)
        new_ids[stack] = ident_id
        say(f"ok: identity '{info['service_account']}' {'created' if created else 'exists'}, Kubernetes Auth set, Viewer on '{stack}'")
    old_to_new = {stacks[s]["identity_id"]: i for s, i in new_ids.items() if stacks[s]["identity_id"] != i}
    if old_to_new and not a.no_repo_update:
        files = replace_ids(old_to_new)
        say(f"ok: replaced {len(old_to_new)} identity ID(s) in {len(files)} file(s):")
        for f in files:
            say(f"      {f}")
        say("    Review with `git diff --stat`, then commit it in a pull request.")
    elif old_to_new:
        say("    New identity IDs (not written to the repo):")
        for s, i in new_ids.items():
            say(f"      {s}: {i}")
    say("\nSETUP DONE")


# ---------------------------------------------------------------- fix-ca

def cmd_fix_ca(a):
    stacks = load_stacks()
    confirm_cluster(a.yes)
    cid, csec = get_login(a)
    if not (cid and csec):
        cid = input("dr-admin client ID: ").strip()
        csec = getpass.getpass("dr-admin client secret: ")
    api = connect(a)
    login(api, cid, csec)
    ca, bad = cluster_ca(), 0
    for stack, info in stacks.items():
        name = info["service_account"]
        try:
            ident_id, created = ensure_identity_lookup(api, name)
            api.patch(f"/api/v1/auth/kubernetes-auth/identities/{ident_id}", {"caCert": ca})
            note = "" if ident_id == info["identity_id"] else f"  (repo has {info['identity_id']}: update it)"
            say(f"updated {stack} ({ident_id}){note}")
        except (ApiError, KeyError) as e:
            bad += 1
            say(f"FAILED {stack} ({name}): {e}")
    if bad:
        die(f"{bad} identity(ies) not updated")
    say("\nCA FIXED")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("setup", "fix-ca"))
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--port-forward", action="store_true", help="reach Infisical through kubectl port-forward")
    ap.add_argument("--client-id")
    ap.add_argument("--client-secret")
    ap.add_argument("--email")
    ap.add_argument("--password")
    ap.add_argument("--org")
    ap.add_argument("--yes", action="store_true", help="do not ask to confirm the kubectl context")
    ap.add_argument("--credentials-file", help="setup: also write the new dr-admin login to this file (mode 600)")
    ap.add_argument("--no-repo-update", action="store_true", help="print the new identity IDs instead of writing them")
    a = ap.parse_args()
    {"setup": cmd_setup, "fix-ca": cmd_fix_ca}[a.command](a)


if __name__ == "__main__":
    main()
