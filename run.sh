#!/usr/bin/env bash

python3 main.py \
	--yaml-root "./data/repo-yamls" \
	--output-dir "data/repos" \
	--max-workers 3 \
	--max-count 9
