import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from helpers import find_coords, find_ranges, getrangestr, loadchmap

# function that plots the projection of wires given a WIB crate and list of WIBs
def plotWIBprojection(WIB_crate, WIB_list):
    df = loadchmap('channel_mapping.txt')

    # filter DataFrame based on LArSOFT channels
    filtered_df = df.loc[(df['WIB Crate #']==WIB_crate) & (df['WIB #'].isin(WIB_list))] 
    
    # format figure
    fig, axs = plt.subplots(2,figsize=(8,10))
    for ax in fig.get_axes():
        ax.set_ylim(0, 3991+1)
        ax.set_xlim(0, 2496*2+1)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines['bottom'].set_color('0.5')
        ax.spines['top'].set_color('0.5')
        ax.spines['right'].set_color('0.5')
        ax.spines['left'].set_color('0.5')
        
    # loop over apas
    for a, apa in [(0,'East'), (1,'West')]:
        
        #loop over planes
        for i, plane, color, nwires in [(2,'Y', 'r', 1664),(0,'U','b', 1984), (1,'V', 'g', 1984)]:

            df_plane = filtered_df.loc[(filtered_df['Wire plane']==plane) & (filtered_df['APA']==apa)] 
            wires = np.array(df_plane['Wire number'])

            # make background grid
            gridwires = np.arange(0, nwires, 64)
            for k in range(len(gridwires)):
                gridpoints = find_coords(plane, gridwires[k])
                axs[a].plot(*zip(*gridpoints), alpha=0.1, linestyle = '-', color='grey')

            # loop over wires in WIB
            for j in range(len(wires)):   
                plane_coords = find_coords(plane, wires[j])    # find coords
                axs[a].plot(*zip(*plane_coords), alpha=0.2, color=color)  # plot lines with specified coords

            # add a legend with # of wires on each plane and ranges
            if len(wires) > 0:
                wire_ranges = find_ranges(wires)
                no_wires = str(len(wires))
            else:
                wire_ranges = []
                no_wires = '0'

            x = 2496*2+100
            y = 3991 - 100 - 1500*i
            axs[a].text(x,y, no_wires+' '+plane+' wires', color = color)

            for l in range(len(wire_ranges)):
                wire_range = 'ch '+str(wire_ranges[l][0])+'-'+str(wire_ranges[l][1])
                y2 = y-(l+1)*200
                axs[a].text(x,y2, wire_range)
        
        axs[a].set_title(apa+' APA', weight='bold')
    
    wib_str = getrangestr(WIB_list)
    fig.suptitle('WIB Crate #'+str(WIB_crate)+' WIB #'+wib_str, weight='bold')
    plt.tight_layout()
    
    plt.show()

# function that plots the projection of wires given a list of LArSOFT chanels
def plotoffchprojection(offlinech_file):
    df = loadchmap('channel_mapping.txt')
    with open(offlinech_file, 'r') as file:
        offlinech = [int(line.strip()) for line in file.readlines()]
    # filter DataFrame based on LArSOFT channels
    filtered_df = df[df["LArSoft ch #"].isin(offlinech)]
    
    if len(offlinech) > 1200:
        print("WARNING: There may be too many input channels for this to be a meaningful visual!")
    
    # format figure
    fig, axs = plt.subplots(2,figsize=(8,10))
    for ax in fig.get_axes():
        ax.set_ylim(0, 3991+1)
        ax.set_xlim(0, 2496*2+1)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines['bottom'].set_color('0.5')
        ax.spines['top'].set_color('0.5')
        ax.spines['right'].set_color('0.5')
        ax.spines['left'].set_color('0.5')
        
    # loop over apas
    for a, apa in [(0,'East'), (1,'West')]:
        
        #loop over planes
        for i, plane, color, nwires in [(2,'Y', 'r', 1664),(0,'U','b', 1984), (1,'V', 'g', 1984)]:

            df_plane = filtered_df.loc[(filtered_df['Wire plane']==plane) & (filtered_df['APA']==apa)] 
            wires = np.array(df_plane['Wire number'])

            # make backgrounds grid
            gridwires = np.arange(0, nwires, 64)
            for k in range(len(gridwires)):
                gridpoints = find_coords(plane, gridwires[k])
                axs[a].plot(*zip(*gridpoints), alpha=0.1, linestyle = '-', color='grey')

            # loop over wires in WIB
            for j in range(len(wires)):   
                plane_coords = find_coords(plane, wires[j])    # find coords
                axs[a].plot(*zip(*plane_coords), alpha=0.1, color=color)  # plot lines with specified coords

            # add a legend with # of wires on each plane and ranges
            if len(wires) > 0:
                wire_ranges = find_ranges(wires)
                no_wires = str(len(wires))
            else:
                wire_ranges = []
                no_wires = '0'

            x = 2496*2+100
            y = 3991 - 100 - 1500*i
            axs[a].text(x,y, no_wires+' '+plane+' wires', color = color)

            for l in range(len(wire_ranges)):
                wire_range = 'ch '+str(wire_ranges[l][0])+'-'+str(wire_ranges[l][1])
                y2 = y-(l+1)*200
                axs[a].text(x,y2, wire_range)
            
        axs[a].set_title(apa+' APA', weight='bold')
    plt.tight_layout()

    plt.show()

