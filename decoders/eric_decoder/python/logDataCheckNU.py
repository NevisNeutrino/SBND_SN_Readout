import os
import sys
import argparse
import uproot
import numpy as np
import pandas as pd

from utils import *
from writeToLog import *

if __name__ == "__main__":
    args = parseArguments()
    froot = uproot.open(args.file)
    logname = os.path.splitext(args.file)[0] + '.log'
    print("Input log file: ", logname)
    flog = open(logname, 'a')

    tree = froot["events"]
    femBranches, femSlots = getFEMs(tree)
    print(f"FEM slots: {femSlots}")

    frameNums = getFrameNums(tree)

    logEventEndMiss(tree, frameNums, 'NU', flog, writeLog=args.write, printTerm=args.print, printDF=args.print)
    if args.write: print("Logged: Event End Miss Metric")

    logFEMHeaderMiss(tree, frameNums, 'NU', femBranches, femSlots, flog, writeLog=args.write, printTerm=args.print, printDF=args.print)
    if args.write: print("Logged: FEM Header Miss Metric")
    
    logEventNumMetric(tree, frameNums, femBranches, femSlots, flog, writeLog=args.write, printTerm=args.print, printDF=args.print)
    if args.write: print("Logged: First Frame Numbers Metric")
    if args.write: print("Logged: Last Frame Numbers Metric")
    if args.write: print("Logged: Frame Number Difference Error Metric")
    if args.write: print("Logged: Frame Number Rollover Metric")

    logADCWordCntErr(tree, 'NU', femBranches, femSlots, flog, writeLog=args.write, printTerm=args.print)
    if args.write: print("Logged: ADC Word Count Difference Error Metric")

    logChannelMissNU(tree, femBranches, femSlots, flog, args.write, args.print)
    if args.write: print("Logged: Channel Start Miss Metric")
    if args.write: print("Logged: Channel End Miss Metric")

    flog.close()
