import socket
import os
import Server
import Client
import sys
import threading

gw = os.popen("ip -4 route show default").read().split()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((gw[2], 0))
ip = s.getsockname()[0]
port = 5000

one = None
two = None

def runServer(ip, port):
    Server.run(str(ip), port)

def runClient(ip, port):
    Client.run(str(ip), port)

if __name__ == "__main__":
    one = threading.Thread(target=runServer, args=(ip, port))
    one.start()

    runClient(ip,port)
    sys.exit()
