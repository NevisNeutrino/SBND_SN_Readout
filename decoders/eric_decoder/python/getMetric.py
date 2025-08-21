import numpy as np
import awkward as ak
import pandas as pd
import uproot
from collections import defaultdict


def getEventEndMiss(tree, numArr, dataType):
    if dataType == 'NU': numType = 'eventNum_'
    elif dataType == 'SN': numType = 'frameNum_'
    
    df = tree.arrays(['eventID', 'eventEndMiss'], library='pd')
    df[numType] = numArr

    nEventEndMiss = df['eventEndMiss'].sum()

    if nEventEndMiss > 0:
        eventEndMiss = df.loc[df['eventEndMiss'], numType].tolist()
    
    return eventEndMiss


def getFEMHeaderMiss(tree, numArr, dataType, femBranches, femSlots):
    if dataType == 'NU': numType = 'eventNum_'
    elif dataType == 'SN': numType = 'frameNum_'
    
    df = pd.DataFrame()
    df[numType] = numArr

    for fem in femBranches:
        slotBranch = fem + '/femSlot_'
        numBranch = fem + '/' + numType
        slots = tree[slotBranch].array(library='np')
        nums = tree[numBranch].array(library='np').astype(float)
        nanNumPadCnt = len(numArr) - len(nums)
        if nanNumPadCnt > 0: 
            slots = np.concatenate((np.full(nanNumPadCnt, 65535), slots))
            nums = np.concatenate((np.full(nanNumPadCnt, np.nan), nums))
        nums[slots == 65535] = np.nan
        df[numBranch] = nums

    femDict = {}

    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/' + numType
        nums = df.loc[pd.isna(df[numBranch]), numType].tolist()
        if len(nums) > 0:
            femDict[slot] = nums

    return femDict


def getEventNumMetric(tree, eventNums, femBranches, femSlots):
    df = pd.DataFrame()
    nEvent = len(eventNums)

    for fem in femBranches:
        slotBranch = fem + '/femSlot_'
        numBranch = fem + '/eventNum_'
        slots = tree[slotBranch].array(library='np')
        nums = tree[numBranch].array(library='np').astype(float)
        nanNumPadCnt = nEvent - len(nums)
        if nanNumPadCnt > 0: 
            slots = np.concatenate((np.full(nanNumPadCnt, 65535), slots))
            nums = np.concatenate((np.full(nanNumPadCnt, np.nan), nums))
        nums[slots == 65535] = np.nan
        df[numBranch] = nums

    firstEventNums = df.apply(lambda fem: fem[fem.first_valid_index()]).values
    lastEventNums = df.apply(lambda fem: fem[fem.last_valid_index()]).values

    eventNumDiffAllowed = 1
    eventNumRolloverThres = 16777215 # 0xFFFFFF

    eventNumDiffDict = {}
    eventNumRolloverDict = {}
    
    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/eventNum_'
        diffBranch = branch + '/eventNumDiff_'
        rolloverBranch = branch + '/eventNumRollover_'

        dfSlot = pd.DataFrame()
        dfSlot[numBranch] = df[numBranch].dropna()
        dfSlot[diffBranch] = dfSlot[numBranch].diff()
        dfSlot.dropna(inplace=True)

        eventNumDiffDict[slot] = dfSlot[dfSlot[diffBranch] >= 0]
        
        eventNumDiffErr = dfSlot[diffBranch] > eventNumDiffAllowed
        eventNumDiffErrCnt = eventNumDiffErr.sum()

        eventNumRolloverDict[slot] = dfSlot[dfSlot[diffBranch] < 0].rename(columns={diffBranch: rolloverBranch})
        eventNumRolloverDict[slot] += eventNumRolloverThres

        eventNumRollover = dfSlot[diffBranch] < 0
        eventNumRolloverCnt = eventNumRollover.sum()
    
    return firstEventNums, lastEventNums, eventNumDiffDict, eventNumRolloverDict


def getFrameNumMetric(tree, frameNums, femBranches, femSlots):
    df = pd.DataFrame()
    nFrame = len(frameNums)

    for fem in femBranches:
        slotBranch = fem + '/femSlot_'
        numBranch = fem + '/frameNum_'
        slots = tree[slotBranch].array(library='np')
        nums = tree[numBranch].array(library='np').astype(float)
        nanNumPadCnt = nFrame - len(nums)
        if nanNumPadCnt > 0: 
            slots = np.concatenate((np.full(nanNumPadCnt, 65535), slots))
            nums = np.concatenate((np.full(nanNumPadCnt, np.nan), nums))
        nums[slots == 65535] = np.nan
        df[numBranch] = nums

    firstFrameNums = df.apply(lambda fem: fem[fem.first_valid_index()]).values
    lastFrameNums = df.apply(lambda fem: fem[fem.last_valid_index()]).values

    frameNumDiffAllowed = set(range(1, 6))
    frameNumRolloverThres = 16777215 # 0xFFFFFF

    frameNumDiffDict = {}
    frameNumRolloverDict = {}
    
    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/frameNum_'
        diffBranch = branch + '/frameNumDiff_'
        rolloverBranch = branch + '/frameNumRollover_'

        dfSlot = pd.DataFrame()
        dfSlot[numBranch] = df[numBranch].dropna()
        dfSlot[diffBranch] = dfSlot[numBranch].diff()
        dfSlot.dropna(inplace=True)

        frameNumDiffDict[slot] = dfSlot[dfSlot[diffBranch] >= 0]
        
        frameNumDiffErr = ~dfSlot[diffBranch].isin(frameNumDiffAllowed)
        frameNumDiffErrCnt = frameNumDiffErr.sum()

        frameNumRolloverDict[slot] = dfSlot[dfSlot[diffBranch] < 0].rename(columns={diffBranch: rolloverBranch})
        frameNumRolloverDict[slot] += frameNumRolloverThres

        frameNumRollover = dfSlot[diffBranch] < 0
        frameNumRolloverCnt = frameNumRollover.sum()

    return firstFrameNums, lastFrameNums, frameNumDiffDict, frameNumRolloverDict


