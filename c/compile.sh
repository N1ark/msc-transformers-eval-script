#!/bin/bash

set -e
dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
filter=$1

# $1: folder to compile
# $2: compilation flag
compile() {
    for i in $(ls -d "$1"/*.c); do
        if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
            continue
        fi
        (dune exec -- gillian-c compile --$2 "$i" > /dev/null  && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
}

# Compile C:
(
    cd ../Gillian
    eval $(opam env)
    compile "$dir/tests/verification" verification
    compile "$dir/tests/biabduction" bi-abduction
    compile "$dir/tests/wpst" wpst
)
