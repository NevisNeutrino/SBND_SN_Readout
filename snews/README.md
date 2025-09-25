# SNEWS Alert

Software package for SNEWS alert implementation in SBND using ZeroMQ

## Requirements
- Python > 3.9
- pyzmq library

## Usage

### Server & Publisher:
- Run on sbnd-tpc13.fnal.gov (SN processing server)
- Host ZeroMQ server listening alerts coming from port 7910 and publishes timestamps to port 7901
- Save SNEWS alert .txt file in ```sbnd-tpc13.fnal.gov:/data/SNEWSAlert```
- Make new directory corresponding to SNEWS alert timestamp and sub-directories corresponding to TPC servers
```
python sbndSNEWSServer.py --log <log_file>
Type 'exit' to stop
```

### Client:
Run on BNL server and send alerts to ZeroMQ server at SBND
- TEST mode:
	```
	python sbndSNEWSClient.py --host <destination_host> --port <destination_port> --test
	```
- SNEW ALERT mode:
	```
	python sbndSNEWSClient.py --host <destination_host> --port <destination_port> --file <alert_txt_file>
	```

### Subscriber:
- Run on each TPC server
- Subscribe to ZeroMQ server at port 7901 for timestamps
- Transfer SN binary files around received SNEWS alert timestamp (10min before and 50min after) to ```sbnd-tpc13.fnal.gov:/data/SNEWSAlert/<timestamp>/<tpc_server>```
```
python saveSNEWSAlertBinFiles.py --log <log_file> --direc <sn_files_directory>
Type 'exit' to stop
```

### Notifier:
- Run on sbnd-tpc13.fnal.gov (SN processing server)
- Send email notification to slack channel when either TEST or SNEWS alert is received
```
python sbndSNEWSEmail.py --log <log_file> --test(send email notification to #sbnd_test_channel if set, otherwise to #sbnd-shift-operations) 
Type 'exit' to stop
```

## Specific to SBND servers
- Location: `/home/nfs/sbnd/SBND_SN_Readout/snews`
- Python venv: `/home/nfs/sbnd/snews_env`
`source bin/activate`
