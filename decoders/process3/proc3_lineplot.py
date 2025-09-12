import numpy as np
import matplotlib.pyplot as plt
import sys, os

if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <run_number>")
        sys.exit(1)

run = sys.argv[1]

fig, axes = plt.subplots(3, 1, figsize=(10, 15), facecolor="black")
fig.subplots_adjust(left=0.1, bottom=0.05, right=0.98, top=0.95, hspace=0.2)

colors = [
    '#FF69B4',  # hot pink
    '#FF7F50',  # coral (soft orange)
    '#FFA500',  # orange
    '#FFD700',  # gold / yellow
    '#FFFF00',  # bright yellow
    '#ADFF2F',  # green yellow
    '#32CD32',  # lime green
    '#00FF7F',  # spring green
    '#1E90FF',  # dodger blue
    '#4169E1',  # royal blue
    '#8A2BE2',  # blue violet / purple
    '#BA55D3'   # medium orchid / purple
]

for tpc in range(1,12):

    file_path = f"/data/SNCommissioning/tpc{tpc:02d}/run{run}/run{run}_tpc{tpc:02d}_dataformat_metrics.txt"

    if not os.path.exists(file_path):
        print(f"Warning: {file_path} does not exist, skipping TPC {tpc:02d}")
        continue

    def getline(y_col,yerr_col):
        x_vals, y_vals = [], []
        x_errs, y_errs = [], []

        with open(file_path, "r") as f:
            next(f)
            for line in f:
                if line.strip():
                    cols = line.split()
                    if len(cols) <= max(y_col, yerr_col or y_col):
                        continue
                    
                    first, second = map(float, cols[:2])
                    y = float(cols[y_col])
                    yerr = float(cols[yerr_col]) if yerr_col is not None else 0.0
                    
                    x = (first + second) / 2.0
                    xerr = abs(second - first) / 2.0
                    
                    x_vals.append(x)
                    y_vals.append(y)
                    x_errs.append(xerr)
                    y_errs.append(yerr)
        
        return x_vals, y_vals, x_errs, y_errs

    x_vals, y_vals, x_errs, y_errs = getline(2,None)

    axes[0].errorbar(
        x_vals, y_vals,
        xerr=x_errs, yerr=y_errs,
        fmt='o', color=colors[tpc-1], ecolor='white', elinewidth=1, label = "TPC"+f"{tpc:02d}", capsize=3
    )

    axes[0].set_xlabel("Missed End of Frame", color="white")
    axes[0].set_ylabel("Rate", color="white")
    axes[0].set_ylim(0)
    axes[0].set_title("Run "+run, color="white")
    axes[0].set_facecolor("black")
    axes[0].tick_params(colors="white")
    axes[0].grid(False)
    axes[0].legend(frameon=False, labelcolor='white')

    x_vals, y_vals, x_errs, y_errs = getline(3, None)

    axes[1].errorbar(
        x_vals, y_vals,
        xerr=x_errs, yerr=y_errs,
        fmt='o', color=colors[tpc-1], ecolor='white', elinewidth=1, capsize=3
    )

    axes[1].set_xlabel("Missed FEM Headers", color="white")
    axes[1].set_ylabel("FEM Average Rate", color="white")
    axes[1].set_ylim(0)
    axes[1].set_facecolor("black")
    axes[1].tick_params(colors="white")
    axes[1].grid(False)

    x_vals, y_vals, x_errs, y_errs = getline(5, None)

    axes[2].errorbar(
        x_vals, y_vals,
        xerr=x_errs, yerr=y_errs,
        fmt='o', color=colors[tpc-1], linestyle = "-", linewidth=0.5, ecolor='white', elinewidth=1, capsize=3
    )

    axes[2].set_xlabel("Missed Channel Start", color="white")
    axes[2].set_ylabel("FEM Average Rate", color="white")
    axes[2].set_ylim(0, np.max(y_vals)+0.05)
    axes[2].set_facecolor("black")
    axes[2].tick_params(colors="white")
    axes[2].grid(False)

    plt.savefig("/data/SNCommissioning/plots/lines.png")
