import numpy as np
import awkward as ak
import pandas as pd
import uproot


def getEventEndMiss(tree, numArr, dataType, logFile, writeLog=False, printDF=False):
    if dataType == 'NU': numType = 'eventNum_'
    elif dataType == 'SN': numType = 'frameNum_'
    
    df = tree.arrays(['eventID', 'eventEndMiss'], library='pd')
    df[numType] = numArr

    if (printDF): display(df)

    file = open(logFile, 'a')

    nEventEndMiss = df['eventEndMiss'].sum()
    if writeLog: print(f"Number of event end missing: {nEventEndMiss}", file=file)
    else: print(f"Number of event end missing: {nEventEndMiss}")

    if nEventEndMiss > 0:
        eventEndMiss = df.loc[df['eventEndMiss'], numType].tolist()
        nums = ", ".join(str(int(num)) for num in eventEndMiss)
        if writeLog:
            if dataType == 'NU': print(f"Event numbers with missing event end: {nums}", file=file)
            elif dataType == 'SN': print(f"Frame numbers with missing event end: {nums}", file=file)
        else:
            if dataType == 'NU': print(f"Event numbers with missing event end: {nums}")
            elif dataType == 'SN': print(f"Frame numbers with missing event end: {nums}")

    file.close()
    
    return eventEndMiss


def getFEMHeaderMiss(tree, numArr, dataType, femBranches, femSlots, logFile, writeLog=False, printDF=False):
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
    
    if (printDF): display(df)

    file = open(logFile, 'a')

    femDict = {}

    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/' + numType
        nums = df.loc[pd.isna(df[numBranch]), numType].tolist()
        if len(nums) > 0:
            femDict[slot] = nums
            nums = ", ".join(str(int(num)) for num in nums)
            if writeLog:
                print(f"Number of FEM header missing for FEM {slot}: {len(nums)}", file=file)
                if dataType == 'NU': print(f"Event numbers with missing FEM header for FEM {slot}: {nums}", file=file)
                elif dataType == 'SN': print(f"Event packet frame numbers with missing FEM header for FEM {slot}: {nums}", file=file)
            else:
                print(f"Number of FEM header missing for FEM {slot}: {len(nums)}")
                if dataType == 'NU': print(f"Event numbers with missing FEM header for FEM {slot}: {nums}")
                elif dataType == 'SN': print(f"Event packet frame numbers with missing FEM header for FEM {slot}: {nums}")

    file.close()

    return femDict


