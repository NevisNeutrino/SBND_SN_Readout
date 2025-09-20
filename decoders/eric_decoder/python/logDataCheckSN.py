import os
import sys
import argparse
import uproot
import numpy as np
import pandas as pd

from utils import *
from writeToLog import *

if __name__ == "__main__":
    try:
        args = parseArguments()
    except argparse.ArgumentTypeError as err:
        print(err)
        sys.exit(1)

    froot = uproot.open(args.file)
    logname = os.path.splitext(args.file)[0] + '.log'
    print("Input log file: ", logname)
    flog = open(logname, 'a')

    try:
        run, subfile, tpc = getFileInfo(args.file)
    except ValueError as err:
        print(err)
        sys.exit(1)

    print(f"Run: {run}", file=flog)
    print(f"Subfile: {subfile}", file=flog)
    print(f"TPC Crate: {tpc}", file=flog)

    tree = froot["events"]
    femBranches, femSlots = getFEMs(tree)
    print(f"FEM slots: {femSlots}")
    print(f"FEM slots: {femSlots}", file=flog)

    frameNums = getFrameNums(tree)

    logEventEndMiss(tree, frameNums, 'SN', flog, writeLog=args.write, printTerm=args.print, printDF=args.print)
    if args.write: print("Logged: Packet Frame End Miss Metric")

    logFEMHeaderMiss(tree, frameNums, 'SN', femBranches, femSlots, flog, writeLog=args.write, printTerm=args.print, printDF=args.print)
    if args.write: print("Logged: FEM Header Miss Metric")
    
    logFrameNumMetric(tree, frameNums, femBranches, femSlots, flog, writeLog=args.write, printTerm=args.print, printDF=args.print)
    if args.write: print("Logged: First and Last Packet Frame Numbers Metric")
    if args.write: print("Logged: Packet Frame Number Difference Error Metric")
    if args.write: print("Logged: Packet Frame Number Rollover Metric")

    logADCWordCntErr(tree, 'SN', femBranches, femSlots, flog, writeLog=args.write, printTerm=args.print)
    if args.write: print("Logged: ADC Word Count Difference Error Metric")

    logChannelStartMissSN(tree, femBranches, femSlots, flog, args.write, args.print)
    if args.write: print("Logged: Channel Start Miss Metric")

    logROIMissCntSN(tree, femBranches, femSlots, flog, args.write, args.print)
    if args.write: print("Logged: ROI Start Miss Metric")
    if args.write: print("Logged: ROI End Miss Metric")

    flog.close()
