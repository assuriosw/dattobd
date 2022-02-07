#!/bin/bash
#----------------------------------------------------------------------
#This script will be copied to docker image and launched as entry point
#----------------------------------------------------------------------
cd /build_dir
make deb RELEASE_NUMBER=$1
cp pkgbuild/DEBS/all/elastio-snap-*.deb pkgbuild/DEBS/amd64/*.deb /build-results
