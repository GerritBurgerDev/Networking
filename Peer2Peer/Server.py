from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import *
from socket import *
import pyaudio
import struct
import time
import os
import pickle
import _thread
import ssl

BUFSIZ = 1024
PORT = 5000

clients = {}
users = {}
ip_to_name = {}
ip_to_sock = {}
addresses = {}
nickname = {}
ports = []

# Class that handles each connected client.
class client:
    def __init__(self, tcp_socket, ip):
        global users
        global ui

        self.tcp_socket = tcp_socket
        self.ip = ip
        ip_to_sock[ip] = tcp_socket
        name = self.tcp_socket.recv(BUFSIZ)
        if name == b'':
            return
        rec_array = pickle.loads(name)

        name = rec_array[0]

        while name in users:
            array = ["Nickname already in use, please try again!"]
            array = pickle.dumps(array)
            array = array.ljust(1024)
            self.tcp_socket.send(array)
            r_array = pickle.loads(self.tcp_socket.recv(BUFSIZ))
            name = r_array[0]

        self.name = name
        ip_to_name[ip] = name
        array = [1]
        array = pickle.dumps(array)
        array = array.ljust(1024)
        self.tcp_socket.send(array)
        clients[self.tcp_socket] = name
        nickname[name] = self.tcp_socket
        users[name] = addresses[self.tcp_socket]
        self.broadcast(users)
        self.handler()

    def send(self):
        filename = '/home/20023669/RW354/P2P/group34/Files/Dennis G. Zill - Differential Equations with Boundary-Value Problems, 8th Ed.pdf'
        self.filename = 'pOOper.txt'

        file_size = os.path.getsize(filename)
        self.filesize = file_size
        send = []
        send.append(self.filename)
        send.append(file_size)
        send = pickle.dumps(send).ljust(1024)
        self.tcp_socket.send(send)
        self.buffer_size = 1024

        file = open(filename, 'rb')
        data = file.read(self.buffer_size)
        while (data):
            self.tcp_socket.send(data)
            data = file.read(self.buffer_size)

    def broadcast(self, array):
        print("")
        """Broadcasts a message to all the clients."""
        array = pickle.dumps(array).ljust(1024)

        for sock in clients:
            sock.send(array)

    def broadcast_to(self, array):
        """Broadcasts a message to all the clients."""
        array = pickle.dumps(array).ljust(1024)

        for sock in clients:
            if addresses[sock] != self.ip:
                sock.send(array)

    def handler(self):

        while True:
            r = self.tcp_socket.recv(1024)

            if r == b'':
                pass
            else:
                r = pickle.loads(r)
                print("R", r)

                if r[0] == "search":
                    array = ["search", r[1], r[2]]
                    print("Client " + r[2] + " searched for file " + r[1])
                    self.broadcast_to(array)

                elif r[0] == "results":
                    sock = nickname[r[2]]
                    send = ["search_results", r[1], self.name]
                    sock.send(pickle.dumps(send).ljust(1024))

                    if len(r[1]) != 0:
                        for res in r[1]:
                            print("Result " + res + " was returned from " + self.name)
                    else:
                        print("No results found from user " + r[2])

                elif r[0] == "download":
                    port = ports.pop(1)
                    print(r[3] + " has requested to download " + r[1] + "from " + r[2])

                    sock = nickname[r[2]]
                    send = ["upload", port, r[1], addresses[nickname[r[3]]]]
                    sock.send(pickle.dumps(send).ljust(1024))

                if r[0] == "message":
                    fr = r[1]

                    if r[2][0] == "ev":
                        send = ["message", fr, "sOmEoNe FoUnD eAsTeRnEgGiE", r[3]]
                        self.broadcast(send)

                    else:

                        for user in r[2]:
                            send = ["message", fr, user, r[3]]
                            for sock in clients:
                                if clients[sock] == user:
                                    sock.send(pickle.dumps(send).ljust(1024))
                                    break

                elif r[0] == "busy_uploading":
                    print(ip_to_name[r[2]] + " is busy uploading, download not possible.")
                    sock = ip_to_sock[r[2]]
                    send = ["busy_uploading", ip_to_name[r[2]]]
                    sock.send(pickle.dumps(send).ljust(1024))

                elif r[0] == "accept_upload":
                    print(self.name + " has accepted to upload " + r[2] + " on port " + str(r[1]))
                    sock = ip_to_sock[r[3]]
                    send = ["accept_upload", r[1], r[2], self.ip]
                    sock.send(pickle.dumps(send).ljust(1024))

                elif r[0] == "pause_dl":
                    sock = ip_to_sock[r[1]]
                    send = ["pause_ul"]
                    sock.send(pickle.dumps(send).ljust(1024))

                elif r[0] == "resume_dl":
                    port = ports.pop(-1)
                    sock_ul = ip_to_sock[r[5]]
                    sock_dl = ip_to_sock[r[1]]
                    send = ["resume_ul", r[1], r[3], r[4], port]
                    sock_ul.send(pickle.dumps(send).ljust(1024))
                    send = ["resume_dl", port]
                    sock_dl.send(pickle.dumps(send).ljust(1024))

                elif r[0] == "{quit}":
                    name = ip_to_name[r[1]]
                    sock = ip_to_sock[r[1]]
                    print(name + " has quit the server.")
                    del users[name]
                    del clients[sock]
                    self.broadcast(users)


