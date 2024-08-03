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
    durations: List[Tuple[str, str, str, float, float, int]] = []
    mode = "?"
    file = "?"
    file_id = 0

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("Mode "):
                mode = line.split(" ")[1]
                mode = mode.split(":")[0]
            elif line.startswith("Running file ") and not line.endswith(":"):
                file = line.split("/")[-1].strip()
                file_id += 1
            elif r := regex.match(time_regex, line):
                action = r.group(1)
                time = float(r.group(2))
                count = float(r.group(3))
                durations.append((mode, file, action, time, count, file_id))
    return durations


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <directory> [mode filter]".format(sys.argv[0]))
        sys.exit(1)

    mode_filter = sys.argv[2] if len(sys.argv) > 2 else None

    log_files = []
    for root, dirs, files in os.walk(sys.argv[1]):
        for file in files:
            if file.endswith(".log"):
                log_files.append(os.path.join(root, file))
    log_files.sort()

    entries = []

    for file in log_files:
        file = file.strip()
        durations = parse_file(file)
        execution = file.split("/")[-1]
        execution = execution.split(".")[0]
        entries.extend(
            [
                (execution, mode, file, action, dur, count, file_id)
                for mode, file, action, dur, count, file_id in durations
            ]
        )
        print(f"Parsed {file} ({execution})")

    if mode_filter:
        entries = [
            e
            for e in entries
            if e[1].lower().find(mode_filter.lower()) != -1
        ]

    # add missing actions as 0 for each (execution, mode, file)
    keys = set([(e[0], e[1], e[2]) for e in entries])
    actions = set([e[3] for e in entries])
    for key in keys:
        for action in actions:
            if not any(
                [
                    e[0] == key[0]
                    and e[1] == key[1]
                    and e[2] == key[2]
                    and e[3] == action
                    for e in entries
                ]
            ):
                entries.append((key[0], key[1], key[2], action, 0.0, 0.0, 0))

    # make pd dataframe with execution, action, duration
    df = pd.DataFrame(
        entries,
        columns=[
            "execution",
            "mode",
            "file",
            "action",
            "total_duration",
            "count",
            "file_id",
        ],
    )
    print("Parsed ", len(df), " entries")

    df["file"] = df["mode"] + "/" + df["file"]
    df["duration"] = (
        df["total_duration"] / df["count"] * 1000
    )  # duration for 1000 executions in ms
    df["action"] = df["action"].str.replace("consume", "cons")
    df["action"] = df["action"].str.replace("produce", "prod")
    df["action"] = df["action"].str.replace("execute_action", "ea")

    def avg_action_duration(fig, ax):
        data = df.copy()
        sns.barplot(
            x="action",
            y="duration",
            hue="execution",
            data=data,
            ax=ax,
            palette="bright",
        )
        sns.despine()
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.axhline(y=0, color="black", linewidth=0.5)
        plt.ylabel("Duration (ms)")
        plt.title("Average action duration for 1000 executions")
        ax.grid(axis="y")
        for container in ax.containers:
            ax.bar_label(container, fmt="%.2f")

    def avg_action_call_count(fig, ax):
        data = df.copy()
        sns.barplot(
            x="action", y="count", hue="execution", data=data, ax=ax, palette="bright"
        )
        sns.despine()
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.axhline(y=0, color="black", linewidth=0.5)
        plt.ylabel("Call count")
        plt.title("Action call count for one run of the tests")
        ax.grid(axis="y")

    # total time spent per action, as stacked bar chart, condensing produce/consume/execute_action
    def time_spent_per_action(fix, ax):
        # merge actions, consume and produce
        data = df.copy()
        data["action"] = data["action"].str.split("/").str[0]

        # sum actions by their name for each file execution
        data = data.groupby(["execution", "mode", "file", "action", "file_id"]).sum()
        data = data.reset_index()
        # average by file (avoids repetition from different iteration counts)
        data = data.groupby(["execution", "mode", "file", "action"]).mean()
        data = data.reset_index()

        # get actions sorted by average duration
        actions = (
            data[["action", "total_duration"]]
            .groupby("action")
            .sum()
            .sort_values("total_duration", ascending=False)
            .index
        )
        colors = sns.color_palette("bright", len(actions))
        legend = actions
        prev = None
        for action in actions:
            subdata = data[data["action"] == action][["execution", "total_duration"]]
            subdata = subdata.groupby("execution").mean()
            subdata = subdata.reset_index()
            if prev is None:
                prev = subdata["total_duration"]
                plt.bar(
                    subdata["execution"],
                    subdata["total_duration"],
                    label=action,
                    color=colors.pop(0),
                )
            else:
                plt.bar(
                    subdata["execution"],
                    subdata["total_duration"],
                    label=action,
                    color=colors.pop(0),
                    bottom=prev,
                )
                prev += subdata["total_duration"]
        ax.grid(axis="y")
        plt.ylabel("Total time spent (ms)")
        plt.title("Shares of total time spent for one run of the tests")
        plt.legend(legend)

    # total time spent per action, as stacked bar chart, without condensing produce/consume/execute_action
    def time_spent_per_action_detailed(fix, ax):
        # merge actions, consume and produce
        data = df.copy()
        data["action"] = data["action"].apply(lambda x: "other" if not "/" in x else x)
        data = data.groupby(["execution", "mode", "file", "action", "file_id"]).sum()
        data = data.reset_index()

        # average by file (avoids repetition from different iteration counts)
        data = data.groupby(["execution", "mode", "file", "action"]).mean()
        data = data.reset_index()

        def re_order_palette(p):
            # alternate between light and dark colors
            return [p[i] for i in range(1, len(p), 2)] + [
                p[i] for i in range(0, len(p), 2)
            ]

        # get actions sorted by average duration
        actions = (
            data[["action", "total_duration"]]
            .groupby("action")
            .sum()
            .sort_values("total_duration", ascending=False)
            .index
        )
        cons_actions = len([a for a in actions if a.startswith("cons")])
        prod_actions = len([a for a in actions if a.startswith("prod")])
        ea_actions = len([a for a in actions if a.startswith("ea")])
        cons_colors = re_order_palette(sns.color_palette("Blues", cons_actions))
        prod_colors = re_order_palette(sns.color_palette("Greens", prod_actions))
        ea_colors = re_order_palette(sns.color_palette("Reds", ea_actions))

        legend = actions
        prev = None
        for action in actions:
            subdata = data[data["action"] == action][["execution", "total_duration"]]
            subdata = subdata.groupby("execution").mean()
            subdata = subdata.reset_index()
            color = None
            if action.startswith("cons"):
                color = cons_colors.pop(0)
            elif action.startswith("prod"):
                color = prod_colors.pop(0)
            elif action.startswith("ea"):
                color = ea_colors.pop(0)
            else:
                #  otherwise, default to grey
                color = "grey"

            if prev is None:
                prev = subdata["total_duration"]
                plt.bar(
                    subdata["execution"],
                    subdata["total_duration"],
                    label=action,
                    color=color,
                )
            else:
                plt.bar(
                    subdata["execution"],
                    subdata["total_duration"],
                    label=action,
                    color=color,
                    bottom=prev,
                )
                prev += subdata["total_duration"]
        ax.grid(axis="y")
        plt.ylabel("Total time spent (ms)")
        plt.title("Detailed shares of total time spent for one run of the tests")
        plt.legend(legend)

    views = [
        avg_action_duration,
        avg_action_call_count,
        time_spent_per_action,
        time_spent_per_action_detailed,
    ]

    for view in views:
        fig, ax = plt.subplots()
        view(fig, ax)
    plt.show()