def getADCWordCnt(tree, dataType, femBranches, femSlots):
    if dataType == 'NU': numType = 'eventNum_'
    elif dataType == 'SN': numType = 'frameNum_'

    femDict = {}

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        numBranch = branch + '/' + numType
        adcCntTrueBranch = branch + '/adcCntTrue_'
        adcCntRecoBranch = branch + '/adcCntReco_'

        slots = tree[slotBranch].array(library='np')
        nums = tree[numBranch].array(library='np')
        trueCnts = tree[adcCntTrueBranch].array(library='np').astype(np.int64)
        recoCnts = tree[adcCntRecoBranch].array(library='np').astype(np.int64)

        nums = nums[slots != 65535]
        trueCnts = trueCnts[slots != 65535]
        recoCnts = recoCnts[slots != 65535]
        diffs = recoCnts - trueCnts

        femDict[slot] = pd.DataFrame({numBranch: nums, f"{branch}/adcCntDiff_": diffs})

    return femDict


def getChannelMissNU(tree, femBranches, femSlots):
    allChNums = set([ch for ch in range(64)])

    chStartMissDict = {}
    chEndMissDict = {}

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        numBranch = branch + '/eventNum_'
        chStartNumBranch = branch + '/channels_/channels_.channelStartNum_'
        chEndMissBranch = branch + '/channels_/channels_.channelEndMiss_'

        slots = tree[slotBranch].array()
        nums = tree[numBranch].array()
        chStartNums = tree[chStartNumBranch].array()
        chEndMisses = tree[chEndMissBranch].array()

        for slot, num, startNums, endMisses in zip(slots, nums, chStartNums, chEndMissess):
            if slot == 65535: continue

            if slot not in chStartMissDict: chStartMissDict[slot] = {} 
            chNums = list(allChNums - set(startNums))
            if len(chNums) > 0:
                for ch in chNums:
                    if ch not in chStartMissDict[slot]: chStartMissDict[slot][ch] = []
                    chStartMissDict[slot][ch].append(num)

            if slot not in chEndMissDict: chEndMissDict[slot] = {} 
            chNums = startNums[endMisses]
            if len(chNums) > 0:
                for ch in chNums:
                    if ch not in chEndMissDict[slot]: chEndMissDict[slot][ch] = []
                    chEndMissDict[slot][ch].append(num)
    
    return chStartMissDict, chEndMissDict


def getChannelStartMissSN(tree, femBranches, femSlots):
    allChNums = set([ch for ch in range(64)])

    chStartMissDict = {}

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        numBranch = branch + '/frameNum_'
        chNumBranch = branch + '/channels_/channels_.channelNum_'

        slots = tree[slotBranch].array()
        nums = tree[numBranch].array()
        chNums = tree[chNumBranch].array()

        for slot, num, channels in zip(slots, nums, chNums):
            if slot == 65535: continue

            if slot not in chStartMissDict: chStartMissDict[slot] = {} 
            chMisses = list(allChNums - set(channels))
            if len(chMisses) > 0:
                for ch in chMisses:
                    if ch not in chStartMissDict[slot]: chStartMissDict[slot][ch] = []
                    chStartMissDict[slot][ch].append(num)

    return chStartMissDict


def getROIMissCntSN(tree, femBranches, femSlots):
    roiStartMissCntDict = {}
    roiEndMissCntDict = {}

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        numBranch = branch + '/frameNum_'
        chNumBranch = branch + '/channels_/channels_.channelNum_'
        roiStartMissCntBranch = branch + '/channels_/channels_.roiStartMissCnt_'
        roiEndMissCntBranch = branch + '/channels_/channels_.roiEndMissCnt_'

        slots = tree[slotBranch].array()
        nums = tree[numBranch].array()
        chNums = tree[chNumBranch].array()
        roiStartMissCnts = tree[roiStartMissCntBranch].array()
        roiEndMissCnts = tree[roiEndMissCntBranch].array()

        for slot, num, channels, startMissCnts, endMissCnts in zip(slots, nums, chNums, roiStartMissCnts, roiEndMissCnts):
            if slot == 65535: continue

            if slot not in roiStartMissCntDict: roiStartMissCntDict[slot] = {} 
            if slot not in roiEndMissCntDict: roiEndMissCntDict[slot] = {} 

            for ch, startMissCnt, endMissCnt in zip(channels, startMissCnts, endMissCnts):
                if ch not in roiStartMissCntDict[slot]: roiStartMissCntDict[slot][ch] = []
                if startMissCnt > 0:
                    roiStartMissCntDict[slot][ch].append((num, startMissCnt))

                if ch not in roiEndMissCntDict[slot]: roiEndMissCntDict[slot][ch] = []
                if endMissCnt > 0:
                    roiEndMissCntDict[slot][ch].append((num, endMissCnt))

    return roiStartMissCntDict, roiEndMissCntDict


