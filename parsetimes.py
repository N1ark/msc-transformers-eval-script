#!/usr/bin/env python3.9

from typing import List, Tuple, Optional
import os
import sys
import regex
import csv
import pathlib

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from matplotlib import font_manager

font_path = pathlib.Path.home() / "Library" / "Fonts" / "cmunrm.ttf"
font_manager.fontManager.addfont(font_path)
prop = font_manager.FontProperties(fname=font_path)

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = prop.get_name()


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
        execution = execution.replace("_", "")
        entries.extend(
            [
                (execution, mode, file, action, dur, count, file_id)
                for mode, file, action, dur, count, file_id in durations
            ]
        )
        print(f"Parsed {file} ({execution}): found {len(durations)} entries")

    if mode_filter:
        entries = [
            e for e in entries if e[1].lower().find(mode_filter.lower()) != -1
        ]
    print(f"Filtered to {len(entries)} entries with mode {mode_filter}")

    # add missing actions as 0 for each (execution, mode, file)
    keys = set([(e[0], e[1], e[2]) for e in entries])
    actions = set([e[3] for e in entries])
    entries_set = set([(e[0], e[1], e[2], e[3]) for e in entries])
    print(
        f"Found {len(keys)} keys and {len(actions)} actions in {len(entries_set)} groups"
    )
    for key in keys:
        for action in actions:
            if not any(
                e[0] == key[0]
                and e[1] == key[1]
                and e[2] == key[2]
                and e[3] == action
                for e in entries_set
            ):
                entries.append((key[0], key[1], key[2], action, 0.0, 0.0, 0))
    print(f"Added missing actions, now {len(entries)} entries")

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

    df.sort_values(["execution", "mode", "file"], inplace=True)

    def cleanup_graph(
        ax,
        *,
        legend=None,
        filename=None,
        title=None,
        axis="y",
        x_label=None,
        y_label=None,
        no_line=False,
        xticks=0,
    ):
        if legend is False:
            lgd = None
        elif legend is not None:
            lgd = plt.legend(legend, loc="lower left", bbox_to_anchor=(1, 0))
        else:
            lgd = plt.legend(loc="lower left", bbox_to_anchor=(1, 0))
        plt.xticks(rotation=xticks)
        if not no_line:
            plt.axhline(y=0, color="black", linewidth=0.5)
        plt.ylabel(y_label)
        plt.xlabel(x_label)
        if axis:
            ax.grid(axis=axis)
        if filename is not None:
            lgd = None if lgd is None else (lgd,)
            fig.savefig(
                f"{filename}.pdf", bbox_extra_artists=lgd, bbox_inches="tight"
            )
        if title is not None:
            plt.title(title)

    def avg_action_duration(fig, ax):
        data = df.copy()
        sns.barplot(
            x="action",
            y="duration",
            hue="execution",
            data=data,
            ax=ax,
            palette="bright",
            errorbar=None,
        )
        sns.despine()
        cleanup_graph(
            ax,
            filename="avg_action_duration",
            xticks=90,
            title="Average action duration for 1000 executions",
            y_label="Duration (ms)",
        )

    def avg_action_call_count(fig, ax):
        data = df.copy()
        data = data.groupby("action").sum()["count"]
        # group all actions with less than 1% of the total count or less than 10th category into a single "other" category
        tenth = 0 if len(data) < 10 else data.nlargest(10).iloc[-1]
        data = pd.concat(
            [
                data[(data >= data.sum() * 0.01) & (data > tenth)],
                pd.Series(
                    data[(data < data.sum() * 0.01) | (data <= tenth)].sum(),
                    index=["other"],
                ),
            ]
        )
        data = data[data >= data.sum() * 0.005]  # hide anything < 0.5%
        data = data.sort_values(ascending=False)
        plt.pie(
            data,
            labels=data.index,
            colors=sns.color_palette("bright"),
        )
        cleanup_graph(
            ax,
            filename="avg_action_call_count",
            legend=False,
            title="Action call count for one run of the tests",
            no_line=True,
        )

    # total time spent per action, as stacked bar chart, condensing produce/consume/execute_action
    def time_spent_per_action(fix, ax):
        # merge actions, consume and produce
        data = df.copy()
        data["action"] = data["action"].apply(
            lambda x: x if "/" not in x else x.split("/")[0]
        )

        # sum actions by their name for each file execution
        data = data.groupby(
            ["execution", "mode", "file", "action", "file_id"]
        ).sum()
        data = data.reset_index()

        # find all actions below X biggest:
        actions = (
            data[["action", "total_duration"]]
            .groupby("action")
            .sum()
            .sort_values("total_duration", ascending=False)
            .index
        )
        smaller = actions[5:]
        #  group all actions below 7 biggest into "other" category
        data["action"] = data["action"].apply(
            lambda x: x if x not in smaller else "other"
        )
        data = data.groupby(
            ["execution", "mode", "file", "action", "file_id"]
        ).sum()

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
            subdata = data[data["action"] == action][
                ["execution", "total_duration"]
            ]
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
        cleanup_graph(
            ax,
            filename="time_spent_per_action",
            y_label="Total time spent (ms)",
            title="Shares of total time spent for one run of the tests",
            legend=legend,
        )

    # total time spent per action, as stacked bar chart, without condensing produce/consume/execute_action
    def time_spent_per_action_detailed(fix, ax):
        # merge actions, consume and produce
        data = df.copy()
        data["action"] = data["action"].apply(
            lambda x: "other" if not "/" in x else x
        )
        data = data.groupby(
            ["execution", "mode", "file", "action", "file_id"]
        ).sum()
        data = data.reset_index()

        # find all actions below X biggest:
        actions = (
            data[["action", "total_duration"]]
            .groupby("action")
            .sum()
            .sort_values("total_duration", ascending=False)
            .index
        )
        smaller = actions[9:]
        #  group all actions below 7 biggest into "other" category
        data["action"] = data["action"].apply(
            lambda x: x if x not in smaller else "other"
        )
        data = data.groupby(
            ["execution", "mode", "file", "action", "file_id"]
        ).sum()

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
        prod_colors = re_order_palette(
            sns.color_palette("Greens", prod_actions)
        )
        ea_colors = re_order_palette(sns.color_palette("Reds", ea_actions))

        legend = actions
        prev = None
        for action in actions:
            subdata = data[data["action"] == action][
                ["execution", "total_duration"]
            ]
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
        cleanup_graph(
            ax,
            filename="time_spent_per_action_detailed",
            y_label="Total time spent (ms)",
            title="Shares of total time spent for one run of the tests",
            legend=legend,
        )

    views = [
        avg_action_duration,
        avg_action_call_count,
        time_spent_per_action,
        time_spent_per_action_detailed,
    ]

    for view in views:
        fig, ax = plt.subplots(figsize=(6, 6))
        view(fig, ax)
    plt.show()
