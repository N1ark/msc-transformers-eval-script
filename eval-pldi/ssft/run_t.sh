#!/bin/bash

dir=~/Documents/GitHub/msc-transformers-eval-script/wisl
for i in $(find $dir/tests/verification/*.gil); do
    t_wisl verify -a --runtime "$dir/tests/runtime" -l disabled "$i"
done