def get_ip():
    gw = os.popen("ip -4 route show default").read().split()
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect((gw[2], 0))
    receiver_ip = s.getsockname()[0]
    return receiver_ip

# Connects clients. 
def connect():
    server_ip = get_ip()
    tcpSocket = socket(AF_INET, SOCK_STREAM)
    tcpSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcpSocket.bind((server_ip, PORT))
    tcpSocket.listen(1)

    while True:
        newsocket, fromaddr = tcpSocket.accept()
        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        sslContext.set_ciphers(
            "NULL-SHA256 AES128-SHA256 AES256-SHA256 AES128-GCM-SHA256 AES256-GCM-SHA384 DH-RSA-AES128-SHA256 DH-RSA-AES256-SHA256 DH-RSA-AES128-GCM-SHA256 DH-RSA-AES256-GCM-SHA384 DH-DSS-AES128-SHA256 DH-DSS-AES256-SHA256 DH-DSS-AES128-GCM-SHA256 DH-DSS-AES256-GCM-SHA384 DHE-RSA-AES128-SHA256 DHE-RSA-AES256-SHA256 DHE-RSA-AES128-GCM-SHA256 DHE-RSA-AES256-GCM-SHA384 DHE-DSS-AES128-SHA256 DHE-DSS-AES256-SHA256 DHE-DSS-AES128-GCM-SHA256 DHE-DSS-AES256-GCM-SHA384 ECDHE-RSA-AES128-SHA256 ECDHE-RSA-AES256-SHA384 ECDHE-RSA-AES128-GCM-SHA256 ECDHE-RSA-AES256-GCM-SHA384 ECDHE-ECDSA-AES128-SHA256 ECDHE-ECDSA-AES256-SHA384 ECDHE-ECDSA-AES128-GCM-SHA256 ECDHE-ECDSA-AES256-GCM-SHA384 ADH-AES128-SHA256 ADH-AES256-SHA256 ADH-AES128-GCM-SHA256 ADH-AES256-GCM-SHA384 AES128-CCM AES256-CCM DHE-RSA-AES128-CCM DHE-RSA-AES256-CCM AES128-CCM8 AES256-CCM8 DHE-RSA-AES128-CCM8 DHE-RSA-AES256-CCM8 ECDHE-ECDSA-AES128-CCM ECDHE-ECDSA-AES256-CCM ECDHE-ECDSA-AES128-CCM8 ECDHE-ECDSA-AES256-CCM8")
        sslContext.load_dh_params("dhparam.pem")
        sslSocket = sslContext.wrap_socket(newsocket, server_side=True, )
        print("Client connected with IP addr: ", fromaddr[0])
        addresses[sslSocket] = fromaddr[0]
        _thread.start_new_thread(client, (sslSocket, fromaddr[0],))

# Creates pool of ports.
def create_ports():
    global ports
    ports = [i for i in range(8000, 8100)]


if __name__ == '__main__':
    create_ports()
    connect()
