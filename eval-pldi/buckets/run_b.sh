#!/bin/bash

dir=~/Documents/GitHub/msc-transformers-eval-script/js
for i in $(find $dir/tests/buckets/*.gil); do
    gillian-js wpst -a --runtime "$dir/tests/runtime" -l disabled "$i"
done
