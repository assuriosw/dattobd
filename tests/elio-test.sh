#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only

#
# Copyright (C) 2019 Datto, Inc.
# Additional contributions by Elastio Software, Inc are Copyright (C) 2020 Elastio Software Inc.
#

if [ "$EUID" -ne 0 ]; then
    echo "Run as sudo or root."
    exit 1
fi

me=$(basename $0)
filesystems=(ext2 ext3 ext4 xfs)

usage()
{
    echo "Usage: $me -d /dev/vda2 -f ext4 | -h"
    echo
    echo "  -f | --filesystem : File system to test: $(echo ${filesystems[*]} | sed "s/ /, /g")."
    echo "                      ext4 is used by default, if this parameter is not specified."
    echo "  -d | --device     : Block device to use instead of the loopback device."
    echo "                      NOTE: This device will be formatted during the test and all data there will be lost!"
    echo "                      A loopback device is used by default, if this parameter is not specified."
    echo "  -h | --help       : Show this usage help."
}

while [ "$1" != "" ]; do
    case $1 in
        -d | --device)      shift && export TEST_DEVICE=$1 ;;
        -f | --filesystem)  shift && export TEST_FS=$1 ;;
        -h | --help)        usage && exit ;;
        *)                  echo "Wrong arguments!"
                            usage && exit 15 ;;
    esac
        shift
done

if [ -n "$TEST_DEVICE" ] && ! lsblk $TEST_DEVICE >/dev/null 2>&1; then
    echo "The script's argumet $TEST_DEVICE seems to be not a block device."
    exit 1
fi

if [ -n "$TEST_FS" ] && ! echo ${filesystems[*]} | grep -w -q $TEST_FS; then
    echo "The script's argumet $TEST_FS seems to be not a supported file system, one of $(echo ${filesystems[*]} | sed "s/ /, /g")."
    exit 1
fi

packman="apt-get"
which yum >/dev/null && packman=yum
which pip3 >/dev/null || $packman install -y python3-pip

if ! pip3 list 2>/dev/null | grep -q cffi ; then
    echo "Python module CFFI is not installed. Installing it..."
    pip3 install cffi
fi

echo
echo "elastio-snap: $(git rev-parse --short HEAD)"
echo "kernel: $(uname -r)"
echo "filesystem: $([ -n "$TEST_FS" ] && echo $TEST_FS || echo ext4 )"
echo "gcc: $(gcc --version | awk 'NR==1 {print $3}')"
echo "bash: ${BASH_VERSION}"
echo "python: $(python3 --version)"
echo

dmesg -c &> /dev/null
>| dmesg.log

python3 -m unittest -v
ret=$?
dmesg > dmesg.log

exit ${ret}
