import uproot
import numpy as np
import awkward as ak
import pandas as pd
import os

# function that takes the root file output of the Analyzer module in the online monitor and saves the metric values into a txt file
def savemetrictxt(root_path, metric):
    root_file = uproot.open(root_path)

    metric_arr = root_file['OfflineAnalysis/event/channel_data/channel_data.'+metric].arrays()

    # format metric array in uproot
    nested_list = ak.to_list(metric_arr)
    column_name = list(nested_list[0].keys())[0]
    metric_values = [d[column_name] for d in nested_list]

    metricdf = pd.DataFrame(metric_values).T
    print('The number of events in this file is: '+str(len(metricdf.columns)))
    metricdf.columns = ['event'+str(i+1)+'_'+metric for i in range(len(metricdf.columns))]

    out_name = os.path.splitext(os.path.basename(root_path))[0]
    out_file = out_name+metric+'.txt'
     
    metricdf.to_csv(out_file, sep='\t', index=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Save metrics from .root output of Analysis.cc in sbndqm as .txt file")

    parser.add_argument("--filepath", type=str, help="Path to input root file")
    parser.add_argument("--metric", type=str, help="Metric to save (e.g. rms)")

    args = parser.parse_args()

    if args.filepath is None:
        raise ValueError("Invalid operation. Specify path to input root file.")
    elif args.metric == 'rms':
        savemetrictxt(args.filepath, args.metric)
    elif args.metric is None:
        raise ValueError("Invalid operation. Specify metric.")
    else:
        print(f"Unsupported metric: {args.metric}. Only 'rms' is supported.")
