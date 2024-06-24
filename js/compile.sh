#!/bin/bash

set -e
dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
filter=$1

# Compile JS:
(
    cd ../Gillian
    eval $(opam env)
    for i in $(ls -d "$dir/tests/verification"/*.js); do
        if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
            continue
        fi
        (dune exec -- gillian-js compile --verification "$i" > /dev/null 2> /dev/null && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
)
