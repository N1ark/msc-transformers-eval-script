#!/bin/bash

set -e
dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

# Compile WISL:
(
    cd ../Gillian
    eval $(opam env)
    for i in $(ls -d "$dir/tests/verification"/*.wisl); do
        (dune exec -- wisl compile --verification "$i" > /dev/null 2> /dev/null && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
    for i in $(ls -d "$dir/tests/biabduction"/*.wisl); do
        (dune exec -- wisl compile --bi-abduction "$i" > /dev/null 2> /dev/null && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
    for i in $(ls -d "$dir/tests/wpst"/*.wisl); do
        (dune exec -- wisl compile --wpst "$i" > /dev/null 2> /dev/null && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
)
