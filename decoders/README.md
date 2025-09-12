# Binary File Decoder

Decodes a serial number from an input file and prints the result.

## Build
- Requirements: g++ (GNU++11), Boost.Filesystem, Boost.System
- Compile:
    ```
    g++ -std=gnu++11 -lboost_filesystem -lboost_system -o binsn decodeSN.cpp
    ```

## Usage
- Run:
    ```
    ./binsn <input-file>
    ```
- Outputs the decoded serial number to stdout.
