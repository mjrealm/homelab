.PHONY: *
.EXPORT_ALL_VARIABLES:

VENV := $(CURDIR)/.venv
PATH := $(VENV)/bin:$(PATH)

default: metal bootstrap

metal:
	make -C metal
bootstrap:
	make -C k8s
apply-root:
	make -C k8s apply-root
decrypt-secrets:
	./scripts/decrypt-secrets.sh
clean-secrets:
	find k8s -type f -name 'secrets.dec.yaml' -delete
deps: venv
	brew install kubectl helm sops age gitleaks
	$(VENV)/bin/ansible-galaxy collection install kubernetes.core community.general
	mkdir -p .keys
	curl -fsSL https://github.com/jkroepke.gpg \
		| awk '/^-----BEGIN/{b=1;h=1;next} /^-----END/{b=0;next} b&&h{if($$0=="")h=0;next} b&&!/^=/' \
		| base64 -d > .keys/helm-secrets.gpg
	for p in secrets secrets-getter secrets-post-renderer; do \
		helm plugin list | grep -q "^$$p[[:space:]]" || \
		helm plugin install oci://ghcr.io/jkroepke/helm-secrets/$${p}:latest --keyring .keys/helm-secrets.gpg || exit 1; \
	done
venv:
	brew install pyenv
	pyenv install --skip-existing
	test -d $(VENV) || "$$(pyenv prefix)/bin/python" -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pre-commit install
kubeconfig:
	make -C metal kubeconfig
