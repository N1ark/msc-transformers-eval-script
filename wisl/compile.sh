#!/bin/bash

set -e
dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
filter=$1

# Compile WISL:
(
    cd ../Gillian
    eval $(opam env)
    for i in $(ls -d "$dir/tests/verification"/*.wisl); do
        if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
            continue
        fi
        (dune exec -- wisl compile --verification "$i" > /dev/null 2> /dev/null && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
    for i in $(ls -d "$dir/tests/biabduction"/*.wisl); do
        if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
            continue
        fi
        (dune exec -- wisl compile --bi-abduction "$i" > /dev/null 2> /dev/null && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
    for i in $(ls -d "$dir/tests/wpst"/*.wisl); do
        if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
            continue
        fi
        (dune exec -- wisl compile --wpst "$i" > /dev/null 2> /dev/null && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
)

# Patching
# 'empty' became a keyword or something? so need to remove that :)
sed -i '' -e 's/empty/emptyy/g' $dir/tests/verification/wand.gil
