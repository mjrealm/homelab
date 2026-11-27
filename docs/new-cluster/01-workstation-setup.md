# Workstation setup

Prepare the machine you run `make` from. This guide assumes macOS with
[Homebrew](https://brew.sh).

## 1. Clone the repo

1. Clone it:

   ```bash
   git clone git@github.com:mjrealm/homelab.git
   cd homelab
   ```

2. Make sure you have an SSH key (`~/.ssh/id_ed25519.pub` or similar). `make
   metal` copies it to the nodes.

## 2. Install the tools

1. Run:

   ```bash
   make deps
   ```

2. Wait for it to finish. It installs:

   - Homebrew packages: `kubectl`, `helm`, `gitleaks`, `node`,
     `pyenv`.
   - The Python version in `.python-version`, through pyenv, in `.venv`.
   - From `requirements.txt` into `.venv`: `ansible`, `kubernetes`, `pre-commit`
     and `yamllint`.
   - The Ansible collections `kubernetes.core` and `community.general`.
   - The `pre-commit` hook, which runs gitleaks on every commit.

3. Run Ansible only through `make`. The Makefile puts `.venv` on `PATH`.

## 3. Check

1. Run:

   ```bash
   .venv/bin/ansible --version
   helm plugin list
   ```

2. Expect Ansible to print a version, and `helm plugin list` to show `secrets`,
   `secrets-getter` and `secrets-post-renderer`.

Next: [Cloud prerequisites](02-cloud-prerequisites.md).

## Preview the docs

1. Run:

   ```bash
   make docs
   ```

2. Open <http://localhost:3000/homelab/>. The page reloads when you save a file
   in `docs/`.
3. Stop it with Ctrl+C.
