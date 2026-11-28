.PHONY: *
.EXPORT_ALL_VARIABLES:

VENV := $(CURDIR)/.venv
PATH := $(VENV)/bin:$(PATH)

default: metal bootstrap

metal:
	make -C metal
bootstrap:
	make -C k8s
upgrade:
	make -C k8s upgrade TAGS=$(TAGS)
# make infisicalsecret   (asks questions; skip them with ARGS="-e stack=apps -e app=convertx")
infisicalsecret:
	ansible-playbook scripts/infisicalsecret/playbook.yml $(ARGS)
# New Infisical: create the admin, projects and identities through its API.
infisical-setup:
	python3 scripts/infisical-admin.py setup $(ARGS)
# After a rebuild: restore (stage 1), fix the CA, then add the stacks.
recover:
	make -C k8s recover
recover-ca:
	python3 scripts/infisical-admin.py fix-ca $(ARGS)
# make recover-stage STAGE=platform   or   STAGE=all
STAGE_ARGS_platform = -e '{"root_stacks":["system","platform"]}'
STAGE_ARGS_all =
recover-stage:
	@test "$(STAGE)" = platform -o "$(STAGE)" = all || { echo "Use: make recover-stage STAGE=platform  or  STAGE=all"; exit 1; }
	cd k8s && ansible-playbook bootstrap/upgrade.yml --tags root $(STAGE_ARGS_$(STAGE))
apply-root:
	make -C k8s apply-root
# Disposable test cluster (needs Docker via OrbStack). Never touches the real cluster:
# the playbooks are pointed at .test/kubeconfig, and the test profile refuses any
# kubectl context that does not start with "k3d-".
# Fail when a database backup could overlap Velero's Longhorn CSI snapshots.
check-backups:
	python3 scripts/check-backup-windows.py
test-up:
	test/cluster.sh up
test-down:
	test/cluster.sh down
test-status:
	test/cluster.sh status
test-bootstrap:
	@test -f .test/kubeconfig || { echo "No test cluster. Run: make test-up"; exit 1; }
	KUBECONFIG=$(CURDIR)/.test/kubeconfig K8S_AUTH_KUBECONFIG=$(CURDIR)/.test/kubeconfig \
		ansible-playbook k8s/bootstrap/bootstrap.yml -e @test/vars.yml -e @.test/keys.yml $(ARGS)
test-recover:
	@test -f .test/kubeconfig || { echo "No test cluster. Run: make test-up"; exit 1; }
	KUBECONFIG=$(CURDIR)/.test/kubeconfig K8S_AUTH_KUBECONFIG=$(CURDIR)/.test/kubeconfig \
		ansible-playbook k8s/bootstrap/recover.yml -e @test/vars.yml -e @.test/keys.yml -e @test/recovery.yml $(ARGS)
test-dr:
	test/dr.sh run
deps: venv
	brew install kubectl helm gitleaks node k3d argocd velero
	brew install --cask orbstack
	$(VENV)/bin/ansible-galaxy collection install kubernetes.core community.general
venv:
	brew install pyenv openssl@3 xz
	CPPFLAGS="-I$$(brew --prefix openssl@3)/include -I$$(brew --prefix xz)/include" \
	LDFLAGS="-L$$(brew --prefix openssl@3)/lib -L$$(brew --prefix xz)/lib" \
	PKG_CONFIG_PATH="$$(brew --prefix openssl@3)/lib/pkgconfig" \
		pyenv install --skip-existing
	test -d $(VENV) || "$$(pyenv prefix)/bin/python" -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pre-commit install
kubeconfig:
	make -C metal kubeconfig
docs:
	npm --prefix website install
	npm --prefix website start
