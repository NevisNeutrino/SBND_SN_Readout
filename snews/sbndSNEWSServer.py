import os
import sys
import time
import subprocess
import argparse
import zmq
import threading
import re
from datetime import datetime

def parseArguments():
    def checkFile(file):
        if not file.endswith(".log"):
            raise argparse.ArgumentTypeError(f"File to send must be a .log file")
        elif not os.access(file, os.R_OK):
            raise argparse.ArgumentTypeError(f"{file} can't be opened")
        return file

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--log", type=checkFile, required=True, help="log file")
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

def getTimestamp(filename):
    timestamps = []
    with open(f"{filename}", 'r') as file:
        for line in file:
            match = re.search(r"Time:\s+(.*)", line)
            if match:
                timestamp = datetime.strptime(match.group(1).split('.')[0], "%b %d %Y %H:%M:%S")
                timestamps.append(timestamp)
    return min(timestamps).strftime("%Y.%m.%d.%H.%M.%S") 

if __name__ == "__main__":
    args = parseArguments()
    logfile = open(args.log, 'a', buffering=1)
    
    context = zmq.Context()

    zmqPullSocket = context.socket(zmq.PULL)
    zmqPullSocket.bind(f"tcp://*:7910")

    zmqPubSocket = context.socket(zmq.PUB)
    zmqPubSocket.bind(f"tcp://*:7901")

    time.sleep(1)

    stopServer = threading.Event()
    threading.Thread(target=listenForExit, args=(stopServer,), daemon=True).start()

    path = '/data/SNEWSAlert'

    print(f"Listening to SNEWS alerts on port 7910. Type 'exit' to stop.")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Listening to SNEWS alerts on port 7910. Type 'exit' to stop.", file=logfile)

    while not stopServer.is_set():
        try:
            data = zmqPullSocket.recv_multipart(flags=zmq.NOBLOCK)
            if len(data) == 1:
                print(f"Received TEST alert from port 7910")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Received TEST alert from port 7910", file=logfile)

                content = data[0].decode('utf-8', errors='replace')

                timestamp = " ".join(content.split()[-2:])
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                timestamp = timestamp.strftime('%Y.%m.%d.%H.%M.%S')
                message = f"TEST ALERT: {timestamp}"

                zmqPubSocket.send_string(message)
                print(f"Published TEST alert timestamp to port 7901: {datetime.strptime(timestamp, '%Y.%m.%d.%H.%M.%S')}")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Published TEST alert timestamp to port 7901: {datetime.strptime(timestamp, '%Y.%m.%d.%H.%M.%S')}", file=logfile)
            else:
                print(f"Received SNEWS alert from port 7910")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Received SNEWS alert from port 7910", file=logfile)

                tempname = path + "/" + data[0].decode(errors='replace')
                content = data[1].decode('utf-8', errors='replace')

                with open(f"{tempname}", 'w', encoding='utf-8') as file:
                    file.write(content)

                timestamp = getTimestamp(tempname)

                filename = os.path.join(path, f"{timestamp}.txt")
                subprocess.run(['mv', tempname, filename], capture_output=True, text=True)
                print(f"Saved SNEWS alert in {filename}")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Saved SNEWS alert in {filename}", file=logfile)

                subprocess.run(['mkdir', f"{path}/{timestamp}"], capture_output=True, text=True)
                for tpc in range(1, 12):
                    subprocess.run(['mkdir', f"{path}/{timestamp}/TPC{tpc:02}"], capture_output=True, text=True)

                message = f"SNEWS ALERT: {timestamp}"
                zmqPubSocket.send_string(message)
                print(f"Published SNEWS alert timestamp to port 7901: {datetime.strptime(timestamp, '%Y.%m.%d.%H.%M.%S')}")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Published SNEWS alert timestamp to port 7901: {datetime.strptime(timestamp, '%Y.%m.%d.%H.%M.%S')}", file=logfile)
        except UnicodeDecodeError:
            print("Could not decode {filename}")
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Could not decode {filename}", file=logfile)
        except zmq.Again:
            pass

    logfile.close()