# function that plots the projection of wires given specific FEM crates
def plotFEMprojection(FEM_crate, FEM_list):
    df = loadchmap('channel_mapping.txt')
    # select portion of data frame that corresponds to WIB
    filtered_df = df.loc[(df['Crate #']==FEM_crate) & (df['FEM #'].isin(FEM_list))]
    
    # format figure
    fig, axs = plt.subplots(2,figsize=(8,10))
    for ax in fig.get_axes():
        ax.set_ylim(0, 3991+1)
        ax.set_xlim(0, 2496*2+1)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines['bottom'].set_color('0.5')
        ax.spines['top'].set_color('0.5')
        ax.spines['right'].set_color('0.5')
        ax.spines['left'].set_color('0.5')
        
    # loop over apas
    for a, apa in [(0,'East'), (1,'West')]:
        
        #loop over planes
        for i, plane, color, nwires in [(2,'Y', 'r', 1664),(0,'U','b', 1984), (1,'V', 'g', 1984)]:

            df_plane = filtered_df.loc[(filtered_df['Wire plane']==plane) & (filtered_df['APA']==apa)] 
            wires = np.array(df_plane['Wire number'])

            # make backgrounds grid
            gridwires = np.arange(0, nwires, 64)
            for k in range(len(gridwires)):
                gridpoints = find_coords(plane, gridwires[k])
                axs[a].plot(*zip(*gridpoints), alpha=0.1, linestyle = '-', color='grey')

            # loop over wires in WIB
            for j in range(len(wires)):   
                plane_coords = find_coords(plane, wires[j])    # find coords
                axs[a].plot(*zip(*plane_coords), alpha=0.2, color=color)  # plot lines with specified coords

            # add a legend with # of wires on each plane and ranges
            if len(wires) > 0:
                wire_ranges = find_ranges(wires)
                no_wires = str(len(wires))
            else:
                wire_ranges = []
                no_wires = '0'

            x = 2496*2+100
            y = 3991 - 100 - 1500*i
            axs[a].text(x,y, no_wires+' '+plane+' wires', color = color)

            for l in range(len(wire_ranges)):
                wire_range = 'ch '+str(wire_ranges[l][0])+'-'+str(wire_ranges[l][1])
                y2 = y-(l+1)*200
                axs[a].text(x,y2, wire_range)
        
        axs[a].set_title(apa+' APA', weight='bold')
    
    fem_str = getrangestr(FEM_list)
    fig.suptitle('TPC Crate #'+str(FEM_crate)+' FEM #'+fem_str, weight='bold')
    plt.tight_layout()
    
    plt.show()

