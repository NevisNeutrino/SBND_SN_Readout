import os
import sys
import time
import glob
import subprocess
import argparse
import threading
import re
import psutil
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

def parseArguments():
    def checkFile(file):
        if not file.endswith(".log"):
            raise argparse.ArgumentTypeError(f"File to send must be a .log file")
        elif not os.access(file, os.R_OK):
            raise argparse.ArgumentTypeError(f"{file} can't be opened")
        return file

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--log", type=checkFile, required=True, help="log file")
    parser.add_argument('--test', action='store_true', help="enable test mode")
    args = parser.parse_args()

    return args

def listenForExit(stopServer):
    while True:
        cmd = input()
        if cmd.strip().lower() == "exit":
            stopServer.set()
            break

def checkNotifications(path):
    if not (os.path.isfile(f"{path}/tpc13.txt")):
        return False

    files = [os.path.join(path, f"tpc{tpc:02}.txt") for tpc in range(1, 12)]

    if not all(os.path.isfile(file) for file in files):
        return False

    open_files = set()
    for proc in psutil.process_iter(['open_files']):
        try:
            flist = proc.info['open_files']
            if flist:
                for f in flist:
                    open_files.add(f.path)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for file in files:
        if file in open_files:
            return False

    return True

if __name__ == "__main__":
    args = parseArguments()
    logfile = open(args.log, 'a', buffering=1)

    stopServer = threading.Event()
    threading.Thread(target=listenForExit, args=(stopServer,), daemon=True).start()

    localTZ = datetime.now().astimezone().tzinfo

    path = '/data/SNEWSAlert'
    
    sender = 'sbnd-tpc13.fnal.gov'
    if args.test:
        receiver = 'sbnd_test_channel-aaaaol6dbrolb2btuuvdsj7wdy@shortbaseline.slack.com'
        channel = '#sbnd_test_channel'
    else:
        receiver = 'sbnd-shift-operations-aaaak3ro3cjdguez5l7glmobwu@shortbaseline.slack.com'
        channel = '#sbnd-shift-operations'

    print(f"Checking for SNEWS alert notifications. Type 'exit' to stop.")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {localTZ}: Checking for SNEWS alert notifications. Type 'exit' to stop.", file=logfile)

    while not stopServer.is_set():
        if checkNotifications(path):
            print(f"Notifications received from SN processing server and all TPC servers")
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {localTZ}: Notifications received from SN processing server and all TPC servers", file=logfile)

            with open(f"{path}/tpc.txt", 'w', encoding='utf-8') as outFile:
                outFile.write('-' * 179)
                outFile.write('\nsbnd-tpc13.fnal.gov\n')
                outFile.write('-' * 179)
                with open(f"{path}/tpc13.txt", 'r', encoding='utf-8') as inFile:
                    outFile.write('\n')
                    content = inFile.read()
                    if "Received TEST alert from port 7910" in content:
                        subject = "TEST Alert Received from SBND SNEWS Alert System"
                        alert = "TEST"
                    elif "Received SNEWS alert from port 7910" in content:
                        subject = "SNEWS Alert Received from SBND SNEWS Alert System!!! PLEASE CONTACT TPC EXPERTS!!!"
                        alert = "SNEWS"
                    outFile.write(content)

                for tpc in range(1, 12):
                    outFile.write('\n')
                    outFile.write('-' * 179)
                    outFile.write(f"\nsbnd-tpc{tpc:02}.fnal.gov\n")
                    outFile.write('-' * 179)
                    with open(f"{path}/tpc{tpc:02}.txt", 'r', encoding='utf-8') as inFile:
                        outFile.write('\n')
                        content = inFile.read()
                        outFile.write(content)

            with open(f"{path}/tpc.txt", 'r', encoding='utf-8') as file:
                body = file.read()

            if args.test:
                subject = "THIS IS A TEST EMAIL FROM SBND SNEWS ALERT SYSTEM. PLEASE IGNORE."

            email = MIMEText(body, 'plain')
            email['Subject'] = subject
            email['From'] = sender
            email['To'] = receiver

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            try:
                with smtplib.SMTP('localhost') as server:
                    server.sendmail(sender, receiver, email.as_string())
                    server.quit()
                print(f"{alert} alert email notification to {channel} slack channel at {now} {localTZ} completed successfully")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {localTZ}: {alert} alert email notification to {channel} slack channel at {now} {localTZ} completed successfully", file=logfile)

                files = glob.glob(f"{path}/tpc*txt")
                result = subprocess.run(['rm'] + files, capture_output=True, text=True)
            except Exception as err:
                print(f"{alert} alert email notification to {channel} slack channel at {now} {localTZ} failed")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {localTZ}: {alert} alert email notification to {channel} slack channel at {now} {localTZ} failed", file=logfile)
                print("Error output:\n", err)
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {localTZ}: Error output:\n", err, file=logfile)
        else:
            pass

    logfile.close()
