#!/usr/bin/env bash

python -m pymigbench_dl.cli.main \
	-vv \
	--log-file tests/dl-single/output/download.log \
	dl-single \
	--yaml-file tests/dl-single/data/repo-yamls/mig.yaml \
	--output-dir tests/dl-single/output/
