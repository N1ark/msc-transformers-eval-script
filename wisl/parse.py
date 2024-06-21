#!/usr/bin/env python3.9

import os
import sys
import regex
import csv

biabduct_regex = r"\w+, \d+, \d+, \d+, \d+, ([\d.]+)"


def parse_file(file_path):
    mode_durations = {}
    file_durations = {}
    mode = None
    file = None

    def increase(duration):
        if mode is None or file is None:
            return
        if mode not in mode_durations:
            mode_durations[mode] = 0
        if file not in file_durations:
            file_durations[file] = 0
        mode_durations[mode] += duration
        file_durations[file] += duration

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("Mode "):
                mode = line.split(" ")[1]
                mode = mode.split(":")[0]
            elif line.startswith("Running file ") and not line.endswith(":"):
                file = line.split("/")[-1]
            elif line.startswith("All specs succeeded"):
                dur = line.split("succeeded: ")[1]
                increase(float(dur))
            elif line.startswith("There were failures"):
                dur = line.split("failures: ")[1]
                increase(float(dur))
            elif regex.match(biabduct_regex, line):
                dur = regex.match(biabduct_regex, line).group(1)
                increase(float(dur))
            elif line.startswith("Compilation time:"):
                # negate to make up for extra
                dur = line.split("time: ")[1]
                dur = dur.split("s")[0]
                increase(-float(dur))
            elif line.startswith("Total time (Compilation + Symbolic testing)"):
                dur = line.split("Symbolic testing):")[1]
                dur = dur.split("s")[0]
                increase(float(dur))

    return mode_durations, file_durations


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: {} <dest> <files...>".format(sys.argv[0]))
        sys.exit(1)

    dest = sys.argv[1]
    if not dest.endswith("/"):
        dest += "/"
    if not os.path.exists(dest):
        os.makedirs(dest)

    mode_entries = []
    file_entries = []

    for file in sys.argv[2:]:
        modes, files = parse_file(file)
        execution = file.split("/")[-1]
        execution = execution.split(".")[0]
        mode_entries.append([(execution, mode, dur) for mode, dur in modes.items()])
        file_entries.append([(execution, file, dur) for file, dur in files.items()])
        print("Parsed", file)

    with open(dest + "mode_durations.csv", "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["execution", "mode", "duration"])
        for entry in mode_entries:
            writer.writerows(entry)

    with open(dest + "file_durations.csv", "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["execution", "filename", "duration"])
        for entry in file_entries:
            writer.writerows(entry)

    print(
        "Wrote: ", len(mode_entries), "mode entries", len(file_entries), "file entries"
    )
