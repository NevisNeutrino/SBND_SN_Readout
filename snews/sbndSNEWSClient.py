import os
import sys
import time
import argparse
import socket
import zmq
from datetime import datetime

def parseArguments():
    def checkFile(file):
        if not file.endswith(".txt"):
            raise argparse.ArgumentTypeError(f"File to send must be a .txt file")
        elif not os.access(file, os.R_OK):
            raise argparse.ArgumentTypeError(f"{file} can't be opened")
        return file

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--file", type=checkFile, help="file to send")
    parser.add_argument("--host", type=str, required=True, help="server hostname")
    parser.add_argument("--port", type=int, required=True, help="server port number")
    parser.add_argument('--test', action='store_true', help="enable test mode")

    args = parser.parse_args()
    if ((not args.test) and (not args.file)):
        parser.error("--file is required unless --test is set")

    if (not args.test): print("File to send: ", args.file)
    print("Server hostname: ", args.host)
    print("Server port number: ", args.port)
    if args.test: print("Test mode: ON")
    else: print("Test mode: OFF")

    return args

def openFile(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File {filename} not found")
    except IOError:
        raise IOError(f"Error: Issue opening file {filename}")
    except Exception as error:
        raise Exception(f"Error: Unexpected error occurred: {error}")

def checkConnection(host, port):
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except:
        return False

if __name__ == "__main__":
    args = parseArguments()
    
    if (not args.test):
        try:
            content = openFile(args.file)
        except Exception as error:
            print(error)
            sys.exit(1)

    context = zmq.Context()
    zmqPushSocket = context.socket(zmq.PUSH)

    if checkConnection(args.host, args.port):
        zmqPushSocket.connect(f"tcp://{args.host}:{args.port}")
        time.sleep(1)
    else:
        print(f"Can't connect to {args.host} on port {args.port}")
        sys.exit(1)

    if args.test:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        zmqPushSocket.send_string(f"TEST alert on {now}")
        print(f"Sent TEST alert on {now} to {args.host} on port {args.port}")
    else:
        zmqPushSocket.send_multipart([args.file.encode(), content.encode()])
        print(f"Sent {args.file} to {args.host} on port {args.port}")

    sys.exit(0)
