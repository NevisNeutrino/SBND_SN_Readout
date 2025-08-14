import argparse
import re
import numpy as np

def parseArguments():
    def checkRootFile(file):
        if not file.endswith(".root"):
            raise argparse.ArgumentTypeError(f"Input root file must be a .root file")
        elif not os.access(file, os.R_OK):
            raise argparse.ArgumentTypeError(f"{file} can't be opened")
        return file

    def checkLogFile(file):
        if not file.endswith(".log"):
            raise argparse.ArgumentTypeError(f"Input log file must be a .log file")
        elif not os.access(file, os.R_OK):
            raise argparse.ArgumentTypeError(f"{file} can't be opened")
        return file

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--root", type=checkRootFile, required=True, help="input root file")
    parser.add_argument("--log", type=checkLogFile, required=True, help="input log file")
    args = parser.parse_args()

    print("Input root file: ", args.root)
    print("Input log file: ", args.log)

    return args

def getFEMs(tree):
    branches = np.array(tree.keys())
    mask = np.char.find(branches, 'fem') >= 0
    mask &= np.char.find(branches, '/') == -1
    femBranches = branches[mask]
    femSlots = [int(re.search(r'\d+', s).group()) for s in femBranches]
    return femBranches, femSlots

def getEventNums(tree):
    eventID = tree['eventID'].array(library='np')
    allFEMHeaderMiss = tree['allFEMHeaderMiss'].array(library='np')

    if sum(allFEMHeaderMiss) == 0:
        nanFrameNumPadCnt = 0
    else:
        nanFrameNumPadCnt = eventID[allFEMHeaderMiss][0] - 1

    fems, _ = getFEMs(tree)
    allEventNum = set()
    for fem in fems:
        branch = fem + '/eventNum_'
        femEventNum = tree[branch].array().tolist()
        allEventNum.update(femEventNum)
    minEventNum = min(allEventNum)

    eventNums = []
    for i in range(len(eventID)):
        if i < nanEventNumPadCnt: eventNums.append(np.nan)
        else: eventNums.append(minEventNum + i)
    return eventNums

def getFrameNums(tree):
    eventID = tree['eventID'].array(library='np')
    allFEMHeaderMiss = tree['allFEMHeaderMiss'].array(library='np')

    if sum(allFEMHeaderMiss) == 0:
        nanFrameNumPadCnt = 0
    else:
        nanFrameNumPadCnt = eventID[allFEMHeaderMiss][0] - 1

    fems, _ = getFEMs(tree)
    allFrameNum = set()
    for fem in fems:
        branch = fem + '/frameNum_'
        femFrameNum = tree[branch].array().tolist()
        allFrameNum.update(femFrameNum)
    minFrameNum = min(allFrameNum)

    frameNums = []
    for i in range(len(eventID)):
        if i < nanFrameNumPadCnt: frameNums.append(np.nan)
        else: frameNums.append(minFrameNum + i)
    return frameNums
