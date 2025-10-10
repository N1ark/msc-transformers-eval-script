#!/bin/bash

set -e
dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
filter=$1

# $1: folder to compile
# $2: compilation flag
compile() {
    for i in $(ls -d "$1"/*.wisl); do
        if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
            continue
        fi
        ($3 compile --$2 "$i" > /dev/null  && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
}

# Compile WISL:
(
    cd ../Gillian
    eval $(opam env)
    dune build
    dune install
    compile "$dir/tests/verification" verification wisl
    compile "$dir/tests/fractional" verification wislf
)
