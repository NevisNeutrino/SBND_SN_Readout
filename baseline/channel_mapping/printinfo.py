import numpy as np
import pandas as pd
from helpers import find_ranges, getrangestr, loadchmap

# function to print wire & WIB/FEMB info given crate number and list of FEMs
def print_fem_info(crate_number, fem_list):
    df = loadchmap('channel_mapping.txt')

    # filter DataFrame based on FEM crate number and FEM list
    filtered_df = df.loc[(df['Crate #'] == crate_number) & (df['FEM #'].isin(fem_list))]

    # print wire information
    print('----------------------------------------------------------------')
    print("WIRE INFO:\n")
    for apa, plane in [('East', 'U'), ('East', 'V'), ('East', 'Y'),
                       ('West', 'U'), ('West', 'V'), ('West', 'Y')]:

        # filter DataFrame for each APA and wire plane
        df_plane = filtered_df.loc[(filtered_df['Wire plane'] == plane) & (filtered_df['APA'] == apa)]
        wires = np.array(df_plane['Wire number'])

        if len(wires) > 0:
            wire_ranges_str = getrangestr(wires)
            no_wires = str(len(wires))

            # print information about wires
            print(f"{no_wires} {apa} APA {plane} wires")
            print(f"  {wire_ranges_str}")

    print('----------------------------------------------------------------')
    print('WIB/FEMB INFO:\n')

    # extract relevant columns for WIB/FEMB information
    CE_combo = filtered_df[['WIB Crate #', 'APA', 'Half', 'WIB #', 'FEMB #', 'FEMB Position',
                            'WIB QFSP', 'QFSP Fiber #', 'ASIC #']].drop_duplicates()
    crates = CE_combo['WIB Crate #'].unique()

    # iterate over unique crates
    for crate in np.sort(crates):
        # map crate numbers to APA labels
        apa = {1: 'SW', 2: 'SE', 3: 'NW', 4: 'NE'}.get(crate, '')
        wibdf = CE_combo.loc[CE_combo['WIB Crate #'] == crate]
        wibs = np.sort(wibdf['WIB #'].unique())

        # iterate over unique WIBs
        for wib in wibs:
            fembdf = wibdf.loc[CE_combo['WIB #'] == wib]
            fembs = fembdf['FEMB #'].unique()
            femb_ranges = find_ranges(fembs)

            # create a list of FEMB ranges
            femb_list = [f'-'.join(map(str, femb_range)) for femb_range in femb_ranges]

            print(f"WIB Crate #{crate} ({apa}),", f"WIB #{wib},", f"FEMB #{','.join(femb_list)}")

        # extract FEMB Positions for the current crate
        pos = wibdf['FEMB Position'].unique()
        print('FEMB Positions:', ', '.join(map(str, pos)))

        # print extra info if only 1 FEM is specified
        if len(fem_list) == 1:

            port = wibdf['WIB QFSP'].unique()[0]
            fiber = wibdf['QFSP Fiber #'].unique()
            fiber_str = getrangestr(fiber)
            asic = wibdf['ASIC #'].unique()
            asic_str = getrangestr(asic)

            # print FEMB ASICs, WIB Port, Fiber information
            print(f"FEMB ASICs {asic_str}, WIB Port {port}, Fiber #{fiber_str}")
    print('----------------------------------------------------------------')

