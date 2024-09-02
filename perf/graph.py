#!/usr/bin/env python3.9
import os, sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def main():
    if len(sys.argv) != 2:
        print("Usage: python graph.py <input_file>")
        sys.exit(1)
    input_file = sys.argv[1]

    # Read the input file (.csv), columns are: file, time, iters
    df = pd.read_csv(input_file)
    # file is "file_NN", so set count to NN
    df['count'] = df['file'].apply(lambda x: int(x.split('_')[1].split('.')[0]))
    df['avg_time'] = df['time'] / df['iters']

    # Plot the graph
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    sns.lineplot(x='count', y='avg_time', data=df)
    plt.title('Time vs Iterations')
    plt.xlabel('Iterations')
    plt.ylabel('Time (s)')
    plt.savefig('graph.png')
    plt.show()




if __name__ == '__main__':
    main()
