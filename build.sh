#!/bin/bash

TARGET_OS=${2:-ubuntu}

#create or rebuild bdsnap_builder image
docker build -t "bdsnap_builder_${TARGET_OS}" --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) -f "Dockerfile_${TARGET_OS}" .

#Run bdsnap_builder and mount sourse files and build-results folder.
WORKING_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
RESULTS_DIR="${WORKING_DIR}/build-results_${TARGET_OS}"

# clean results dir
echo "Clean '$RESULTS_DIR'"
mkdir -p "$RESULTS_DIR"
rm -rf "$RESULTS_DIR/*"

docker run -v "${RESULTS_DIR}":/build-results "bdsnap_builder_${TARGET_OS}" /build_dir/entry.sh $1
