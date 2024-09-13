#!/usr/bin/env python3.9
import os, json


dirs = ["c", "js", "wisl"]
accepted_ext = [".c", ".js", ".wisl"]

def main():
    # directory, test category, name, base locs, compiled locs, (#procs, #specs, #preds, #lemmas)
    files: list[tuple[str, str, str, int, int, tuple[int,int,int, int]]] = []

    for d in dirs:
        # list directories in {d}/tests
        test_dirs = os.listdir(f"{d}/tests")
        for td in test_dirs:
            if td == "runtime" or not os.path.isdir(f"{d}/tests/{td}"):
                continue
            # list files in {d}/tests/{td}
            test_files = os.listdir(f"{d}/tests/{td}")
            for tf in test_files:
                # check if file is accepted
                if os.path.splitext(tf)[1] in accepted_ext:
                    # get size of file
                    with open(f"{d}/tests/{td}/{tf}", "r") as f:
                        size = len([l for l in f if l.strip() != ""])
                    # get size of compiled file (eg. "abc.c" -> "ab.gil")
                    compiled = os.path.splitext(tf)[0] + ".gil"
                    size_compiled = 0
                    counters = [0, 0, 0, 0]
                    with open(f"{d}/tests/{td}/{compiled}", "r") as f:
                        init_data = False
                        for l in f:
                            l = l.strip()
                            if l == "":
                                continue
                            if l == "#begin_init_data":
                                init_data = True
                            elif l == "#end_init_data":
                                init_data = False
                            elif not init_data:
                                size_compiled += 1
                                if l.startswith("proc"):
                                    counters[0] += 1
                                elif l.startswith("spec"):
                                    counters[1] += 1
                                elif l.startswith("pred"):
                                    counters[2] += 1
                                elif l.startswith("lemma"):
                                    counters[3] += 1

                    print(f"({d}) {td}/{tf} has {size}/{size_compiled} lines")
                    files.append((d, td, tf, size, size_compiled, (counters[0], counters[1], counters[2], counters[3])))

    # sorty by: directory, test category, name
    files.sort(key=lambda x: (x[0], x[1], x[2]))
    # write to file
    with open("testfiles.json", "w") as f:
        json.dump(files, f, indent=4)
    with open("outlatex.tex", "w") as f:
        for d, td, tf, size, size_compiled, counts in files:
            parsed_name = td + "/" + tf.replace("_", "\\_")
            counts_parsed = "/".join(str(c) for c in counts)
            f.write(f"{d.upper()} & {{\\footnotesize \\code{{{parsed_name}}} }} & {size} & {size_compiled} & {counts_parsed} \\\\ \\hline\n")


if __name__ == '__main__':
    main()
