# Set up your workstation

Prepare the Mac you run every command from. You need this once, and again on any
new machine. It takes about 15 minutes.

You need:

- A Mac with [Homebrew](https://brew.sh) installed. Check: `brew --version`
  prints a version.
- Access to the GitHub repository `mjrealm/homelab` and a GitHub account with an
  SSH key (step 1).
- The Bitwarden vault that holds the homelab items (listed in
  [Cloud prerequisites](02-cloud-prerequisites.md)).

All commands run in the macOS Terminal app.

## 1. Check your GitHub SSH access

1. Run:

   ```bash
   ssh -T git@github.com
   ```

2. Expect: `Hi <your-username>! You've successfully authenticated, but GitHub
   does not provide shell access.` That message is correct. Go to step 2.
3. If you see `Permission denied (publickey)`, you have no key on GitHub yet.
   Create one and add it:

   ```bash
   ssh-keygen -t ed25519 -C "homelab"
   cat ~/.ssh/id_ed25519.pub
   ```

   Press Enter at each question to accept the defaults. Copy the line that `cat`
   prints. In the browser, open GitHub, **Settings**, **SSH and GPG keys**,
   **New SSH key**, paste it, and **Add SSH key**. Run `ssh -T git@github.com`
   again.

The same key is also copied to the cluster nodes later, so keep it.

## 2. Clone the repo

```bash
git clone git@github.com:mjrealm/homelab.git
cd homelab
```

Expect a new folder `homelab`. Every later command runs from inside it.

## 3. Install the tools

1. Run:

   ```bash
   make deps
   ```

2. It may ask for your Mac password (to install OrbStack). It takes about 10
   minutes. It installs:

   - Homebrew packages: `kubectl`, `helm`, `gitleaks`, `node`, `k3d`, `argocd`,
     `velero`, `pyenv`.
   - OrbStack, the Docker engine used by the local test cluster.
   - The Python version in `.python-version`, through pyenv, in `.venv`.
   - From `requirements.txt` into `.venv`: `ansible`, `kubernetes`, `pre-commit`
     and `yamllint`.
   - The Ansible collections `kubernetes.core` and `community.general`.
   - The `pre-commit` hook, which runs gitleaks on every commit.

3. Expect the last lines to mention the Ansible collections, with no red error
   text. If a step fails, run `make deps` again. It skips what is installed.

Run Ansible only through `make`. The Makefile puts `.venv` on `PATH`, so a bare
`ansible-playbook` will not find the right Python.

## 4. Start OrbStack

1. Open **OrbStack** from Applications. Accept the permission prompts.
2. Leave its built-in Kubernetes switched off. Only Docker is used.
3. In the Terminal, run:

   ```bash
   docker info --format '{{.ServerVersion}}'
   ```

4. Expect a version number. An error means OrbStack is not
   running yet.

OrbStack is only needed for the local test cluster. Skip this step if you only
rebuild the real cluster.

## 5. Check the tools

Run all of these from the repo root:

```bash
.venv/bin/ansible --version
kubectl version --client
helm version --short
argocd version --client --short
velero version --client-only
k3d version
```

Expect each command to print a version and no `command not found`. If `kubectl`,
`helm`, `argocd` or `velero` is missing, run `make deps` again.

Next: [Cloud prerequisites](02-cloud-prerequisites.md).

## Preview the docs (optional)

1. Run:

   ```bash
   make docs
   ```

2. Open <http://localhost:3000/homelab/>. The page reloads when you save a file
   in `docs/`.
3. Stop it with Ctrl+C.
