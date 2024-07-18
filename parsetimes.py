#!/usr/bin/env python3.9

from typing import List, Tuple, Optional
import os
import sys
import regex
import csv


import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# execute_action/Alloc: 0.3ms (427)

time_regex = r"([\w|/]+): ([\d.]+)ms \((\d+)\)"


def parse_file(file_path):
    durations: List[Tuple[str, float]] = []

    with open(file_path, "r") as f:
        for line in f:
            if r := regex.match(time_regex, line):
                durations.append((r.group(1), float(r.group(2))))
    return durations


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <files...>".format(sys.argv[0]))
        sys.exit(1)

    entries: List[Tuple[str, str, float]] = []

    for file in sys.argv[1:]:
        file = file.strip()
        durations = parse_file(file)
        execution = file.split("/")[-1]
        execution = execution.split(".")[0]
        if execution.startswith("sample"):
            execution = execution.split("sample")[1]
        entries.extend([(execution, action, dur) for action, dur in durations])
        print(f"Parsed {file} ({execution})")

    # make pd dataframe with execution, action, duration
    df = pd.DataFrame(entries, columns=["execution", "action", "duration"])

    sns.violinplot(y="action", x="duration", hue="execution", data=df, split=True)
    plt.show()
