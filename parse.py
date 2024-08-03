#!/usr/bin/env python3.9

from typing import List, Tuple, Optional
import os
import sys
import regex

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

biabduct_regex = r"\w+, \d+, \d+, \d+, \d+, ([\d.]+)"
cat_regex = r"^[A-Za-z]+"


def parse_file(file_path):
    durations: List[Tuple[str, str, float]] = []
    mode = None
    file = None
    duration_so_far = 0.0

    def flush():
        if mode is None or file is None or duration_so_far == 0.0:
            return
        durations.append((mode, file, duration_so_far))

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("Mode "):
                flush()
                duration_so_far = 0.0
                mode = line.split(" ")[1]
                mode = mode.split(":")[0]
            elif line.startswith("Running file ") and not line.endswith(":"):
                flush()
                duration_so_far = 0.0
                file = line.split("/")[-1].strip()
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
    return durations


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <directory> [mode filter]".format(sys.argv[0]))
        sys.exit(1)

    dest = sys.argv[1]
    mode_filter = sys.argv[2] if len(sys.argv) == 3 else None
    if not dest.endswith("/"):
        dest += "/"
    if not os.path.exists(dest):
        os.makedirs(dest)

    log_files = []
    for root, dirs, files in os.walk(dest):
        for file in files:
            if file.endswith(".log"):
                log_files.append(os.path.join(root, file))
    log_files.sort()

    entries: List[Tuple[str, str, str, float]] = []

    for file in log_files:
        file = file.strip()
        durations = parse_file(file)
        execution = file.split("/")[-1]
        execution = execution.split(".")[0]
        entries.extend([(execution, mode, file, dur) for mode, file, dur in durations])
        print(f"Parsed {file} ({execution})")

    df = pd.DataFrame(entries, columns=["execution", "mode", "filename", "duration"])

    if mode_filter:
        df = df[df["mode"].str.contains(mode_filter, case=False)]

    # update "filename" to be "mode/filename"
    df["filename"] = df["mode"] + "/" + df["filename"]

    # calculate relative differences in durations, compared to the average of the base executions for that file
    df_base = (
        df[df["execution"] == "base"]
        .groupby("filename")["duration"]
        .mean()
        .reset_index()
    )
    df_base.columns = ["filename", "base"]
    df = df.merge(df_base, on="filename", how="left")
    df["relative"] = (df["base"] - df["duration"]) / df["base"] * 100
    df.drop("base", axis=1, inplace=True)

    # save base
    df.to_csv(dest + "file_durations.csv", index=False)

    # save summed by mode
    df_mode = df.groupby(["execution", "mode"])["duration"].mean().reset_index()
    df_mode.to_csv(dest + "mode_durations.csv", index=False)

    print("Wrote: ", len(df), "entries")

    # plot the relative differences in durations, per mode+category, using boxplots
    def show_file_relative_diffs(fig, ax):
        data = df[df["execution"] != "base"]
        colors = sns.color_palette("bright", n_colors=len(data["mode"].unique()) + 1)[1:]
        sns.boxplot(
            y="relative",
            x="filename",
            hue="execution",
            data=data,
            ax=ax,
            palette=colors,
        )
        sns.despine()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.axhline(y=0, color="black", linewidth=0.5)
        plt.title("Relative differences in durations per file")

    def show_mode_relative_diffs(fig, ax):
        data = df[df["execution"] != "base"]
        colors = sns.color_palette("bright", n_colors=len(data["execution"].unique()) + 1)[1:]
        sns.boxplot(
            y="relative", x="mode", hue="execution", data=data, ax=ax, palette=colors
        )
        sns.despine()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.axhline(y=0, color="black", linewidth=0.5)
        plt.title("Relative differences in durations per mode")

    # plot the average duration per mode using barplots
    def show_avg_durations(fig, ax):
        data = df.groupby(["execution", "mode"])["duration"].mean().reset_index()
        sns.barplot(
            y="duration", x="mode", hue="execution", data=data, ax=ax, palette="bright"
        )
        sns.despine()
        plt.xticks(rotation=45)
        plt.tight_layout()
        ax.grid(axis="y")
        plt.title("Average durations per mode")

    # plot the average duration per execution using barplots
    def show_avg_file_durations(fig, ax):
        data = (
            df.groupby(["execution", "mode", "filename"])["duration"]
            .mean()
            .reset_index()
        )
        sns.barplot(
            y="duration",
            x="filename",
            hue="execution",
            data=data,
            ax=ax,
            palette="bright",
        )
        sns.despine()
        plt.xticks(rotation=45)
        plt.tight_layout()
        ax.grid(axis="y")
        plt.title("Average durations per file")

    # plot the average relative difference per mode using barplots
    def show_avg_mode_relative_diff(fig, ax):
        data = df[df["execution"] != "base"]
        data = data.groupby(["execution", "mode"])["relative"].mean().reset_index()
        colors = sns.color_palette("bright", n_colors=len(data["execution"].unique()) + 1)[1:]
        sns.barplot(
            y="relative", x="mode", hue="execution", data=data, ax=ax, palette=colors
        )
        sns.despine()
        plt.xticks(rotation=45)
        plt.axhline(y=0, color="black", linewidth=0.5)
        plt.tight_layout()
        plt.title("Average of relative differences per mode")
        ax.grid(axis="y")
        for container in ax.containers:
            ax.bar_label(container, fmt="%.2f%%")

    views = [
        show_mode_relative_diffs,
        show_avg_durations,
        show_avg_mode_relative_diff,
    ]

    for i, view in enumerate(views):
        fig, ax = plt.subplots()
        view(fig, ax)

    plt.show()