def getEventNumMetric(tree, eventNums, femBranches, femSlots, logFile, writeLog=False, printDF=False):
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
            nums = np.concatenate((np.full(nFrameNumPad, np.nan), nums))
        nums[slots == 65535] = np.nan
        df[numBranch] = nums

    if (printDF): display(df)

    file = open(logFile, 'a')

    firstEventNums = df.apply(lambda fem: fem[fem.first_valid_index()]).values
    lastEventNums = df.apply(lambda fem: fem[fem.last_valid_index()]).values
    if writeLog:
        print(f"FEM slots: {", ".join(str(int(num)) for num in femSlots)}", file=file)
        nums = ", ".join(str(int(num)) for num in firstEventNums)
        print(f"First event number from FEMs: {nums}", file=file)
        nums = ", ".join(str(int(num)) for num in lastEventNums)
        print(f"Last event number from FEMs: {nums}", file=file)
    else:
        print(f"FEM slots: {", ".join(str(int(num)) for num in femSlots)}")
        nums = ", ".join(str(int(num)) for num in firstEventNums)
        print(f"First event number from FEMs: {nums}")
        nums = ", ".join(str(int(num)) for num in lastEventNums)
        print(f"Last event number from FEMs: {nums}")

    eventNumDiffAllowed = 1
    eventNumRolloverThres = 16777215 # 0xFFFFFF

    eventNumDiffDict = {}
    eventNumRolloverDict = {}
    
    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/' + numType
        diffBranch = branch + '/' + numType[:-1] + 'Diff_'
        df[diffBranch] = df[numBranch].diff()
        
        eventNumDiffErr = df[eventNumDiff] > eventNumDiffAllowed
        eventNumDiffErrCnt = frameNumDiffErr.sum()
        
        if eventNumDiffErrCnt > 0:
            diffs = df.loc[eventNumDiffErr, diffBranch].to_numpy()
            diffs = diffs[~np.isnan(diffs)]
            nums = df.loc[eventNumDiffErr, numBranch].to_numpy()
            nums = nums[~np.isnan(nums)]
            elems = list(zip(nums, diffs))
            eventNumDiffDict[slot] = elems

            diffs = ", ".join(str(int(num)) for num in diffs)
            nums = ", ".join(str(int(num)) for num in nums)
            if writeLog:
                print(f"Number of event number differences > 1 for FEM {slot}: {eventNumDiffErrCnt}", file=file)
                print(f"Event numbers with jump > {eventNumDiffAllowed} for FEM {slot}: {nums}", file=file)
                print(f"Event number differences for FEM {slot}: {diffs}", file=file)
            else:
                print(f"Number of event number differences > 1 for FEM {slot}: {eventNumDiffErrCnt}")
                print(f"Event numbers with jump > {eventNumDiffAllowed} for FEM {slot}: {nums}")
                print(f"Event number differences for FEM {slot}: {diffs}")

        eventNumRollover = df[eventNumDiff] < 0
        eventNumRolloverCnt = eventNumRollover.sum()
        
        if eventNumRolloverCnt > 0:
            rollovers = df.loc[eventNumRollover, diffBranch].to_numpy()
            rollovers = rollovers[~np.isnan(rollovers)]
            rollovers += eventNumRolloverThres
            nums = df.loc[eventNumRollover, numBranch].to_numpy()
            nums = nums[~np.isnan(nums)]
            elems = list(zip(nums, diffs))
            eventNumRolloverDict[slot] = elems

            rollovers = ", ".join(str(int(num)) for num in eventNumRollovers)
            nums = ", ".join(str(int(num)) for num in nums)
            if writeLog:
                print(f"Number of event number rollovers for FEM {slot}: {eventNumRolloverCnt}", file=file)
                print(f"Event numbers with rollover for FEM {slot}: {nums}", file=file)
                print(f"Event number rollovers for FEM {slot}: {rollovers}", file=file)
            else:
                print(f"Number of event number rollovers for FEM {slot}: {eventNumRolloverCnt}")
                print(f"Event numbers with rollover for FEM {slot}: {nums}")
                print(f"Event number rollovers for FEM {slot}: {rollovers}")


    file.close()
    
    return eventNumDiffDict, eventNumRolloverDict