# function that plots the projection of wires given a WIB crate, WIB and list of FEMBs
def plotFEMBprojection(WIB_crate, WIB, femb_list):
    df = loadchmap('channel_mapping.txt')

    filtered_df = df.loc[(df['WIB Crate #']==WIB_crate) & (df['WIB #']==WIB) & (df['FEMB #'].isin(femb_list))] 
    
    # format figure
    fig, axs = plt.subplots(2,figsize=(8,10))
    for ax in fig.get_axes():
        ax.set_ylim(0, 3991+1)
        ax.set_xlim(0, 2496*2+1)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines['bottom'].set_color('0.5')
        ax.spines['top'].set_color('0.5')
        ax.spines['right'].set_color('0.5')
        ax.spines['left'].set_color('0.5')
        
    # loop over apas
    for a, apa in [(0,'East'), (1,'West')]:
        
        #loop over planes
        for i, plane, color, nwires in [(2,'Y', 'r', 1664),(0,'U','b', 1984), (1,'V', 'g', 1984)]:

            df_plane = filtered_df.loc[(filtered_df['Wire plane']==plane) & (filtered_df['APA']==apa)] 
            wires = np.array(df_plane['Wire number'])

            # make backgrounds grid
            gridwires = np.arange(0, nwires, 64)
            for k in range(len(gridwires)):
                gridpoints = find_coords(plane, gridwires[k])
                axs[a].plot(*zip(*gridpoints), alpha=0.1, linestyle = '-', color='grey')

            # loop over wires in WIB
            for j in range(len(wires)):   
                plane_coords = find_coords(plane, wires[j])    # find coords
                axs[a].plot(*zip(*plane_coords), alpha=0.2, color=color)  # plot lines with specified coords

            # add a legend with # of wires on each plane and ranges
            if len(wires) > 0:
                wire_ranges = find_ranges(wires)
                no_wires = str(len(wires))
            else:
                wire_ranges = []
                no_wires = '0'

            x = 2496*2+100
            y = 3991 - 100 - 1500*i
            axs[a].text(x,y, no_wires+' '+plane+' wires', color = color)

            for l in range(len(wire_ranges)):
                wire_range = 'ch '+str(wire_ranges[l][0])+'-'+str(wire_ranges[l][1])
                y2 = y-(l+1)*200
                axs[a].text(x,y2, wire_range)
        
        axs[a].set_title(apa+' APA', weight='bold')
    
    femb_str = getrangestr(femb_list)
    fig.suptitle('WIB Crate #'+str(WIB_crate)+' WIB #'+str(WIB)+' FEMB #'+femb_str, weight='bold')
    plt.tight_layout()
    
    plt.show()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot out wire-plane project given WIBs, FEMs, or LArSOFT Ch #s")

    parser.add_argument("input", choices=["FEMB", "WIB", "FEM", "LArSOFT"], help="Specify what info you have (FEMB, WIB, FEM or LArSOFT)")
    parser.add_argument("--wibcrate", nargs="?", type=int, help="WIB Crate # (if input=FEMB/WIB)")
    parser.add_argument("--fembs", nargs="*", type=int, help="FEMB # (if input=FEMB)")
    parser.add_argument("--wib", nargs="?", type=int, help="WIB # (if input=FEMB)")
    parser.add_argument("--wibs", nargs="*", type=int, help="WIB # (if input=WIB)")
    parser.add_argument("--tpccrate", nargs="?", type=int, help="TPC Crate # (if input=FEM)")
    parser.add_argument("--fems", nargs="*", type=int, help="FEM # (if input=FEM)")
    parser.add_argument("--offlinech", nargs="?", type=str, help="Text file with offline ch #s (if input=LArSOFT)")
    

    args = parser.parse_args()

    if args.input == "FEMB":
        if args.wibcrate is None or args.wib is None or args.fembs is None:
            raise ValueError("Invalid operation. Specify WIB Crate #, WIB # and FEMB # for FEMB input.")
        result = plotFEMBprojection(args.wibcrate, args.wib, args.fembs)
    elif args.input == "WIB":
        if args.wibcrate is None or args.wibs is None:
            raise ValueError("Invalid operation. Specify WIB Crate # and WIB #s for WIB input.")
        result = plotWIBprojection(args.wibcrate, args.wibs)
    elif args.input == "FEM":
        if args.tpccrate is None or args.fems is None:
            raise ValueError("Invalid operation. Specify TPC Crate # and FEM # for FEM input.")
        result = plotFEMprojection(args.tpccrate, args.fems)
    elif args.input == "LArSOFT":
        if args.offlinech is None:
            raise ValueError("Invalid operation. Specify the path to the offline ch file for LArSOFT input.")
        result = plotoffchprojection(args.offlinech)
    else:
        raise ValueError("Invalid operation. Choose 'FEMB', 'WIB', 'FEM', or 'LArSOFT'")

