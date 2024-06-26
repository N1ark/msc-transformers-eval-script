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

transformerState() {
    echo "Setting up transformer state..."
    cd "$dir/../../gillian-instantiation-template"
    eval $(opam env)
    sed -i '' "s/module Prebuilt = .*/module Prebuilt = Prebuilt.C/" bin/main.ml
    dune build
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

    for i in $(seq 1 $iterations); do
        printf "\n----- Iteration $i -----"
        phase "Verification" verification "$1 verify" "$logfile"
        # phase "Biabduction" biabduction "$1 act" "$logfile"
        # phase "WPST" wpst "$1 wpst" "$logfile"
    done

    printf "\n\n"
}

if [ -z "$1" ]; then
    echo "Usage: $0 (b|t|a) [iterations] [test filter]"
    exit 1
fi

if [ "$1" == "b" ] || [ "$1" == "a" ]; then
    baseState
    test gillian-c base
fi
if [ "$1" == "t" ] || [ "$1" == "a" ]; then
    transformerState
    test instantiation transformers
fi

${dir}/../parse.py $dir $(ls -d $dir/*.log)

echo "Done."
