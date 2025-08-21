import numpy as np
import awkward as ak
import pandas as pd
import uproot


def logEventEndMiss(tree, numArr, dataType, logFile, writeLog=False, printTerm=False, printDF=False):
    if dataType == 'NU': numType = 'eventNum_'
    elif dataType == 'SN': numType = 'frameNum_'
    
    df = tree.arrays(['eventID', 'eventEndMiss'], library='pd')
    df[numType] = numArr

    if (printDF): display(df)

    nEventEndMiss = df['eventEndMiss'].sum()
    if writeLog: print(f"Number of event end missing: {nEventEndMiss}", file=logFile)
    elif printTerm: print(f"Number of event end missing: {nEventEndMiss}")

    if nEventEndMiss > 0:
        eventEndMiss = df.loc[df['eventEndMiss'], numType].tolist()
        nums = ", ".join(str(int(num)) for num in eventEndMiss)
        if writeLog:
            if dataType == 'NU': print(f"Event numbers with missing event end: {nums}", file=logFile)
            elif dataType == 'SN': print(f"Frame numbers with missing event end: {nums}", file=logFile)
        elif printTerm:
            if dataType == 'NU': print(f"Event numbers with missing event end: {nums}")
            elif dataType == 'SN': print(f"Frame numbers with missing event end: {nums}")


def logFEMHeaderMiss(tree, numArr, dataType, femBranches, femSlots, logFile, writeLog=False, printTerm=False, printDF=False):
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

    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/' + numType
        nums = df.loc[pd.isna(df[numBranch]), numType].tolist()
        if len(nums) > 0:
            nums = ", ".join(str(int(num)) for num in nums)
            if writeLog:
                print(f"Number of FEM header missing for FEM {slot}: {len(nums)}", file=logFile)
                if dataType == 'NU': print(f"Event numbers with missing FEM header for FEM {slot}: {nums}", file=logFile)
                elif dataType == 'SN': print(f"Event packet frame numbers with missing FEM header for FEM {slot}: {nums}", file=logFile)
            elif printTerm:
                print(f"Number of FEM header missing for FEM {slot}: {len(nums)}")
                if dataType == 'NU': print(f"Event numbers with missing FEM header for FEM {slot}: {nums}")
                elif dataType == 'SN': print(f"Event packet frame numbers with missing FEM header for FEM {slot}: {nums}")


def logEventNumMetric(tree, eventNums, femBranches, femSlots, logFile, writeLog=False, printTerm=False, printDF=False):
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

    if (printDF): display(df)

    firstEventNums = df.apply(lambda fem: fem[fem.first_valid_index()]).values
    lastEventNums = df.apply(lambda fem: fem[fem.last_valid_index()]).values
    if writeLog:
        print(f"FEM slots: {", ".join(str(int(num)) for num in femSlots)}", file=logFile)
        nums = ", ".join(str(int(num)) for num in firstEventNums)
        print(f"First event number from FEMs: {nums}", file=logFile)
        nums = ", ".join(str(int(num)) for num in lastEventNums)
        print(f"Last event number from FEMs: {nums}", file=logFile)
    elif printTerm:
        print(f"FEM slots: {", ".join(str(int(num)) for num in femSlots)}")
        nums = ", ".join(str(int(num)) for num in firstEventNums)
        print(f"First event number from FEMs: {nums}")
        nums = ", ".join(str(int(num)) for num in lastEventNums)
        print(f"Last event number from FEMs: {nums}")

    eventNumDiffAllowed = 1
    eventNumRolloverThres = 16777215 # 0xFFFFFF
    
    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/eventNum_'
        diffBranch = branch + '/eventNumDiff_'
        rolloverBranch = branch + '/eventNumRollover_'

        dfSlot = pd.DataFrame()
        dfSlot[numBranch] = df[numBranch].dropna()
        dfSlot[diffBranch] = dfSlot[numBranch].diff()
        dfSlot.dropna(inplace=True)
        
        eventNumDiffErr = dfSlot[diffBranch] > eventNumDiffAllowed
        eventNumDiffErrCnt = eventNumDiffErr.sum()
        
        if eventNumDiffErrCnt > 0:
            diffs = dfSlot.loc[eventNumDiffErr, diffBranch].to_numpy()
            diffs = ", ".join(str(int(diff)) for diff in diffs)
            nums = dfSlot.loc[eventNumDiffErr, numBranch].to_numpy()
            nums = ", ".join(str(int(num)) for num in nums)

            if writeLog:
                print(f"Number of event number differences > 1 for FEM {slot}: {eventNumDiffErrCnt}", file=logFile)
                print(f"Event numbers with jump > {eventNumDiffAllowed} for FEM {slot}: {nums}", file=logFile)
                print(f"Event number differences for FEM {slot}: {diffs}", file=logFile)
            elif printTerm:
                print(f"Number of event number differences > 1 for FEM {slot}: {eventNumDiffErrCnt}")
                print(f"Event numbers with jump > {eventNumDiffAllowed} for FEM {slot}: {nums}")
                print(f"Event number differences for FEM {slot}: {diffs}")

        eventNumRollover = dfSlot[diffBranch] < 0
        eventNumRolloverCnt = eventNumRollover.sum()
        
        if eventNumRolloverCnt > 0:
            rollovers = dfSlot.loc[eventNumRollover, diffBranch].to_numpy()
            rollovers += eventNumRolloverThres
            rollovers = ", ".join(str(int(num)) for num in rollovers)
            nums = dfSlot.loc[eventNumRollover, numBranch].to_numpy()
            nums = ", ".join(str(int(num)) for num in nums)

            if writeLog:
                print(f"Number of event number rollovers for FEM {slot}: {eventNumRolloverCnt}", file=logFile)
                print(f"Event numbers with rollover for FEM {slot}: {nums}", file=logFile)
                print(f"Event number rollovers for FEM {slot}: {rollovers}", file=logFile)
            elif printTerm:
                print(f"Number of event number rollovers for FEM {slot}: {eventNumRolloverCnt}")
                print(f"Event numbers with rollover for FEM {slot}: {nums}")
                print(f"Event number rollovers for FEM {slot}: {rollovers}")


