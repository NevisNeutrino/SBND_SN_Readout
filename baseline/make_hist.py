import uproot
import numpy as np
import pandas as pd
import os
import glob

# Directory with ROOT files
data_dir = "/nevis/riverside/data/sc5303/sbnd/continuous_readout"
file_pattern = os.path.join(data_dir, "*.root")
root_files = glob.glob(file_pattern)

for file_path in root_files:
    base_name = os.path.basename(file_path)
    file_id = os.path.splitext(base_name)[0]  # strip .root extension
    output_npz = os.path.join(data_dir, f"channel_adc_count_{file_id}.npz")

    if os.path.exists(output_npz):
        print(f"Skipping already processed file: {output_npz}")
        continue

    print(f"Processing: {file_path}")
    try:
        with uproot.open(file_path) as f:
            if "tpc_data" not in f:
                print(f"  Skipped (no tpc_data): {file_path}")
                continue
            tree = f["tpc_data"]
            channels = tree["channel"].array(library="np")
            adcs = tree["adc"].array(library="np")

        # Build and group DataFrame
        df = pd.DataFrame({"channel": channels, "adc": adcs})
        grouped = df.groupby(["channel", "adc"]).size().reset_index(name="count")

        # Save grouped data
        np.savez_compressed(output_npz,
                            channel=grouped["channel"].values,
                            adc=grouped["adc"].values,
                            count=grouped["count"].values)
        print(f"  Saved to: {output_npz}")
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
