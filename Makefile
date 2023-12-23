.PHONY: *
.EXPORT_ALL_VARIABLES:

# KUBECONFIG = $(shell pwd)/metal/kubeconfig.yaml

default: metal bootstrap

metal:
	make -C metal
bootstrap:
	make -C bootstrap
