#!/usr/bin/env bash

python -m pymigbench_dl.cli.main \
	-vv \
	--log-file tests/dl-all/output/download.log \
	dl-all \
	--yaml-root tests/dl-all/data/repo-yamls/ \
	--output-dir tests/dl-all/output/
