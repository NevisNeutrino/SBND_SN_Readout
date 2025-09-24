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

def getTPCServer():
    hostname = subprocess.check_output(['hostname'], text=True).strip()
    match = re.search(r'tpc(\d+)', hostname)
    if match:
        tpc = match.group(1)
        return tpc
    else:
        raise ValueError("Could not extract TPC server number from hostname")

def transferFile(file, host, path):
    command = ['rsync', '-z', '--ignore-existing', file, f"{host}:{path}"]
    status = subprocess.run(command, capture_output=True, text=True)
    return status

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

    path = '/data/SNEWSAlert'

    print(f"Subscribed to SNEWS alert timestamps from {host} on port {port}. Type 'exit' to stop.")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Subscribed to SNEWS alert timestamps from {host} on port {port}. Type 'exit' to stop.", file=logfile)

    try:
        tpc = getTPCServer()
    except ValueError as err:
        print(err)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {err}", file=logfile)
        logfile.close()
        sys.exit(1)

    while not stopServer.is_set():
        try:
            message = zmqSubSocket.recv_string(flags=zmq.NOBLOCK)
            message = message.split()
 
            text = f"{args.direc}/tpc{tpc}.txt"
            email = open(text, 'w', buffering=1)

            alertTimestamp = datetime.strptime(message[-1], "%Y.%m.%d.%H.%M.%S")
            print(f"{message[0]} alert received with timestamp: {alertTimestamp}")
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message[0]} alert received with timestamp: {alertTimestamp}", file=logfile)
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message[0]} alert received with timestamp: {alertTimestamp}", file=email)

            if message[0] == "SNEWS":
                startTimestamp = alertTimestamp - timedelta(minutes=10)
                endTimestamp = alertTimestamp + timedelta(minutes=50)
                print(f"Saving files in time window: {startTimestamp} -> {endTimestamp}")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Saving files in time window: {startTimestamp} -> {endTimestamp}", file=logfile)
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Saving files in time window: {startTimestamp} -> {endTimestamp}", file=email)

                for filename in os.listdir(args.direc):
                    if ((filename.endswith('SN.dat')) and (os.path.isfile(os.path.join(args.direc, filename)))):
                        filepath = os.path.join(args.direc, filename)
                        filetime = datetime.utcfromtimestamp(os.path.getmtime(filepath))
                        if startTimestamp <= filetime <= endTimestamp:
                            print(f"Transferring {filepath} to {host.replace('-daq', '.fnal.gov')} ...")
                            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Transferring {filepath} to {host.replace('-daq', '.fnal.gov')} ...", file=logfile)
                            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Transferring {filepath} to {host.replace('-daq', '.fnal.gov')} ...", file=email)

                            status = transferFile(filepath, host, f"{path}/{message[-1]}/TPC{tpc}")
                            if status.returncode == 0:
                                print("File transfer completed successfully")
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: File transfer completed successfully", file=logfile)
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: File transfer completed successfully", file=email)
                            else:
                                print("File transfer failed")
                                print("Error output:\n", status.stderr)
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: File transfer failed", file=logfile)
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error output:\n", status.stderr, file=logfile)
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: File transfer failed", file=email)
                                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error output:\n", status.stderr, file=email)

            email.close()
            status = transferFile(text, host, path)
            if status.returncode == 0:
                print("Notification transfer completed successfully")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Notification transfer completed successfully", file=logfile)
                subprocess.run(['rm', text], capture_output=True, text=True)
            else:
                print("Notification transfer failed")
                print("Error output:\n", status.stderr)
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Notification transfer failed", file=logfile)
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error output:\n", status.stderr, file=logfile)
        except UnicodeDecodeError:
            print("Could not decode message")
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Could not decode message", file=logfile)
        except zmq.Again:
            pass

    logfile.close()
