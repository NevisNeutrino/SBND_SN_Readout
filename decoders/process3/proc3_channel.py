import numpy as np
import matplotlib.pyplot as plt
import sys, os

if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <run_number>")
        sys.exit(1)

run = sys.argv[1]

x_min, x_max = 3, 18
y_min, y_max = 0, 63
num_tpcs = 11

for i, metric in enumerate(["Rate of Number of ROI Starts", "Rate of Number of ROI Ends", "Average Baseline", "Average Amplitude", "Ratio of Missed ROI Starts", "Ratio of Missed ROI Ends"]):
    tpc_heatmaps = []
    for tpc in range(1, num_tpcs + 1):

        file_path = f"/data/SNCommissioning/tpc{tpc:02d}/run{run}/run{run}_tpc{tpc:02d}_channel_metrics.txt"

        if not os.path.exists(file_path):
            print(f"Warning: {file_path} does not exist, skipping TPC {tpc:02d}")
            continue

        data = np.loadtxt(file_path, skiprows=2, delimiter='\t')
        fem = data[:, 0].astype(int)
        channel = data[:, 1].astype(int)
        z = data[:, i+2]

        metricname = np.loadtxt(file_path, skiprows=1, max_rows=1, dtype = str, delimiter='\t')[i+2]

        heatmap = np.zeros((y_max - y_min + 1, x_max - x_min + 1))
        for f, c, val in zip(fem, channel, z):
            if x_min <= f <= x_max and y_min <= c <= y_max:
                heatmap[c - y_min, f - x_min] = val

        tpc_heatmaps.append(heatmap)

    combined_heatmap = np.hstack(tpc_heatmaps)

    x_edges = np.arange(0, combined_heatmap.shape[1] + 1) - 0.5
    y_edges = np.arange(y_min, y_max + 2) - 0.5

    fig, ax = plt.subplots(figsize=(18,10), facecolor='black')
    fig.subplots_adjust(left=0.05, right=1.06, top=0.9, bottom=0.06)
    mesh = ax.pcolormesh(x_edges, y_edges, combined_heatmap, cmap='viridis_r', vmin=0, vmax=np.max(combined_heatmap), shading='flat')

    cbar = plt.colorbar(mesh, ax=ax)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(cbar.ax.get_yticklabels(), color='white')
    cbar.set_label(metric, color='white', fontsize=16)

    ax.set_xlabel("FEM", color='white', fontsize=16)
    ax.set_ylabel("Channel", color='white', fontsize=16)

    fem_labels = np.tile(np.arange(x_min, x_max + 1), num_tpcs)
    ax.set_xticks(np.arange(len(fem_labels)))
    ax.set_xticklabels(fem_labels, rotation=90, color='white')

    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    tpc_start_cols = np.arange(0, num_tpcs * 16, 16)
    tpc_midpoints = tpc_start_cols + (16 / 2) - 0.5
    ax2.set_xticks(tpc_midpoints)
    ax2.set_xticklabels(range(1, num_tpcs + 1), color='white', fontsize=12)
    ax2.set_xlabel("TPC", color='white', fontsize=16)
    ax2.tick_params(colors='white')

    ax.set_yticks(np.arange(y_min, y_max + 1, 2))
    ax.tick_params(colors='white')

    for tpc in range(1, num_tpcs):
        start_col = tpc * 16
        ax.vlines(start_col-0.5, ymin=y_min - 0.5, ymax=y_max + 0.5, colors='white', linestyles='dashed', linewidth=2)

    if os.path.exists(f"/data/SNCommissioning/tpc01/run{run}/run{run}_tpc01_channel_metrics.txt"):
        info = np.genfromtxt(f"/data/SNCommissioning/tpc01/run{run}/run{run}_tpc01_channel_metrics.txt", max_rows=1, delimiter='\t', dtype=str, invalid_raise=False)
        plt.title(f"Run {run}: {info}", color='white', fontsize=16)
    
    plt.savefig("/data/SNCommissioning/plots/"+metricname+"_channels.png", facecolor='black')

