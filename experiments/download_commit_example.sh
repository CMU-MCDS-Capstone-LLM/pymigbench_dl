#!/usr/bin/env bash

source ./envrc
source config.sh

ZIPPED_REPO_PATH=""$REPO_BASE"/example.zip"

mkdir -p "$ZIPPED_REPO_PATH"

curl -L \
	-H "Authorization: token "$GITHUB_TOKEN"" \
	-o "$REPO_PATH" \
	https://api.github.com/repos/"$REPO"/zipball/"$COMMIT_SHA"

cd "$REPO_BASE"
unzip "$ZIPPED_REPO_PATH"
rm "$ZIPPED_REPO_PATH"
