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
        run, tpc = getFileInfo(args.file)
    except ValueError as err:
        print(err)
        sys.exit(1)

    tree = froot["events"]
    femBranches, femSlots = getFEMs(tree)
    chNums = range(64)
    print(f"FEM slots: {femSlots}")

    eventNums = getEventNums(tree)

    plt.figure(figsize=(10, 6))

    eventEndMiss = getEventEndMiss(tree, eventNums, 'NU')
    nEvent = len(tree['eventID'].array())
    nEventEndMiss = len(eventEndMiss)
    x = [0, 1]
    y = [(nEvent - nEventEndMiss), nEventEndMiss]
    labels = [
        f"Total number of events = {sum(y)}",
        f"Number of events with Event End = {y[0]}",
        f"Number of events without Event End = {y[1]}"
    ]
    handles = [Patch(facecolor='none', edgecolor='none', label=label) for label in labels]
    plt.bar(x, y, width=1.0, align='center', edgecolor='black', linewidth=2.0)
    plt.yscale('log')
    plt.title(f"Run: {run}, TPC Crate: {tpc}, Metric: Event End Miss")
    plt.xticks(x, ["Event End Exist", "Event End Miss"])
    plt.ylabel("Number of events")
    plt.grid(True)
    plt.legend(handles=handles, loc='upper right', eventon=True, handlelength=0, handletextpad=0.)
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Event End Miss Metric")
    if args.show: plt.show()
    plt.clf()

    femDict = getFEMHeaderMiss(tree, eventNums, 'NU', femBranches, femSlots)
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
    plt.title(f"Run: {run}, TPC Crate: {tpc}, Metric: FEM Header Miss")
    plt.xticks(x, labels)
    plt.xlabel("FEM slot")
    plt.ylabel("Number of missing FEM headers")
    plt.grid(True)
    labels = [
        f"Total number of events = {nEvent}",
    ]
    handles = [Patch(facecolor='none', edgecolor='none', label=label) for label in labels]
    plt.legend(handles=handles, loc='upper right', frameon=True, handlelength=0, handletextpad=0.)
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: FEM Header Miss Metric")
    if args.show: plt.show()
    plt.clf()
    
    firstEventNums, lastEventNums, eventNumDiffDict, eventNumRolloverDict = getEventNumMetric(tree, eventNums, femBranches, femSlots)
    df = pd.DataFrame({'FEM Slot': femSlots, 'First Event Frame Number': firstEventNums, 'Last Event Frame Number': lastEventNums})
    df = df.astype(int).astype(str)
    plt.table(cellText=df.values, colLabels=df.columns, loc='center')
    plt.title(f"Run: {run}, TPC Crate: {tpc}, Metric: First and Last Event Frame Number")
    plt.axis('off')
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Table saved: First and Last Event Frame Numbers Metric")
    if args.show: plt.show()
    plt.clf()
    slots = []
    data = []
    for slot, df in eventNumDiffDict.items():
        slots.append(slot)
        data.append(df[f"fem{slot}/eventNumDiff_"])
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
    plt.title(f"Run: {run}, TPC Crate: {tpc}, Metric: Event Frame Number Difference")
    plt.xticks(centers, labels)
    plt.xlabel("Event frame number difference")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Event Frame Number Difference Metric")
    if args.show: plt.show()
    plt.clf()
    data = []
    for slot, df in eventNumRolloverDict.items():
        data.append(df[f"fem{slot}/eventNumRollover_"])
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
    plt.title(f"Run: {run}, TPC Crate: {tpc}, Metric: Event Frame Number Rollover")
    plt.xlabel("Event frame number rollover")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Event Frame Number Rollover Metric")
    if args.show: plt.show()
    plt.clf()

    plt.figure(figsize=(12, 6))

    femDict = getADCWordCnt(tree, 'NU', femBranches, femSlots)
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
    plt.title(f"Run: {run}, TPC Crate: {tpc}, Metric: ADC Word Count Difference")
    plt.xticks(centers, labels)
    plt.xlabel("ADC word count difference")
    plt.ylabel("Number of event frames")
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

    chStartMissDict chEndMissDict = getChannelMissNUtree, femBranches, femSlots)
    data = np.array([
        [len(chStartMissDict[x][y]) if y in chStartMissDict[x] else 0 for x in femSlots]
        for y in chNums
    ])
    data = np.ma.masked_less(data, 1)
    plt.imshow(data.T, cmap=cmap, vmin=0, aspect='auto')
    plt.title(f"Run: {run}, TPC Crate: {tpc}, Metric: Channel Start Miss")
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
    data = np.array([
        [len(chEndMissDict[x][y]) if y in chEndMissDict[x] else 0 for x in femSlots]
        for y in chNums
    ])
    data = np.ma.masked_less(data, 1)
    plt.imshow(data.T, cmap=cmap, vmin=0, aspect='auto')
    plt.title(f"Run: {run}, TPC Crate: {tpc}, Metric: Channel End Miss")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Frequency")
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Channel End Miss Metric")
    if args.show: plt.show()
    plt.clf()

    plt.close()
    if args.save: fpdf.close()
