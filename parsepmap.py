#!/usr/bin/env python3.9

from typing import List, Tuple, Optional
import os
import sys
import regex

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


from matplotlib import font_manager, ticker
font_path = '/Users/oscar/Library/Fonts/cmunrm.ttf'
font_manager.fontManager.addfont(font_path)
prop = font_manager.FontProperties(fname=font_path)

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = prop.get_name()

biabduct_regex = r"\w+, \d+, \d+, \d+, \d+, ([\d.]+)"
cat_regex = r"^[A-Za-z]+"


def parse_file(file_path):
    durations: List[Tuple[str, int, float]] = []
    mode = None

    with open(file_path, "r") as f:
        for line in f:
            # if line.startswith("Mode "):
            #     mode = line.split(" ")[1]
            #     mode = mode.split(":")[0]
            # if mode != "Buckets":
            #     continue
            # validate_index: %f (%i) (%s)
            if line.startswith("validate_index: "):
                dur = line.split("validate_index: ")[1]
                dur = dur.split(" ")[0]
                dur = float(dur)
                size = line.split("(")[1]
                size = size.split(")")[0]
                size = (int(size) // 5) * 5 + 2
                mode = line.split(") (")[1].split(")")[0]
                durations.append((mode, size, dur))
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

    entries: List[Tuple[str, int, float]] = []

    for file in log_files:
        file = file.strip()
        durations = parse_file(file)
        execution = file.split("/")[-1]
        execution = execution.split(".")[0]
        execution = execution.replace("_", "")
        entries.extend(durations)
        print(f"Parsed {file} ({execution})")

    df = pd.DataFrame(entries, columns=["execution", "size", "duration"])

    print("Found: ", len(df), "entries")

    # average duration per size
    df = df.groupby(["execution", "size"]).mean().reset_index()
    df["duration"] = df["duration"] * 1_000_000 # ms to ns

    def cleanup_graph(
        ax,
        *,
        legend=None, filename=None, title=None, axis="y", x_label=None, y_label=None, no_line=False
    ):
        if legend is False:
            lgd = None
        elif legend is not None:
            lgd = plt.legend(legend, loc="lower left", bbox_to_anchor=(1, 0))
        else:
            lgd = plt.legend(loc="lower left", bbox_to_anchor=(1, 0))
        plt.xticks(rotation=0)
        if not no_line:
            plt.axhline(y=0, color="black", linewidth=0.5)
        plt.ylabel(y_label)
        plt.xlabel(x_label)
        # plt.gca().set_yticklabels([i.get_text().replace('−', '$-$') for i in ax.get_yticklabels()])
        if axis:
            ax.grid(axis=axis)
        if filename is not None:
            lgd = None if lgd is None else (lgd,)
            fig.savefig(f"{filename}.pdf", bbox_extra_artists=lgd, bbox_inches="tight")
        if title is not None:
            plt.title(title)

    # plot time taken per size for each execution
    def show_time_per_size(fig, ax):
        sns.lineplot(data=df, x="size", y="duration", hue="execution", ax=ax,
            errorbar=('ci', 95))
        ax.set_yscale("log")

        def ticks_format(value, index):
            """
            get the value and returns the value as:
               integer: [0,99]
               1 digit float: [0.1, 0.99]
               n*10^m: otherwise
            To have all the number of the same size they are all returned as latex strings
            """
            return '{0:.1f}'.format(value)

        ax.minorticks_on()
        # major lines for X, major+minor for Y
        plt.grid(which='major', color='k', linestyle='-', linewidth=0.5)
        plt.grid(which='minor', color='k', alpha=0.5, linestyle=':', linewidth=0.5)
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.tick_params(axis='both', which='minor', labelsize=8)
        # ax.yaxis.set_major_formatter(ScalarFormatter())
        # ax.yaxis.set_minor_formatter(ScalarFormatter())
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())   # remove the major ticks
        ax.yaxis.set_minor_formatter(ticker.FuncFormatter(ticks_format))  #add the custom ticks



        # ax.set_xscale("log")
        cleanup_graph(ax, x_label="Size", y_label="Time (ns)", filename="time_per_size",
            title="Time taken per size for each execution")

    views = [
        show_time_per_size,
    ]

    for i, view in enumerate(views):
        fig, ax = plt.subplots(figsize=(12, 5))
        view(fig, ax)

    plt.show()
