# SBND Channel Mapping Tool

```channel_mapping.xlsx``` contains a complete map of wires to front-end hardware

## **Plotting Wire Plane Views** 

```plotprojections.py``` contains functions to plot different wire plane views of warm electronics hardware groupings

**To plot wires corresponding to a set of FEMBs in a WIB: ```python plotprojections.py FEMB --wibcrate <WIB_CRATE_NUMBER> --wib <WIB_NUMBER> --fembs <FEMB_NUMBER_1> <FEMB_NUMBER_2>...```**

Inputs:

```--wibcrate```: Specify the WIB crate number (between 1-4). (e.g., --wibcrate 3)

```--wib```: Specify the WIB number (between 1-6). (e.g., --wib 2)

```--fembs```: Specify the WIB numbers separated by spaces (between 0-3). (e.g., --fembs 0 1)

**To plot wires corresponding to a set of WIBs in a WIB crate: ```python plotprojections.py WIB --wibcrate <WIB_CRATE_NUMBER> --wibs <WIB_NUMBER_1> <WIB_NUMBER_2>...```**

Inputs:

```--wibcrate```: Specify the WIB crate number (between 1-4). (e.g., --wibcrate 3)

```--wibs```: Specify the WIB numbers separated by spaces (between 1-6). (e.g., --wibs 2 4 5)

**To plot wires corresponding to a set of FEMs in a TPC crate: ```python plotprojections.py FEM --tpccrate <TPC_CRATE_NUMBER> --fems <FEM_NUMBER_1> <FEM_NUMBER_2>...```**

Inputs:

```--tpccrate```: Specify the TPC crate number (between 1-11). (e.g., --tpccrate 10)

```--fems```: Specify the FEM numbers separated by spaces (between 1-16). (e.g., --fems 10 11 12)

**To plot wires corresponding to a list of LArSOFT Channels: ```python plotprojections.py LArSOFT --offlinech <LArSOFTch.txt> $```**

Inputs:

```--offlinech```: Provide a ```.txt``` file with a set of offline channels (between 1-11264). (e.g., samplech.txt)

## **Printing Upstream Info**

```printinfo.py``` contains functions to return the upstream info corresponding to TPC hardware and offline channels

**To print TPC wires, FEMB & WIB info corresponding to a set of FEMs in a TPC crate: ```python printinfo.py FEM --tpccrate <TPC_CRATE_NUMBER> --fems <FEM_NUMBER_1> <FEM_NUMBER_2>...```**

Inputs:

```--tpccrate```: Specify the TPC crate number (between 1-11). (e.g., --tpccrate 10)

```--fems```: Specify the FEM numbers separated by spaces (between 1-16). (e.g., --fems 10 11 12)

**To print TPC wires, FEMB, WIB & FEM info corresponding to a list of LArSOFT Channels: ```python printinfo.py LArSOFT --offlinech <LArSOFTch.txt> $```**

Inputs:

```--offlinech```: Provide a ```.txt``` file with a set of offline channels (between 1-11264). (e.g., samplech.txt)

## **Process offline ROOT file output from online monitor**

**To generate a text file with metric info per event from the output of the SBNDQM Analysis module: ```python processroot.py --filepath <INPUT_ROOT_FILE> --metric <METRIC_NAME>```**

Inputs:

```--filepath```: Specify the root file to process (output of Analysis.cc in sbndqm). (e.g., --filepath sampledecoded.root)

```--metric```: Specify the metric to save. (e.g., --metric rms)

## **Plotting Channel Metrics**

**To plot a channel metric vs. LArSOFT ch. split by plane & APA: ```python plotmetric.py LArSOFT --filepath <INPUT_TXT_FILE>  --metric <METRIC_NAME>``` --eventno <EVENT_NO>**

Inputs:

```--filepath```: Specify the .txt file with channel metric info (output of ```process.root.py```). (e.g., --filepath sampledecoded_rms.txt)

```--metric```: Specify the metric to plot. (e.g., --metric rms)

Optional: ```--eventno```: Specify the event to plot (If not specified, first event (column) in .txt file is plotted). (e.g., 1)

**To plot a channel metric in wire-plane view: ```python plotmetric.py TPCwires --filepath <INPUT_TXT_FILE>  --metric <METRIC_NAME> --eventno <EVENT_NO>```**

Inputs:

```--filepath```: Specify the .txt file with channel metric info (output of ```process.root.py```). (e.g., --filepath sampledecoded_rms.txt)

```--metric```: Specify the metric to plot. (e.g., --metric rms)

Optional: ```--eventno```: Specify the event to plot (If not specified, first event (column) in .txt file is plotted). (e.g., 1)

**To plot a channel metric in mezzanine (FEM crate) view: ```python plotmetric.py FEM --filepath <INPUT_TXT_FILE> --metric <METRIC_NAME> --eventno <EVENT_NO>```**

Inputs:

```--filepath```: Specify the .txt file with channel metric info (output of ```process.root.py```). (e.g., --filepath sampledecoded_rms.txt)

```--metric```: Specify the metric to plot. (e.g., --metric rms)

Optional: ```--eventno```: Specify the event to plot (If not specified, first event (column) in .txt file is plotted). (e.g., 1)
