#!/bin/bash

dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
runtime="$dir/tests/runtime"
iterations=$2
filefilter=$3

if [ -z "$iterations" ]; then
    iterations=1
fi

baseState() {
    echo "Setting up base state..."
    cd "$dir/../../Gillian"
    eval $(opam env)
    dune build
}

_transformerState() {
    echo "Setting up transformer state ($1)..."
    cd "$dir/../../gillian-instantiation-template"
    eval $(opam env)
    sed -i '' "s/module Prebuilt = .*/module Prebuilt = $1/" bin/main.ml
    dune build
}

transformerState() {
    _transformerState "Prebuilt.Lib.JSIL_Base"
}

transformerALocState() {
    _transformerState "Prebuilt.Lib.JSIL_ALoc"
}

transformerSplitState() {
    _transformerState "Prebuilt.Lib.JSIL_Split"
}

transformerALocSplitState() {
    _transformerState "Prebuilt.Lib.JSIL_ALocSplit"
}

# $1: Name of the phase
# $2: Test directory
# $3: Command
# $4: Log file
phase() {
    printf "\n\n"
    echo "$1 tests..."

    printf "\nMode $1:\n" >> "$4"

    for i in $(ls -d "$dir/tests/$2"/*.gil); do
        if [ ! -z "$filefilter" ] && [[ ! "$i" == *"$filefilter"* ]]; then
            continue
        fi

        echo -n "- $(basename $i)"
        echo "Running file $i" >> "$4"
        dune exec --no-build -- $3 --runtime "$runtime" -l disabled -a "$i" >> "$4" 2>&1
        echo " -- $?"
    done
}

# $1: Command
# $2: Log file
test() {
    logfile="$dir/$2.log"
    touch "$logfile"
    > "$logfile"
    echo "Running tests ($(date))" >> "$logfile"
    echo "Iterations: $iterations" >> "$logfile"

    for i in $(seq 1 $iterations); do
        printf "\n----- Iteration $i -----"
        phase "Verification" verification "$1 verify" "$logfile"
        # They don't work :(
        # phase "Biabduction" biabduction "$1 act" "$logfile"
        phase "WPST" wpst "$1 wpst" "$logfile"
        phase "Buckets" buckets "$1 wpst" "$logfile"
    done

    printf "\n\n"
}

if [ -z "$1" ]; then
    echo "Usage: $0 (b|t|aloc|split|alocsplit|a) [iterations] [test filter]"
    exit 1
fi

if [ "$1" == "b" ] || [ "$1" == "a" ]; then
    baseState
    test gillian-js base
fi
if [ "$1" == "t" ] || [ "$1" == "a" ]; then
    transformerState
    test instantiation tr
fi
if [ "$1" == "aloc" ] || [ "$1" == "a" ]; then
    transformerALocState
    test instantiation tr-aloc
fi
if [ "$1" == "split" ] || [ "$1" == "a" ]; then
    transformerSplitState
    test instantiation tr-split
fi
if [ "$1" == "alocsplit" ] || [ "$1" == "a" ]; then
    transformerALocSplitState
    test instantiation tr-alocsplit
fi

echo "Done."