def getFrameNumMetric(tree, frameNums, femBranches, femSlots, logFile, writeLog=False, printDF=False):
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
            nums = np.concatenate((np.full(nFrameNumPad, np.nan), nums))
        nums[slots == 65535] = np.nan
        df[numBranch] = nums

    if (printDF): display(df)

    file = open(logFile, 'a')

    firstFrameNums = df.apply(lambda fem: fem[fem.first_valid_index()]).values
    lastFrameNums = df.apply(lambda fem: fem[fem.last_valid_index()]).values
    if writeLog:
        print(f"FEM slots: {", ".join(str(int(num)) for num in femSlots)}", file=file)
        nums = ", ".join(str(int(num)) for num in firstFrameNums)
        print(f"First frame number from FEMs: {nums}", file=file)
        nums = ", ".join(str(int(num)) for num in lastFrameNums)
        print(f"Last frame number from FEMs: {nums}", file=file)
    else:
        print(f"FEM slots: {", ".join(str(int(num)) for num in femSlots)}")
        nums = ", ".join(str(int(num)) for num in firstFrameNums)
        print(f"First frame number from FEMs: {nums}")
        nums = ", ".join(str(int(num)) for num in lastFrameNums)
        print(f"Last frame number from FEMs: {nums}")

    frameNumDiffAllowed = set([1, 4])
    frameNumRolloverThres = 16777215 # 0xFFFFFF

    frameNumDiffDict = {}
    frameNumRolloverDict = {}
    
    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/' + numType
        diffBranch = branch + '/' + numType[:-1] + 'Diff_'
        df[diffBranch] = df[numBranch].diff()
        
        frameNumDiffErr = df[frameNumDiff] > frameNumDiffAllowed
        frameNumDiffErrCnt = frameNumDiffErr.sum()
        
        if frameNumDiffErrCnt > 0:
            diffs = df.loc[frameNumDiffErr, diffBranch].to_numpy()
            diffs = diffs[~np.isnan(diffs)]
            nums = df.loc[frameNumDiffErr, numBranch].to_numpy()
            nums = nums[~np.isnan(nums)]
            elems = list(zip(nums, diffs))
            frameNumDiffDict[slot] = elems

            diffs = ", ".join(str(int(num)) for num in diffs)
            nums = ", ".join(str(int(num)) for num in nums)
            if writeLog:
                print(f"Number of frame number differences not in {frameNumDiffAllowed} for FEM {slot}: {frameNumDiffErrCnt}", file=file)
                print(f"Frame numbers with jump not in {frameNumDiffAllowed} for FEM {slot}: {nums}", file=file)
                print(f"Frame number differences for FEM {slot}: {diffs}", file=file)
            else:
                print(f"Number of frame number differences not in {frameNumDiffAllowed} for FEM {slot}: {frameNumDiffErrCnt}")
                print(f"Frame numbers with jump not in {frameNumDiffAllowed} for FEM {slot}: {nums}")
                print(f"Frame number differences for FEM {slot}: {diffs}")

        frameNumRollover = df[frameNumDiff] < 0
        frameNumRolloverCnt = frameNumRollover.sum()
        
        if frameNumRolloverCnt > 0:
            rollovers = df.loc[frameNumRollover, diffBranch].to_numpy()
            rollovers = rollovers[~np.isnan(rollovers)]
            rollovers += frameNumRolloverThres
            nums = df.loc[frameNumRollover, numBranch].to_numpy()
            nums = nums[~np.isnan(nums)]
            elems = list(zip(nums, diffs))
            frameNumRolloverDict[slot] = elems

            rollovers = ", ".join(str(int(num)) for num in frameNumRollovers)
            nums = ", ".join(str(int(num)) for num in nums)
            if writeLog:
                print(f"Number of frame number rollovers for FEM {slot}: {frameNumRolloverCnt}", file=file)
                print(f"Frame numbers with rollover for FEM {slot}: {nums}", file=file)
                print(f"Frame number rollovers for FEM {slot}: {rollovers}", file=file)
            else:
                print(f"Number of frame number rollovers for FEM {slot}: {frameNumRolloverCnt}")
                print(f"Frame numbers with rollover for FEM {slot}: {nums}")
                print(f"Frame number rollovers for FEM {slot}: {rollovers}")


    file.close()
    
    return frameNumDiffDict, frameNumRolloverDict


def getADCWordCntErr(tree, datatype, femBranches, femSlots, logFile, writeLog=False):
    if dataType == 'NU': numType = 'eventNum_'
    elif dataType == 'SN': numType = 'frameNum_'

    file = open(logFile, 'a')

    femDict = {}

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        numBranch = branch + '/' + numType
        adcCntTrueBranch = branch + '/adcCntTrue_'
        adcCntRecoBranch = branch + '/adcCntReco_'

        slots = tree[slotBranch].array(library='np')
        nums = tree[numBranch].array(library='np')
        trueCnts = tree[adcCntTrueBranch].array(library='np')
        recoCnts = tree[adcCntRecoBranch].array(library='np')

        nums = nums[slots != 65535]
        trueCnts = trueCnts[slots != 65535]
        recoCnts = recoCnts[slots != 65535]
        diffs = trueCnts - recoCnts

        nums = nums[diffs != 0]
        diffs = diffs[diffs != 0]
        nDiffErr = len(nums)
        if nDiffErr > 0:
            if writeLog:
                print(f"Number of ADC word count mismatches for FEM {slot}: {nDiffErr}", file=file)
                femDict[slot] = list(zip(nums, diffs))
                nums = ", ".join(str(int(num)) for num in nums)
                if dataType == 'NU':
                    print(f"Event numbers with ADC word count mismatch for FEM {slot}: {nums}", file=file)
                elif dataType == 'SN':
                    print(f"Frame numbers with ADC word count mismatch for FEM {slot}: {nums}", file=file)
                print(f"ADC word count differences for FEM {slot}: {diffs}", file=file)
            else:
                print(f"Number of ADC word count mismatches for FEM {slot}: {nDiffErr}")
                femDict[slot] = list(zip(nums, diffs))
                nums = ", ".join(str(int(num)) for num in nums)
                if dataType == 'NU':
                    print(f"Event numbers with ADC word count mismatch for FEM {slot}: {nums}")
                elif dataType == 'SN':
                    print(f"Frame numbers with ADC word count mismatch for FEM {slot}: {nums}")
                print(f"ADC word count differences for FEM {slot}: {diffs}")

    file.close()

    return femDict


