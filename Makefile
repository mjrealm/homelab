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
apply-root:
	make -C k8s apply-root
deps: venv
	brew install kubectl helm gitleaks node k3d
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
