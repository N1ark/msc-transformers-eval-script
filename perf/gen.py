#!/usr/bin/env python3

import os, sys

MAX_SIZE = 50

program = """
spec get(i, a)
  [[  (i == #idx) *
      (a == #addr) *
      (0i i<=# #idx) *
      (#idx i<# <SIZE>) *
      (#addr == {{ <ADDRESSES> }}) *
      <PREDICATES>
  ]]
  [[  ret == 1i ]]
  normal
proc get(i, a) {
    x := l-nth(a, i);
    r := [load](x);
    ret := l-nth(r, 1i);
    return
};
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gen.py <outdir>")
        sys.exit(1)
    outdir = sys.argv[1]
    intervals = 1 if len(sys.argv) < 3 else int(sys.argv[2])
    max = 50 if len(sys.argv) < 4 else int(sys.argv[3])
    start = 1 + intervals if intervals != 10 else 10

    if not outdir.endswith("/"):
        outdir += "/"
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    def gen_file(size):
        gen_address = lambda i: f"_$l_fresh_{i}"
        disjunctions = " \\/ ".join([f"(#x == {gen_address(i)})" for i in range(size)])
        preds = " * ".join([f"<points_to>({gen_address(i)}; 1i)" for i in range(size)])
        program_parsed = (program \
                .replace("<SIZE>", str(size) + "i") \
                .replace("<ADDRESSES>", ", ".join([gen_address(i) for i in range(size)])) \
                # .replace("<DISJUNCTIONS>", disjunctions) \
                .replace("<PREDICATES>", preds))

        with open(outdir + f"file_{size:03d}.gil", "w") as f:
            f.write(program_parsed)

    gen_file(1)
    for i in range(start, max, intervals):
        gen_file(i)

if __name__ == '__main__':
    main()
