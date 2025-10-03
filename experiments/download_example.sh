#!/usr/bin/env bash

# Example script to download PyMigBench dataset
# Make sure to set your GITHUB_TOKEN environment variable first

# Source environment variables
source ./envrc

# Example usage of the Python downloader
# Make sure you have downloaded PyMigBench YAML files to ./repo-yamls first
python3 main.py \
    --yaml-root "./repo-yamls" \
    --output-dir "repos" \
    --max-workers 3 \
    --max-count 10  # Remove this for full download

echo "Download complete! Check the 'repos' directory for downloaded commits."