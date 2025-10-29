#!/bin/bash

# Before each script, runs:
# cd ~/Documents/GitHub/Gillian
# eval $(opam env)
# dune build
# dune install
#

GILLIAN=~/Documents/GitHub/Gillian
HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "Running from $HERE"
hyperfine --warmup 1 -i $@ \
  --setup "cd $GILLIAN && eval \$(opam env) && dune build" \
  --prepare "cd $GILLIAN && dune install" \
  --export-csv "$HERE/results.csv" \
  -n "Monolithic" "$HERE/run_b.sh > $HERE/log_b.log" \
  -n "Combinators" "$HERE/run_t.sh > $HERE/log_t.log" \
  -n "Combinators ALoc" "$HERE/run_t_a.sh > $HERE/log_t_a.log" \
  -n "Combinators Split" "$HERE/run_t_s.sh > $HERE/log_t_s.log"
