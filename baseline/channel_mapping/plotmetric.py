import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from helpers import find_coords, loadchmap

def mergedf(input_path):
    metricdf = pd.read_csv(input_path, sep='\t')
    chmap = loadchmap('channel_mapping.txt')
    drop = ['Top/Side', 'FEMB Position', 'FEMB Serial #', 'FEMB #', 'ASIC #', 'WIB Crate #', 'WIB #', 'WIB ch #', 'WIB QFSP', 'QFSP Fiber #']
    chmap = chmap.drop(columns=drop)
    metricdf['LArSoft ch #'] = metricdf.index
    df = pd.merge(metricdf, chmap, on='LArSoft ch #', how='inner')
    return df

# function that plots metric values by channel (split by APA & wire plane)
def bychannel(eventno, metric, df):
    fig, axes = plt.subplots(2, 3, figsize=(28, 7), sharey=True)
    plt.subplots_adjust(wspace=0.1, hspace=0.3)
    for a, apa in enumerate(['East', 'West']):
        for b, (plane, color) in enumerate([('Y', 'r'), ('U', 'b'), ('V', 'g')]):
            # select part of dataframe corresponding to plane & APA
            filtered_df = df.loc[(df['Wire plane'] == plane) & (df['APA']==apa)]
            
            ax = axes[a,b]
            ax.plot(filtered_df['Wire number'], filtered_df['event'+eventno+'_'+metric], color=color, label = plane+' wires')
            
            ax.set_ylim([0,5])
            ax.set_xlabel('Wire no.', size = 10)
            ax.grid(alpha=0.5)
            
            if a==0:
                ax.legend(frameon=False)
            if b == 0:
                ax.set_ylabel(metric, size = 15)
            if b==1:
                ax.set_title(apa+' APA', size = 15)
        
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            
    plt.tight_layout()    
    plt.show()

# function that plots metric values in a wire-plane view
def wireplaneview(eventno, metric, df):
    fig, axes = plt.subplots(2, 3, figsize=(35, 7), sharey=True)
    plt.subplots_adjust(wspace=0.1, hspace=0.1)
    for a, apa in enumerate(['East', 'West']):
        for b, (plane, color) in enumerate([('Y', 'r'), ('U', 'b'), ('V', 'g')]):
            ax = axes[a,b]

            ax.set_ylim(0, 3991+1)
            ax.set_xlim(0, 2496*2+1)
            ax.set_yticks([])
            ax.set_xticks([])

            # make background grid
            for plane2 in ['U', 'V', 'Y']:
                gridlines = np.arange(0, len(df), 64)
                for i in range(len(gridlines)):
                    gridpoints = find_coords(plane2, gridlines[i])
                    ax.plot(*zip(*gridpoints), alpha=0.2, linestyle='--', color='grey')
            
            # select part of dataframe corresponding to plane & APA
            df_plane = df.loc[(df['Wire plane'] == plane) & (df['APA'] == apa)]

            wires = np.array(df_plane['Wire number'])
            metricvals = np.array(df_plane['event'+eventno+'_'+metric])
            metricvals[metricvals == 0] = np.nan

            # set colormap values from metric values
            cmap = plt.cm.viridis
            norm = plt.Normalize(0, 5)
            colors = cmap(norm(metricvals))

            # plot wires
            for j in range(len(wires)):
                plane_coords = find_coords(plane, wires[j])
                ax.plot(*zip(*plane_coords), color=colors[j])

            if a==1:
                ax.set_xlabel(plane + " plane", size = 15) 
            if b==1:
                ax.set_title(apa + " APA", size=15)
            
            for spine in ax.spines.values():
                spine.set_linewidth(2)       

    # add colorbar
    cbar_ax = fig.add_axes([0.92, 0.125, 0.01, 0.75])
    cbar = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm), cax=cbar_ax, orientation='vertical')
    cbar.set_label(metric, size=15)

    plt.show()

def femview(eventno, metric, df):
    # matrix of TPC crate numbers as they are layed out in the mezzanine racks
    crate_layout = [[9, 6, 3, 1], [10, 7, 4, 2], [11, 8, 5]]

    fig, axes = plt.subplots(3, 4, figsize=(28, 8))
    plt.subplots_adjust(wspace=0.1, hspace=0.4)

    custom_xticks_positions = np.arange(32, 1024, 64)
    custom_xticks_labels = np.arange(1, 17, 1)

    for i, row in enumerate(crate_layout):
        for j, crate in enumerate(row):
            ax = axes[i,j]

            # select part of dataframe corresponding to plane & APA
            df_fem = df.loc[df["Crate #"] == crate][['event'+eventno+'_'+metric, 'FEM #', 'FEM ch #']]
            df_fem['Ch'] = (df['FEM #'] - 1) * 64 + df['FEM ch #']
            channels = np.array(df_fem['Ch'])
            metricvals = np.array(df_fem['event'+eventno+'_'+metric])
            metricvals[metricvals == 0] = np.nan

            # set colormap values from metric values
            cmap = plt.cm.viridis
            norm = plt.Normalize(vmin=0, vmax=5)
            colors = cmap(norm(metricvals))

            ax.bar(channels, 1024, color=colors, width=1.0)

            for k in range(64, 1024, 64):
                ax.axvline(k, color='black', linestyle='--', linewidth=0.5)

            ax.set_xlim([0, 1024])
            ax.set_ylim([0, 1])

            ax.yaxis.set_ticks([])
            ax.tick_params(axis='both', which='major', labelsize=7)
            ax.set_xticks(custom_xticks_positions)
            ax.set_xticklabels(custom_xticks_labels)

            for spine in ax.spines.values():
                spine.set_linewidth(1)

            ax.invert_xaxis()

            ax.set_title('TPC Crate #' + str(crate), size=10)
            ax.tick_params(axis='x', which='both', bottom=False, top=False)
            if j==0:
                ax.text(1135, -0.1, 'FEM #', size=7)

        # remove last plot since it doesnt correspong to a FEM crate
        if i == 2:
            fig.delaxes(axes[2][-1])

    # add colorbar
    cbar_ax = fig.add_axes([0.92, 0.125, 0.01, 0.75])
    cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm), cax=cbar_ax, orientation='vertical')
    cbar.set_label(metric)

    plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot channel metrics in different views")

    parser.add_argument("input", choices=["LArSOFT", "TPCwires", "FEM"], help="Specify what view to plot metrics (LArSOFT, TPCwires, or FEM)")
    parser.add_argument("--filepath", type=str, help="Path to input .txt file")
    parser.add_argument("--eventno", nargs="?", type=str, help="Event #")
    parser.add_argument("--metric", type=str, help="Channel metric (eg. rms)")

    args = parser.parse_args()
    if args.filepath is None:
        raise ValueError("Invalid operation. Specify path to input root file.")
    elif args.metric== 'rms':
        df = mergedf(args.filepath)
        if args.eventno is None:
            # set to first event if no event number is provided
            args.eventno = '1'
        if args.input == "LArSOFT":
            result = bychannel(args.eventno, args.metric, df)
        elif args.input == "TPCwires":
            result = wireplaneview(args.eventno, args.metric, df)
        elif args.input == "FEM":
            result = femview(args.eventno, args.metric, df)
    elif args.metric is None:
        raise ValueError("Invalid operation. Specify metric.")
    else:
        print(f"Unsupported metric: {args.metric}. Only 'rms' is supported.")