# function to print wire, WIB/FEMB & FEM info given a list LArSOFT channels          
def print_ch_info(offlinech_file):
    df = loadchmap('channel_mapping.txt')
    with open(offlinech_file, 'r') as file:
        offlinech = [int(line.strip()) for line in file.readlines()]
    # filter DataFrame based on LArSOFT channels
    filtered_df = df[df["LArSoft ch #"].isin(offlinech)]

    # print wire information
    print('----------------------------------------------------------------')
    print("WIRE INFO:\n")
    for apa, plane in [('East', 'U'), ('East', 'V'), ('East', 'Y'),
                        ('West', 'U'), ('West', 'V'), ('West', 'Y')]:
        
        # filter DataFrame for each APA and wire plane
        df_plane = filtered_df.loc[(filtered_df['Wire plane'] == plane) & (filtered_df['APA'] == apa)]
        wires = np.array(df_plane['Wire number'])
        if len(wires) > 0:
            wire_ranges_str = getrangestr(wires)
            no_wires = str(len(wires))

            print(f"{no_wires} {apa} APA {plane} wires")
            print(f"  {wire_ranges_str}")

    print('----------------------------------------------------------------')
    print('WIB/FEMB INFO:\n')
    # extract relevant columns for WIB/FEMB information
    CE_combo = filtered_df[['WIB Crate #', 'APA', 'Half', 'WIB #', 'FEMB #', 'FEMB Position',
                            'WIB QFSP', 'QFSP Fiber #', 'ASIC #']].drop_duplicates()
    crates = CE_combo['WIB Crate #'].unique()

    # iterate over unique crates
    for crate in np.sort(crates):
        # map crate numbers to APA labels
        apa = {1: 'SW', 2: 'SE', 3: 'NW', 4: 'NE'}.get(crate, '')
        wibdf = CE_combo.loc[CE_combo['WIB Crate #'] == crate]
        wibs = np.sort(wibdf['WIB #'].unique())
        
        # iterate over unique WIBs
        for wib in wibs:
            fembdf = wibdf.loc[CE_combo['WIB #'] == wib]
            fembs = fembdf['FEMB #'].unique()
            femb_ranges = find_ranges(fembs)
            
            # create a list of FEMB ranges
            femb_list = [f'-'.join(map(str, femb_range)) for femb_range in femb_ranges]

            print(f"WIB Crate #{crate} ({apa}),", f"WIB #{wib},", f"FEMB #{','.join(femb_list)}")
        
        # extract FEMB Positions for the current crate
        pos = wibdf['FEMB Position'].unique()
        
        # print extra info if only <= 64 ch are specified
        if len(offlinech) < 65:
            port = wibdf['WIB QFSP'].unique()[0]
            fiber = wibdf['QFSP Fiber #'].unique()
            fiber_str = getrangestr(fiber)
            asic = wibdf['ASIC #'].unique()
            asic_str = getrangestr(asic)

            print(f"FEMB ASICs {asic_str}, WIB Port {port}, Fiber #{fiber_str}")
        
        # print FEMB ASICs, WIB Port, Fiber information    
        print('FEMB Positions:', ', '.join(map(str, pos)))

    print('----------------------------------------------------------------')
    print('FEM INFO:\n')

    WE_combo = filtered_df[['Crate #', 'FEM #']].drop_duplicates()
    crates = np.sort(WE_combo['Crate #'].unique())
    
    # iterate over unique FEM crates
    for crate in crates:
        fems = WE_combo.loc[WE_combo['Crate #'] == crate]['FEM #'].unique()
        fem_str = getrangestr(fems)

        print(f'TPC Crate #{crate}', f'FEM #{fem_str}')
    print('----------------------------------------------------------------')

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Print out upstream electronics info given FEMs or LArSOFT Ch #s")

    parser.add_argument("input", choices=["FEM", "LArSOFT"], help="Specify what info you have (LArSOFT or FEM)")
    parser.add_argument("--tpccrate", nargs="?", type=int, help="TPC Crate # (if input=FEM)")
    parser.add_argument("--fems", nargs="*", type=int, help="FEM # (if input=FEM)")
    parser.add_argument("--offlinech", nargs="?", type=str, help="Text file with offline ch #s (if input=LArSOFT)")

    args = parser.parse_args()

    if args.input == "FEM":
        if args.tpccrate is None or args.fems is None:
            raise ValueError("Invalid operation. Specify TPC Crate # and FEM # for FEM input.")
        result = print_fem_info(args.tpccrate, args.fems)
    elif args.input == "LArSOFT":
        if args.offlinech is None:
            raise ValueError("Invalid operation. Specify the path to the offline ch file for LArSOFT input.")
        result = print_ch_info(args.offlinech)
    else:
        raise ValueError("Invalid operation. Choose 'FEM' or 'LArSOFT'.")
