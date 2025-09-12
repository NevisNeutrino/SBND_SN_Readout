# Binary File Decoder

Decodes binary files from SBND DAQ (SN/NU).

## `nupur_decoder`
### Build
- Requirements: g++ (GNU++11), Boost.Filesystem, Boost.System
- Compile:
    ```
    g++ -std=gnu++11 -lboost_filesystem -lboost_system -o <EXECUTABLE> <SOURCECODE>
    ```

### Usage
- Run:
    ```
    ./<EXECUTALBE> <input-file>
    ```

## `eric_decoder`
### Build
- Requirements: uproot, awkward
- Compile:
    ```
    mkdir build && cd build
    cmake ..
    make
    ```

### Usage
- Run:
    ```
    ./app/decodeSN -i <input_file> -o <output_directory>
    python plotDataCheckSN.py --file <input_root_file> --save
    ```


## `process3`
### Build
- Requirements: g++ (GNU++11), Boost.Filesystem, Boost.System
- Compile:
    ```
    g++ -std=gnu++11 -lboost_filesystem -lboost_system -o <EXECUTABLE> <SOURCECODE>
    ```

### Usage
- Run:
    ```
    ./<EXECUTALBE> <input-file> <run_number> <tpc_number>
    ```
