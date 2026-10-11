default: cluster

ssh-access:
	../scripts/ensure-ssh-access.sh inventory metal
cluster: ssh-access
	ansible-playbook --inventory inventory cluster-playbook.yml -K
kubeconfig:
	../scripts/ensure-ssh-access.sh inventory master
	ansible-playbook --inventory inventory kubeconfig-playbook.yml -K
