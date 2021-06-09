# http://clarkgrubb.com/makefile-style-guide

MAKEFLAGS += --warn-undefined-variables --no-print-directory
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := package
.DELETE_ON_ERROR:
.SUFFIXES:
NODE_VERSION := 6.10
.PHONY: init
init:
	/bin/bash $$HOME/.nvm/nvm.sh install ${NODE_VERSION}

.PHONY: install_packages
install_packages: init
	npm install

.PHONY: package
package: install_packages
	rm -fr build
	mkdir build
	zip -r ./build/ccr-nodejs-$$(git describe --exact-match --tags $$(git log -n1 --pretty='%h')).zip .


.PHONY: cloudflare_record
cloudflare_record:
	rm -fr cloudflare_record_build
	mkdir cloudflare_record_build
	cd cloudflare_record && sam build --use-container
	cd cloudflare_record/.aws-sam/build/CloudflareRecordCustomResource && zip -r ../../../../cloudflare_record_build/cloudflare-record-python-$$(git describe --exact-match --tags $$(git log -n1 --pretty='%h')).zip *