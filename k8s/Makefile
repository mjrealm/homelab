default: bootstrap

.PHONY: bootstrap recover upgrade apply-root
bootstrap:
	ansible-playbook bootstrap/bootstrap.yml

recover:
	ansible-playbook bootstrap/recover.yml

# make upgrade TAGS=root   (tags: root, argocd, aws-credentials)
upgrade:
	@test -n "$(TAGS)" || { echo "Pick what to run: make upgrade TAGS=<tag>"; echo "Tags: root, argocd, aws-credentials"; exit 1; }
	ansible-playbook bootstrap/upgrade.yml --tags "$(TAGS)"

apply-root:
	$(MAKE) upgrade TAGS=root
