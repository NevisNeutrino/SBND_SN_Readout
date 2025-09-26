import os
import sys
import argparse
import uproot
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch
from concurrent.futures import ProcessPoolExecutor

from utils import *
from getMetric import *

if __name__ == "__main__":
    try:
        args = parseArguments()
    except argparse.ArgumentTypeError as err:
        print(err)
        sys.exit(1)

    froot = uproot.open(args.file)
    if args.save:
        pdfname = os.path.splitext(args.file)[0] + '.pdf'
        print("Output pdf file: ", pdfname)
        fpdf = PdfPages(pdfname)

    try:
        run, subfile, tpc = getFileInfo(args.file)
    except ValueError as err:
        print(err)
        sys.exit(1)

    tree = froot["events"]
    femBranches, femSlots = getFEMs(tree)
    chNums = range(64)
    print(f"FEM slots: {femSlots}")

    frameNums = getFrameNums(tree)

    tasks = [
        (getChannelStartMissSN, (tree, femBranches, femSlots), 'getChannelStartMissSN'),
        (getROIMissCntSN, (tree, femBranches, femSlots), 'getROIMissCntSN'),
        (getROICntAveSN, (tree, femBranches, femSlots), 'getROICntAveSN'),
        (getROIBaselineAveSN, (tree, femBranches, femSlots), 'getROIBaselineAveSN'),
        (getROIAmplAveSN, (tree, femBranches, femSlots), 'getROIAmplAveSN')
    ]

    results = {}

    with ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(func, *args): task
            for func, args, task in tasks
        }

        for future in futures:
            future.result()

        for future, task in futures.items():
            try:
                result = future.result()
            except Exception as e:
                result = f"Error: {e}"
            results[task] = result

    plt.figure(figsize=(10, 6))

    eventEndMiss = getEventEndMiss(tree, frameNums, 'SN')
    nEvent = len(tree['eventID'].array())
    nEventEndMiss = len(eventEndMiss)
    x = [0, 1]
    y = [(nEvent - nEventEndMiss), nEventEndMiss]
    labels = [
        f"Total number of packet frames = {sum(y)}",
        f"Number of packet frames with Packet Frame End = {y[0]}",
        f"Number of packet frames without Packet Frame End = {y[1]}"
    ]
    handles = [Patch(facecolor='none', edgecolor='none', label=label) for label in labels]
    plt.bar(x, y, width=1.0, align='center', edgecolor='black', linewidth=2.0)
    plt.yscale('log')
    plt.ylim(top=(max(y) * 1.05))
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: Packet Frame End Miss")
    plt.xticks(x, ["Packet Frame End Exist", "Packet Frame End Miss"])
    plt.ylabel("Number of packet frames")
    plt.grid(True)
    plt.legend(handles=handles, loc='upper right', frameon=True, handlelength=0, handletextpad=0.)
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Packet Frame End Miss Metric")
    if args.show: plt.show()
    plt.clf()

    femDict = getFEMHeaderMiss(tree, frameNums, 'SN', femBranches, femSlots)
    x = []
    y = []
    labels = []
    for idx, slot in enumerate(femSlots):
        x.append(idx)
        if slot in femDict: y.append(len(femDict[slot]))
        else: y.append(0)
        labels.append(slot)
    plt.bar(x, y, width=1.0, align='center', edgecolor='black', linewidth=2.0)
    plt.ylim(top=(max(y) * 1.1))
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: FEM Header Miss")
    plt.xticks(x, labels)
    plt.xlabel("FEM slot")
    plt.ylabel("Number of missing FEM headers")
    plt.grid(True)
    labels = [
        f"Total number of packet frames = {nEvent}",
    ]
    handles = [Patch(facecolor='none', edgecolor='none', label=label) for label in labels]
    plt.legend(handles=handles, loc='upper right', frameon=True, handlelength=0, handletextpad=0.)
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: FEM Header Miss Metric")
    if args.show: plt.show()
    plt.clf()
    
    firstFrameNums, lastFrameNums, frameNumDiffDict, frameNumRolloverDict = getFrameNumMetric(tree, frameNums, femBranches, femSlots)
    df = pd.DataFrame({'FEM Slot': femSlots, 'First Packet Frame Number': firstFrameNums, 'Last Packet Frame Number': lastFrameNums})
    df = df.astype(object).apply(lambda col: col.map(lambda x: str(int(x)) if pd.notna(x) else 'nan'))
    plt.table(cellText=df.values, colLabels=df.columns, loc='center')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: First and Last Packet Frame Number")
    plt.axis('off')
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Table saved: First and Last Packet Frame Numbers Metric")
    if args.show: plt.show()
    plt.clf()
    slots = []
    data = []
    for slot, df in frameNumDiffDict.items():
        slots.append(slot)
        data.append(df[f"fem{slot}/frameNumDiff_"])
    flatten = [diff for diffs in data for diff in diffs]
    if len(flatten) == 0: flatten = [0]
    high = int(max(flatten))
    bins = list(range(0, 6))
    labels = list(range(0, 5))
    if high > max(bins): bins.append(high)
    else: bins.append((max(bins) + 1))
    labels.append('overflow')
    counts = np.array([np.histogram(fem, bins=bins)[0] for fem in data])
    edges = np.arange(len(bins))
    bottoms = np.zeros_like(counts[0])
    for slot, cnt in zip(slots, counts):
        plt.bar(edges[:-1], cnt, width=1, align='edge', edgecolor='black', bottom=bottoms, label=f"FEM {slot}")
        bottoms += cnt
    centers = (edges[:-1] + edges[1:]) / 2
    for x, y in zip(centers, bottoms):
        plt.text(x, y, str(int(y)), ha='center', va='bottom', fontweight='bold', fontsize=16)
    if max(bottoms) == 0: bottoms += 1
    plt.ylim(bottom=0, top=(max(bottoms) * 1.1))
    #plt.yscale('symlog')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: Packet Frame Number Difference")
    plt.xticks(centers, labels)
    plt.xlabel("Packet frame number difference (should be 1 or 4)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Packet Frame Number Difference Metric")
    if args.show: plt.show()
    plt.clf()
    data = []
    for slot, df in frameNumRolloverDict.items():
        data.append(df[f"fem{slot}/frameNumRollover_"])
    flatten = [rollover for rollovers in data for rollover in rollovers]
    if len(flatten) == 0: flatten = [0]
    high = int(max(flatten))
    bins = list(range(0, 6))
    labels = list(range(0, 5))
    if high > max(bins): bins.append(high)
    else: bins.append((max(bins) + 1))
    labels.append('overflow')
    counts = np.array([np.histogram(fem, bins=bins)[0] for fem in data])
    edges = np.arange(len(bins))
    bottoms = np.zeros_like(counts[0])
    for slot, cnt in zip(slots, counts):
        plt.bar(edges[:-1], cnt, width=1, align='edge', edgecolor='black', bottom=bottoms, label=f"FEM {slot}")
        bottoms += cnt
    centers = (edges[:-1] + edges[1:]) / 2
    for x, y in zip(centers, bottoms):
        plt.text(x, y, str(int(y)), ha='center', va='bottom', fontweight='bold', fontsize=16)
    if max(bottoms) == 0: bottoms += 1
    plt.ylim(bottom=0, top=(max(bottoms) * 1.1))
    #plt.yscale('symlog')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: Packet Frame Number Rollover")
    plt.xticks(centers, labels)
    plt.xlabel("Rollover-corrected packet frame number difference (should be 1 or 4)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Packet Frame Number Rollover Metric")
    if args.show: plt.show()
    plt.clf()

    plt.figure(figsize=(12, 6))

    femDict = getADCWordCnt(tree, 'SN', femBranches, femSlots)
    slots = []
    data = []
    for slot, df in femDict.items():
        slots.append(slot)
        data.append(df[f"fem{slot}/adcCntDiff_"])
    flatten = [diff for diffs in data for diff in diffs]
    if len(flatten) == 0: flatten = [0]
    low = int(min(flatten))
    high = int(max(flatten))
    bins = list(range(-3, 5))
    labels = list(range(-3, 4))
    if low < min(bins): bins.insert(0, low)
    else: bins.insert(0, (min(bins)-1))
    labels.insert(0, 'underflow')
    if high > max(bins): bins.append(high)
    else: bins.append((max(bins) + 1))
    labels.append('overflow')
    counts = np.array([np.histogram(fem, bins=bins)[0] for fem in data])
    edges = np.arange(len(bins))
    bottoms = np.zeros_like(counts[0])
    for slot, cnt in zip(slots, counts):
        plt.bar(edges[:-1], cnt, width=1, align='edge', edgecolor='black', bottom=bottoms, label=f"FEM {slot}")
        bottoms += cnt
    centers = (edges[:-1] + edges[1:]) / 2
    for x, y in zip(centers, bottoms):
        plt.text(x, y, str(int(y)), ha='center', va='bottom', fontweight='bold', fontsize=16)
    plt.ylim(top=(max(bottoms) * 1.1))
    #plt.yscale('symlog')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: ADC Word Count Difference")
    plt.xticks(centers, labels)
    plt.xlabel("ADC word count difference")
    plt.ylabel("Number of packet frames")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: ADC Word Count Difference Metric")
    if args.show: plt.show()
    plt.clf()

    plt.figure(figsize=(18, 6))
    cmap = plt.cm.viridis
    cmap.set_bad(color='white')

    chStartMissDict = results['getChannelStartMissSN']
    data = np.array([
        [len(chStartMissDict[x][y]) if x in chStartMissDict and y in chStartMissDict[x] else 0 for x in femSlots]
        for y in chNums
    ])
    data = np.ma.masked_less(data, 1)
    plt.imshow(data.T, cmap=cmap, vmin=0, aspect='auto')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: Channel Start Miss")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Frequency")
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Channel Start Miss Metric")
    if args.show: plt.show()
    plt.clf()

    roiStartMissCntDict, roiEndMissCntDict = results['getROIMissCntSN']
    data = np.array([
        [len(roiStartMissCntDict[x][y]) if x in roiStartMissCntDict and y in roiStartMissCntDict[x] else 0 for x in femSlots]
        for y in chNums
    ])
    data = np.ma.masked_less(data, 1)
    plt.imshow(data.T, cmap=cmap, vmin=0, aspect='auto')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: ROI Start Miss")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Number of missed ROI starts")
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: ROI Start Miss Metric")
    if args.show: plt.show()
    plt.clf()
    data = np.array([
        [len(roiEndMissCntDict[x][y]) if x in roiEndMissCntDict and y in roiEndMissCntDict[x] else 0 for x in femSlots]
        for y in chNums
    ])
    data = np.ma.masked_less(data, 1)
    plt.imshow(data.T, cmap=cmap, vmin=0, aspect='auto')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: ROI End Miss")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Number of missed ROI ends")
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: ROI End Miss Metric")
    if args.show: plt.show()
    plt.clf()

    dfROI = results['getROICntAveSN']
    plt.imshow(dfROI.T, cmap='viridis', aspect='auto')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: Average Number of ROIs")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Number of ROIs per packet frame")
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Average Number of ROIs Metric")
    if args.show: plt.show()
    plt.clf()

    dfROI = results['getROIBaselineAveSN']
    plt.imshow(dfROI.T, cmap='viridis', aspect='auto')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: Average ROI Baseline")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Average ROI baseline (ADC counts)")
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Average ROI Baseline Metric")
    if args.show: plt.show()
    plt.clf()

    dfROI = results['getROIAmplAveSN']
    plt.imshow(dfROI.T, cmap='viridis', aspect='auto')
    plt.title(f"Run: {run}, Subfile: {subfile}, TPC Crate: {tpc}, Metric: Average ROI Amplitude")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Average ROI amplitude (ADC counts)")
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Average ROI Amplitude Metric")
    if args.show: plt.show()
    plt.clf()

    plt.close()
    if args.save: fpdf.close()