def logFrameNumMetric(tree, frameNums, femBranches, femSlots, logFile, writeLog=False, printTerm=False, printDF=False):
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

    if (printDF): display(df)

    firstFrameNums = df.apply(lambda fem: fem[fem.first_valid_index()]).values
    lastFrameNums = df.apply(lambda fem: fem[fem.last_valid_index()]).values
    if writeLog:
        print(f"FEM slots: {", ".join(str(int(num)) for num in femSlots)}", file=logFile)
        nums = ", ".join(str(int(num)) for num in firstFrameNums)
        print(f"First frame number from FEMs: {nums}", file=logFile)
        nums = ", ".join(str(int(num)) for num in lastFrameNums)
        print(f"Last frame number from FEMs: {nums}", file=logFile)
    elif printTerm:
        print(f"FEM slots: {", ".join(str(int(num)) for num in femSlots)}")
        nums = ", ".join(str(int(num)) for num in firstFrameNums)
        print(f"First frame number from FEMs: {nums}")
        nums = ", ".join(str(int(num)) for num in lastFrameNums)
        print(f"Last frame number from FEMs: {nums}")

    frameNumDiffAllowed = set(range(1, 6))
    frameNumRolloverThres = 16777215 # 0xFFFFFF
    
    for branch, slot in zip(femBranches, femSlots):
        numBranch = branch + '/frameNum_'
        diffBranch = branch + '/frameNumDiff_'
        rolloverBranch = branch + '/frameNumRollover_'

        dfSlot = pd.DataFrame()
        dfSlot[numBranch] = df[numBranch].dropna()
        dfSlot[diffBranch] = dfSlot[numBranch].diff()
        dfSlot.dropna(inplace=True)
        
        frameNumDiffErr = ~dfSlot[diffBranch].isin(frameNumDiffAllowed)
        frameNumDiffErrCnt = frameNumDiffErr.sum()
        
        if frameNumDiffErrCnt > 0:
            diffs = dfSlot.loc[frameNumDiffErr, diffBranch].to_numpy()
            diffs = ", ".join(str(int(diff)) for diff in diffs)
            nums = dfSlot.loc[frameNumDiffErr, numBranch].to_numpy()
            nums = ", ".join(str(int(num)) for num in nums)

            if writeLog:
                print(f"Number of frame number differences not in {frameNumDiffAllowed} for FEM {slot}: {frameNumDiffErrCnt}", file=logFile)
                print(f"Frame numbers with jump not in {frameNumDiffAllowed} for FEM {slot}: {nums}", file=logFile)
                print(f"Frame number differences for FEM {slot}: {diffs}", file=logFile)
            elif printTerm:
                print(f"Number of frame number differences not in {frameNumDiffAllowed} for FEM {slot}: {frameNumDiffErrCnt}")
                print(f"Frame numbers with jump not in {frameNumDiffAllowed} for FEM {slot}: {nums}")
                print(f"Frame number differences for FEM {slot}: {diffs}")

        frameNumRollover = dfSlot[diffBranch] < 0
        frameNumRolloverCnt = frameNumRollover.sum()
        
        if frameNumRolloverCnt > 0:
            rollovers = dfSlot.loc[frameNumRollover, diffBranch].to_numpy()
            rollovers += frameNumRolloverThres
            rollovers = ", ".join(str(int(num)) for num in rollovers)
            nums = dfSlot.loc[frameNumRollover, numBranch].to_numpy()
            nums = ", ".join(str(int(num)) for num in nums)

            if writeLog:
                print(f"Number of frame number rollovers for FEM {slot}: {frameNumRolloverCnt}", file=logFile)
                print(f"Frame numbers with rollover for FEM {slot}: {nums}", file=logFile)
                print(f"Frame number rollovers for FEM {slot}: {rollovers}", file=logFile)
            elif printTerm:
                print(f"Number of frame number rollovers for FEM {slot}: {frameNumRolloverCnt}")
                print(f"Frame numbers with rollover for FEM {slot}: {nums}")
                print(f"Frame number rollovers for FEM {slot}: {rollovers}")