def getChannelMissNU(tree, femBranches, femSlots, logFile, writeLog=False):
    allChNums = set([ch for ch in range(64)])

    file = open(logFile, 'a')

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
                    chNums = ", ".join(str(int(num)) for num in chNums)
                    if writeLog:
                        print(f"Event number {num}: Channel start miss for channels {chNums} in FEM {slot}", file=file)
                    else:
                        print(f"Event number {num}: Channel start miss for channels {chNums} in FEM {slot}")

            if slot not in chEndMissDict: chEndMissDict[slot] = {} 
            chNums = startNums[endMisses]
            if len(chNums) > 0:
                for ch in chNums:
                    if ch not in chEndMissDict[slot]: chEndMissDict[slot][ch] = []
                    chEndMissDict[slot][ch].append(num)
                chNums = ", ".join(str(int(num)) for num in chNums)
                if writeLog:
                    print(f"Event number {num}: Channel end miss for channels {chNums} in FEM {slot}", file=file)
                else:
                    print(f"Event number {num}: Channel end miss for channels {chNums} in FEM {slot}")

    file.close()
    
    return chStartMissDict, chEndMissDict


def getChannelStartMissSN(tree, femBranches, femSlots, logFile, writeLog=False):
    allChNums = set([ch for ch in range(64)])

    file = open(logFile, 'a')

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
                chMisses = ", ".join(str(int(num)) for num in chMisses)
                if writeLog:
                    print(f"Frame number {num}: Channel start miss for channels {chMisses} in FEM {slot}", file=file)
                else:
                    print(f"Frame number {num}: Channel start miss for channels {chMisses} in FEM {slot}")

    file.close()

    return chStartMissDict


def getROIMissCntSN(tree, femBranches, femSlots, logFile, writeLog=False):
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

            if slot not in roiStartMissDict: roiStartMissDict[slot] = {} 
            if slot not in roiEndMissDict: roiEndMissDict[slot] = {} 

            for ch, startMissCnt, endMissCnt in zip(channels, startMissCnts, endMissCnts):
                if ch not in roiStartMissDict[slot]: roiStartMissDict[slot][ch] = []
                if startMissCnt > 0:
                    roiStartMissDict[slot][ch].append(num, startMissCnt)
                    if writeLog:
                        print(f"Frame number {num}: {startMissCnt} ROI start miss for channel {ch} in FEM {slot}", file=file)
                    else:
                        print(f"Frame number {num}: {startMissCnt} ROI start miss for channel {ch} in FEM {slot}")

                if ch not in roiEndMissDict[slot]: roiEndMissDict[slot][ch] = []
                if endMissCnt > 0:
                    roiEndMissDict[slot][ch].append(num, endMissCnt)
                    if writeLog:
                        print(f"Frame number {num}: {endMissCnt} ROI end miss for channel {ch} in FEM {slot}", file=file)
                    else:
                        print(f"Frame number {num}: {endMissCnt} ROI end miss for channel {ch} in FEM {slot}")

    return roiStartMissCntDict, roiEndMissCntDict


def getROICntSN(tree, femBranches, femSlots, femSelect, printDF=False):
    allChNums = [ch for ch in range(64)]

    roiCntDict = {}

    for branch, slot in zip(femBranches, femSlots):
        slotBranch = branch + '/femSlot_'
        numBranch = branch + '/frameNum_'
        chNumBranch = branch + '/channels_/channels_.channelNum_'
        roiTimestampBranch = branch + '/channels_/channels_.roiTimestamps_'

        slots = tree[slotBranch].array()
        nums = tree[numBranch].array()
        chNums = tree[chNumBranch].array()
        roiTimestamps = tree[roiTimestampBranch].array()

        for slot, num, channels, timestamps in zip(slots, nums, chNums, roiTimestamps):
            if slot != femSelect: continue

            if slot not in roiCntDict: 
                roiCntDict[slot] = pd.DataFrame(np.nan, index=allChNums, columns=nums)
                roiCntDict[slot].index.name = branch + '/channelNum_'

            rois = list(map(len, timestamps))
            roiCntDict[slot].loc[channels, num] = rois
            roiCntDict[slot].dropna(axis=1, how='all', inplace=True)

            if (printDF): display(roiCntDict[slot])

    return roiCntDict
