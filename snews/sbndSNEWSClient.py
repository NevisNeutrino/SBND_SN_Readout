import os
import sys
import argparse
import socket
import zmq

def parseArguments():
    def checkFile(file):
        if not file.endswith(".txt"):
            raise argparse.ArgumentTypeError(f"File to send must be a .txt file")
        elif not os.access(file, os.R_OK):
            raise argparse.ArgumentTypeError(f"{file} can't be opened")
        return file

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--file", type=checkFile, required=True, help="file to send")
    parser.add_argument("--host", type=str, required=True, help="server hostname")
    parser.add_argument("--port", type=int, required=True, help="server port number")
    args = parser.parse_args()

    print("File to send: ", args.file)
    print("Server hostname: ", args.host)
    print("Server port number: ", args.port)

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
    
    try:
        content = openFile(args.file)
    except Exception as error:
        print(error)
        sys.exit(1)

    context = zmq.Context()
    zmqPushSocket = context.socket(zmq.PUSH)

    if checkConnection(args.host, args.port):
        zmqPushSocket.connect(f"tcp://{args.host}:{args.port}")
    else:
        print(f"Can't connect to {args.host} on port {args.port}")
        sys.exit(1)

    zmqPushSocket.send_multipart([args.file.encode(), content.encode()])
    print(f"Sent {args.file} to {args.host} on port {args.port}")

    sys.exit(0)
