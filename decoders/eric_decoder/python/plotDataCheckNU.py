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
    args = parseArguments()
    froot = uproot.open(args.root)
    if args.save:
        pdfname = os.path.splitext(args.root)[0] + '.pdf'
        print("Output pdf file: ", pdfname)
        fpdf = PdfPages(pdfname)

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
    plt.title("Event End Miss Metric")
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
    plt.title("FEM Header Miss Metric")
    plt.xticks(x, labels)
    plt.xlabel("FEM slot")
    plt.ylabel("Number of events")
    plt.grid(True)
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: FEM Header Miss Metric")
    if args.show: plt.show()
    plt.clf()
    
    firstEventNums, lastEventNums, eventNumDiffDict, eventNumRolloverDict = getEventNumMetric(tree, eventNums, femBranches, femSlots)
    indices = []
    labels = []
    for idx, slot in enumerate(femSlots):
        indices.append(idx)
        labels.append(slot)
    plt.bar(indices, firstEventNums, width=1.0, align='center', edgecolor='black', linewidth=2.0)
    plt.title("First Event Numbers Metric")
    plt.xticks(indices, labels)
    plt.xlabel("FEM slot")
    plt.ylabel("Event number")
    plt.grid(True)
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: First Event Numbers Metric")
    if args.show: plt.show()
    plt.clf()
    plt.bar(indices, lastEventNums, width=1.0, align='center', edgecolor='black', linewidth=2.0)
    plt.title("Last Event Numbers Metric")
    plt.xticks(indices, labels)
    plt.xlabel("FEM slot")
    plt.ylabel("Event number")
    plt.grid(True)
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Last Event Numbers Metric")
    if args.show: plt.show()
    plt.clf()
    data = []
    for slot, df in eventNumDiffDict.items():
        data.append(df[f"fem{slot}/eventNumDiff_"])
    flatten = [diff for diffs in data for diff in diffs]
    if len(flatten) == 0: bins = 1
    else: bins = range(0, (int(max(flatten)) + 2))
    counts, edges, _ = plt.hist(data, bins=bins, stacked=True, label=[f"FEM {slot}" for slot in eventNumDiffDict], edgecolor='black')
    heights = counts.max(axis=0)
    centers = (edges[:-1] + edges[1:]) / 2
    for x, y in zip(centers, heights):
        plt.text(x, y, str(int(y)), ha='center', va='bottom', fontweight='bold', fontsize=20)
    plt.ylim(top=(max(heights) * 1.1))
    #plt.yscale('symlog')
    plt.title("Event Number Difference Metric")
    plt.xlabel("Event number difference")
    plt.ylabel("Number of events")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Event Number Difference Metric")
    if args.show: plt.show()
    plt.clf()
    data = []
    for slot, df in eventNumRolloverDict.items():
        data.append(df[f"fem{slot}/eventNumRollover_"])
    flatten = [rollover for rollovers in data for rollover in rollovers]
    if len(flatten) == 0: bins = 1
    else: bins = range(0, (int(max(flatten)) + 2))
    counts, edges, _ = plt.hist(data, bins=bins, stacked=True, label=[f"FEM {slot}" for slot in eventNumRolloverDict], edgecolor='black')
    heights = counts.max(axis=0)
    centers = (edges[:-1] + edges[1:]) / 2
    if max(heights) > 0:
        for x, y in zip(centers, heights):
            plt.text(x, y, str(int(y)), ha='center', va='bottom', fontweight='bold', fontsize=20)
        plt.ylim(top=(max(heights) * 1.1))
    #plt.yscale('symlog')
    plt.title("Event Number Rollover Metric")
    plt.xlabel("Event number rollover")
    plt.ylabel("Number of events")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Event Number Rollover Metric")
    if args.show: plt.show()
    plt.clf()

    plt.figure(figsize=(18, 6))

    chStartMissDict chEndMissDict = getChannelMissNUtree, femBranches, femSlots)
    data = np.array([
        [len(chStartMissDict[x][y]) if y in chStartMissDict[x] else 0 for x in femSlots]
        for y in chNums
    ])
    plt.imshow(data.T, cmap='viridis', aspect='auto')
    plt.title("Channel Start Miss Metric")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Number of events")
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
    plt.imshow(data.T, cmap='viridis', aspect='auto')
    plt.title("Channel End Miss Metric")
    plt.xticks(ticks=chNums, labels=chNums)
    plt.yticks(ticks=np.arange(len(femSlots)), labels=femSlots)
    plt.xlabel("Channel number")
    plt.ylabel("FEM slot")
    plt.colorbar(label="Number of events")
    plt.tight_layout()
    if args.save: 
        fpdf.savefig()
        print("Plot saved: Channel End Miss Metric")
    if args.show: plt.show()
    plt.clf()

    plt.close()
    if args.save: fpdf.close()
