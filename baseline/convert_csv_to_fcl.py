# V_3_0_0
# Modify format in accordance with Daisy's request

import pandas as pd
import os
from collections import defaultdict

# Input files
analysis_csv = "channel_analysis_results.csv"
mapping_csv = "channel_map.csv"

# Channel map column names (since no header in file)
mapping_columns = [
    'Wire number', 'Wire plane', 'APA', 'Half', 'Top/Side',
    'FEMB Position', 'FEMB Serial #', 'FEMB #', 'FEMB ch #', 'ASIC #',
    'WIB Crate #', 'WIB #', 'WIB ch #', 'WIB QFSP', 'QFSP Fiber #',
    'Crate #', 'FEM #', 'FEM ch #', 'LArSoft ch #'
]

# Read CSVs
df_analysis = pd.read_csv(analysis_csv)
df_map = pd.read_csv(mapping_csv, delim_whitespace=True, names=mapping_columns)

# Merge based on LArSoft ch #
merged_df = pd.merge(df_analysis, df_map, left_on="channel", right_on="LArSoft ch #", how="inner")

# Output directory
output_dir = "fcl_files"
os.makedirs(output_dir, exist_ok=True)

# Group by Crate #
for crate, crate_df in merged_df.groupby("Crate #"):
    # Group again by slot for proper ordering
    grouped_by_slot = defaultdict(list)

    for _, row in crate_df.iterrows():
        fem = row['FEM #']
        fem_ch = row['FEM ch #']
        slot = f"slot{fem + 2}"
        threshold = row['threshold_1_delta']
        baseline = row['most_probable_adc']

        grouped_by_slot[slot].append((fem_ch, threshold, baseline))

    lines = []
    for slot in sorted(grouped_by_slot.keys(), key=lambda s: int(s[4:])):
        # Sort channels within each slot
        for fem_ch, threshold, baseline in sorted(grouped_by_slot[slot]):
            lines.append(f"{slot}.ch{fem_ch} {threshold}")
        for fem_ch, threshold, baseline in sorted(grouped_by_slot[slot]):
            lines.append(f"{slot}.ped{fem_ch} {baseline}")

    filename = os.path.join(output_dir, f"crate{crate}new.txt")
    with open(filename, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {filename}")


