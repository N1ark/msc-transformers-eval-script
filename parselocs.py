#!/usr/bin/env python3.9
import os
from pathlib import Path
import sys
import regex
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ignored_files = [".DS_Store"]


def parse_folder(folder):
    # category, filename, locs
    locs: List[Tuple[str, str, int]] = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file in ignored_files:
                continue
            with open(os.path.join(root, file), "rb") as f:
                loc = 0
                for line in f:
                    if len(line.strip()) > 0:
                        loc += 1
                # category is path to file
                category = os.path.relpath(root, folder)
                locs.append((category, file, loc))

    return locs


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <directory>".format(sys.argv[0]))
        sys.exit(1)

    entries: List[Tuple[str, str, str, int]] = []
    # iterate over top folders inside directory, call parse_folder
    for path in Path(sys.argv[1]).iterdir():
        if path.is_dir():
            print("Parsing", path)
            e = parse_folder(path)
            entries.extend(
                [(path.name, category, filename, loc) for category, filename, loc in e]
            )

    paths = set([e[0] for e in entries])
    categories = set([e[1] for e in entries])
    # if the category doesn't exist for a path, add it with 0 locs
    for category in categories:
        for path in paths:
            if not any([e[1] == category and e[0] == path for e in entries]):
                entries.append((path, category, "", 0))

    df = pd.DataFrame(
        entries, columns=["instantiation", "category", "filename", "locs"]
    )
    df.sort_values(by=["instantiation", "category", "filename"], inplace=True)
    df.to_csv("locs.csv", index=False)

    def show_locs(fig, ax):
        data = df.copy()
        data.drop("filename", axis=1, inplace=True)
        # sum locs by category
        data = data.groupby(["instantiation", "category"]).sum()
        data = data.reset_index()
        # get categories sorted by total locs
        categories = (
            data.groupby("category").sum().sort_values(by="locs", ascending=False).index
        )
        colors = [
            # "#023EFF", <- used for transformers
            "#FF7C00",
            "#1AC938",
            # "#E8000B", <- used for removed
            "#8B2BE2",
            "#9F4800",
            "#F14CC1",
            "#A3A3A3",
            "#FFC400",
            "#00D7FF",
        ]
        legend = categories
        prev = None
        for cat in categories:
            subdata = data[data["category"] == cat]
            subdata = subdata.groupby("instantiation").sum()
            subdata = subdata.reset_index()
            color = None
            if cat == "transformers":
                color = "#023EFF"
            elif cat == "removed":
                color = "#E8000B"
            else:
                color = colors.pop(0)
            if prev is None:
                prev = subdata["locs"]
                plt.bar(
                    subdata["instantiation"], subdata["locs"], label=cat, color=color
                )
            else:
                plt.bar(
                    subdata["instantiation"],
                    subdata["locs"],
                    label=cat,
                    color=color,
                    bottom=prev,
                )
                prev += subdata["locs"]
        ax.grid(axis="y")
        plt.ylabel("LOCs")
        plt.title("LOCs per instantiation")
        plt.legend(legend)

    views = [show_locs]

    for i, view in enumerate(views):
        fig, ax = plt.subplots()
        view(fig, ax)

    plt.show()
