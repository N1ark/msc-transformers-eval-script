#!/bin/bash

dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
runtime="$dir/tests/runtime"
filefilter=$2

baseState() {
    echo "Setting up base state..."
    cd "$dir/../../Gillian"
    eval $(opam env)
}

transformerState() {
    echo "Setting up transformer state..."
    cd "$dir/../../gillian-instantiation-template"
    eval $(opam env)
}

# $1: Name of the phase
# $2: Test directory
# $3: Command
# $4: Log file
phase() {
    time {
        printf "\n"
        printf "$1 tests:\n\n" >> "$4"
        echo "$1 tests..."

        for i in $(ls -d "$dir/tests/$2"/*.gil); do
            if [ ! -z "$filefilter" ] && [[ ! "$i" == *"$filefilter"* ]]; then
                continue
            fi

            echo -n "- $(basename $i)"
            echo "Running $i" >> "$4"
            dune exec -- $3 --runtime "$runtime" -l disabled -a "$i" >> "$4" 2>&1
            echo " -- $?"
        done
    }
}

# $1: Command
# $2: Log file
test() {
    touch "$2"
    > "$2"
    echo "Running tests ($(date))" >> "$2"

    phase "Verification" verification "$1 verify" "$2"
    phase "Bi-abduction" biabduction "$1 act" "$2"
    phase "WPST" wpst "$1 wpst" "$2"
}

if [ -z "$1" ]; then
    echo "Usage: $0 (base|transformers|all) [test filter]"
    exit 1
fi

if [ "$1" == "base" ] || [ "$1" == "all" ]; then
    baseState
    test wisl "$dir/base.log"
fi
if [ "$1" == "transformers" ] || [ "$1" == "all" ]; then
    transformerState
    test instantiation "$dir/transformers.log"
fi

echo "Done."
