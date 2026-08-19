default: bootstrap

.PHONY: bootstrap apply-root
bootstrap:
	ansible-playbook bootstrap/bootstrap-playbook.yml

apply-root:
	helm template bootstrap/charts/root -n argocd | kubectl apply -f -