def getROICntSN(tree, femBranches, femSlots, femSelect):
    allChNums = [ch for ch in range(64)]

    dfROICnt = pd.DataFrame(np.nan, index=allChNums, columns=nums)
    dfROICnt.index.name = 'channelNum_'

    for branch, slot in zip(femBranches, femSlots):
        if slot != femSelect: continue

        slotBranch = branch + '/femSlot_'
        numBranch = branch + '/frameNum_'
        chNumBranch = branch + '/channels_/channels_.channelNum_'
        roiTimestampBranch = branch + '/channels_/channels_.roiTimestamps_'

        slots = tree[slotBranch].array()
        nums = tree[numBranch].array()
        chNums = tree[chNumBranch].array()
        roiTimestamps = tree[roiTimestampBranch].array()

        for slot, num, channels, timestamps in zip(slots, nums, chNums, roiTimestamps):
            if slot == 65535: continue

            rois = list(map(len, timestamps))
            dfROICnt.loc[channels, num] = rois

    dfROICnt.dropna(axis=1, how='all', inplace=True)

    return dfROICnt


def getROICntAveSN(tree, femBranches, femSlots):
    allChNums = [ch for ch in range(64)]

    dfROICntAve = pd.DataFrame(0, index=allChNums, columns=femBranches, dtype=float)
    dfROICntAve.index.name = 'channel'

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        chNumBranch = branch + '/channels_/channels_.channelNum_'
        roiTimestampBranch = branch + '/channels_/channels_.roiTimestamps_'

        slots = tree[slotBranch].array()
        chNums = tree[chNumBranch].array()
        roiTimestamps = tree[roiTimestampBranch].array()

        chROICntDict = defaultdict(list)
        for slot, channels, timestamps in zip(slots, chNums, roiTimestamps):
            if slot == 65535: continue

            for channel, rois in zip(channels, timestamps):
                chROICntDict[channel].append(len(rois))

        roiCntAve = [np.mean(cnts) for cnts in chROICntDict.values()]
        dfROICntAve.loc[list(chROICntDict.keys()), branch] = roiCntAve

    return dfROICntAve


def getROIBaselineAveSN(tree, femBranches, femSlots):
    allChNums = [ch for ch in range(64)]

    dfROIBaselineAve = pd.DataFrame(0, index=allChNums, columns=femBranches, dtype=float)
    dfROIBaselineAve.index.name = 'channel'

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        chNumBranch = branch + '/channels_/channels_.channelNum_'
        roiTimestampBranch = branch + '/channels_/channels_.roiTimestamps_'

        slots = tree[slotBranch].array()
        chNums = tree[chNumBranch].array()
        roiTimestamps = tree[roiTimestampBranch].array()

        chROIBaselineDict = defaultdict(list)
        for slot, channels, timestamps in zip(slots, chNums, roiTimestamps):
            if slot == 65535: continue

            for channel, rois in zip(channels, timestamps):
                if len(rois) == 0: continue
                chROIBaselineDict[channel].append(rois[0])

        roiBaselineAve = [np.mean(cnts) for cnts in chROIBaselineDict.values()]
        dfROIBaselineAve.loc[list(chROIBaselineDict.keys()), branch] = roiBaselineAve

    return dfROIBaselineAve


def getROIAmplAveSN(tree, femBranches, femSlots):
    allChNums = [ch for ch in range(64)]

    dfROIAmplAve = pd.DataFrame(0, index=allChNums, columns=femBranches, dtype=float)
    dfROIAmplAve.index.name = 'channel'

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        chNumBranch = branch + '/channels_/channels_.channelNum_'
        roiTimestampBranch = branch + '/channels_/channels_.roiTimestamps_'

        slots = tree[slotBranch].array()
        chNums = tree[chNumBranch].array()
        roiTimestamps = tree[roiTimestampBranch].array()

        chROIAmplDict = defaultdict(list)
        for slot, channels, timestamps in zip(slots, chNums, roiTimestamps):
            if slot == 65535: continue

            for channel, rois in zip(channels, timestamps):
                if len(rois) == 0: continue
                chROIAmplDict[channel].append(max(rois))

        roiAmplAve = [np.mean(cnts) for cnts in chROIAmplDict.values()]
        dfROIAmplAve.loc[list(chROIAmplDict.keys()), branch] = roiAmplAve

    return dfROIAmplAve
