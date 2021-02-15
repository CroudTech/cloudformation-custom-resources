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
	mkdir build
	zip -r ./build/cfn-ccr-nodejs${NODE_VERSION}.zip .
