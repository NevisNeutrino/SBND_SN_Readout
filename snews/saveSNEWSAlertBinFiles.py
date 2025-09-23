import os
import sys
import time
import subprocess
import argparse
import socket
import zmq
import threading
import re
import glob
import shutil
from datetime import datetime, timedelta

def parseArguments():
    def checkFile(file):
        if not file.endswith(".log"):
            raise argparse.ArgumentTypeError(f"File to send must be a .log file")
        elif not os.access(file, os.R_OK):
            raise argparse.ArgumentTypeError(f"{file} can't be opened")
        return file

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--log", type=checkFile, required=True, help="log file")
    parser.add_argument("--direc", type=str, required=True, help="binary files directory")

    args = parser.parse_args()
    return args

def checkConnection(host, port):
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except:
        return False

def listenForExit(stopServer):
    while True:
        cmd = input()
        if cmd.strip().lower() == "exit":
            stopServer.set()
            break

def fileTransfer(file, host, path):
    hostname = subprocess.check_output(['hostname'], text=True).strip()
    match = re.search(r'tpc(\d+)', hostname)
    if match:
        tpc = match.group(1)
        path = path + "/TPC" + tpc
        command = ['rsync', '-z', '--ignore-existing', file, f"{host}:{path}"]
        status = subprocess.run(command, capture_output=True, text=True)
        return status
    else:
        raise ValueError("Could not extract TPC server number from hostname")

if __name__ == "__main__":
    args = parseArguments()
    logfile = open(args.log, 'a', buffering=1)

    context = zmq.Context()
    zmqSubSocket = context.socket(zmq.SUB)

    host = 'sbnd-tpc13-daq'
    port = 7901
    if checkConnection(host, port):
        zmqSubSocket.connect(f"tcp://{host}:{port}")
        time.sleep(1)
    else:
        print(f"Can't connect to {host} on port {port}")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Can't connect to {host} on port {port}", file=logfile)
        sys.exit(1)

    zmqSubSocket.setsockopt_string(zmq.SUBSCRIBE, "")
    time.sleep(1)

    stopServer = threading.Event()
    threading.Thread(target=listenForExit, args=(stopServer,), daemon=True).start()

    print(f"Subscribed to SNEWS alert timestamps from {host} on port {port}. Type 'exit' to stop.")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Subscribed to SNEWS alert timestamps from {host} on port {port}. Type 'exit' to stop.", file=logfile)

    while not stopServer.is_set():
        try:
            message = zmqSubSocket.recv_string(flags=zmq.NOBLOCK)
            message = message.split()

            alertTimestamp = datetime.strptime(message[-1], "%Y.%m.%d.%H.%M.%S")
            print(f"{message[0]} alert received with timestamp: {alertTimestamp}")
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message[0]} alert received with timestamp: {alertTimestamp}", file=logfile)

            if message[0] == "SNEWS":
                startTimestamp = alertTimestamp - timedelta(minutes=10)
                endTimestamp = alertTimestamp + timedelta(minutes=50)
                print(f"Saving files in time window: {startTimestamp} -> {endTimestamp}")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Saving files in time window: {startTimestamp} -> {endTimestamp}", file=logfile)

                for filename in os.listdir(args.direc):
                    if ((filename.endswith('SN.dat')) and (os.path.isfile(os.path.join(args.direc, filename)))):
                        filepath = os.path.join(args.direc, filename)
                        filetime = datetime.utcfromtimestamp(os.path.getmtime(filepath))
                        if startTimestamp <= filetime <= endTimestamp:
                            print(f"Transferring {filepath} to {host.replace('-daq', '.fnal.gov')} ...")
                            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Transferring {filepath} to {host.replace('-daq', '.fnal.gov')} ...", file=logfile)
                            try:
                                status = fileTransfer(filepath, host, f"/data/SNEWSAlert/{message[-1]}")
                                if status.returncode == 0:
                                    print("File transfer completed successfully")
                                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: File transfer completed successfully", file=logfile)
                                else:
                                    print("File transfer failed")
                                    print("Error output:\n", status.stderr)
                                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: File transfer failed", file=logfile)
                                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error output:\n", status.stderr, file=logfile)
                            except ValueError as err:
                                print("File transfer failed")
                                print("Error output:\n", err)
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: File transfer failed", file=logfile)
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error output:\n", err, file=logfile)
        except zmq.Again:
            pass

    logfile.close()
