#!/bin/bash

dir=~/Documents/GitHub/msc-transformers-eval-script/wisl
for i in $(find $dir/tests/fractional/*.gil); do
    echo "wislf verify -a --runtime "$dir/tests/runtime" -l disabled "$i""
    wislf verify -a --runtime "$dir/tests/runtime" -l disabled "$i"
done
