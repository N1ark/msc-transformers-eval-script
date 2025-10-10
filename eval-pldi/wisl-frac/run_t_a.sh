#!/bin/bash

dir=~/Documents/GitHub/msc-transformers-eval-script/wisl
for i in $(find $dir/tests/fractional/*.gil); do
    t_wislf_a verify -a --runtime "$dir/tests/runtime" -l disabled "$i"
done
