#!/usr/bin/env bash

python -m pymigbench_dl.cli.main -v dl-single \
	--yaml-file dl-single/data/repo-yamls/mig.yaml \
	--output-dir dl-single/output/repos
