#!/usr/bin/env python3.9

from typing import List, Tuple, Optional
import os
import sys
import regex
import csv

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

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

    entries: List[Tuple[str, str, str, float]] = []

    for file in sys.argv[2:]:
        file = file.strip()
        durations = parse_file(file)
        execution = file.split("/")[-1]
        execution = execution.split(".")[0]
        entries.extend([(execution, mode, file, dur) for mode, file, dur in durations])
        print(f"Parsed {file} ({execution})")

    df = pd.DataFrame(entries, columns=["execution", "mode", "filename", "duration"])

    # calculate relative differences in durations, compared to the average of the base executions for that file
    df_base = (
        df[df["execution"] == "base"]
        .groupby("filename")["duration"]
        .mean()
        .reset_index()
    )
    df_base.columns = ["filename", "base"]
    df = df.merge(df_base, on="filename")
    df["relative"] = (df["base"] - df["duration"]) / df["base"]
    df.drop("base", axis=1, inplace=True)

    # save base
    df.to_csv(dest + "file_durations.csv", index=False)

    # save summed by mode
    df_mode = df.groupby(["execution", "mode"])["duration"].sum().reset_index()
    df_mode.to_csv(dest + "mode_durations.csv", index=False)

    print("Wrote: ", len(df), "entries")

    # plot the relative differences in durations, per mode+category, using boxplots
    def show_relative_diffs():
        fig, ax = plt.subplots()
        data = df[df["execution"] != "base"]
        sns.boxplot(y="relative", x="filename", hue="execution", data=data, ax=ax)
        sns.despine()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.axhline(y=0, color="black", linewidth=0.5)

    # plot the average duration per mode using barplots
    def show_avg_durations():
        fig, ax = plt.subplots()
        data = df.groupby(["execution", "mode"])["duration"].mean().reset_index()
        sns.barplot(y="duration", x="mode", hue="execution", data=data, ax=ax)
        sns.despine()
        plt.xticks(rotation=45)
        plt.tight_layout()

    show_relative_diffs()

    plt.show()
