# Binary File Decoder and Data Quality Metric Plotter

- Decode SBND DAQ NU or SN binary file to a ROOT file
- Plot data quality metrics from decoded ROOT file
- Log data quality issues from decoded ROOT file

## Requirements

### Decoder
- CMake > 3
- ROOT > 6

### Plotter and Logger
- Python 3.13.5
- Libraries: numpy, pandas, matplotlib, uproot, awkward

## Structure
- ```lib/utils```: C++ general methods for decoder
- ```lib/nu```: C++ classes for NU data
- ```lib/sn```: C++ classes for SN data
- ```app```: C++ source codes for decoder
- ```python```: Python source codes for plotter and logger

## Build

### Decoder
```
mkdir build && cd build
cmake ..
make
```

## Usage

### Decoder
- NU:
	```
	cd build
	./app/decodeNU -i <input_binary_file> -o <output_directory> -d(debug mode: gives full printouts)
	```
- SN:
	```
	cd build
	./app/decodeSN -i <input_binary_file> -o <output_directory> -d(debug mode: gives full printouts)
	```

### Plotter
- NU:
	```
	cd python
	python plotDataCheckNU.py --file <input_root_file> --save/show(either save plots to a PDF file or just show the plots)
	```
- SN:
	```
	cd python
	python plotDataCheckSN.py --file <input_root_file> --save/show(either save plots to a PDF file or just show the plots)
	```

### Logger
- NU:
	```
	cd python
	python logDataCheckNU.py --file <input_root_file> --write/print(either writes data quality issues to log file or just print to terminal)
	```
- SN:
	```
	cd python
	python logDataCheckSN.py --file <input_root_file> --write/print(either writes data quality issues to log file or just print to terminal)
	```
