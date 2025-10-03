#!/bin/bash

set -e
dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
filter=$1

# $1: folder to compile
# $2: compilation flag
compile() {
    dune build
    for i in $(ls -d "$1"/*.c); do
        if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
            continue
        fi
        (dune exec --no-build -- gillian-c compile --$2 "$i" > /dev/null 2> /dev/null && echo "Compiled $i") || echo "Failed to compile $i -- ignoring."
    done
}

# $1: folder with the collections-c-for-gillian files
compileCollectionsC() {
    dune build
    for i in $(ls -d "$1"/*.c); do
        if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
            continue
        fi
        (
            dune exec --no-build -- gillian-c compile --wpst \
                -I "$1/headers" -S "$1/sources" \
                --ignore-undef --allocated-functions "$i" > /dev/null 2> /dev/null \
             && echo "Compiled $i"
        ) || echo "Failed to compile $i -- ignoring."
    done
}

compileAmazon() {
# for i in $(ls -d "$1"/*.c); do
#     if [ ! -z "$filter" ] && [[ ! "$i" == *"$filter"* ]]; then
#         continue
#     fi
#     (
#         dune exec -- gillian-c compile --verif \
#             -I $1 -I $1/includes -S $1 \
#             --fstruct-passing "$i" \
#         > /dev/null && echo "Compiled $i"
#     ) || echo "Failed to compile $i -- ignoring."
# done
    dune exec -- gillian-c compile --verif \
        $1/header.c $1/edk.c $1/array_list.c $1/ec.c $1/byte_buf.c \
        $1/hash_table.c $1/string.c $1/allocator.c \
        $1/error.c $1/base.c \
        --fstruct-passing --allocated-functions -I $1/includes  > /dev/null 2> /dev/null
    echo "Compiled Amazon"
}

# Compile C:
(
    cd ../Gillian
    eval $(opam env)
    compile "$dir/tests/verification" verification
    compile "$dir/tests/biabduction" bi-abduction
    compile "$dir/tests/wpst" wpst
    compileCollectionsC "$dir/tests/collections-c"
    # compileAmazon "$dir/tests/amazon" don't compile amazon, use Gillian-C interpreter directly
)