def logADCWordCntErr(tree, dataType, femBranches, femSlots, logFile, writeLog=False, printTerm=False):
    if dataType == 'NU': numType = 'eventNum_'
    elif dataType == 'SN': numType = 'frameNum_'

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
        trueCnts = tree[adcCntTrueBranch].array(library='np').astype(np.int64)
        recoCnts = tree[adcCntRecoBranch].array(library='np').astype(np.int64)
        diffs = recoCnts - trueCnts

        nums = nums[diffs != 0]
        diffs = diffs[diffs != 0]
        nDiffErr = len(nums)
        if nDiffErr > 0:
            nums = ", ".join(str(int(num)) for num in nums)
            diffs = ", ".join(str(int(diff)) for diff in diffs)
            if writeLog:
                print(f"Number of ADC word count mismatches for FEM {slot}: {nDiffErr}", file=logFile)
                if dataType == 'NU':
                    print(f"Event numbers with ADC word count mismatch for FEM {slot}: {nums}", file=logFile)
                elif dataType == 'SN':
                    print(f"Frame numbers with ADC word count mismatch for FEM {slot}: {nums}", file=logFile)
                print(f"ADC word count differences for FEM {slot}: {diffs}", file=logFile)
            elif printTerm:
                print(f"Number of ADC word count mismatches for FEM {slot}: {nDiffErr}")
                if dataType == 'NU':
                    print(f"Event numbers with ADC word count mismatch for FEM {slot}: {nums}")
                elif dataType == 'SN':
                    print(f"Frame numbers with ADC word count mismatch for FEM {slot}: {nums}")
                print(f"ADC word count differences for FEM {slot}: {diffs}")


def logChannelMissNU(tree, femBranches, femSlots, logFile, writeLog=False, printTerm=False):
    allChNums = set([ch for ch in range(64)])

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

            chNums = list(allChNums - set(startNums))
            if len(chNums) > 0:
                chNums = ", ".join(str(int(num)) for num in chNums)
                if writeLog:
                    print(f"Event number {num}: Channel start miss for channels {chNums} in FEM {slot}", file=logFile)
                elif printTerm:
                    print(f"Event number {num}: Channel start miss for channels {chNums} in FEM {slot}")

            chNums = startNums[endMisses]
            if len(chNums) > 0:
                chNums = ", ".join(str(int(num)) for num in chNums)
                if writeLog:
                    print(f"Event number {num}: Channel end miss for channels {chNums} in FEM {slot}", file=logFile)
                elif printTerm:
                    print(f"Event number {num}: Channel end miss for channels {chNums} in FEM {slot}")


def logChannelStartMissSN(tree, femBranches, femSlots, logFile, writeLog=False, printTerm=False):
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

            chMisses = list(allChNums - set(channels))
            if len(chMisses) > 0:
                chMisses = ", ".join(str(int(num)) for num in chMisses)
                if writeLog:
                    print(f"Frame number {num}: Channel start miss for channels {chMisses} in FEM {slot}", file=logFile)
                elif printTerm:
                    print(f"Frame number {num}: Channel start miss for channels {chMisses} in FEM {slot}")


def logROIMissCntSN(tree, femBranches, femSlots, logFile, writeLog=False, printTerm=False):
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

            for ch, startMissCnt, endMissCnt in zip(channels, startMissCnts, endMissCnts):
                if startMissCnt > 0:
                    if writeLog:
                        print(f"Frame number {num}: {startMissCnt} ROI start miss for channel {ch} in FEM {slot}", file=logFile)
                    elif printTerm:
                        print(f"Frame number {num}: {startMissCnt} ROI start miss for channel {ch} in FEM {slot}")

                if endMissCnt > 0:
                    if writeLog:
                        print(f"Frame number {num}: {endMissCnt} ROI end miss for channel {ch} in FEM {slot}", file=logFile)
                    elif printTerm:
                        print(f"Frame number {num}: {endMissCnt} ROI end miss for channel {ch} in FEM {slot}")
