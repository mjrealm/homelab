.PHONY: *
.EXPORT_ALL_VARIABLES:

default: metal bootstrap

metal:
	make -C metal
bootstrap:
	make -C k8s

docker: docker-metal docker-bootstrap
docker-metal:
	make -C metal docker
docker-bootstrap:
	make -C docker