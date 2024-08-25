#!/usr/bin/env python3

import sys, os, time

TEST_DURATION = 60 * 2 # 2 minutes per test file
OUT = "results.csv"
LOGS = "logs.txt"

def main():
    if len(sys.argv) != 2:
        print("Usage: python exec.py <input folder>")
        sys.exit(1)
    inputs = sys.argv[1]
    if inputs[-1] != '/':
        inputs += '/'

    # make log and outs files if they don't exist
    out = inputs + OUT
    logs = inputs + LOGS
    with open(out, 'w') as f:
        f.write("file,time,iters\n")
    with open(logs, 'w') as f:
        f.write("")

    files = []
    for file in os.listdir(inputs):
        if file.endswith(".gil"):
            files.append(file)

    files = sorted(files)
    print(f"Running {len(files)} files in {inputs}...")
    for file in files:
        now = time.time()
        iters = 0
        print(f"Running {file}...")
        while time.time() - now < TEST_DURATION:
            iters += 1
            res = os.system(f"dune exec --no-build -- instantiation verify -a -l disabled {inputs}{file} >> {logs}")
            if res != 0:
                print(f"Error running {file}")
                sys.exit(1)
        total_time = time.time() - now
        print(f"Finished {file} in {total_time} seconds with {iters} iterations.")
        with open(out, 'a') as f:
            f.write(f"{file},{total_time},{iters}\n")

if __name__ == '__main__':
    main()
