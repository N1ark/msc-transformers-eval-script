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
    dune install
}

_transformerState() {
    echo "Setting up transformer state ($1)..."
    cd "$dir/../../Gillian/transformers"
    eval $(opam env)
    sed -i '' "s/module Prebuilt = .*/module Prebuilt = $1/" bin/transformers.ml
    dune build
    dune install
}

transformerState() {
    _transformerState "Prebuilt.Lib.C_Base"
}

transformerALocState() {
    _transformerState "Prebuilt.Lib.C_ALoc"
}

transformerSplitState() {
    _transformerState "Prebuilt.Lib.C_Split"
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
        $3 -a --runtime "$runtime" -l disabled "$i" >> "$4" 2>&1
        echo " -- $?"
    done
}

phaseAmazon() {
    awsDir="$dir/tests"

    printf "\n\n"
    echo "Amazon tests..."
    printf "\nMode Amazon:\n" >> "$2"

    echo -n "- Simpler tests"
    echo "Running file proc/aws/simple" >> "$2"
    $1 verify \
        $awsDir/amazon/header.c $awsDir/amazon/edk.c $awsDir/amazon/array_list.c $awsDir/amazon/ec.c $awsDir/amazon/byte_buf.c \
        $awsDir/amazon/hash_table.c $awsDir/amazon/string.c $awsDir/amazon/allocator.c $awsDir/amazon/error.c $awsDir/amazon/base.c \
        --runtime "$runtime" -I $awsDir/amazon/includes \
        --proc aws_cryptosdk_algorithm_taglen --proc aws_byte_cursor_read --proc aws_byte_buf_clean_up \
        --proc aws_byte_cursor_read_u8 --proc aws_cryptosdk_algorithm_ivlen \
        --proc aws_byte_cursor_read_and_fill_buffer --proc aws_byte_cursor_read_be32 --proc aws_byte_cursor_read_be16 \
        --proc aws_cryptosdk_algorithm_is_known --proc aws_string_destroy --proc aws_cryptosdk_hdr_clear \
        --proc aws_string_new_from_array --proc aws_byte_cursor_advance --proc is_known_type \
        --fstruct-passing --no-lemma-proof -l disabled >> "$2" 2>&1
    echo " -- $?"

    echo -n "- aws_cryptosdk_hdr_parse"
    echo "Running file proc/aws/aws_cryptosdk_hdr_parse" >> "$2"
    $1 verify \
        $awsDir/amazon/header.c $awsDir/amazon/edk.c $awsDir/amazon/array_list.c $awsDir/amazon/ec.c $awsDir/amazon/byte_buf.c \
        $awsDir/amazon/hash_table.c $awsDir/amazon/string.c $awsDir/amazon/allocator.c $awsDir/amazon/error.c $awsDir/amazon/base.c \
        --runtime "$runtime" -I $awsDir/amazon/includes --proc aws_cryptosdk_hdr_parse \
        --fstruct-passing --no-lemma-proof -l disabled >> "$2" 2>&1
    echo " -- $?"

    echo -n "- aws_cryptosdk_enc_ctx_deserialize"
    echo "Running file proc/aws/aws_cryptosdk_enc_ctx_deserialize" >> "$2"
    $1 verify \
        $awsDir/amazon/header.c $awsDir/amazon/edk.c $awsDir/amazon/array_list.c $awsDir/amazon/ec.c $awsDir/amazon/byte_buf.c \
        $awsDir/amazon/hash_table.c $awsDir/amazon/string.c $awsDir/amazon/allocator.c $awsDir/amazon/error.c $awsDir/amazon/base.c \
        --runtime "$runtime" -I $awsDir/amazon/includes --proc aws_cryptosdk_enc_ctx_deserialize \
        --fstruct-passing --no-lemma-proof -l disabled >> "$2" 2>&1
    echo " -- $?"

    echo -n "- parse_edk"
    echo "Running file proc/aws/parse_edk" >> "$2"
    # Z3 is a bit flaky and this test fails by itself, but passes if verified with anything else (eg. aws_byte_buf_init)
    $1 verify \
        $awsDir/amazon/header.c $awsDir/amazon/edk.c $awsDir/amazon/array_list.c $awsDir/amazon/ec.c $awsDir/amazon/byte_buf.c \
        $awsDir/amazon/hash_table.c $awsDir/amazon/string.c $awsDir/amazon/allocator.c $awsDir/amazon/error.c $awsDir/amazon/base.c \
        --runtime $awsDir/runtime -I $awsDir/amazon/includes --proc aws_byte_buf_init --proc parse_edk \
        --fstruct-passing --no-lemma-proof -l disabled >> "$2" 2>&1
    echo " -- $?"
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
        # phase "Verification" verification "$1 verify" "$logfile"
        # phase "Biabduction" biabduction "$1 act --specs-to-stdout" "$logfile"
        # phase "WPST" wpst "$1 wpst" "$logfile"
        phase "Collections-C" collections-c "$1 wpst" "$logfile"
        # phaseAmazon $1 "$logfile"
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
if [ "$1" == "t" ] || [ "$1" == "T" ] || [ "$1" == "a" ]; then
    baseState
    test transformers tr
fi
if [ "$1" == "aloc" ] || [ "$1" == "T" ] || [ "$1" == "a" ]; then
    transformerALocState
    test transformers tr-aloc
fi
if [ "$1" == "split" ] || [ "$1" == "T" ] || [ "$1" == "a" ]; then
    transformerSplitState
    test transformers tr-split
fi

echo "Done."
