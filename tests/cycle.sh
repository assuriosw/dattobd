#!/bin/bash

for i in {1..10}; do
    echo
    echo "=============== $i ======================"
    echo
    sudo ./elio-test.sh -f xfs
done
