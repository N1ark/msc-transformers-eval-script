#!/bin/bash

dir=~/Documents/GitHub/msc-transformers-eval-script/c
runtime="$dir/tests/runtime"
awsDir="$dir/tests/amazon"

# Simple tests
t_c_a verify \
    $awsDir/header.c $awsDir/edk.c $awsDir/array_list.c $awsDir/ec.c $awsDir/byte_buf.c \
    $awsDir/hash_table.c $awsDir/string.c $awsDir/allocator.c $awsDir/error.c $awsDir/base.c \
    --runtime "$runtime" -I $awsDir/includes \
    --proc aws_cryptosdk_algorithm_taglen --proc aws_byte_cursor_read --proc aws_byte_buf_clean_up \
    --proc aws_byte_cursor_read_u8 --proc aws_cryptosdk_algorithm_ivlen \
    --proc aws_byte_cursor_read_and_fill_buffer --proc aws_byte_cursor_read_be32 --proc aws_byte_cursor_read_be16 \
    --proc aws_cryptosdk_algorithm_is_known --proc aws_string_destroy --proc aws_cryptosdk_hdr_clear \
    --proc aws_string_new_from_array --proc aws_byte_cursor_advance --proc is_known_type \
    --fstruct-passing --no-lemma-proof -l disabled

# aws_cryptosdk_hdr_parse
t_c_a verify \
    $awsDir/header.c $awsDir/edk.c $awsDir/array_list.c $awsDir/ec.c $awsDir/byte_buf.c \
    $awsDir/hash_table.c $awsDir/string.c $awsDir/allocator.c $awsDir/error.c $awsDir/base.c \
    --runtime "$runtime" -I $awsDir/includes --proc aws_cryptosdk_hdr_parse \
    --fstruct-passing --no-lemma-proof -l disabled

# aws_cryptosdk_enc_ctx_deserialize
t_c_a verify \
    $awsDir/header.c $awsDir/edk.c $awsDir/array_list.c $awsDir/ec.c $awsDir/byte_buf.c \
    $awsDir/hash_table.c $awsDir/string.c $awsDir/allocator.c $awsDir/error.c $awsDir/base.c \
    --runtime "$runtime" -I $awsDir/includes --proc aws_cryptosdk_enc_ctx_deserialize \
    --fstruct-passing --no-lemma-proof -l disabled

# parse_edk
t_c_a verify \
    $awsDir/header.c $awsDir/edk.c $awsDir/array_list.c $awsDir/ec.c $awsDir/byte_buf.c \
    $awsDir/hash_table.c $awsDir/string.c $awsDir/allocator.c $awsDir/error.c $awsDir/base.c \
    --runtime "$runtime" -I $awsDir/includes --proc aws_byte_buf_init --proc parse_edk \
    --fstruct-passing --no-lemma-proof -l disabled
