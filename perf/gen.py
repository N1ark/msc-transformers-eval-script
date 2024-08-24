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
    if len(sys.argv) != 2:
        print("Usage: python3 gen.py <outdir>")
        sys.exit(1)
    outdir = sys.argv[1]
    if not outdir.endswith("/"):
        outdir += "/"
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    def gen_file(size):
        gen_address = lambda i: f"#a_{i}"
        disjunctions = " \\/ ".join([f"(#x == {gen_address(i)})" for i in range(size)])
        preds = " * ".join([f"<points_to>({gen_address(i)}; 1i)" for i in range(size)])
        program_parsed = (program \
                .replace("<SIZE>", str(size) + "i") \
                .replace("<ADDRESSES>", ", ".join([gen_address(i) for i in range(size)])) \
                # .replace("<DISJUNCTIONS>", disjunctions) \
                .replace("<PREDICATES>", preds))

        with open(outdir + f"file_{size:02d}.gil", "w") as f:
            f.write(program_parsed)

    for i in range(1, MAX_SIZE, 1):
        gen_file(i)

if __name__ == '__main__':
    main()
