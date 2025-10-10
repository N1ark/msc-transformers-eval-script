#!/bin/bash

# Before each script, runs:
# cd ~/Documents/GitHub/Gillian
# eval $(opam env)
# dune build
# dune install
#

GILLIAN=~/Documents/GitHub/Gillian
HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

hyperfine --warmup 1 --shell=none -i $@ \
  --setup "cd $GILLIAN && eval \$(opam env) && dune build" \
  --prepare "cd $GILLIAN && dune install" \
  --export-csv "$HERE/results.csv" \
  -n "Monolithic" "$HERE/run_b.sh" \
  -n "Combinators" "$HERE/run_t.sh" \
  -n "Combinators ALoc" "$HERE/run_t_a.sh" \
  -n "Combinators Split" "$HERE/run_t_s.sh"
