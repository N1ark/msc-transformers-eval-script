#!/bin/bash

dir=~/Documents/GitHub/msc-transformers-eval-script/c
for i in $(find $dir/tests/collections-c/*.gil); do
    t_c_s wpst -a --runtime "$dir/tests/runtime" -l disabled "$i"
done
