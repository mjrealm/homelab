.PHONY: *
.EXPORT_ALL_VARIABLES:

default: metal bootstrap

metal:
	make -C metal
bootstrap:
	make -C k8s
docker:
	make -C metal docker