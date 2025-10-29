#!/usr/bin/env python3.9
import os
from pathlib import Path
import sys
import regex
from typing import List, Tuple
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

ignored_files = [".DS_Store"]


def parse_folder(folder):
    # category, filename, locs
    locs: List[Tuple[str, str, int]] = []

    for root, dirs, files in os.walk(folder):
        # category is path to file
        category = os.path.relpath(root, folder)
        if "_" in category:
            category = category.split("_")[1].strip()

        for file in files:
            if file in ignored_files:
                continue
            with open(os.path.join(root, file), "rb") as f:
                loc = 0
                for line in f:
                    if len(line.strip()) > 0:
                        loc += 1
                locs.append((category, file, loc))

    return locs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <directories>".format(sys.argv[0]))
        sys.exit(1)

    entries: List[Tuple[str, str, str, int]] = []
    # iterate over top folders inside directory, call parse_folder
    for folder in sys.argv[1:]:
        folder = Path(folder)
        for path in folder.iterdir():
            if path.is_dir():
                print("Parsing", path)
                e = parse_folder(path)
                entries.extend(
                    [
                        (folder.name + "/" + path.name, category, filename, loc)
                        for category, filename, loc in e
                    ]
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
    # df.sort_values(by=["instantiation", "category", "filename"], inplace=True)
    # df.to_csv("locs.csv", index=False)

    def cleanup_graph(
        ax,
        *,
        legend=None,
        filename=None,
        title=None,
        axis=None,
        x_label=None,
        y_label=None,
        no_line=False,
    ):
        if legend is False:
            lgd = None
        elif legend is not None:
            lgd = plt.legend(legend, loc="lower left", bbox_to_anchor=(1, 0))
        else:
            lgd = plt.legend(loc="lower left", bbox_to_anchor=(1, 0))
        # plt.xticks(rotation=0)
        # if not no_line:
        #     plt.axhline(y=0, color="black", linewidth=0.5)
        plt.ylabel(y_label)
        plt.xlabel(x_label)
        if axis:
            ax.grid(axis=axis)
        if filename is not None:
            lgd = None if lgd is None else (lgd,)
            fig.savefig(f"{filename}.pdf", bbox_extra_artists=lgd, bbox_inches="tight")
        if title is not None:
            plt.title(title)

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

        # remove "combinators" from categories, add it at the end
        categories = [cat for cat in categories if cat != "combinators"]
        categories = categories + ["combinators"]

        colors = [
            # "#023EFF", <- used for combinators
            # "#FF7C00",
            "#1AC938",
            # "#E8000B", <- used for removed
            # "#8B2BE2", <- used for tailored
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
            # group by, sorting desc
            subdata = (
                subdata.groupby("instantiation")
                .sum()
                .sort_values(by="instantiation", ascending=False)
            )
            subdata = subdata.reset_index()
            color = None
            if cat == "combinators":
                color = "#d7e7fa"
            elif cat == "removed":
                color = "#E8000B"
            elif cat == "monolith":
                color = "#E9474C"
            elif cat == "custom":
                color = "#8B2BE2"
            else:
                color = colors.pop(0)
            if prev is None:
                prev = subdata["locs"]
                plt.barh(
                    subdata["instantiation"],
                    subdata["locs"],
                    label=cat,
                    color=color,
                )
            else:
                plt.barh(
                    subdata["instantiation"],
                    subdata["locs"],
                    label=cat,
                    color=color,
                    left=prev,
                )
                prev += subdata["locs"]
        cleanup_graph(
            ax,
            legend=legend,
            filename="locs",
            title="LOCs per instantiation",
            x_label="LOCs",
        )

    views = [show_locs]

    for i, view in enumerate(views):
        fig, ax = plt.subplots(figsize=(6, 2))
        view(fig, ax)

    out_dir = "out.pdf"
    plt.tight_layout()
    plt.savefig(out_dir)

    plt.show()
