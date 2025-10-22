#!/usr/bin/env bash

python -m pymigbench_dl.cli.main -v dl-all \
	--yaml-root dl-all/data/repo-yamls/ \
	--output-dir dl-all/output/repos
