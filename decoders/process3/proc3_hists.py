import numpy as np
import matplotlib.pyplot as plt
import sys, os

if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <run_number>")
        sys.exit(1)

run = sys.argv[1]

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


fig, axes = plt.subplots(1, 2, figsize=(12,5), facecolor="black")

bin_labels = ["0", "1", "2", "3", "4", "overflow"]
frame_bottom = np.zeros(len(bin_labels))
word_bottom  = np.zeros(len(bin_labels))

for tpc in range(1,12):

    file_path = f"/data/SNCommissioning/tpc{tpc:02d}/run{run}/run{run}_tpc{tpc:02d}_hists.txt" 
    
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} does not exist, skipping TPC {tpc:02d}")
        continue

    with open(file_path, "r") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")
    if len(blocks) != 2:
        print(f"Warning: Expected exactly 2 blocks, skipping TPC {tpc:02d}")
        continue

    def build_hist(block):
        counts = [0] * len(bin_labels)
        lines = block.strip().split("\n")[1:]
        for line in lines:
            if line.strip():
                val_str, count_str = line.split("\t")
                val = int(val_str)
                count = int(count_str)
                if val >= 5 or val < 0:
                    counts[-1] += count
                else:
                    counts[val] += count
        return counts

    frame_counts = build_hist(blocks[0])
    word_counts  = build_hist(blocks[1])

    # Frame difference
    axes[0].bar(bin_labels, frame_counts, bottom = frame_bottom, color=colors[tpc-1], edgecolor="white", log=True, alpha=0.8)
    frame_bottom += frame_counts
    
    # Wordcount difference
    axes[1].bar(bin_labels, word_counts, bottom = word_bottom, color=colors[tpc-1], edgecolor="white", label = "TPC"+f"{tpc:02d}", log=True, alpha=0.8)
    word_bottom  += word_counts

# Frame difference
axes[0].set_facecolor("black")
axes[0].set_xlabel("Frame Difference", color="white")
axes[0].set_ylabel("Log Counts", color="white")
axes[0].set_title("Run "+run, color="white")
axes[0].tick_params(colors="white")
axes[0].grid(False)

# Wordcount difference
axes[1].set_facecolor("black")
axes[1].set_xlabel("Wordcount Difference", color="white")
axes[1].set_ylabel("Log Counts", color="white")
axes[1].set_title("Run "+run, color="white")
axes[1].tick_params(colors="white")
axes[1].grid(False)
axes[1].legend(frameon=False, labelcolor='white')

plt.tight_layout()
plt.savefig("/data/SNCommissioning/plots/hists.png")
