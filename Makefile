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
apply-root:
	make -C k8s apply-root
# Disposable test cluster (needs Docker via OrbStack). Never touches the real cluster:
# the playbooks are pointed at .test/kubeconfig, and the test profile refuses any
# kubectl context that does not start with "k3d-".
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
