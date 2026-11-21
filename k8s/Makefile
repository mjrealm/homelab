default: bootstrap

.PHONY: bootstrap bootstrap-infisical apply-root
bootstrap:
	ansible-playbook bootstrap/bootstrap-playbook.yml

bootstrap-infisical:
	ansible-playbook bootstrap/bootstrap-playbook.yml \
		--tags cnpg,external-secrets,barman-cloud,infisical,infisical-operator

apply-root:
	helm template bootstrap/charts/root -n argocd | kubectl apply -f -
