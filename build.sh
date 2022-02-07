#!/bin/bash
#create or rebuild elastiosnap_builder image
docker build -t elastiosnap_builder --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .
#Run elastiosnap_builder and mount sourse files and build-results folder.
WORKING_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
RESULTS_DIR="$WORKING_DIR"/build-results

# clean results dir
echo "Clean '$RESULTS_DIR'"
mkdir -p "$RESULTS_DIR"
rm -rf "$RESULTS_DIR/*"

docker run -v "$RESULTS_DIR":/build-results elastiosnap_builder $1
