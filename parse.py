#!/usr/bin/env python3.9

from typing import List, Tuple, Optional
import os
import sys
import regex
import csv

biabduct_regex = r"\w+, \d+, \d+, \d+, \d+, ([\d.]+)"
cat_regex = r"^[A-Za-z]+"


def parse_file(file_path):
    durations: List[Tuple[str, str, float]] = []
    mode = None
    file = None
    iterations = 1

    duration_so_far = 0.0

    def flush():
        if mode is None or file is None or duration_so_far == 0.0:
            return
        durations.append((mode, file, duration_so_far))

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("Iterations: "):
                iterations = int(line.split(" ")[1])
            elif line.startswith("Mode "):
                mode = line.split(" ")[1]
                mode = mode.split(":")[0]
                duration_so_far = 0.0
            elif line.startswith("Running file ") and not line.endswith(":"):
                flush()
                duration_so_far = 0.0
                file = line.split("/")[-1]
            elif line.startswith("All specs succeeded"):
                dur = line.split("succeeded: ")[1]
                duration_so_far += float(dur)
            elif line.startswith("There were failures"):
                dur = line.split("failures: ")[1]
                duration_so_far += float(dur)
            elif regex.match(biabduct_regex, line):
                dur = regex.match(biabduct_regex, line).group(1)
                duration_so_far += float(dur)
            elif line.startswith("Compilation time:"):
                # negate to make up for extra
                dur = line.split("time: ")[1]
                dur = dur.split("s")[0]
                duration_so_far -= float(dur)
            elif line.startswith("Total time (Compilation + Symbolic testing)"):
                dur = line.split("Symbolic testing):")[1]
                dur = dur.split("s")[0]
                duration_so_far += float(dur)

    # Average by iterations
    durations = [(mode, file, dur / iterations) for mode, file, dur in durations]
    return durations


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: {} <dest> <files...>".format(sys.argv[0]))
        sys.exit(1)

    dest = sys.argv[1]
    if not dest.endswith("/"):
        dest += "/"
    if not os.path.exists(dest):
        os.makedirs(dest)

    entries: List[Tuple[str, str, str, str, float]] = []

    def get_cat(file):
        m = regex.match(cat_regex, file)
        if m is None:
            return file
        return m.group(0)

    for file in sys.argv[2:]:
        file = file.strip()
        durations = parse_file(file)
        execution = file.split("/")[-1]
        execution = execution.split(".")[0]
        entries.extend(
            [
                (execution, mode, get_cat(file), file, dur)
                for mode, file, dur in durations
            ]
        )
        print(f"Parsed {file} ({execution})")

    # exec, mode, cat, file, dur, rel
    rel_entries: List[Tuple[str, str, str, str, float, float]] = []
    for exec, mode, cat, file, dur in entries:
        if exec == "base":
            rel_entries.append((exec, mode, cat, file, dur, 0))
            continue
        base_dur = None
        for e, m, c, f, d in entries:
            if e == "base" and m == mode and c == cat and f == file:
                base_dur = d
                break
        if base_dur is None:
            print("Could not find base for", exec, mode, cat, file)
            rel_entries.append((exec, mode, cat, file, dur, -1))
            continue
        rel_entries.append(
            (exec, mode, cat, file, dur, (base_dur - dur) / base_dur * 100)
        )

    # sum durations by cat, ignoring relative
    cat_entries: List[Tuple[str, str, str, float]] = []
    done_cats = set()
    for exec, mode, cat, file, dur, _ in rel_entries:
        if (exec, mode, cat) in done_cats:
            continue
        sum_dur = 0
        for e, m, c, _, d, _ in rel_entries:
            if e == exec and m == mode and c == cat:
                sum_dur += d
        cat_entries.append((exec, mode, cat, sum_dur))
        done_cats.add((exec, mode, cat))
    rel_cat_entries: List[Tuple[str, str, str, float, float]] = []
    for exec, mode, cat, dur in cat_entries:
        if exec == "base":
            rel_cat_entries.append((exec, mode, cat, dur, 0))
            continue
        base_dur = None
        for e, m, c, d in cat_entries:
            if e == "base" and m == mode and c == cat:
                base_dur = d
                break
        if base_dur is None:
            print("Could not find base for", exec, mode, cat)
            rel_cat_entries.append((exec, mode, cat, dur, -1))
            continue
        rel_cat_entries.append(
            (exec, mode, cat, dur, (base_dur - dur) / base_dur * 100)
        )

    # sum durations by mode, ignoring relative
    mode_entries: List[Tuple[str, str, float]] = []
    done_modes = set()
    for exec, mode, cat, file, dur, _ in rel_entries:
        if (exec, mode) in done_modes:
            continue
        sum_dur = 0
        for e, m, _, _, d, _ in rel_entries:
            if e == exec and m == mode:
                sum_dur += d
        mode_entries.append((exec, mode, sum_dur))
        done_modes.add((exec, mode))
    mode_rel_entries: List[Tuple[str, str, float, float]] = []
    for exec, mode, dur in mode_entries:
        if exec == "base":
            mode_rel_entries.append((exec, mode, dur, 0))
            continue
        base_dur = None
        for e, m, d in mode_entries:
            if e == "base" and m == mode:
                base_dur = d
                break
        if base_dur is None:
            print("Could not find base for", execution, mode)
            mode_rel_entries.append((execution, mode, dur, -1))
            continue
        mode_rel_entries.append(
            (execution, mode, dur, (base_dur - dur) / base_dur * 100)
        )

    with open(dest + "mode_durations.csv", "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["execution", "mode", "duration", "relative (%)"])
        for entry in mode_rel_entries:
            writer.writerows([entry])

    with open(dest + "file_durations.csv", "w+") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["execution", "mode", "category", "filename", "duration", "relative (%)"]
        )
        for entry in rel_entries:
            writer.writerows([entry])

    with open(dest + "category_durations.csv", "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["execution", "mode", "category", "duration", "relative (%)"])
        for entry in rel_cat_entries:
            writer.writerows([entry])

    print(
        "Wrote: ",
        len(mode_entries),
        "mode entries",
        len(rel_entries),
        "file entries",
        len(rel_cat_entries),
        "category entries",
    )

    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    # plot the relative differences in durations, per mode+category, using boxplots
    fig, ax = plt.subplots()
    data = {}
    groups = []
    for exec, _, cat, file, _, rel in rel_entries:
        if exec == "base":
            groups.append(cat)
            continue
        if exec not in data:
            data[exec] = []
        data[exec].append(rel)

    df = pd.DataFrame(data)
    df["Category"] = groups
    ax = (
        df.set_index("Category", append=True)
        .stack()
        .to_frame()
        .reset_index()
        .rename(columns={"level_2": "execution", 0: "relative"})
        .drop("level_0", axis="columns")
        .pipe((sns.boxplot, "data"), x="Category", y="relative", hue="execution")
    )
    sns.despine()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.axhline(y=0, color="black", linewidth=0.5)
    plt.show()
